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
1. Downloads PRODES data from INPE servers
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

1. **Input and organize Files:**
   ```bash
   # Create directory structure
   mkdir -p data/SICAR/2024/
   mkdir -p data/PRODES
   
   # Place files according to expected structure
   ```

## Stage 2: Database Loading

### Overview
Database loading imports spatial data into PostgreSQL/PostGIS for analysis.

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

### Spatial Indexing Strategy

```sql
-- Primary spatial indexes for geometric operations
CREATE INDEX idx_car_data_geometry ON car_data USING GIST (geometry);
CREATE INDEX idx_prodes_geometry ON prodes USING GIST (geometry);

-- Temporal indexes for year-based queries
CREATE INDEX idx_car_data_year ON car_data (year);
CREATE INDEX idx_car_data_year_cod_imovel ON car_data (year, cod_imovel);

-- Text search indexes for property code searches
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_car_data_cod_imovel_trgm ON car_data USING GIN (cod_imovel gin_trgm_ops);
```

### Loading Performance Optimization

## Stage 3: Spatial Analysis

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

#### 1. Geometry Change Detection

**Purpose:** Identify CAR properties with boundary changes between years

```sql
-- Identify properties with geometry changes
WITH geometry_changes AS (
    SELECT 
        e.cod_imovel,
        e.year as year_earlier,
        l.year as year_later,
        e.geometry as geometry_earlier,
        l.geometry as geometry_later,
        NOT ST_Equals(e.geometry, l.geometry) as geometry_changed,
        ST_Area(e.geometry::geography) / 10000 as area_earlier_ha,
        ST_Area(l.geometry::geography) / 10000 as area_later_ha
    FROM car_data e
    JOIN car_data l ON e.cod_imovel = l.cod_imovel
    WHERE e.year = {{year_earlier}} AND l.year = {{year_later}}
      AND e.ind_status = 'AT' AND l.ind_status = 'AT'  -- Active properties only
)
SELECT * FROM geometry_changes WHERE geometry_changed = true;
```

#### 2. PRODES Intersection Analysis

**Purpose:** Find properties that intersect with deforestation areas

```sql
-- Find CAR properties intersecting with PRODES
WITH car_prodes_intersections AS (
    SELECT DISTINCT
        c.cod_imovel,
        c.year,
        c.geometry as car_geometry,
        p.geometry as prodes_geometry,
        ST_Area(ST_Intersection(c.geometry, p.geometry)::geography) / 10000 as intersection_area_ha
    FROM car_data c
    JOIN prodes_subdivided p ON ST_Intersects(c.geometry, p.geometry)
    WHERE c.year IN ({{years}})
      AND ST_Area(ST_Intersection(c.geometry, p.geometry)) > 0
)
SELECT * FROM car_prodes_intersections;
```

#### 3. Change Impact Analysis

**Purpose:** Determine if geometry changes affect PRODES intersections

```sql
-- Analyze impact of geometry changes on PRODES intersections
SELECT 
    gc.cod_imovel,
    gc.geometry_changed,
    CASE 
        WHEN pe.cod_imovel IS NOT NULL AND pl.cod_imovel IS NOT NULL THEN 'both_intersect'
        WHEN pe.cod_imovel IS NOT NULL AND pl.cod_imovel IS NULL THEN 'earlier_only'
        WHEN pe.cod_imovel IS NULL AND pl.cod_imovel IS NOT NULL THEN 'later_only'
        ELSE 'no_intersection'
    END as intersection_pattern
FROM geometry_changes gc
LEFT JOIN prodes_intersections pe ON gc.cod_imovel = pe.cod_imovel AND pe.year = gc.year_earlier
LEFT JOIN prodes_intersections pl ON gc.cod_imovel = pl.cod_imovel AND pl.year = gc.year_later;
```

### Analysis Results

#### Output Tables

1. **car_geom_changed**: Properties with geometry changes
2. **car_prodes_intersections**: CAR-PRODES intersection analysis
3. **car_changed_to_exclude_prodes**: Properties that changed to exclude deforestation
4. **relevant_prodes_subdivided**: Optimized PRODES data for visualization

#### Materialized Views

```sql
-- Create materialized view for visualization performance
CREATE MATERIALIZED VIEW car_analysis_summary AS
SELECT 
    cod_imovel,
    year_earlier,
    year_later,
    geometry_earlier,
    geometry_later,
    area_change_ha,
    prodes_intersection_before,
    prodes_intersection_after,
    excludes_prodes
FROM car_changed_to_exclude_prodes;

-- Create spatial index on materialized view
CREATE INDEX idx_car_analysis_summary_geom_earlier 
ON car_analysis_summary USING GIST (geometry_earlier);
```

### Performance Optimization

#### Query Optimization
```sql
-- Use spatial indexes effectively
-- Always use && operator before ST_Intersects for performance
SELECT * FROM car_data c
JOIN prodes p ON c.geometry && p.geometry  -- Bounding box check first
WHERE ST_Intersects(c.geometry, p.geometry);  -- Exact intersection check
```

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