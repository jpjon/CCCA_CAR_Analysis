# Installation Guide

Complete installation and setup guide for the CCCA CAR Analysis Platform.

## System Requirements

### Required Software

#### Docker & Docker Compose
The platform runs entirely in Docker containers for consistent deployment across environments.

Install it here:
https://docs.docker.com/get-started/get-docker/

#### Node.js & npm
Required for web frontend development.

https://docs.npmjs.com/downloading-and-installing-node-js-and-npm

### Optional Dependencies

#### Tesseract OCR
Required only if processing scanned documents or image-based data.

https://docs.npmjs.com/downloading-and-installing-node-js-and-npm


## Installation Steps

### 3. Initial Setup

```bash
# Install all dependencies and start services
make setup
```

This command will:
- Install Python dependencies from `requirements.txt`
- Install npm dependencies in the `web/` directory
- Start Docker services (PostgreSQL, API, Martin tile server)
- Wait for services to be ready

Expected services:
- PostgreSQL/PostGIS: `localhost:5432`
- FastAPI backend: `localhost:8000`
- Martin tile server: `localhost:3000`
- Web frontend: `localhost:5173` (when running `make web`)


## Data Preparation

### Required Data Structure

Prepare your data directory structure before running analysis:

```
data/
├── SICAR/
│   ├── 2023/
│   │   └── merged_car_2023_*.shp  # CAR data files
│   ├── 2024/
│   │   └── merged_car_2024_*.shp  # CAR data files
│   └── 2025/  # Latest year with state-based structure
│       ├── AC/
│       │   └── AREA_IMOVEL_1.*    # Acre state CAR data
│       ├── AM/
│       │   └── AREA_IMOVEL_1.*    # Amazonas state CAR data
│       └── ...  # Other Amazon states
└── PRODES/
    └── prodes_amazonia_nb.gpkg    # PRODES deforestation data
```

### Data Download

The system can automatically download data:

```bash
# Download/ingest CAR and PRODES data
make ingest-data LATEST_YEAR=2025
```

Or manually place data files in the appropriate directories following the structure above.

## Next Steps

After successful installation:

1. **Load Data**: Follow the [Data Pipeline Guide](data-pipeline.md)
2. **Development**: See the [Development Guide](development.md)
3. **Commands**: Reference the [Makefile Documentation](makefile-reference.md)