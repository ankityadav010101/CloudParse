"""Generate immutable teacher-labelled shards with Ollama's local API."""
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def teacher_reply(command: str) -> str:
    prompt = (ROOT / "prompts/teacher_prompt.txt").read_text(encoding="utf-8").replace("{command}", command)
    body = json.dumps({"model": "phi3.5", "prompt": prompt, "stream": False,
                       "options": {"temperature": 0, "seed": 42, "num_predict": 128}}).encode()
    req = urllib.request.Request(os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate"),
                                 data=body, headers={"Content-Type": "application/json"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=180) as response:
                return json.loads(response.read())["response"]
        except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError):
            if attempt == 4:
                raise
            time.sleep(2 ** attempt)


def main():
    shard_index = int(os.environ.get("SHARD_INDEX", "0"))
    shard_count = int(os.environ.get("SHARD_COUNT", "1"))
    if shard_count < 1 or not 0 <= shard_index < shard_count:
        raise SystemExit("require SHARD_COUNT >= 1 and 0 <= SHARD_INDEX < SHARD_COUNT")
    source = ROOT / "data/commands_pool.jsonl"
    out = ROOT / f"datasets/teacher/shard-{shard_index}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    completed = set()
    if out.exists():
        with out.open(encoding="utf-8") as prior:
            for line in prior:
                try:
                    completed.add(json.loads(line)["id"])
                except (json.JSONDecodeError, KeyError):
                    continue
    with source.open(encoding="utf-8") as inp, out.open("a", encoding="utf-8") as dst:
        for line_no, line in enumerate(inp):
            if line_no % shard_count != shard_index:
                continue
            row = json.loads(line)
            if row["id"] in completed:
                continue
            raw = teacher_reply(row["text"])
            dst.write(json.dumps({"id": row["id"], "text": row["text"], "teacher_raw": raw}, ensure_ascii=False) + "\n")
            dst.flush()
            completed.add(row["id"])
            count += 1
    print(f"shard={shard_index}/{shard_count} records={count} path={out}")


if __name__ == "__main__":
    main()
