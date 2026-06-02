# Makefile for the NLP Sentiment Analysis Engine
# Usage: make <target>

PYTHON ?= python
PIP ?= $(PYTHON) -m pip

.DEFAULT_GOAL := help

.PHONY: help install train test serve docker-build lint format pipeline augment clean

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install: ## Install all Python dependencies
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

pipeline: ## Run the data pipeline end-to-end
	$(PYTHON) -m src.data_pipeline

augment: ## Run data augmentation on minority classes
	$(PYTHON) -m src.augmentation

train: ## Fine-tune the BERT sentiment model
	$(PYTHON) -m src.trainer

test: ## Run the full test suite
	$(PYTHON) -m pytest -v

serve: ## Launch the FastAPI inference server
	$(PYTHON) -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

demo: ## Launch the Gradio demo UI
	$(PYTHON) app.py

docker-build: ## Build the Docker image
	docker build -t sentiment-engine:latest .

lint: ## Run Black (check) and mypy
	$(PYTHON) -m black --check .
	$(PYTHON) -m mypy src api config.py

format: ## Auto-format the codebase with Black
	$(PYTHON) -m black .

clean: ## Remove caches and build artifacts
	$(PYTHON) -c "import shutil,glob,os; [shutil.rmtree(p, ignore_errors=True) for p in glob.glob('**/__pycache__', recursive=True)]"
	$(PYTHON) -c "import shutil; shutil.rmtree('.pytest_cache', ignore_errors=True)"
