#!/bin/bash

##############################################
#          PRODES Data Ingestion
##############################################
# Prompt the user to download PRODES data
while true; do
    read -p "Do you want to download PRODES data if necessary? (yes/no): " DOWNLOAD_PRODES
    if [[ "$DOWNLOAD_PRODES" == "yes" ]]; then
        # Check if PRODES data exists and contains at least one .gpkg file
        if [ -d "./data/PRODES" ] && ls ./data/PRODES/*.gpkg 1> /dev/null 2>&1; then
            echo "✅ Found PRODES data folder with .gpkg file(s), skipping ingestion."
        else
            echo "❌ PRODES data folder not found or no .gpkg files present. Running data ingestion for PRODES..."
            python3 data_ingestion/ingest_prodes_data.py
        fi
        break
    elif [[ "$DOWNLOAD_PRODES" == "no" ]]; then
        echo "⏩ Skipping PRODES download."
        break
    else
        echo "Invalid input. Please enter 'yes' or 'no'."
    fi
done

##############################################
#           SICAR Data Ingestion
##############################################

# Define the latest year with available SICAR data
LATEST_YEAR=2025

# Prompt the user to download SICAR data
while true; do
    read -p "Do you want to download SICAR data for the latest year ($LATEST_YEAR)? (yes/no): " DOWNLOAD_SICAR
    if [[ "$DOWNLOAD_SICAR" == "yes" ]]; then
        echo "⏬ Running data ingestion for SICAR..."
        python3 data_ingestion/ingest_latest_car_data.py "$LATEST_YEAR"
        break
    elif [[ "$DOWNLOAD_SICAR" == "no" ]]; then
        echo "⏩ Skipping SICAR data download."
        break
    else
        echo "Invalid input. Please enter 'yes' or 'no'."
    fi
done

##############################################
#            Data Processing
##############################################

# Ask for years to analyze
read -p "Enter the first year: " YEAR1
read -p "Enter the second year: " YEAR2

# Function to check if a folder exists for a year, and create if missing
check_data_exists_and_not_empty() {
    FOLDER="./data/SICAR/$1"
    if [ ! -d "$FOLDER" ]; then
        echo "⚠️  Data folder for year $1 not found. Creating empty folder: $FOLDER"
        mkdir -p "$FOLDER"
        echo "ℹ️  Created empty folder for year $1. Please add data (shapefiles) to this folder before running the pipeline."
        return 1
    elif [ -z "$(ls -A "$FOLDER" 2>/dev/null)" ]; then
        echo "⚠️  Data folder for year $1 exists but is empty: $FOLDER"
        echo "ℹ️  Please add data (shapefiles) to this folder before running the pipeline."
        return 1
    else
        echo "✅ Found data folder for year $1 with data."
        return 0
    fi
}

MISSING=0

if [[ "$YEAR1" != "$LATEST_YEAR" ]]; then
    check_data_exists_and_not_empty "$YEAR1" || MISSING=1
fi

if [[ "$YEAR2" != "$LATEST_YEAR" ]]; then
    check_data_exists_and_not_empty "$YEAR2" || MISSING=1
fi

if [[ "$MISSING" -eq 1 ]]; then
    echo "❌ One or more required SICAR year folders were missing or empty."
    echo "   Please add the necessary data to these folders and re-run the pipeline."
    exit 1
fi

# Now run processing and visualization scripts
echo "⚙️ Running data processing for $YEAR1 and $YEAR2..."
python3 data_processing/data_processing.py "$YEAR1" "$YEAR2" "$LATEST_YEAR"

##############################################
#            Data Visualization
##############################################

# Get most recent output folder
LATEST_OUTPUT_DIR=$(ls -dt ./outputs/*/ | head -n 1 | sed 's:/*$::')

# Run visualization
echo "📊 Visualizing using data from $LATEST_OUTPUT_DIR"

# Copy latest output GeoJSONs to webmap/data/
WEBMAP_DATA_DIR="./webmap/data"
mkdir -p "$WEBMAP_DATA_DIR"
rm -f "$WEBMAP_DATA_DIR"/*
cp "$LATEST_OUTPUT_DIR"/*.geojson "$WEBMAP_DATA_DIR/"

# Write config.json with the selected years
cat <<EOF > "$WEBMAP_DATA_DIR/config.json"
{
  "year1": "$YEAR1",
  "year2": "$YEAR2"
}
EOF

echo "🌐 Latest GeoJSON files and config.json copied to $WEBMAP_DATA_DIR for webmap use."

# Run webmap
echo "🚀 Starting webmap server...
Navigate to http://localhost:8000 to view the webmap."
python3 -m http.server 8000 --directory webmap &
