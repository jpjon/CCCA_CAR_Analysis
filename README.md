# CCCA – Client-Facing Pipeline

## Setup Instructions for Beginners

### 0. Prerequisites

- Python 3.10+
- pip
- virtualenv

### 0.1. Install Python

```bash
brew install python
```

### 0.2. Install pip

```bash
brew install pip
```

### 0.3. Install virtualenv

```bash
brew install virtualenv
```

### 0.4. Git clone and create a new branch

```bash
git clone <repo_url>
git checkout -b <branch_name>
```

### 1. Setting up a Virtual Environment

First, make sure you have Python installed on your system. Then:

```bash
python -m venv myenv
source myenv/bin/activate
```

### 2. Installing Dependencies

```bash
pip install -r requirements.txt
``` 

### 3. Install a new package

```bash
pip install <package_name>
```
Save the new package to requirements.txt

```bash
pip freeze > requirements.txt
``` 

### 4. Run a script

```bash
python src/scripts/script_name.py
``` 

---

## 🔧 Project Description

This project provides an end-to-end pipeline for detecting overlaps between **rural property registries (CARs)** and **deforestation alerts (PRODES)** in Brazil. It includes tools for:

- Downloading the most recent data for two input years
- Cleaning and filtering rural property records
- Measuring boundary changes between years
- Exporting results into a **Leaflet HTML map** and geospatial data files

---

## 🚀 Workflow Overview

The full process is automated via a shell script (`run_pipeline.sh`) that does the following:

1. Prompts the user to select two years for comparison (e.g., 2023 vs 2024)
2. Checks if data already exists; downloads CAR and PRODES data if missing
3. Runs Python notebooks/scripts to:
   - Filter by property type (`IRU`) and valid status (`AT` / `PE`)
   - Intersect CARs with deforestation polygons
   - Compute movement (distance) between CAR boundaries year-over-year
4. Outputs:
   - Clean `.geoparquet` files
   - Leaflet-ready `.html` map preview

---

## 📂 Key Files

| File | Description |
|------|-------------|
| `run_pipeline.sh` | Automates ingestion, processing, and export of deforestation analysis |
| `ingest_latest_car_data.py` | Downloads and processes CAR shapefiles from SICAR; merges state files and filters valid rural properties |
| `ingest_prodes_data.py` | Downloads PRODES deforestation data for a specified year |
| `data_processing.py` | Performs spatial joins, filters duplicate overlaps, and merges cross-year CAR records |
| `standardize_data.py` | Standardizes columns, validates geometry, and harmonizes schema across years |
| `d_p.ipynb` | Optional inspection notebook for visualizing CARs or checking outputs |

---

## ⚠️ Notes & Known Challenges

- **Column name mismatches** across years are handled using if-statements during preprocessing.
- **CRS must remain geographic (EPSG:4674)** – geodesic distance calculations are used to account for Earth’s curvature.
- Distance thresholds can be adjusted to define what counts as "significant displacement" (>10m, >1km, etc.).

---

## 🗺️ Output

At the end of the pipeline, you will find:

- A merged dataset showing CARs intersecting with PRODES deforestation
- A table of CARs that shifted between years (with distance in meters)
- Optional Leaflet `.html` file showing interactive comparison map

---

## ✅ To Run Everything At Once

```bash
bash run_pipeline.sh
```

This command will walk the user through the full data update and processing workflow.

---
