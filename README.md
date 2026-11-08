# Cloud Command Parser - Knowledge Distillation Mini Project

This repository implements the assignment brief using the supplied student kit. It trains a Pythia-70M student on exact JSON replies generated locally by Ollama Phi-3.5, then serves the model through FastAPI on a local k3d cluster. SeaweedFS provides the S3-compatible object store. The project uses the supplied 3,000-command pool and keeps `data/validation.jsonl` out of labeling and training.

## Repository map

- `data/`, `tools/score.py`, `tools/nacl_sim.py`, `tools/locustfile.py`: unmodified assignment kit inputs and evaluators.
- `prompts/`, `worker/`: teacher labeling shards and deterministic cleaning.
- `training/`: pinned training settings and CPU LoRA sequence-level fine-tuning.
- `service/`, `Dockerfile`: inference API image; model weights are loaded from object storage at startup.
- `cluster/`, `k8s/`, `network/`: local cluster, SeaweedFS, app deployment, subnet plan, and NACL.
- `.github/workflows/ci.yml`, `tests/`, `Makefile`: validation and repeatable commands.
- `report/report-template.md`: evidence-first report outline. Replace placeholders with measurements.

## Prerequisites

Install Docker, k3d, kubectl, Ollama, Python 3.11, and GNU Make. Pull the fixed teacher once with `ollama pull phi3.5`. Install CPU PyTorch with `python -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.3.1`, then install the remaining project dependencies with `python -m pip install -r requirements.txt`. Fine-tuning and inference use CPU-only settings. The dataset labeling and training stages can take hours; model download and cluster image builds also require network access.

## End-to-end order

1. Create the local cluster and object store: `make up`. In another terminal run `make port-forward`; keep that port-forward active. Set `S3_ENDPOINT=http://localhost:8333` and credentials if the local S3 configuration requires them, then upload the source commands to the `datasets` bucket with `python tools/publish.py --dataset`.
2. Build the worker image and start the two parallel teacher shards: `make label`. Ollama must be running on the host. The workers use temperature 0 and seed 42 from the committed prompt/settings.
3. Monitor the pods with `kubectl -n pipeline get pods`. Once both shard files have been written, retrieve them with `make pull-labels`. The PVC is persistent for the cluster lifetime. Then clean and checksum: `make clean-data`. The cleaner fails if shard IDs do not cover every input command exactly once.
4. Train and save two versions, using separate invocations to manage memory: `make train SUBSET=50`, then `make train`; `make train-v2` creates a second version. Remove `SUBSET=50` for the final model. Configuration is in `training/config.yaml`.
5. Upload cleaned data or model files: `python tools/publish.py --dataset`, `python tools/publish.py --model-version v1`, and repeat for v2. Before uploading, set `S3_ENDPOINT` to the forwarded SeaweedFS S3 endpoint (for example `http://localhost:8333`) and provide local S3 credentials if your SeaweedFS configuration requires them.
6. Evaluate teacher and base/student models on the held-out file and preserve raw outputs under `results/`. Run `python tools/evaluate_teacher.py` for the teacher, `python tools/evaluate.py --model-dir EleutherAI/pythia-70m --predictions results/base_predictions.jsonl` for the untrained base, and `python tools/evaluate.py --model-dir models/v1` for the student. Do not use validation examples to edit training labels or tune training data.
7. Package a release asset with `python tools/package_model.py v1`. Publish `results/v1-model.tar.gz` as the `v1` GitHub Release asset; CI downloads this exact asset and applies the >=95% JSON-validity gate.
8. Create the namespace and local Secret before starting the deployment: `kubectl create namespace app --dry-run=client -o yaml | kubectl apply -f -`, then `kubectl create secret generic object-store -n app --from-literal=AWS_ACCESS_KEY_ID="$env:AWS_ACCESS_KEY_ID" --from-literal=AWS_SECRET_ACCESS_KEY="$env:AWS_SECRET_ACCESS_KEY"` in PowerShell (use `$AWS_ACCESS_KEY_ID` syntax in bash). Provide credentials outside Git. Build and deploy the API with `make deploy`.
9. Run `make nacl`, then the supplied Locust command against the Ingress at `http://localhost:8080`. Record the actual load, resource, recovery, and cold-start evidence in `report/report-template.md` and copy command output to `results/`.
10. Tear down with `make destroy` when finished.

## Submission report

The personalized PDF is at `report/report.pdf`; its source is `report/report-template.md` and the reproducible builder is `report/build_report.py` (`make report`). It includes Ankit Yadav, roll number 230101069, and the specified GitHub repository. Operational result fields remain pending until the local labeling, training, deployment, and load-test runs produce evidence.

## API contract

- `POST /parse` with `{"text":"..."}` returns only `intent`, `date`, `time`, and `place` on success.
- Invalid model JSON or schema output returns HTTP 500 with `{"error":"invalid_model_output"}`.
- `GET /healthz` reports process liveness; `GET /readyz` remains 503 until startup has loaded the model.
- Successful and error responses include `X-Model-Version` and `X-Served-By` headers.
- `FAULT_INJECT=1` exercises the invalid-output path.

The model is a small baseline, not a general-purpose assistant. If the tokenizer fails to produce valid JSON, the service fails closed. The single-node local cluster cannot demonstrate machine-level fault tolerance. The report must state this and use observed measurements only.

## Repeatable development commands

`make up`, `make label`, `make clean-data`, `make train SUBSET=50`, `make image`, `make deploy`, `make nacl`, `make down`. The `make lint` target compiles and runs unit tests. CI includes linting, unit checks, released-model evaluation, a strict JSON-validity quality gate, and secret scanning. The `v1` release asset must exist before the model-evaluation job can pass.
