import json
import os
import re
import socket
from pathlib import Path

import boto3
import torch
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
from jsonschema import Draft202012Validator

app = FastAPI(title="Cloud Command Parser", version="1.0.0")
MODEL_VERSION = os.getenv("MODEL_VERSION", "v1")
MODEL_DIR = Path(os.getenv("MODEL_DIR", "/var/lib/model"))
MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "96"))
FAULT_INJECT = os.getenv("FAULT_INJECT", "0") == "1"
SCHEMA_PATH = Path(os.getenv("SCHEMA_PATH", "/app/data/schema.json"))
schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8")) if SCHEMA_PATH.exists() else None
model = tokenizer = None


class ParseRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


def _download_model():
    uri = os.environ.get("MODEL_URI")
    if not uri or not uri.startswith("s3://"):
        raise RuntimeError("MODEL_URI must be s3://bucket/prefix")
    bucket, _, prefix = uri[5:].partition("/")
    client = boto3.client("s3", endpoint_url=os.getenv("S3_ENDPOINT"))
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    response = client.list_objects_v2(Bucket=bucket, Prefix=prefix.rstrip("/") + "/")
    objects = response.get("Contents", [])
    if not objects:
        raise RuntimeError(f"no model objects found at {uri}")
    for item in objects:
        key = item["Key"]
        relative = key[len(prefix.rstrip("/")) + 1:]
        target = MODEL_DIR / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        client.download_file(bucket, key, str(target))


@app.on_event("startup")
def load_model():
    global model, tokenizer
    if not MODEL_DIR.exists() or not any(MODEL_DIR.iterdir()):
        _download_model()
    meta = json.loads((MODEL_DIR / "base_model.json").read_text(encoding="utf-8"))
    base_path = MODEL_DIR if not meta.get("adapter") else meta["base_model"]
    base = AutoModelForCausalLM.from_pretrained(base_path)
    model = PeftModel.from_pretrained(base, MODEL_DIR) if meta.get("adapter") else base
    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
    model.eval()


def _extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("model did not return JSON")
    obj = json.loads(match.group(0))
    if schema:
        errors = list(Draft202012Validator(schema["json_schema"]).iter_errors(obj))
        if errors:
            raise ValueError("model JSON does not match schema")
    return obj


def parse_command(text: str) -> dict:
    if model is None or tokenizer is None:
        raise RuntimeError("model is not ready")
    prompt = f"Command: {text}\nJSON:"
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=192)
    with torch.inference_mode():
        output = model.generate(**inputs, max_new_tokens=MAX_NEW_TOKENS, do_sample=False,
                                pad_token_id=tokenizer.eos_token_id)
    generated = tokenizer.decode(output[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
    if FAULT_INJECT:
        generated = "not json"
    return _extract_json(generated)


@app.post("/parse")
def parse(payload: ParseRequest):
    try:
        result = parse_command(payload.text)
    except Exception as exc:
        if isinstance(exc, (ValueError, json.JSONDecodeError)):
            return JSONResponse(status_code=500, content={"error": "invalid_model_output"})
        raise HTTPException(status_code=503, detail={"error": "model_unavailable"}) from exc
    return result


@app.get("/healthz")
def healthz():
    return {"status": "alive"}


@app.get("/readyz")
def readyz():
    if model is None:
        raise HTTPException(status_code=503, detail="model is loading")
    return {"status": "ready"}


@app.middleware("http")
async def response_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Model-Version"] = MODEL_VERSION
    response.headers["X-Served-By"] = socket.gethostname()
    return response
