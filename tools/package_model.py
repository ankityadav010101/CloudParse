"""Build a versioned tarball and SHA-256 manifest for a GitHub Release asset."""
import argparse
import hashlib
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("version", choices=("v1", "v2"))
    args = parser.parse_args()
    source = ROOT / "models" / args.version
    if not source.is_dir() or not any(source.iterdir()):
        raise SystemExit(f"trained model directory is empty: {source}")
    output = ROOT / "results" / f"{args.version}-model.tar.gz"
    output.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(output, "w:gz") as archive:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                archive.add(path, arcname=path.relative_to(source).as_posix())
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(output.suffix + ".sha256").write_text(f"{digest}  {output.name}\n", encoding="ascii")
    print(output)
    print(f"SHA-256 {digest}")


if __name__ == "__main__":
    main()
