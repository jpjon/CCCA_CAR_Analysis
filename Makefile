.PHONY: start stop load-data analyze run-all setup clean web logs psql

# Configuration variables
YEARS ?= 2023,2024,2025
LATEST_YEAR ?= 2025

# Start all services
start:
	cd docker && LATEST_YEAR=$(LATEST_YEAR) docker compose up -d
	@echo "Services started!"
	@echo "PostGIS: localhost:5432"
	@echo "Martin: localhost:3000"

# Stop all services
stop:
	cd docker && docker compose down

# Ingest CAR and PRODES data
ingest-data:
	python src/ingestion/prodes.py
	LATEST_YEAR=$(LATEST_YEAR) python src/ingestion/sicar.py

# Load CAR and PRODES data into PostGIS
load-data:
	@echo "Loading data for years: $(YEARS)"
	@echo "Latest year with state folders: $(LATEST_YEAR)"
	python src/processing/load_car_prodes_data.py --years $(YEARS) --latest-year $(LATEST_YEAR)

# Run CAR analysis
analyze:
	@echo "Running analysis for years: $(YEARS)"
	python src/processing/run_car_analysis.py --years $(YEARS)

# Run full pipeline (ingest, load + analyze, deploy on dev)
run-all: ingest-data load-data analyze web-dev

# Install web dependencies
web-install:
	cd web && npm install

# Run web development server
web-dev:
	cd web && npm run dev

# Build web for production
web-build:
	cd web && npm run build

# Initial setup
setup:
	pip install -r requirements.txt
	make web-install
	make start
	sleep 5  # Wait for PostGIS to be ready

# Clean everything
clean:
	cd docker && docker compose down -v
	rm -rf docker/pgdata

# View logs
logs:
	cd docker && docker compose logs -f

# Access PostGIS
psql:
	docker exec -it geoanalytics_db psql -U postgres -d geoanalytics

# Help
help:
	@echo "Available targets:"
	@echo "  make start          - Start Docker services"
	@echo "  make stop           - Stop Docker services"
	@echo "  make load-data      - Load CAR and PRODES data (default years: $(YEARS))"
	@echo "  make analyze        - Run analysis on loaded data"
	@echo "  make run-all        - Load data and run analysis"
	@echo "  make web-install    - Install web dependencies"
	@echo "  make web-dev        - Run web development server"
	@echo "  make clean          - Remove all data and containers"
	@echo "  make psql           - Access PostgreSQL CLI"
	@echo ""
	@echo "To use different years:"
	@echo "  make load-data YEARS=2020,2021,2022,2023,2024,2025 LATEST_YEAR=2025"
	@echo "  make analyze YEARS=2020,2021,2022,2023,2024,2025"
