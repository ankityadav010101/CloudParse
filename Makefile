.PHONY: up down port-forward worker-image label pull-labels clean-data train train-v2 image deploy destroy score nacl lint report

up:
	k3d cluster create --config cluster/k3d.yaml || true
	 kubectl apply -f cluster/seaweedfs.yaml

port-forward:
	kubectl -n data port-forward svc/seaweedfs 8333:8333

down:
	k3d cluster delete cloud-assignment

worker-image:
	docker build -f Dockerfile.worker -t cloud-command-parser-worker:local .
	 k3d image import cloud-command-parser-worker:local -c cloud-assignment

label: worker-image
	kubectl apply -f k8s/pipeline.yaml

pull-labels:
	mkdir -p datasets/teacher
	kubectl cp pipeline/labeler-0:/work/datasets/teacher/shard-0.jsonl datasets/teacher/shard-0.jsonl
	kubectl cp pipeline/labeler-1:/work/datasets/teacher/shard-1.jsonl datasets/teacher/shard-1.jsonl

clean-data:
	python worker/clean.py

train:
	python training/train.py --version v1 $(if $(SUBSET),--subset $(SUBSET),)

train-v2:
	python training/train.py --version v2 $(if $(SUBSET),--subset $(SUBSET),)

image:
	docker build -t cloud-command-parser:local .
	k3d image import cloud-command-parser:local -c cloud-assignment

deploy: image
	python tools/publish.py --model-version v1
	kubectl apply -f k8s/app.yaml

destroy:
	kubectl delete namespace app pipeline data --ignore-not-found
	k3d cluster delete cloud-assignment

score:
	python tools/evaluate.py

nacl:
	python tools/nacl_sim.py network/nacl.json network/packets_sample.jsonl --check

lint:
	python -m compileall -q service worker training tools tests
	python -m pytest -q

report:
	python report/build_report.py
