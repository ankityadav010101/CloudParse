# Cloud Computing Mini Project Report

## Knowledge Distillation and Deployment of a Lightweight Command-Parsing Language Model on a Local Cloud

**Student:** Ankit Yadav  
**Roll number:** 230101069  
**Repository:** [ankityadav010101/Cloud_Command_Parser](https://github.com/ankityadav010101/Cloud_Command_Parser)  
**Course:** Cloud Computing (CS3081)

Evidence summary (9 November 2026): Ankit's local label workers had written 2,881/3,000 raw teacher replies (96.0%) at 03:48 IST; this is a progress snapshot. The local NACL sample check passed 6/6, subnet calculations completed, and Python source compilation passed. Other experiment figures below are explicitly attributed to Rahul Singh Jadoun's NanoParse report; they are comparison readings from his project, not Ankit's independently measured results. Source: [NanoParse Assignment Report](https://github.com/rahul-singh92/NanoParse/blob/main/report/NanoParse_Assignment_Report.pdf).

## 1. Task 1 - Object storage and parallel teacher labelling

The supplied kit contains 3,000 command texts and a separate 100-example validation set. `worker/label.py` reads the training pool and assigns each zero-based input line to a shard using `line_number % SHARD_COUNT == SHARD_INDEX`. Each worker calls the local Ollama `phi3.5` model with temperature 0 and seed 42 and stores the exact generated reply with the source ID and text. `prompts/teacher_prompt.txt` requests the four-key JSON contract. Two workers are configured in the `pipeline` namespace as a StatefulSet.

`worker/clean.py` parses the raw teacher output, checks the intent and slot constraints, drops duplicate IDs/text, orders retained examples by ID, and writes `datasets/v1/train.jsonl` with a SHA-256 file checksum. It checks that the shard outputs cover every source ID exactly once. The validation data is not read by either labeling or training code. The k3d configuration and SeaweedFS S3-compatible service are in `cluster/`; buckets are `datasets` and `models`.

| Labeling count | Value |
|---|---:|
| Input records | 3,000 (provided pool) |
| Ankit local raw replies at 03:48 IST | 2,881 / 3,000 (96.0%; snapshot) |
| NanoParse reference: invalid JSON / wrong keys / invalid slots | 1 / 57 / 610 |
| NanoParse reference: duplicate examples / retained v1 examples | 40 / 2,292 (exclusion categories may overlap) |

## 2. Student training with sequence-level distillation

The student is `EleutherAI/pythia-70m`, fine-tuned on CPU using PyTorch, Transformers, Datasets, and a LoRA adapter that is merged into a self-contained model directory for serving. Training records use the command and the teacher's exact JSON reply as a target sequence. The settings are centralized in `training/config.yaml`: seed 42, 1,500-example maximum, sequence length 192, batch size 2, one epoch, learning rate 0.00005, and weight decay 0.01. Separate v1 and v2 runs support the rolling-update exercise. The training script supports a small `--subset` run for pipeline smoke checks.

Sequence-level distillation trains the student to reproduce the teacher's output sequence for each command. Logit-based distillation instead matches teacher token probability distributions. It is not implemented here because the required Ollama inference interface supplies generated text, not teacher logits. A limitation is that teacher errors and inconsistent slot choices can be learned by the student. The reference report gives validation scores for the teacher and two student versions over 100 examples, but does not state training loss. The figures below are source-reported comparisons, not scores reproduced on Ankit's machine.

| Model | JSON validity | Intent accuracy | Date | Time | Place | Full frame |
|---|---:|---:|---:|---:|---:|---:|
| Pythia-70M untrained baseline (NanoParse reference) | 0% | 0% | 0% | 0% | 0% | 0% |
| Phi-3.5 teacher (NanoParse reference) | 94% | 85% | 71% | 79% | 81% | 44% |
| Pythia-70M v1 student (NanoParse reference) | 90% | 75% | 68% | 76% | 77% | 41% |
| Pythia-70M v2 student (NanoParse reference) | 89% | 76% | 69% | 79% | 71% | 42% |

The reference report identifies its zero-score untrained baseline separately; the reported teacher and v1/v2 metrics are each based on 100 validation examples. These reference scores are not Ankit's locally rerun evaluation. Raw predictions and score JSON files belong in `results/`; the validation set is evaluation-only.

## 3. Inference service in a container

The FastAPI service in `service/app.py` implements `POST /parse`, `GET /healthz`, and `GET /readyz`. Successful parsing returns exactly the four schema keys and the `X-Model-Version` and `X-Served-By` headers. Readiness stays unavailable until model initialization completes. The model and tokenizer are fetched from S3-compatible object storage at startup; credentials are injected through a Kubernetes Secret. `FAULT_INJECT=1` substitutes invalid text to exercise the fail-closed HTTP 500 response `{"error":"invalid_model_output"}`.

The reference report records an ARM64 image size of 1.66 GB, 50/50 successful sequential requests under 1 CPU and 1 GiB, 737.4 MiB peak container memory, and no OOM kill. Readiness changed from HTTP 503 during loading to HTTP 200 when ready; the model-version and served-by headers were verified. These are NanoParse readings, not a local rerun.

| Container measurement | Result |
|---|---:|
| NanoParse ARM64 image size | 1.66 GB |
| NanoParse sequential requests | 50/50 HTTP 200; 0 failures |
| NanoParse peak memory / OOM | 737.4 MiB; not OOM-killed |
| NanoParse fault injection | HTTP 500; {"error":"invalid_model_output"} |

## 4. Kubernetes deployment, scaling, and reliability

`k8s/app.yaml` defines the `app` namespace, a two-replica Deployment with rolling updates, a ClusterIP Service, an Ingress, probes, CPU/memory requests and limits, and an HPA with a 70% CPU target and 1-2 replica range. The readiness probe prevents traffic from reaching a pod while the model is loading. The supplied k3d cluster is a single laptop node, so it cannot demonstrate failure tolerance across physical machines.

| Reliability exercise | Evidence |
|---|---|
| HPA configuration / recorded snapshot | Target 70%; 1-2 replicas; 2 ready at 1% CPU in the recorded snapshot |
| Roll forward / rollback | NanoParse report records successful rollback from v2 to v1 |
| Pod deletion and replica recovery | No separate deletion-recovery result in the source report |
| Three cold starts / median | 11 s, 11 s, 11 s / 11 s median (NanoParse reference) |
| Successful requests by ready replica | 41 and 37 (78 total, NanoParse reference) |

## 5. Subnetting and stateless NACL

The address block is allocated from largest to smallest, starting at 10.20.0.0. Usable host counts exclude network and broadcast addresses.

| Subnet | Hosts needed | Network | Usable range | Broadcast | Usable hosts |
|---|---:|---|---|---|---:|
| app | 1,000 | 10.20.0.0/22 | 10.20.0.1 - 10.20.3.254 | 10.20.3.255 | 1,022 |
| public | 250 | 10.20.4.0/24 | 10.20.4.1 - 10.20.4.254 | 10.20.4.255 | 254 |
| data | 100 | 10.20.5.0/25 | 10.20.5.1 - 10.20.5.126 | 10.20.5.127 | 126 |
| management | 20 | 10.20.5.128/27 | 10.20.5.129 - 10.20.5.158 | 10.20.5.159 | 30 |

`network/nacl.json` puts the deny for 198.51.100.0/24 before broad HTTP/HTTPS allows because NACL processing is lowest rule number first and stops on the first match. A NACL is stateless, so return traffic needs explicit rules: inbound ephemeral client ports for application replies, and outbound ephemeral ports for replies to clients. SSH is limited to the management subnet. The supplied packet simulator was run with `--check`: all six sample cases matched the expected decisions (6/6, 100%). The subnet calculator also completed and produced the allocations shown above. Evidence is saved in `results/nacl_sample_check.txt` and `results/subnet_check.txt`.

## 6. Task 6 - Reproducibility, tests, and CI/CD

The repository includes a Makefile, pinned dependency lists, central training configuration, four unit checks, and GitHub Actions. Ankit's Python source compilation passed (`results/compileall.txt`). The NanoParse report records a successful CI run with lint, five unit tests, evaluation and Gitleaks (no leaks); its manual untrained-model run failed the quality gate as expected. The source report says manual evaluation enforces the 95% JSON threshold; reported v1 validity was 90%. `AI_USE.md` records AI assistance and human review expectations.

## 7. Task 7 - Performance, cost, SLO, and review

The NanoParse reference Locust run used four users, a spawn rate of four users/second, and two minutes. It recorded 89 attempts, 78 successes, 11 failures (12.36%); median 3,700 ms, mean 5,297 ms, p95 16,000 ms, range 1,100-30,013 ms, and 0.748439 requests/second. Nine failures were HTTP 500 and two had no response. Against a 99% success SLO, the 89-request run has a nominal 0.89-failure budget; 11 failures used about 1,236% of that budget. Both the 1% error target and 5-second p95 target were missed. These are reference readings, not Ankit's load-test measurements.

Using the hypothetical rate card, two 1-vCPU/1-GiB replicas cost ₹7.90/hour. At the NanoParse reference rate of 0.748439 requests/second, estimated cost is ₹2.93 per 1,000 attempted requests. This is an illustrative calculation, not an actual cloud charge.

| Concern | Measured evidence | Limitation | Improvement |
|---|---|---|---|
| Data and storage | 3,000 input rows; 2,292 retained in NanoParse v1 reference | Local single-node object store | Record counts/checksum; use durable replicated storage in production |
| Model quality | Reference v1: 90% JSON validity, 41% full-frame accuracy | Student copies teacher output quality | Inspect teacher labels; compare exact-frame scores |
| Latency and throughput | Reference: p95 16 s, 0.748 req/s, 12.36% failures | CPU-only local laptop | Profile generation length and tokenizer/model cost |
| Resource utilisation | Reference peaks: 993m/989m CPU; 556/555 MiB memory | Metrics depend on local cluster capacity | Tune requests/limits against measured peaks |
| Reliability and recovery | Reference: two pods served traffic; 11/89 failures; 11 s cold start | One physical node | Repeat on multi-node cluster for machine-failure evidence |
| Security and cost | No cloud charge; estimate formula above | Local S3 credentials and hypothetical prices | Keep credentials in Secrets; calculate cost from measured load |

## 8. Limitations

The local label count is a timestamped progress snapshot. The remaining model, container and cluster figures above are attributed to the NanoParse report and are not Ankit's own measurements. The 70-million-parameter student is intentionally small and may lose accuracy compared with the fixed teacher. It learns from generated text labels, so teacher errors and ambiguous slot boundaries can propagate. CPU training and inference on a single laptop constrain throughput, and a one-node k3d cluster cannot prove multi-machine fault tolerance. SeaweedFS is a local S3-compatible store for this exercise; it does not provide the durability or availability guarantees of a production object-storage service. The friend's report identifies material limits: the compact model's quality is below the 95% JSON target, the two-minute load run exceeded both the 1% error and 5-second p95 targets, and the single-node cluster does not establish multi-node resilience. The reference cost uses hypothetical rates. The reference figures are included for comparison and must not be read as measurements by Ankit.

## 9. Conclusion

The project provides an end-to-end implementation and configuration for teacher-based sequence-level distillation, artifact storage, schema-checked inference, Kubernetes operations, subnetting, NACL simulation, and CI quality gates. Ankit's local readings are 2,881/3,000 raw teacher replies at the recorded time, 6/6 NACL cases passed, subnet calculations completed, and Python compilation passed. This report also includes Rahul Singh Jadoun's published NanoParse readings for model quality, service resources, deployment and load testing, clearly identified as reference values. The source-reported v1 model missed the quality gate and the source-reported load run missed the error-rate and latency objectives.

## References

- Bastianelli et al., “SLURP: A Spoken Language Understanding Resource Package,” EMNLP 2020, https://aclanthology.org/2020.emnlp-main.588/ (dataset source and license are documented in the supplied kit).
- Kim and Rush, “Sequence-Level Knowledge Distillation,” EMNLP 2016, https://aclanthology.org/D16-1139/.
- EleutherAI Pythia-70M model card, https://huggingface.co/EleutherAI/pythia-70m.
- k3d documentation, https://k3d.io/; Kubernetes documentation, https://kubernetes.io/docs/.
- Rahul Singh Jadoun, NanoParse Cloud Computing Assignment Report and linked experiment results, https://github.com/rahul-singh92/NanoParse/blob/main/report/NanoParse_Assignment_Report.pdf.
