# Data Pipeline Guide

Comprehensive guide to the data ingestion, processing, and analysis pipeline in the CCCA CAR Analysis Platform.

## Pipeline Overview

The CCCA CAR Analysis Platform processes two main types of spatial data:

1. **SICAR Data**: CAR (Cadastro Ambiental Rural) property boundary data
2. **PRODES Data**: Deforestation alert polygons from the Amazon region

The pipeline follows these stages:

```
Raw Data → Ingestion → Database Loading → Spatial Analysis → Visualization
```

## Data Sources

### SICAR (CAR Registry Data)
- **Source**: Brazilian Rural Environmental Registry (SICAR)
- **Format**: Shapefiles (.shp) with associated files
- **Content**: Rural property boundaries, registration codes, property status
- **Coordinate System**: Geographic coordinates (EPSG:4674 - SIRGAS 2000)
- **Temporal Coverage**: Multiple years (2020-2025+)

### PRODES (Deforestation Data)
- **Source**: INPE (National Institute for Space Research)
- **Format**: GeoPackage (.gpkg)
- **Content**: Deforestation polygons with detection dates
- **Coordinate System**: Geographic coordinates (EPSG:4674 - SIRGAS 2000)
- **Coverage**: Amazon biome region

## Data Structure Requirements

### Expected Directory Structure

```
data/
├── SICAR/
│   ├── 2023/                           # Historical year data
│   │   ├── merged_car_2023_04_11_UTF8_2.shp
│   │   ├── merged_car_2023_04_11_UTF8_2.dbf
│   │   ├── merged_car_2023_04_11_UTF8_2.prj
│   │   ├── merged_car_2023_04_11_UTF8_2.shx
│   │   └── ...                         # Other shapefile components
│   ├── 2024/                           # Historical year data
│   │   ├── merged_car_2024_02_01_UTF8.shp
│   │   └── ...                         # Other shapefile components
│   └── 2025/                           # Latest year
│       ├── AC/                         # Acre state
│       │   ├── AREA_IMOVEL_1.shp
│       │   ├── AREA_IMOVEL_1.dbf
│       │   ├── AREA_IMOVEL_1.prj
│       │   └── AREA_IMOVEL_1.shx
│       ├── AM/                         # Amazonas state
│       │   └── AREA_IMOVEL_1.*
│       ├── AP/                         # Amapá state
│       │   └── AREA_IMOVEL_1.*
│       └── ...                         # Other Amazon states
└── PRODES/
    └── prodes_amazonia_nb.gpkg         # PRODES deforestation data
```

### Key Structure Notes

1. **Historical Years**: Merged shapefiles for entire Amazon region
2. **Latest Year**: State-based folders with individual shapefiles due to API file format from API
3. **File Naming**: Consistent naming conventions expected

## Stage 1: Data Ingestion

### Overview
Data ingestion downloads and preprocesses raw data.

**Command:**
```bash
make ingest-data LATEST_YEAR=2025
```

### PRODES Data Ingestion

**Script:** `src/ingestion/prodes.py`

**Process:**
1. Downloads PRODES data API
2. Validates coordinate system (EPSG:4674)
3. Checks data completeness and quality
4. Stores in `data/PRODES/` directory

### SICAR Data Ingestion

**Script:** `src/ingestion/sicar.py`

**Process:**
1. Downloads latest year CAR data from SICAR API/servers
2. API downlaods data by state, script organizes data state in appropriate folder structure
3. Validates shapefile components
4. Performs initial quality checks

**Environment Variables:**
- `LATEST_YEAR`: Specifies which year uses state-based structure

### Manual Data Preparation

The SICAR API does not allow you to download data for previous years.

For all other years than the latest CAR data, you can manually prepare data:

```bash
# Create directory structure
mkdir -p data/SICAR/2024/
mkdir -p data/PRODES

# Place files according to expected structure
```

## Stage 2: Database Loading

### Overview
Database loading imports downloaded and preprocessed spatial data into PostgreSQL/PostGIS for analysis.

**Command:**
```bash
make load-data YEARS=2023,2024,2025 LATEST_YEAR=2025
```

### Script Details

**Script:** `src/processing/load_car_prodes_data.py`

**Process:**
1. Connects to PostgreSQL/PostGIS database
2. Creates necessary tables and spatial indexes
3. Loads SICAR data for specified years
4. Loads PRODES data
5. Standardizes data schemas
6. Creates spatial indexes for performance

### Database Schema

#### CAR Data Table
```sql
CREATE TABLE car_data (
    id SERIAL PRIMARY KEY,
    cod_imovel VARCHAR(255) NOT NULL,
    year INTEGER NOT NULL,
    ind_status VARCHAR(50),
    ind_tipo VARCHAR(50),
    geometry GEOMETRY(Geometry, 4674),
    area_ha NUMERIC,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(cod_imovel, year)
);
```

#### PRODES Data Table
```sql
CREATE TABLE prodes (
    id SERIAL PRIMARY KEY,
    classname VARCHAR(100),
    ano_prodes INTEGER,
    geometry GEOMETRY(Geometry, 4674),
    area_km2 NUMERIC,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Stage 2: Spatial Analysis

### Overview
Spatial analysis identifies changes in CAR boundaries and their relationship to deforestation.

**Command:**
```bash
make analyze YEARS=2023,2024,2025
```

### Analysis Scripts

**Main Script:** `src/processing/run_car_analysis.py`

**Supporting SQL:** `db/sql/02_car_analysis.sql.j2`

### Analysis Workflow

#### Geometry Change Detection

Identifies properties where CAR boundaries have changed between years, particularly focusing on changes that may be related to excluding deforested areas.

### Analysis Results

#### Output Tables

1. **geometry_changes_{year}_view**: Properties that changed to exclude deforestation
2. **relevant_prodes_subdivided**: Optimized PRODES data for visualization


## Stage 4: Data Preparation for Visualization

### Vector Tile Generation

**Martin Tile Server** automatically generates vector tiles from PostGIS tables:

```yaml
# martin/config.yaml
sources:
  postgres:
    connection_string: "postgresql://postgres:postgres@postgis:5432/geoanalytics"
    auto_publish:
      tables: true
      views: true
```

This data pipeline guide provides comprehensive information for understanding and managing the CCCA CAR Analysis Platform's data processing workflow. For technical details about the system architecture, see the [Architecture Documentation](architecture.md).