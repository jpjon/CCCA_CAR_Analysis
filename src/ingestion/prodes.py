import os
import requests
import zipfile
from clint.textui import progress

# === Configuration ===

# Path where all data will be saved
DATA_DIR = "./data"

# PRODES directory root
PRODES_DIR = os.path.join(DATA_DIR, "PRODES")

# PRODES dataset filenames
PRODES_ZIP = os.path.join(PRODES_DIR, "prodes_amazonia_nb.gpkg.zip")
PRODES_EXTRACTED = os.path.join(PRODES_DIR, "PRODES", "prodes_amazonia_nb.gpkg")

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


def download_file(url: str, output_path: str) -> None:
    """Download a file from a URL with a progress bar."""
    try:
        print(f"Starting download from {url}")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        total_length = int(response.headers.get('content-length', 0))

        with open(output_path, 'wb') as f:
            for chunk in progress.bar(
                response.iter_content(chunk_size=1024),
                expected_size=(total_length / 1024) + 1
            ):
                if chunk:
                    f.write(chunk)
                    f.flush()

        print(f"Download completed! File saved to: {output_path}")

    except requests.RequestException as e:
        print(f"Error downloading file: {e}")


# === Download Functions ===

def download_prodes_data() -> None:
    if not os.path.exists(PRODES_ZIP):
        download_file(
            "https://terrabrasilis.dpi.inpe.br/download/dataset/amz-prodes/vector/prodes_amazonia_nb.gpkg.zip",
            PRODES_ZIP
        )

    unzip_file(PRODES_ZIP, PRODES_DIR)

# === Main Execution ===

if __name__ == "__main__":
    # Create data directories if they don't exist
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(PRODES_DIR, exist_ok=True)

    # Download PRODES dataset
    download_prodes_data()
