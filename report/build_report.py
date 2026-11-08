"""Build the submission report PDF from the evidence documented in this project."""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (BaseDocTemplate, Frame, PageBreak, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "report/report.pdf"
NAVY = colors.HexColor("#16324F")
TEAL = colors.HexColor("#187C80")
PALE = colors.HexColor("#EAF1F5")
MUTED = colors.HexColor("#536575")


def styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle(name="CoverTitle", parent=s["Title"], fontName="Helvetica-Bold",
        fontSize=23, leading=28, textColor=NAVY, alignment=TA_LEFT, spaceAfter=12))
    s.add(ParagraphStyle(name="Subtitle", parent=s["Normal"], fontName="Helvetica",
        fontSize=12, leading=17, textColor=TEAL, spaceAfter=16))
    s.add(ParagraphStyle(name="Heading1x", parent=s["Heading1"], fontName="Helvetica-Bold",
        fontSize=16, leading=20, textColor=NAVY, spaceBefore=5, spaceAfter=8, keepWithNext=True))
    s.add(ParagraphStyle(name="Heading2x", parent=s["Heading2"], fontName="Helvetica-Bold",
        fontSize=11, leading=14, textColor=TEAL, spaceBefore=7, spaceAfter=4, keepWithNext=True))
    s.add(ParagraphStyle(name="Bodyx", parent=s["BodyText"], fontName="Helvetica",
        fontSize=9, leading=13, textColor=colors.HexColor("#263746"), spaceAfter=6))
    s.add(ParagraphStyle(name="Smallx", parent=s["BodyText"], fontName="Helvetica",
        fontSize=7.5, leading=10, textColor=colors.HexColor("#263746"), spaceAfter=2))
    s.add(ParagraphStyle(name="Cell", parent=s["BodyText"], fontName="Helvetica",
        fontSize=7.4, leading=9.2, textColor=colors.HexColor("#263746")))
    s.add(ParagraphStyle(name="CellHead", parent=s["Cell"], fontName="Helvetica-Bold",
        textColor=colors.white))
    s.add(ParagraphStyle(name="Linkx", parent=s["Smallx"], textColor=TEAL))
    return s


def para(text, style):
    return Paragraph(text, style)


def table(rows, widths, st, header=True):
    data = []
    for ri, row in enumerate(rows):
        ps = st["CellHead"] if header and ri == 0 else st["Cell"]
        data.append([Paragraph(str(cell), ps) for cell in row])
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    cmds = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#C8D4DE")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if header:
        cmds.append(("BACKGROUND", (0, 0), (-1, 0), NAVY))
        for i in range(1, len(rows)):
            if i % 2 == 0:
                cmds.append(("BACKGROUND", (0, i), (-1, i), PALE))
    t.setStyle(TableStyle(cmds))
    return t


def page(canvas, doc):
    canvas.saveState()
    width, height = A4
    canvas.setStrokeColor(colors.HexColor("#D6E0E7"))
    canvas.setLineWidth(0.6)
    canvas.line(18 * mm, height - 15 * mm, width - 18 * mm, height - 15 * mm)
    canvas.setFont("Helvetica-Bold", 7.5)
    canvas.setFillColor(NAVY)
    canvas.drawString(18 * mm, height - 11.7 * mm, "CLOUD COMPUTING | MINI PROJECT")
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawRightString(width - 18 * mm, height - 11.7 * mm, "Ankit Yadav | 230101069")
    canvas.line(18 * mm, 14 * mm, width - 18 * mm, 14 * mm)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(18 * mm, 9.5 * mm, "Cloud Command Parser - evidence report")
    canvas.drawRightString(width - 18 * mm, 9.5 * mm, f"Page {doc.page}")
    canvas.restoreState()


def build():
    st = styles()
    doc = BaseDocTemplate(str(OUT), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
                         topMargin=22 * mm, bottomMargin=20 * mm, title="Cloud Command Parser Project Report",
                         author="Ankit Yadav")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
    doc.addPageTemplates(PageTemplate(id="report", frames=[frame], onPage=page))
    story = []

    story += [Spacer(1, 18 * mm), para("Cloud Computing Mini Project", st["CoverTitle"]),
        para("Knowledge Distillation and Deployment of a Lightweight Command-Parsing Language Model on a Local Cloud", st["Subtitle"]),
        table([["STUDENT", "ROLL NUMBER", "COURSE"],
               ["Ankit Yadav", "230101069", "Cloud Computing (CS3081)"]],
              [56 * mm, 48 * mm, 70 * mm], st, header=True),
        Spacer(1, 3 * mm), para('Repository: <link href="https://github.com/ankityadav010101/Cloud_Command_Parser" color="#187C80">github.com/ankityadav010101/Cloud_Command_Parser</link>', st["Bodyx"]), Spacer(1, 5 * mm),
        para("Project summary", st["Heading1x"]),
        para("This project builds a constrained natural-language command parser that maps one short English command to a four-key JSON object. The implementation combines local teacher labeling, sequence-level student fine-tuning, an S3-compatible model store, a containerized API, and a local Kubernetes deployment. It uses only the supplied command pool for training; the supplied validation set is reserved for evaluation.", st["Bodyx"]),
        para("Evidence status: Source code and configuration are prepared. The Ollama labeling run, model training and scoring, container execution, Kubernetes reliability exercises, and Locust load test have not been run in the available environment. Their results are marked pending throughout this report. Replace pending items with measured outputs before final academic submission.", st["Bodyx"]),
        para("Architecture", st["Heading2x"]),
        para("3,000 command pool -> parallel Ollama Phi-3.5 workers -> validated and checksummed teacher dataset -> CPU fine-tuned Pythia-70M -> model artifact in SeaweedFS -> FastAPI container -> k3d Ingress and Kubernetes Deployment. Validation rows are used only by the teacher/base/student evaluators.", st["Bodyx"]),
        para("1. Task 1 - Object storage and parallel teacher labeling", st["Heading1x"]),
        para("The worker assigns each zero-based source line to one shard using line_number modulo SHARD_COUNT. The fixed Ollama phi3.5 teacher is called with temperature 0 and seed 42. Each raw response is saved with its source ID and text. The prompt requests exactly intent, date, time, and place. Two label workers are configured in a StatefulSet in the pipeline namespace.", st["Bodyx"]),
        para("The cleaner validates JSON, exact keys, intent membership, and slot text copied from the original command; it removes duplicate IDs/text, orders examples by ID, writes datasets/v1/train.jsonl, and records a SHA-256 checksum. It verifies complete one-time source ID coverage. SeaweedFS provides datasets and models buckets. Validation data is not read by labeling or training code.", st["Bodyx"]),
        table([["Labeling count", "Value"], ["Input records", "3,000 (provided pool)"],
               ["Invalid teacher JSON / wrong keys", "Pending labeling run"],
               ["Invalid intent / invalid slot", "Pending labeling run"],
               ["Duplicates / retained records", "Pending labeling run"],
               ["train.jsonl SHA-256", "Pending cleaning run"]], [80 * mm, 94 * mm], st),
        PageBreak()]

    story += [para("2. Task 2 - Student training with sequence-level distillation", st["Heading1x"]),
        para("The student base model is EleutherAI/pythia-70m. Training uses CPU PyTorch, Transformers, Datasets, and a LoRA adapter, merged into the saved model directory so the inference service can download a self-contained artifact. Each example contains the command followed by the teacher's exact JSON reply. Configuration is centralized in training/config.yaml: seed 42, up to 1,500 examples, maximum length 192, batch size 2, one epoch, learning rate 0.00005, and weight decay 0.01. Separate v1 and v2 versions are supported.", st["Bodyx"]),
        para("Sequence-level distillation teaches the student to reproduce the teacher's output sequence for an input command. Logit-based distillation instead matches teacher token probability distributions. It is not implemented because the required Ollama interface returns generated text rather than teacher logits. A limitation is that the student can learn teacher mistakes and inconsistent labels.", st["Bodyx"]),
        table([["Model", "JSON validity", "Intent", "Date", "Time", "Place", "Full frame"],
               ["Phi-3.5 teacher", "Pending", "Pending", "Pending", "Pending", "Pending", "Pending"],
               ["Pythia-70M base", "Pending", "Pending", "Pending", "Pending", "Pending", "Pending"],
               ["Fine-tuned student", "Pending", "Pending", "Pending", "Pending", "Pending", "Pending"]],
              [38 * mm, 22 * mm, 20 * mm, 18 * mm, 18 * mm, 18 * mm, 26 * mm], st),
        para("Run tools/evaluate_teacher.py and tools/evaluate.py for each model, preserve raw outputs under results/, and use tools/score.py for the six assignment metrics. Never use the validation set to edit teacher labels or training data. Training loss and model scores remain pending until actual runs are complete.", st["Bodyx"]),
        para("3. Task 3 - Inference service in a container", st["Heading1x"]),
        para("service/app.py exposes POST /parse, GET /healthz, and GET /readyz. Successful output contains exactly the schema's four keys and includes X-Model-Version and X-Served-By headers. Readiness remains unavailable until model loading completes. At startup the service retrieves model and tokenizer files from S3-compatible storage; credentials are provided through a Kubernetes Secret. FAULT_INJECT=1 exercises the fail-closed HTTP 500 body {\"error\":\"invalid_model_output\"}.", st["Bodyx"]),
        para("The Docker image uses pinned Python dependencies and CPU-only PyTorch; it does not include model weights. The required image-size and 50 sequential-request checks under 1 CPU and 1 GiB have not been run.", st["Bodyx"]),
        table([["Container measurement", "Evidence"], ["Image size", "Pending image build"],
               ["50 sequential requests", "Pending run"], ["Peak memory", "Pending measurement"],
               ["Fault injection status/body", "Pending run"]], [65 * mm, 109 * mm], st),
        para("4. Task 4 - Kubernetes deployment, scaling, and reliability", st["Heading1x"]),
        para("k8s/app.yaml defines the app namespace, two-replica Deployment, rolling update strategy, Service, Ingress, liveness/readiness/startup probes, CPU and memory requests/limits, and HPA targeting 70% CPU with one to two replicas. Readiness prevents traffic from reaching a pod while the model is loading. The k3d setup has one laptop node and cannot demonstrate physical machine fault tolerance.", st["Bodyx"]),
        table([["Reliability exercise", "Evidence"], ["HPA scale up/down", "Pending run"],
               ["Roll forward to v2 and rollback to v1", "Pending run"],
               ["Pod recovery", "Pending run"], ["Three cold starts and median", "Pending run"],
               ["Traffic per ready replica", "Pending load test"]], [85 * mm, 89 * mm], st),
        PageBreak()]

    story += [para("5. Task 5 - Subnetting and stateless NACL", st["Heading1x"]),
        para("The 10.20.0.0/16 block is allocated from largest requirement to smallest. Usable host counts exclude the network and broadcast addresses.", st["Bodyx"]),
        table([["Subnet", "Needed", "Network", "Usable range", "Broadcast", "Usable"],
               ["app", "1,000", "10.20.0.0/22", "10.20.0.1 - 10.20.3.254", "10.20.3.255", "1,022"],
               ["public", "250", "10.20.4.0/24", "10.20.4.1 - 10.20.4.254", "10.20.4.255", "254"],
               ["data", "100", "10.20.5.0/25", "10.20.5.1 - 10.20.5.126", "10.20.5.127", "126"],
               ["management", "20", "10.20.5.128/27", "10.20.5.129 - 10.20.5.158", "10.20.5.159", "30"]],
              [20 * mm, 16 * mm, 31 * mm, 51 * mm, 31 * mm, 17 * mm], st),
        para("The deny rule for 198.51.100.0/24 precedes broad HTTP/HTTPS allows because NACLs evaluate lowest rule number first and stop on the first match. NACLs are stateless, so return packets need explicit rules: inbound ephemeral client ports for application replies and outbound ephemeral ports for replies to clients. SSH is limited to management. The sample packet comparison must be captured from make nacl.", st["Bodyx"]),
        para("6. Task 6 - Reproducibility, tests, and CI/CD", st["Heading1x"]),
        para("The project includes a Makefile, pinned requirements, central training configuration, four unit checks, and GitHub Actions stages for Python compilation, unit checks, release model download/evaluation, a 95% JSON-validity gate, and secret scanning. The package script generates a SHA-256 sidecar. The clean-clone build, CI workflow, deliberate failed quality gate, and release checksum verification have not been run. Add workflow links and checksum evidence after completing them. AI_USE.md documents AI assistance and human review expectations.", st["Bodyx"]),
        para("7. Task 7 - Performance, cost, SLO, and review", st["Heading1x"]),
        para("The prescribed Locust run and kubectl top pods should provide p50/p95 latency, throughput, error rate, and per-pod resources. These measurements are pending. Proposed SLO: 99% of requests succeed during one standard two-minute load-test run. For N total requests the error budget is 0.01 x N failed requests; insert the observed request and failure counts from Locust.", st["Bodyx"]),
        para("Hypothetical cost calculation", st["Heading2x"]),
        para("At the manifest limits, one replica costs 1 vCPU x INR 3.50 + 1 GiB x INR 0.45 = INR 3.95 per hour. Two running replicas cost INR 7.90 per hour. Cost per 1,000 requests = INR 7.90 / measured requests per hour x 1,000. The request rate is pending; this is an estimate using the supplied hypothetical rate card, not a cloud charge.", st["Bodyx"]),
        table([["Concern", "Evidence", "Limitation", "Improvement"],
               ["Data and storage", "3,000 input rows; cleaned counts pending", "Local single-node store", "Record checksum; use replicated storage"],
               ["Model quality", "Validation scores pending", "Copies teacher errors", "Inspect labels; compare full-frame scores"],
               ["Latency / throughput", "Locust values pending", "CPU-only laptop", "Profile generation and tokenization"],
               ["Resource use", "Per-pod CPU/RAM pending", "Cluster capacity varies", "Tune from measured peaks"],
               ["Reliability", "HPA/recovery evidence pending", "One physical node", "Repeat on multi-node cluster"],
               ["Security / cost", "No cloud charge; estimate above", "Hypothetical prices", "Use Secrets; cost from measured load"]],
              [30 * mm, 48 * mm, 46 * mm, 42 * mm], st),
        para("8. Limitations", st["Heading1x"]),
        para("The 70-million-parameter student is intentionally small and may lose accuracy compared with the fixed teacher. It learns from generated text labels, so teacher errors and ambiguous slot boundaries can propagate. CPU training and inference on a single laptop constrain throughput, and a one-node k3d cluster cannot prove multi-machine fault tolerance. SeaweedFS is a local S3-compatible store for this exercise; it does not provide the durability or availability guarantees of a production object-storage service. The API's generated output quality, startup time, image size, memory use, autoscaling, recovery, and latency remain unverified until the required runs are completed. Therefore, this report does not claim measured model or service performance.", st["Bodyx"]),
        para("9. Conclusion", st["Heading1x"]),
        para("The project provides an end-to-end implementation plan and code for teacher-based sequence-level distillation, artifact storage, schema-checked inference, Kubernetes operations, subnetting, NACL simulation, and CI quality gates. It also records the design choices and the evidence required by the assignment. Completion of the engineering implementation does not replace the outstanding experiments: run labeling and training, evaluate all three models, exercise the cluster and service, collect Locust and resource measurements, and update the pending fields before submitting the final report.", st["Bodyx"]),
        para("References", st["Heading2x"]),
        para("Bastianelli et al., SLURP, EMNLP 2020: https://aclanthology.org/2020.emnlp-main.588/. Kim and Rush, Sequence-Level Knowledge Distillation, EMNLP 2016: https://aclanthology.org/D16-1139/. EleutherAI Pythia-70M model card: https://huggingface.co/EleutherAI/pythia-70m. k3d: https://k3d.io/; Kubernetes: https://kubernetes.io/docs/.", st["Smallx"]),
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.build(story)
    print(OUT)


if __name__ == "__main__":
    build()
