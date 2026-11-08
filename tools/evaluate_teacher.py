"""Score the specified local Ollama teacher on held-out validation commands."""
import json
import subprocess
import sys
from pathlib import Path

from worker.label import teacher_reply

ROOT = Path(__file__).resolve().parents[1]


def main():
    gold = ROOT / "data/validation.jsonl"
    predictions = ROOT / "results/teacher_predictions.jsonl"
    predictions.parent.mkdir(parents=True, exist_ok=True)
    with gold.open(encoding="utf-8") as source, predictions.open("w", encoding="utf-8") as target:
        for line in source:
            row = json.loads(line)
            raw = teacher_reply(row["text"])
            target.write(json.dumps({"id": row["id"], "prediction": raw}, ensure_ascii=False) + "\n")
    subprocess.run([sys.executable, str(ROOT / "tools/score.py"), str(predictions), str(gold),
                    "--out", str(ROOT / "results/teacher_validation.json")], check=True)


if __name__ == "__main__":
    main()
