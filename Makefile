.PHONY: start stop load-data setup clean web

# Start all services
start:
	cd docker && docker-compose up -d
	@echo "Services started!"
	@echo "PostGIS: localhost:5432"
	@echo "Martin: localhost:3000"

# Stop all services
stop:
	cd docker && docker-compose down

# Load data into PostGIS
load-data:
	python src/processing/spatial_analysis_postgis.py $(YEAR1) $(YEAR2) $(LATEST_YEAR)

# Initial setup
setup:
	pip install -r requirements.txt
	make start
	sleep 5  # Wait for PostGIS to be ready

# Clean everything
clean:
	cd docker && docker-compose down -v
	rm -rf docker/pgdata

# View logs
logs:
	cd docker && docker-compose logs -f

# Access PostGIS
psql:
	docker exec -it geoanalytics_db psql -U postgres -d geoanalytics

# Serve web interface
web:
	cd web && python3 -m http.server 8080 --bind 127.0.0.1

# Or if you have Node.js:
web-node:
	cd web && npx http-server -p 8080