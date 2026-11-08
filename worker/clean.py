"""Validate generated shards and create an ordered, checksummed training set."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEYS = {"intent", "date", "time", "place"}
INTENTS = {"alarm_set", "alarm_query", "calendar_set", "calendar_query", "calendar_remove",
           "weather_query", "datetime_query", "recommendation_events"}
SLOTS = ("date", "time", "place")


def main():
    records = []
    seen_ids, seen_text = set(), set()
    counts = {"invalid_json": 0, "wrong_keys": 0, "invalid_intent": 0, "invalid_slot": 0, "duplicates": 0}
    shard_files = sorted((ROOT / "datasets/teacher").glob("shard-*.jsonl"))
    input_rows = [json.loads(line) for line in (ROOT / "data/commands_pool.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    expected_ids = [row["id"] for row in input_rows]
    shard_ids = []
    for shard in shard_files:
        for line in shard.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                counts["invalid_json"] += 1
                continue
            if not all(k in row for k in ("id", "text", "teacher_raw")):
                counts["invalid_json"] += 1
                continue
            shard_ids.append(row["id"])
            try:
                label = json.loads(row["teacher_raw"])
            except (TypeError, json.JSONDecodeError):
                counts["invalid_json"] += 1
                continue
            if not isinstance(label, dict) or set(label) != KEYS:
                counts["wrong_keys"] += 1
                continue
            if not isinstance(label["intent"], str) or label["intent"] not in INTENTS:
                counts["invalid_intent"] += 1
                continue
            if any(v is not None and (not isinstance(v, str) or v.lower() not in row["text"].lower()) for v in (label[s] for s in SLOTS)):
                counts["invalid_slot"] += 1
                continue
            if row["id"] in seen_ids or row["text"] in seen_text:
                counts["duplicates"] += 1
                continue
            seen_ids.add(row["id"])
            seen_text.add(row["text"])
            records.append({"id": row["id"], "text": row["text"], "label": label})
    records.sort(key=lambda r: r["id"])
    out = ROOT / "datasets/v1/train.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    with out.open("wb") as f:
        for record in records:
            line = (json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
            f.write(line)
            digest.update(line)
    (out.parent / "train.sha256").write_text(f"{digest.hexdigest()}  train.jsonl\n", encoding="ascii")
    counts.update(input=len(input_rows), kept=len(records))
    if sorted(shard_ids) != sorted(expected_ids):
        raise SystemExit(f"Shard coverage error: expected {len(expected_ids)} records exactly once; found {len(shard_ids)}. Check SHARD_INDEX/SHARD_COUNT and rerun missing shards.")
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()
