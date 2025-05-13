import os
import requests
import zipfile
from clint.textui import progress

from SICAR import Sicar, State, Polygon
from SICAR.drivers import Tesseract
import pytesseract
import sys  # Added to accept arguments from the shell script

# === Configuration ===

# Path where all data will be saved
DATA_DIR = "../data"

# SICAR directory root
SICAR_DIR = os.path.join(DATA_DIR, "SICAR")

# Configure Tesseract path (needed by the SICAR library)
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

# === Utility Functions ===

def unzip_file(zip_path: str, extract_to: str) -> None:
    """Unzip a .zip file to a folder and remove the zip file after extraction."""
    if not zipfile.is_zipfile(zip_path):
        print(f"Not a valid zip file: {zip_path}")
        return

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
        print(f"Extracted: {zip_path} → {extract_to}")

    os.remove(zip_path)  # Remove the zip after successful extraction


def has_shapefile_components(folder_path: str) -> bool:
    """
    Check if the folder contains the minimum required files 
    for a shapefile: .shp, .shx, and .dbf.
    """
    if not os.path.exists(folder_path):
        return False

    files = os.listdir(folder_path)
    required_exts = {'.shp', '.shx', '.dbf'}
    present_exts = {os.path.splitext(f)[1].lower() for f in files}

    return required_exts.issubset(present_exts)

# === Download Functions ===

def download_sicar_data(state_codes: list[str], year: str) -> None:
    """
    Download and extract SICAR data for a list of state codes.
    If shapefiles are already present, the download is skipped.
    """
    car = Sicar(driver=Tesseract)

    # Create a year-specific folder for SICAR data
    year_folder = os.path.join(SICAR_DIR, year)
    os.makedirs(year_folder, exist_ok=True)

    for code in state_codes:
        folder_path = os.path.join(year_folder, code)

        if has_shapefile_components(folder_path):
            print(f"SICAR data for state {code} already exists in {folder_path}. Skipping download.")
            continue

        try:
            print(f"Downloading SICAR data for state: {code}")
            state_enum = getattr(State, code)
            car.download_state(state_enum, Polygon.AREA_PROPERTY, folder=folder_path)

            # Unzip all zip files in the folder
            for fname in os.listdir(folder_path):
                if fname.endswith(".zip"):
                    zip_path = os.path.join(folder_path, fname)
                    unzip_file(zip_path, folder_path)

            if has_shapefile_components(folder_path):
                print(f"✔ Successfully downloaded and extracted shapefiles for state {code}")
            else:
                print(f"⚠ Warning: Required shapefile components missing in {folder_path} after extraction")

        except AttributeError:
            print(f"Invalid state code: {code}")
        except Exception as e:
            print(f"Error downloading SICAR data for {code}: {e}")

# === Main Execution ===

if __name__ == "__main__":
    # Create data directories if they don't exist
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(SICAR_DIR, exist_ok=True)

    # Get the year from the command-line arguments
    if len(sys.argv) < 2:
        print("Error: Missing year argument. Usage: python ingest_latest_car_data.py <year>")
        sys.exit(1)

    LATEST_YEAR = sys.argv[1]

    # List of states in the Legal Amazon region
    amazon_states = ['AC', 'AM', 'PA', 'RO', 'RR', 'AP', 'MA', 'MT', 'TO']

    # Download SICAR datasets for each state
    download_sicar_data(amazon_states, LATEST_YEAR)
