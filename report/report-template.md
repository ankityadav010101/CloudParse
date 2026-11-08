# Cloud Computing Mini Project Report

## Knowledge Distillation and Deployment of a Lightweight Command-Parsing Language Model on a Local Cloud

**Student:** Ankit Yadav  
**Roll number:** 230101069  
**Repository:** [ankityadav010101/Cloud_Command_Parser](https://github.com/ankityadav010101/Cloud_Command_Parser)  
**Course:** Cloud Computing (CS3081)

Evidence status: Source code and configuration are prepared. The Ollama labeling run, model training and scoring, container execution, Kubernetes reliability exercises, and Locust load test have not been run in the available environment. Their results are marked pending throughout this report. Replace pending items with measured outputs before final academic submission.

## 1. Task 1 - Object storage and parallel teacher labelling

The supplied kit contains 3,000 command texts and a separate 100-example validation set. `worker/label.py` reads the training pool and assigns each zero-based input line to a shard using `line_number % SHARD_COUNT == SHARD_INDEX`. Each worker calls the local Ollama `phi3.5` model with temperature 0 and seed 42 and stores the exact generated reply with the source ID and text. `prompts/teacher_prompt.txt` requests the four-key JSON contract. Two workers are configured in the `pipeline` namespace as a StatefulSet.

`worker/clean.py` parses the raw teacher output, checks the intent and slot constraints, drops duplicate IDs/text, orders retained examples by ID, and writes `datasets/v1/train.jsonl` with a SHA-256 file checksum. It checks that the shard outputs cover every source ID exactly once. The validation data is not read by either labeling or training code. The k3d configuration and SeaweedFS S3-compatible service are in `cluster/`; buckets are `datasets` and `models`.

| Labeling count | Value |
|---|---:|
| Input records | 3,000 (provided pool) |
| Invalid teacher JSON | Pending execution |
| Wrong key set | Pending execution |
| Invalid intent | Pending execution |
| Invalid slot | Pending execution |
| Duplicate records | Pending execution |
| Retained records | Pending execution |
| Clean training file SHA-256 | Pending execution |

## 2. Task 2 - Student training with sequence-level distillation

The student is `EleutherAI/pythia-70m`, fine-tuned on CPU using PyTorch, Transformers, Datasets, and a LoRA adapter that is merged into a self-contained model directory for serving. Training records use the command and the teacher's exact JSON reply as a target sequence. The settings are centralized in `training/config.yaml`: seed 42, 1,500-example maximum, sequence length 192, batch size 2, one epoch, learning rate 0.00005, and weight decay 0.01. Separate v1 and v2 runs support the rolling-update exercise. The training script supports a small `--subset` run for pipeline smoke checks.

Sequence-level distillation trains the student to reproduce the teacher's output sequence for each command. Logit-based distillation instead matches teacher token probability distributions. It is not implemented here because the required Ollama inference interface supplies generated text, not teacher logits. A limitation is that teacher errors and inconsistent slot choices can be learned by the student. Training losses and final model scores must be collected from actual runs.

| Model | JSON validity | Intent accuracy | Date | Time | Place | Full frame |
|---|---:|---:|---:|---:|---:|---:|
| Phi-3.5 teacher | Pending | Pending | Pending | Pending | Pending | Pending |
| Pythia-70M base | Pending | Pending | Pending | Pending | Pending | Pending |
| Fine-tuned student | Pending | Pending | Pending | Pending | Pending | Pending |

Raw predictions and score JSON files belong in `results/`. The validation set is evaluation-only and must not be used to create or edit training labels.

## 3. Task 3 - Inference service in a container

The FastAPI service in `service/app.py` implements `POST /parse`, `GET /healthz`, and `GET /readyz`. Successful parsing returns exactly the four schema keys and the `X-Model-Version` and `X-Served-By` headers. Readiness stays unavailable until model initialization completes. The model and tokenizer are fetched from S3-compatible object storage at startup; credentials are injected through a Kubernetes Secret. `FAULT_INJECT=1` substitutes invalid text to exercise the fail-closed HTTP 500 response `{"error":"invalid_model_output"}`.

The Dockerfile uses pinned Python dependencies and CPU-only PyTorch, and contains no model weights. The requested image-size check and 50 sequential requests under a 1 CPU / 1 GiB limit have not been run.

| Container measurement | Result |
|---|---:|
| Built image size | Pending build |
| 50-request completion | Pending run |
| Peak memory | Pending measurement |
| Fault-injection HTTP status/body | Pending run |

## 4. Task 4 - Kubernetes deployment, scaling, and reliability

`k8s/app.yaml` defines the `app` namespace, a two-replica Deployment with rolling updates, a ClusterIP Service, an Ingress, probes, CPU/memory requests and limits, and an HPA with a 70% CPU target and 1-2 replica range. The readiness probe prevents traffic from reaching a pod while the model is loading. The supplied k3d cluster is a single laptop node, so it cannot demonstrate failure tolerance across physical machines.

| Reliability exercise | Evidence |
|---|---|
| HPA scale from 1 to 2 and scale down | Pending run |
| Rolling update to v2 and rollback to v1 | Pending run |
| Pod deletion and replica recovery | Pending run |
| Three cold-start durations / median | Pending run |
| Requests served per ready replica | Pending load test |

## 5. Task 5 - Subnetting and stateless NACL

The address block is allocated from largest to smallest, starting at 10.20.0.0. Usable host counts exclude network and broadcast addresses.

| Subnet | Hosts needed | Network | Usable range | Broadcast | Usable hosts |
|---|---:|---|---|---|---:|
| app | 1,000 | 10.20.0.0/22 | 10.20.0.1 - 10.20.3.254 | 10.20.3.255 | 1,022 |
| public | 250 | 10.20.4.0/24 | 10.20.4.1 - 10.20.4.254 | 10.20.4.255 | 254 |
| data | 100 | 10.20.5.0/25 | 10.20.5.1 - 10.20.5.126 | 10.20.5.127 | 126 |
| management | 20 | 10.20.5.128/27 | 10.20.5.129 - 10.20.5.158 | 10.20.5.159 | 30 |

`network/nacl.json` puts the deny for 198.51.100.0/24 before broad HTTP/HTTPS allows because NACL processing is lowest rule number first and stops on the first match. A NACL is stateless, so return traffic needs explicit rules: inbound ephemeral client ports for application replies, and outbound ephemeral ports for replies to clients. SSH is limited to the management subnet. The supplied packet-simulator result should be attached after running `make nacl`.

## 6. Task 6 - Reproducibility, tests, and CI/CD

The repository includes a Makefile, pinned dependency lists, a central training configuration, four unit checks, and a GitHub Actions workflow. CI compiles Python sources, runs unit checks, downloads the v1 model release asset, evaluates it against the validation set, enforces at least 95% valid JSON, and runs a secret scan. The model package script emits a SHA-256 sidecar. The local clean-clone build, full workflow, deliberate quality-gate failure, and final release verification have not been run. Attach the corresponding workflow links and checksum comparison before submission. `AI_USE.md` records AI assistance and the required human review of generated code/labels.

## 7. Task 7 - Performance, cost, SLO, and review

Latency, throughput, error rate, and pod resources must be collected from the prescribed Locust run and `kubectl top pods`; no load test has been recorded yet. A proposed SLO is **99% successful requests during one standard two-minute load-test run**. If the run receives N requests, the error budget is `0.01 x N` failed requests; fill in N and observed failures from Locust.

Using the hypothetical rate card and manifest limits, one replica at 1 vCPU and 1 GiB is billed at `1 x (₹3.50 + ₹0.45) = ₹3.95 per hour`. Two continuously running replicas therefore cost ₹7.90 per hour under this exercise's assumptions. Cost per 1,000 requests is `₹7.90 / measured requests per hour x 1,000`; the measured request rate is pending. This is a hypothetical estimate, not an actual cloud charge.

| Concern | Measured evidence | Limitation | Improvement |
|---|---|---|---|
| Data and storage | Input pool: 3,000 rows; cleaned counts pending | Local single-node object store | Record counts/checksum; use durable replicated storage in production |
| Model quality | Validation scores pending | Student copies teacher output quality | Inspect teacher labels; compare exact-frame scores |
| Latency and throughput | Locust p50/p95/RPS pending | CPU-only local laptop | Profile generation length and tokenizer/model cost |
| Resource utilisation | Per-pod CPU/RAM pending | Metrics depend on local cluster capacity | Tune requests/limits against measured peaks |
| Reliability and recovery | HPA/rollout/cold-start evidence pending | One physical node | Repeat on multi-node cluster for machine-failure evidence |
| Security and cost | No cloud charge; estimate formula above | Local S3 credentials and hypothetical prices | Keep credentials in Secrets; calculate cost from measured load |

## 8. Limitations

The 70-million-parameter student is intentionally small and may lose accuracy compared with the fixed teacher. It learns from generated text labels, so teacher errors and ambiguous slot boundaries can propagate. CPU training and inference on a single laptop constrain throughput, and a one-node k3d cluster cannot prove multi-machine fault tolerance. SeaweedFS is a local S3-compatible store for this exercise; it does not provide the durability or availability guarantees of a production object-storage service. The API's generated output quality, startup time, image size, memory use, autoscaling, recovery, and latency remain unverified until the required runs are completed. Therefore, this report does not claim measured model or service performance.

## 9. Conclusion

The project provides an end-to-end implementation plan and code for teacher-based sequence-level distillation, artifact storage, schema-checked inference, Kubernetes operations, subnetting, NACL simulation, and CI quality gates. It also records the design choices and the evidence required by the assignment. Completion of the engineering implementation does not replace the outstanding experiments: run labeling and training, evaluate all three models, exercise the cluster and service, collect Locust and resource measurements, and update the pending fields before submitting the final report.

## References

- Bastianelli et al., “SLURP: A Spoken Language Understanding Resource Package,” EMNLP 2020, https://aclanthology.org/2020.emnlp-main.588/ (dataset source and license are documented in the supplied kit).
- Kim and Rush, “Sequence-Level Knowledge Distillation,” EMNLP 2016, https://aclanthology.org/D16-1139/.
- EleutherAI Pythia-70M model card, https://huggingface.co/EleutherAI/pythia-70m.
- k3d documentation, https://k3d.io/; Kubernetes documentation, https://kubernetes.io/docs/.
