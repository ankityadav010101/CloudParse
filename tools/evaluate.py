"""Generate raw model predictions for the held-out validation set and score them."""
import argparse
import json
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", type=Path, default=ROOT / "models/v1")
    parser.add_argument("--predictions", type=Path, default=ROOT / "results/student_predictions.jsonl")
    parser.add_argument("--gold", type=Path, default=ROOT / "data/validation.jsonl")
    args = parser.parse_args()
    tokenizer = AutoTokenizer.from_pretrained(args.model_dir)
    model = AutoModelForCausalLM.from_pretrained(args.model_dir)
    model.eval()
    args.predictions.parent.mkdir(parents=True, exist_ok=True)
    with args.gold.open(encoding="utf-8") as src, args.predictions.open("w", encoding="utf-8") as dst:
        for line in src:
            row = json.loads(line)
            prompt = f"Command: {row['text']}\nJSON:"
            inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=192)
            with torch.inference_mode():
                output = model.generate(**inputs, max_new_tokens=96, do_sample=False,
                                        pad_token_id=tokenizer.eos_token_id)
            raw = tokenizer.decode(output[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
            dst.write(json.dumps({"id": row["id"], "prediction": raw}, ensure_ascii=False) + "\n")
    # Reuse the supplied scoring implementation and preserve its quality-gate semantics.
    import subprocess, sys
    subprocess.run([sys.executable, str(ROOT / "tools/score.py"), str(args.predictions), str(args.gold),
                    "--out", str(ROOT / "results/student_validation.json"), "--min-validity", "95"],
                   check=True)


if __name__ == "__main__":
    main()
