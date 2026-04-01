COMPOSE ?= docker compose
PYTHON ?= python
CLI := $(PYTHON) -m src.cli
COMPOSE_RUN_API := $(COMPOSE) run --rm api

.PHONY: help build up down restart logs ps api-logs frontend-logs api-shell frontend-shell kb transcribe analyze docker-kb docker-transcribe docker-analyze

help:
	@echo "Available targets:"
	@echo "  make build          Build the API image"
	@echo "  make up             Start API and frontend services"
	@echo "  make down           Stop services and remove containers"
	@echo "  make restart        Restart services"
	@echo "  make logs           Follow logs for all services"
	@echo "  make ps             Show service status"
	@echo "  make api-logs       Follow API logs"
	@echo "  make frontend-logs  Follow frontend logs"
	@echo "  make api-shell      Open a shell in the API container"
	@echo "  make frontend-shell Open a shell in the frontend container"
	@echo "  make kb             Build KB artifacts locally"
	@echo "  make transcribe     Run the transcription pipeline locally"
	@echo "  make analyze        Run the full analysis pipeline locally"
	@echo "  make docker-kb      Build KB artifacts in the API container"
	@echo "  make docker-transcribe Run the transcription pipeline in the API container"
	@echo "  make docker-analyze Run the full analysis pipeline in the API container"
	@echo ""
	@echo "Argument examples:"
	@echo "  make transcribe FILE=path/to/media.mp4 OUTPUT_DIR=outputs/transcribe"
	@echo "  make analyze FILE=path/to/media.mp4 NOTES=doctor_notes.txt OUTPUT_DIR=outputs/demo_run"
	@echo "  make docker-analyze FILE=path/to/media.mp4 NOTES=doctor_notes.txt OUTPUT_DIR=outputs/demo_run"

build:
	$(COMPOSE) build api

up:
	$(COMPOSE) up --build

down:
	$(COMPOSE) down --remove-orphans

restart: down up

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

api-logs:
	$(COMPOSE) logs -f api

frontend-logs:
	$(COMPOSE) logs -f frontend

api-shell:
	$(COMPOSE) exec api sh

frontend-shell:
	$(COMPOSE) exec frontend sh

kb:
	$(CLI) build-kb

transcribe:
ifndef FILE
	$(error FILE is required. Usage: make transcribe FILE=path/to/media.mp4 [OUTPUT_DIR=outputs/transcribe])
endif
	$(CLI) transcribe --input "$(FILE)" $(if $(OUTPUT_DIR),--output-dir "$(OUTPUT_DIR)")

analyze:
ifndef FILE
	$(error FILE is required. Usage: make analyze FILE=path/to/media.mp4 NOTES=doctor_notes.txt [OUTPUT_DIR=outputs/demo_run])
endif
ifndef NOTES
	$(error NOTES is required. Usage: make analyze FILE=path/to/media.mp4 NOTES=doctor_notes.txt [OUTPUT_DIR=outputs/demo_run])
endif
	$(CLI) analyze --file "$(FILE)" --notes "$(NOTES)" $(if $(OUTPUT_DIR),--output-dir "$(OUTPUT_DIR)")

docker-kb:
	$(COMPOSE_RUN_API) python -m src.cli build-kb

docker-transcribe:
ifndef FILE
	$(error FILE is required. Usage: make docker-transcribe FILE=path/to/media.mp4 [OUTPUT_DIR=outputs/transcribe])
endif
	$(COMPOSE_RUN_API) python -m src.cli transcribe --input "$(FILE)" $(if $(OUTPUT_DIR),--output-dir "$(OUTPUT_DIR)")

docker-analyze:
ifndef FILE
	$(error FILE is required. Usage: make docker-analyze FILE=path/to/media.mp4 NOTES=doctor_notes.txt [OUTPUT_DIR=outputs/demo_run])
endif
ifndef NOTES
	$(error NOTES is required. Usage: make docker-analyze FILE=path/to/media.mp4 NOTES=doctor_notes.txt [OUTPUT_DIR=outputs/demo_run])
endif
	$(COMPOSE_RUN_API) python -m src.cli analyze --file "$(FILE)" --notes "$(NOTES)" $(if $(OUTPUT_DIR),--output-dir "$(OUTPUT_DIR)")
