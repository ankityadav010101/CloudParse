"""CPU LoRA sequence-level distillation fine-tune for Pythia-70M."""
import argparse
import hashlib
import json
import os
import random
from pathlib import Path

import numpy as np
import torch
from datasets import Dataset
from peft import LoraConfig, get_peft_model
from transformers import (AutoModelForCausalLM, AutoTokenizer, Trainer,
                          TrainingArguments, set_seed)

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subset", type=int)
    ap.add_argument("--version", default="v1")
    args = ap.parse_args()
    cfg = __import__("yaml").safe_load((ROOT / "training/config.yaml").read_text())
    seed = int(cfg["seed"])
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed); set_seed(seed)
    rows = [json.loads(x) for x in (ROOT / "datasets/v1/train.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    rows = rows[:min(args.subset or cfg["max_examples"], cfg["max_examples"])]
    if not rows:
        raise SystemExit("No cleaned teacher data. Run the label workers and worker/clean.py first.")
    model_name = cfg["model_name"]
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.pad_token = tokenizer.eos_token
    examples = [{"text": f"Command: {r['text']}\nJSON: {json.dumps(r['label'], ensure_ascii=False, separators=(',', ':'))}{tokenizer.eos_token}"} for r in rows]
    dataset = Dataset.from_list(examples)
    def encode(batch):
        tok = tokenizer(batch["text"], truncation=True, max_length=cfg["max_length"], padding="max_length")
        tok["labels"] = [ids.copy() for ids in tok["input_ids"]]
        return tok
    dataset = dataset.map(encode, batched=True, remove_columns=["text"])
    model = AutoModelForCausalLM.from_pretrained(model_name)
    model.config.pad_token_id = tokenizer.pad_token_id
    model = get_peft_model(model, LoraConfig(r=8, lora_alpha=16, lora_dropout=0.05,
                                               target_modules=["query_key_value"], task_type="CAUSAL_LM"))
    output = ROOT / "training/output"
    train_args = TrainingArguments(output_dir=str(output), num_train_epochs=cfg["epochs"],
        learning_rate=cfg["learning_rate"], per_device_train_batch_size=cfg["batch_size"],
        weight_decay=cfg["weight_decay"], logging_steps=cfg["logging_steps"], save_steps=cfg["save_steps"],
        save_strategy="epoch", report_to=[], use_cpu=True, seed=seed, data_seed=seed,
        dataloader_num_workers=0, fp16=False, bf16=False)
    Trainer(model=model, args=train_args, train_dataset=dataset).train()
    destination = ROOT / f"models/{args.version}"
    destination.mkdir(parents=True, exist_ok=True)
    model = model.merge_and_unload()
    model.save_pretrained(destination, safe_serialization=True)
    tokenizer.save_pretrained(destination)
    (destination / "base_model.json").write_text(json.dumps({"base_model": model_name, "adapter": False,
        "seed": seed, "examples": len(rows), "version": args.version}, indent=2) + "\n")
    manifest = []
    for path in sorted(destination.rglob("*")):
        if path.is_file() and path.name != "model.sha256":
            manifest.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(destination).as_posix()}")
    (destination / "model.sha256").write_text("\n".join(manifest) + "\n", encoding="ascii")
    print(f"Saved {args.version} to {destination}; merge adapter before service export if needed.")


if __name__ == "__main__":
    main()
