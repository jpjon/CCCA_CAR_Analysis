# Makefile Reference

Complete reference for all available Makefile commands in the CCCA CAR Analysis Platform.

## Overview

The Makefile provides automation for common development and deployment tasks. All commands are designed to work consistently across different environments and handle the complexity of the microservices architecture.

## Configuration Variables

### Default Variables
```makefile
YEARS ?= 2023,2024,2025      # Comma-separated list of analysis years
LATEST_YEAR ?= 2025          # Latest year with state-based folder structure
```

### Customizing Variables
```bash
# Override default years
make load-data YEARS=2020,2021,2022,2023,2024,2025

# Override latest year
make ingest-data LATEST_YEAR=2024

# Combine multiple overrides
make run-all YEARS=2022,2023,2024 LATEST_YEAR=2024
```

## Service Management Commands

### `make start`
Start all Docker services in the background.

**Usage:**
```bash
make start
```

**What it does:**
- Starts PostgreSQL/PostGIS database container
- Starts FastAPI backend container
- Starts Martin tile server container
- Sets up Docker network for service communication
- Displays service endpoint information

**Output:**
```
Services started!
PostGIS: localhost:5432
Martin: localhost:3000
```

**Dependencies:** Docker and Docker Compose must be installed

---

### `make stop`
Stop all running Docker services.

**Usage:**
```bash
make stop
```

**What it does:**
- Gracefully stops all running containers
- Preserves data volumes
- Removes containers but keeps images

**Use when:** Stopping development work or switching branches

---

### `make logs`
Display logs from all services in real-time.

**Usage:**
```bash
make logs
```

**What it does:**
- Shows combined logs from all Docker containers
- Follows log output (use Ctrl+C to exit)
- Color-coded by service

**Useful for:** Debugging service issues and monitoring system health

---

### `make clean`
Remove all containers, volumes, and data.

**Usage:**
```bash
make clean
```

**What it does:**
- Stops all running containers
- Removes all volumes (deletes all data!)
- Removes the pgdata directory
- Provides a clean slate for fresh start

**⚠️ Warning:** This command permanently deletes all data. Use with caution.

## Data Pipeline Commands

### `make ingest-data`
Download and ingest raw SICAR and PRODES data.

**Usage:**
```bash
make ingest-data
make ingest-data LATEST_YEAR=2024
```

**What it does:**
- Downloads PRODES deforestation data via `src/ingestion/prodes.py`
- Downloads SICAR CAR data via `src/ingestion/sicar.py`
- Uses LATEST_YEAR environment variable for state-based downloads
- Stores data in appropriate `data/` subdirectories

**Environment Variables:**
- `LATEST_YEAR`: Specifies which year has state-based folder structure

**Output Structure:**
```
data/
├── PRODES/
│   └── prodes_amazonia_nb.gpkg
└── SICAR/
    └── 2025/  # Based on LATEST_YEAR
        ├── AC/
        ├── AM/
        └── ...
```

---

### `make load-data`
Load ingested data into PostgreSQL/PostGIS database.

**Usage:**
```bash
make load-data
make load-data YEARS=2020,2021,2022 LATEST_YEAR=2022
```

**What it does:**
- Processes CAR data for specified years
- Loads PRODES deforestation data
- Creates spatial indexes for performance
- Prepares data for analysis

**Parameters:**
- `YEARS`: Comma-separated list of years to process
- `LATEST_YEAR`: Year with state-based folder structure

**Prerequisites:** 
- Services must be running (`make start`)
- Data must be ingested (`make ingest-data`)

---

### `make analyze`
Run spatial analysis on loaded data.

**Usage:**
```bash
make analyze
make analyze YEARS=2023,2024,2025
```

**What it does:**
- Executes geometry change detection algorithms
- Identifies CAR properties that intersect with PRODES
- Calculates distance metrics
- Creates materialized views for visualization

**Parameters:**
- `YEARS`: Comma-separated list of years to analyze

**Prerequisites:**
- Services running (`make start`)
- Data loaded (`make load-data`)

**Output:** Analysis results stored in database tables and views

---

### `make run-all`
Execute the complete data pipeline.

**Usage:**
```bash
make run-all
make run-all YEARS=2022,2023,2024 LATEST_YEAR=2024
```

**What it does:**
- Equivalent to running: `make ingest-data load-data analyze`
- Provides end-to-end pipeline execution
- Uses specified year parameters throughout

**Use when:** Setting up analysis from scratch or reprocessing data

## Setup and Installation Commands

### `make setup`
Complete initial setup of the development environment.

**Usage:**
```bash
make setup
```

**What it does:**
1. Installs Python dependencies from `requirements.txt`
2. Installs npm dependencies in `web/` directory (`make web-install`)
3. Starts Docker services (`make start`)
4. Waits 5 seconds for PostgreSQL to be ready

**Use when:** First-time setup or after major dependency changes

---

### `make web-install`
Install npm dependencies for the web frontend.

**Usage:**
```bash
make web-install
```

**What it does:**
- Changes to `web/` directory
- Runs `npm install` to install package.json dependencies
- Creates `node_modules/` and `package-lock.json`

**Prerequisites:** Node.js and npm must be installed

---

### `make web-dev`
Start the React development server.

**Usage:**
```bash
make web-dev
```

**What it does:**
- Changes to `web/` directory
- Runs `npm run dev` (Vite development server)
- Enables hot module replacement (HMR)
- Serves frontend at `http://localhost:5173`

**Features:**
- Automatic reload on file changes
- Fast refresh for React components
- Source maps for debugging

---

### `make web-build`
Build the web frontend for production.

**Usage:**
```bash
make web-build
```

**What it does:**
- Changes to `web/` directory
- Runs `npm run build` (Vite production build)
- Creates optimized static files in `web/dist/`
- Minifies JavaScript and CSS
- Optimizes assets for production

---

### `make web`
Start the web development server (alias for `make web-dev`).

**Usage:**
```bash
make web
```

**What it does:**
- Executes `make web-dev`
- Provides shorter command for common development task

## Database Commands

### `make psql`
Access PostgreSQL command line interface.

**Usage:**
```bash
make psql
```

**What it does:**
- Connects to running PostgreSQL container
- Opens psql CLI as postgres user
- Connects to geoanalytics database

**Prerequisites:** PostgreSQL container must be running (`make start`)

**Common psql commands:**
```sql
\dt                 -- List tables
\d table_name       -- Describe table structure
\q                  -- Quit psql
SELECT version();   -- Check PostgreSQL version
```

## Utility Commands

### `make help`
Display help information about available commands.

**Usage:**
```bash
make help
```

**What it does:**
- Shows list of all available make targets
- Provides brief description of each command
- Shows example usage with custom parameters

**Output:**
```
Available targets:
  make start          - Start Docker services
  make stop           - Stop Docker services
  make load-data      - Load CAR and PRODES data (default years: 2023,2024,2025)
  make analyze        - Run analysis on loaded data
  make run-all        - Load data and run analysis
  make web-install    - Install web dependencies
  make web-dev        - Run web development server
  make web            - Alias for web-dev
  make clean          - Remove all data and containers
  make psql           - Access PostgreSQL CLI

To use different years:
  make load-data YEARS=2020,2021,2022,2023,2024,2025 LATEST_YEAR=2025
  make analyze YEARS=2020,2021,2022,2023,2024,2025
```

## Advanced Usage Examples

### Complete Development Workflow
```bash
# 1. Initial setup
make setup

# 2. Run complete pipeline with custom years
make run-all YEARS=2020,2021,2022,2023,2024,2025 LATEST_YEAR=2025

# 3. Start web development
make web-dev

# 4. Monitor logs
make logs
```

### Data Update Workflow
```bash
# Update data for new year
make ingest-data LATEST_YEAR=2026
make load-data YEARS=2023,2024,2025,2026 LATEST_YEAR=2026
make analyze YEARS=2023,2024,2025,2026
```

### Development Debugging
```bash
# Clean start
make clean
make setup

# Check database
make psql

# Monitor specific service
docker logs -f geoanalytics_api
```

### Production Build
```bash
# Build optimized frontend
make web-build

# Package for deployment
tar -czf ccca-analysis.tar.gz web/dist/ docker/ requirements.txt Makefile
```

## Environment Configuration

### Docker Compose Override
Create `docker/docker-compose.override.yml` for local customizations:

```yaml
version: '3.8'
services:
  postgis:
    ports:
      - "5433:5432"  # Use different port
  api:
    environment:
      - DEBUG=true
    volumes:
      - ../src:/app/src:ro  # Mount source for development
```

### Environment Variables File
Create `.env` file in project root:

```bash
# Default configuration
YEARS=2023,2024,2025
LATEST_YEAR=2025

# Database configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=geoanalytics
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# API configuration
API_HOST=0.0.0.0
API_PORT=8000
```

## Troubleshooting Commands

### Service Health Checks
```bash
# Check if services are running
docker ps

# Check service health
curl http://localhost:8000/health  # API health
curl http://localhost:3000/health  # Martin health

# Check database connection
make psql -c "SELECT version();"
```

### Resource Monitoring
```bash
# Monitor Docker resource usage
docker stats

# Check disk usage
docker system df

# Monitor database performance
make psql -c "SELECT * FROM pg_stat_activity;"
```

### Clean Recovery
```bash
# Complete clean slate
make clean
docker system prune -f
make setup
```

## Integration with IDEs

### VS Code Tasks
Add to `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Start Services",
      "type": "shell",
      "command": "make start",
      "group": "build"
    },
    {
      "label": "Run Pipeline",
      "type": "shell",
      "command": "make run-all",
      "group": "build"
    }
  ]
}
```

### PyCharm External Tools
- **Name**: Start Services
- **Program**: make
- **Arguments**: start
- **Working Directory**: $ProjectFileDir$

## Performance Optimization

### Parallel Execution
```bash
# Run multiple commands in parallel
make start &
make web-install &
wait  # Wait for both to complete
```

### Resource Allocation
```bash
# Increase Docker memory for large datasets
export DOCKER_DEFAULT_MEMORY=8g
make start
```

## Security Considerations

### Development Security
- Default passwords are used in development
- Services are bound to localhost only
- No authentication required for local access

### Production Considerations
- Change all default passwords
- Use environment variables for secrets
- Enable authentication for external access
- Use HTTPS for web frontend
- Restrict database access

This Makefile reference provides comprehensive information for using all available commands effectively. For additional help, use `make help` or refer to the [Development Guide](development.md).