.PHONY: help venv install run build push deploy clean test health check-deps lint

# Configuration
IMAGE_NAME = test-metrics
IMAGE_TAG = latest
REGISTRY = docker.io/sohom83
NAMESPACE = test-metrics
PORT = 8000
VENV_DIR = venv
PYTHON = $(VENV_DIR)/bin/python
PIP = $(VENV_DIR)/bin/pip

# Colors for output
RED = \033[31m
GREEN = \033[32m
YELLOW = \033[33m
BLUE = \033[34m
NC = \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Metrics Generator - Available commands:$(NC)"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ { printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

venv: ## Create Python virtual environment
	@echo "$(BLUE)Creating Python virtual environment...$(NC)"
	python3 -m venv $(VENV_DIR)
	@echo "$(GREEN)Virtual environment created at $(VENV_DIR)$(NC)"

install: venv ## Install Python dependencies in virtual environment
	@echo "$(BLUE)Installing dependencies in virtual environment...$(NC)"
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)Dependencies installed successfully$(NC)"

run: install ## Run the metrics generator locally
	@echo "$(BLUE)Starting metrics generator on port $(PORT)...$(NC)"
	$(PYTHON) metrics_generator.py --port $(PORT) --verbose

run-config: install ## Run with custom configuration
	@echo "$(BLUE)Starting metrics generator with custom config...$(NC)"
	$(PYTHON) metrics_generator.py --config example_config.json --port $(PORT) --verbose

build: ## Build the container image
	@echo "$(BLUE)Building container image $(IMAGE_NAME):$(IMAGE_TAG)...$(NC)"
	podman build -t $(IMAGE_NAME):$(IMAGE_TAG) .
	@echo "$(GREEN)Image built successfully$(NC)"

push: build ## Push the container image to registry
	@echo "$(BLUE)Pushing image to $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)...$(NC)"
	podman tag $(IMAGE_NAME):$(IMAGE_TAG) $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)
	podman push $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)
	@echo "$(GREEN)Image pushed successfully$(NC)"

deploy: ## Deploy to Kubernetes
	@echo "$(BLUE)Deploying to Kubernetes namespace $(NAMESPACE)...$(NC)"
	kubectl create namespace $(NAMESPACE) --dry-run=client -o yaml | kubectl apply -f -
	kubectl create configmap metrics-generator-config --from-file=example_config.json -n $(NAMESPACE) --dry-run=client -o yaml | tee k8s/configmap.yaml | kubectl apply -f -
	kubectl apply -f k8s/deployment.yaml -n $(NAMESPACE)
	kubectl apply -f k8s/servicemonitor.yaml -n $(NAMESPACE)
	@echo "$(GREEN)Deployment complete - using example_config.json$(NC)"

undeploy: ## Remove from Kubernetes
	@echo "$(YELLOW)Removing from Kubernetes...$(NC)"
	kubectl delete -f k8s/ -n $(NAMESPACE) --ignore-not-found=true
	@echo "$(GREEN)Cleanup complete$(NC)"

status: ## Check deployment status
	@echo "$(BLUE)Checking deployment status...$(NC)"
	kubectl get pods -l app=metrics-generator -n $(NAMESPACE)
	kubectl get svc metrics-generator -n $(NAMESPACE)

logs: ## Show application logs
	@echo "$(BLUE)Showing logs...$(NC)"
	kubectl logs -l app=metrics-generator -n $(NAMESPACE) --tail=100 -f

port-forward: ## Port forward to local machine
	@echo "$(BLUE)Port forwarding $(PORT):8000...$(NC)"
	@echo "$(YELLOW)Access metrics at: http://localhost:$(PORT)/metrics$(NC)"
	kubectl port-forward svc/metrics-generator $(PORT):8000 -n $(NAMESPACE)

test: install ## Run basic functionality tests
	@echo "$(BLUE)Running tests...$(NC)"
	@$(PYTHON) -c "import sys; sys.exit(0 if __import__('subprocess').call(['$(PYTHON)', '-m', 'py_compile', 'metrics_generator.py']) == 0 else 1)"
	@echo "$(GREEN)Syntax check passed$(NC)"
	@echo "$(BLUE)Testing HTTP endpoints...$(NC)"
	@make test-endpoints

test-endpoints: ## Test HTTP endpoints (requires running server)
	@echo "$(BLUE)Testing endpoints...$(NC)"
	@timeout 30 bash -c 'until curl -s http://localhost:$(PORT)/health > /dev/null; do sleep 1; done' || (echo "$(RED)Server not responding$(NC)" && exit 1)
	@echo "$(GREEN)Health endpoint: $$(curl -s http://localhost:$(PORT)/health | $(PYTHON) -m json.tool | grep status || echo 'OK')$(NC)"
	@echo "$(GREEN)Metrics endpoint: $$(curl -s http://localhost:$(PORT)/metrics | wc -l) lines of metrics$(NC)"

health: ## Check health of running service
	@echo "$(BLUE)Checking health...$(NC)"
	@curl -s http://localhost:$(PORT)/health | $(PYTHON) -m json.tool || echo "$(RED)Service not responding$(NC)"

metrics: ## Fetch current metrics
	@echo "$(BLUE)Current metrics:$(NC)"
	@curl -s http://localhost:$(PORT)/metrics || echo "$(RED)Service not responding$(NC)"

check-deps: ## Check if required tools are installed
	@echo "$(BLUE)Checking dependencies...$(NC)"
	@command -v python3 >/dev/null 2>&1 || (echo "$(RED)python3 is required$(NC)" && exit 1)
	@command -v podman >/dev/null 2>&1 || (echo "$(RED)podman is required$(NC)" && exit 1)
	@command -v kubectl >/dev/null 2>&1 || (echo "$(RED)kubectl is required$(NC)" && exit 1)
	@command -v curl >/dev/null 2>&1 || (echo "$(RED)curl is required$(NC)" && exit 1)
	@echo "$(GREEN)All dependencies are available$(NC)"

lint: install ## Run basic linting
	@echo "$(BLUE)Running lint checks...$(NC)"
	@$(PYTHON) -m py_compile metrics_generator.py
	@echo "$(GREEN)Lint check passed$(NC)"

clean: ## Clean up local resources
	@echo "$(YELLOW)Cleaning up...$(NC)"
	podman rmi $(IMAGE_NAME):$(IMAGE_TAG) 2>/dev/null || true
	podman rmi $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG) 2>/dev/null || true
	rm -rf $(VENV_DIR)
	@echo "$(GREEN)Cleanup complete$(NC)"

dev: install ## Start development environment
	@echo "$(BLUE)Starting development environment...$(NC)"
	@echo "$(YELLOW)Starting metrics generator in background...$(NC)"
	@$(PYTHON) metrics_generator.py --port $(PORT) --verbose &
	@sleep 2
	@echo "$(GREEN)Development environment ready$(NC)"
	@echo "$(BLUE)Endpoints:$(NC)"
	@echo "  Health: http://localhost:$(PORT)/health"
	@echo "  Metrics: http://localhost:$(PORT)/metrics"
	@echo "$(YELLOW)Press Ctrl+C to stop$(NC)"

example: ## Show example usage
	@echo "$(BLUE)Example Usage:$(NC)"
	@echo "  make run                    # Start server locally"
	@echo "  make build                  # Build container image"
	@echo "  make deploy                 # Deploy to Kubernetes"
	@echo "  make port-forward           # Access via localhost"
	@echo "  make test                   # Run tests"
	@echo "  make health                 # Check service health"