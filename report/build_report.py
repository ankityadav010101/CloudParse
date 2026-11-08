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
        para("Evidence summary (9 November 2026): Ankit's local label workers had written 2,881/3,000 raw teacher replies (96.0%) at 03:48 IST; this is a progress snapshot. The local NACL sample check passed 6/6, subnet calculations completed, and Python source compilation passed. Other experiment figures below are explicitly attributed to Rahul Singh Jadoun's NanoParse report; they are comparison readings from his project, not Ankit's independently measured results. Source report: NanoParse Assignment Report (see References).", st["Bodyx"]),
        para("Architecture", st["Heading2x"]),
        para("3,000 command pool -> parallel Ollama Phi-3.5 workers -> validated and checksummed teacher dataset -> CPU fine-tuned Pythia-70M -> model artifact in SeaweedFS -> FastAPI container -> k3d Ingress and Kubernetes Deployment. Validation rows are used only by the teacher/base/student evaluators.", st["Bodyx"]),
        para("1. Object storage and parallel teacher labeling", st["Heading1x"]),
        para("The worker assigns each zero-based source line to one shard using line_number modulo SHARD_COUNT. The fixed Ollama phi3.5 teacher is called with temperature 0 and seed 42. Each raw response is saved with its source ID and text. The prompt requests exactly intent, date, time, and place. Two label workers are configured in a StatefulSet in the pipeline namespace.", st["Bodyx"]),
        para("The cleaner validates JSON, exact keys, intent membership, and slot text copied from the original command; it removes duplicate IDs/text, orders examples by ID, writes datasets/v1/train.jsonl, and records a SHA-256 checksum. It verifies complete one-time source ID coverage. SeaweedFS provides datasets and models buckets. Validation data is not read by labeling or training code.", st["Bodyx"]),
        table([["Labeling count", "Value"], ["Input records", "3,000 (provided pool)"],
               ["Ankit local raw replies at 03:48 IST", "2,881 / 3,000 (96.0%; snapshot)"],
               ["NanoParse reference: invalid JSON / wrong keys / invalid slots", "1 / 57 / 610"],
               ["NanoParse reference: duplicates / retained v1 examples", "40 / 2,292; categories may overlap"]], [80 * mm, 94 * mm], st),
        PageBreak()]

    story += [para("2. Student training with sequence-level distillation", st["Heading1x"]),
        para("The student base model is EleutherAI/pythia-70m. Training uses CPU PyTorch, Transformers, Datasets, and a LoRA adapter, merged into the saved model directory so the inference service can download a self-contained artifact. Each example contains the command followed by the teacher's exact JSON reply. Configuration is centralized in training/config.yaml: seed 42, up to 1,500 examples, maximum length 192, batch size 2, one epoch, learning rate 0.00005, and weight decay 0.01. Separate v1 and v2 versions are supported.", st["Bodyx"]),
        para("Sequence-level distillation teaches the student to reproduce the teacher's output sequence for an input command. Logit-based distillation instead matches teacher token probability distributions. It is not implemented because the required Ollama interface returns generated text rather than teacher logits. A limitation is that the student can learn teacher mistakes and inconsistent labels.", st["Bodyx"]),
        table([["Model", "JSON validity", "Intent", "Date", "Time", "Place", "Full frame"],
               ["Pythia-70M untrained baseline (NanoParse reference)", "0%", "0%", "0%", "0%", "0%", "0%"],
               ["Phi-3.5 teacher (NanoParse reference)", "94%", "85%", "71%", "79%", "81%", "44%"],
               ["Pythia-70M v1 student (NanoParse reference)", "90%", "75%", "68%", "76%", "77%", "41%"],
               ["Pythia-70M v2 student (NanoParse reference)", "89%", "76%", "69%", "79%", "71%", "42%"]],
              [38 * mm, 22 * mm, 20 * mm, 18 * mm, 18 * mm, 18 * mm, 26 * mm], st),
        para("The reference report gives validation scores for the teacher and two student versions over 100 examples, but does not state training loss. The figures above are source-reported comparisons, not scores reproduced on Ankit's machine. The validation set must remain evaluation-only.", st["Bodyx"]),
        para("3. Inference service in a container", st["Heading1x"]),
        para("service/app.py exposes POST /parse, GET /healthz, and GET /readyz. Successful output contains exactly the schema's four keys and includes X-Model-Version and X-Served-By headers. Readiness remains unavailable until model loading completes. At startup the service retrieves model and tokenizer files from S3-compatible storage; credentials are provided through a Kubernetes Secret. FAULT_INJECT=1 exercises the fail-closed HTTP 500 body {\"error\":\"invalid_model_output\"}.", st["Bodyx"]),
        para("The reference report records an ARM64 image size of 1.66 GB, 50/50 successful sequential requests under 1 CPU and 1 GiB, 737.4 MiB peak container memory, and no OOM kill. Readiness changed from HTTP 503 during loading to HTTP 200 when ready; model-version and served-by headers were verified. These are NanoParse readings, not a local rerun.", st["Bodyx"]),
        table([["Container measurement", "Evidence"], ["NanoParse ARM64 image size", "1.66 GB"],
               ["NanoParse sequential requests", "50/50 HTTP 200; 0 failures"],
               ["NanoParse peak memory / OOM", "737.4 MiB; no OOM kill"],
               ["NanoParse fault injection", "HTTP 500; invalid_model_output JSON error"],
               ["NanoParse readiness / response headers", "503 while loading; 200 ready; headers verified"]], [65 * mm, 109 * mm], st),
        PageBreak(),
        para("4. Kubernetes deployment, scaling, and reliability", st["Heading1x"]),
        para("k8s/app.yaml defines the app namespace, two-replica Deployment, rolling update strategy, Service, Ingress, liveness/readiness/startup probes, CPU and memory requests/limits, and HPA targeting 70% CPU with one to two replicas. Readiness prevents traffic from reaching a pod while the model is loading. The k3d setup has one laptop node and cannot demonstrate physical machine fault tolerance.", st["Bodyx"]),
        table([["Reliability exercise", "Evidence"], ["HPA configuration / recorded snapshot", "Target 70%; 1-2 replicas; 2 ready at 1% CPU"],
               ["Roll forward / rollback", "NanoParse report records rollback from v2 to v1"],
               ["Pod deletion and replica recovery", "No separate deletion-recovery result in source report"],
               ["Three cold starts / median", "11 s, 11 s, 11 s / 11 s median (reference)"],
               ["Successful requests by ready replica", "41 and 37 (78 total, reference)"]], [85 * mm, 89 * mm], st)]

    story += [para("5. Subnetting and stateless NACL", st["Heading1x"]),
        para("The 10.20.0.0/16 block is allocated from largest requirement to smallest. Usable host counts exclude the network and broadcast addresses.", st["Bodyx"]),
        table([["Subnet", "Needed", "Network", "Usable range", "Broadcast", "Usable"],
               ["app", "1,000", "10.20.0.0/22", "10.20.0.1 - 10.20.3.254", "10.20.3.255", "1,022"],
               ["public", "250", "10.20.4.0/24", "10.20.4.1 - 10.20.4.254", "10.20.4.255", "254"],
               ["data", "100", "10.20.5.0/25", "10.20.5.1 - 10.20.5.126", "10.20.5.127", "126"],
               ["management", "20", "10.20.5.128/27", "10.20.5.129 - 10.20.5.158", "10.20.5.159", "30"]],
              [20 * mm, 16 * mm, 31 * mm, 51 * mm, 31 * mm, 17 * mm], st),
        para("The deny rule for 198.51.100.0/24 precedes broad HTTP/HTTPS allows because NACLs evaluate lowest rule number first and stop on the first match. NACLs are stateless, so return packets need explicit rules: inbound ephemeral client ports for application replies and outbound ephemeral ports for replies to clients. SSH is limited to management. The packet simulator was run with --check: all 6 sample decisions matched (6/6, 100%). The subnet calculator completed with the allocations shown above. Evidence is saved in results/nacl_sample_check.txt and results/subnet_check.txt.", st["Bodyx"]),
        para("6. Task 6 - Reproducibility, tests, and CI/CD", st["Heading1x"]),
        para("The project includes a Makefile, pinned requirements, central training configuration, unit checks and GitHub Actions for compilation, testing, model evaluation and secret scanning. Ankit's Python compilation passed (results/compileall.txt). The NanoParse report records one successful CI run (lint, five unit tests, model evaluation, Gitleaks with no leaks) and a manual untrained-model evaluation that failed its quality gate as expected. According to the source report, manual evaluation enforces the 95% JSON threshold; the v1 model scored 90%. AI_USE.md documents AI assistance and human review expectations.", st["Bodyx"]),
        para("7. Task 7 - Performance, cost, SLO, and review", st["Heading1x"]),
        para("The NanoParse reference Locust run used four users, a spawn rate of four users/second, and two minutes. It recorded 89 attempts, 78 successes, 11 failures (12.36%); median 3,700 ms, mean 5,297 ms, p95 16,000 ms, range 1,100-30,013 ms, and 0.748439 requests/second. Nine failures were HTTP 500 and two had no response. Against a 99% success SLO, the 89-request run has a nominal 0.89-failure budget; 11 failures used about 1,236% of that budget. Both the 1% error target and 5-second p95 target were missed. These are reference readings, not Ankit's load-test measurements.", st["Bodyx"]),
        para("Hypothetical cost calculation", st["Heading2x"]),
        para("At the hypothetical rate card, two replicas cost INR 7.90/hour. Using the source-reported rate of 0.748439 requests/second, estimated cost is INR 2.93 per 1,000 attempted requests. These are illustrative calculations, not a cloud bill.", st["Bodyx"]),
        table([["Concern", "Evidence", "Limitation", "Improvement"],
               ["Data and storage", "NanoParse reference: 2,292 / 3,000 retained", "Local single-node store", "Use replicated storage"],
               ["Model quality", "Reference v1: 90% JSON / 41% full-frame", "Below 95% JSON target", "Improve data and output reliability"],
               ["Latency / throughput", "Reference p95 16 s; 0.748 req/s; 12.36% failures", "Misses both SLO targets", "Profile and retest"],
               ["Resource use", "Reference peaks: 993m/989m CPU; 556/555 MiB", "CPU near saturation", "Tune against measured peaks"],
               ["Reliability", "Two pods served traffic; 11/89 failures; 11 s cold start", "Single-node cluster", "Test multi-node recovery"],
               ["Security / cost", "No cloud charge; estimate above", "Hypothetical prices", "Use Secrets; cost from measured load"]],
              [30 * mm, 48 * mm, 46 * mm, 42 * mm], st),
        para("8. Limitations", st["Heading1x"]),
        para("The local label count is a timestamped progress snapshot. Model, container, Kubernetes and load-test figures drawn from NanoParse are comparison readings, not Ankit's measurements. The reference report identifies material limits: the compact model falls below the 95% JSON target, the two-minute load run exceeds both the 1% error and 5-second p95 targets, and its single-node cluster does not establish multi-node resilience. Its cost estimate uses hypothetical rates.", st["Bodyx"]),
        para("9. Conclusion", st["Heading1x"]),
        para("The project implements teacher-based sequence-level distillation, artifact storage, schema-checked inference, Kubernetes operations, subnetting, NACL simulation and CI quality gates. Ankit's local evidence includes 2,881/3,000 raw teacher replies at the recorded time, a 6/6 NACL pass, completed subnet calculations and successful Python compilation. Additional figures are attributed to the NanoParse report; they show the reference v1 model missed the JSON-quality gate and its load run missed both latency and error-rate goals. They are comparative evidence, not Ankit's local measurements.", st["Bodyx"]),
        para("References", st["Heading2x"]),
        para("Reference readings: Rahul Singh Jadoun, NanoParse Cloud Computing Assignment Report, https://github.com/rahul-singh92/NanoParse/blob/main/report/NanoParse_Assignment_Report.pdf. These results are attributed to that project. Bastianelli et al., SLURP, EMNLP 2020: https://aclanthology.org/2020.emnlp-main.588/. Kim and Rush, Sequence-Level Knowledge Distillation, EMNLP 2016: https://aclanthology.org/D16-1139/. EleutherAI Pythia-70M model card: https://huggingface.co/EleutherAI/pythia-70m. k3d: https://k3d.io/; Kubernetes: https://kubernetes.io/docs/.", st["Smallx"]),
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.build(story)
    print(OUT)


if __name__ == "__main__":
    build()
