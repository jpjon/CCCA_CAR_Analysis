
from utils import rename_car_data
import geopandas as gpd
import pandas as pd
from tqdm import tqdm
import time
import os
import argparse
import gc

from db_loader import PostGISLoader

import warnings

warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message="Geometry is in a geographic CRS. Results from 'centroid' are likely incorrect.*")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Load CAR and PRODES data into PostGIS')
    parser.add_argument(
        '--years',
        type=str,
        required=True,
        help='Comma-separated list of years to process (e.g., 2023,2024,2025)'
    )
    parser.add_argument(
        '--latest-year',
        type=int,
        required=True,
        help='The latest year that requires state-by-state processing'
    )
    return parser.parse_args()


def main():
    """Main execution function."""
    args = parse_arguments()
    
    # Parse years from comma-separated string
    years = [int(year.strip()) for year in args.years.split(',')]
    latest_year = args.latest_year
    
    ##############################################
    #        Preprocess and Load SICAR data      #
    ##############################################

    # Define the path to the SICAR folders
    sicar_folders = {str(year): f"./data/SICAR/{year}" for year in years}

    print("Loading and preprocessing SICAR data for all years...")

    # Initialize loader
    loader = PostGISLoader()

    for year in years:
        year_str = str(year)
        CAR_yearly_data = sicar_folders[year_str]
        
        start_time = time.time()
        
        if year == latest_year:
            # Data from the latest year must be concatenated across all states
            sicar_dataframes = []
            state_folders = [sf for sf in os.listdir(CAR_yearly_data) if os.path.isdir(os.path.join(CAR_yearly_data, sf))]
            for state_folder in tqdm(state_folders, desc=f"States for {year}"):
                state_path = os.path.join(CAR_yearly_data, state_folder)
                shp_files = [f for f in os.listdir(state_path) if f.endswith(".shp")]
                for file in tqdm(shp_files, desc=f"Shapefiles in {state_folder}", leave=False):
                    file_path = os.path.join(state_path, file)
                    gdf = gpd.read_file(file_path)
                    sicar_dataframes.append(gdf)
            car_gdf = gpd.GeoDataFrame(pd.concat(sicar_dataframes, ignore_index=True))
            del gdf, sicar_dataframes
            gc.collect()
        else:
            shp_files = [f for f in os.listdir(CAR_yearly_data) if f.endswith(".shp")]
            for file in shp_files:
                file_path = os.path.join(CAR_yearly_data, file)
                car_gdf = gpd.read_file(file_path)
        
        # Rename and filter CAR data
        car_gdf = rename_car_data(car_gdf)
        car_gdf = car_gdf[['cod_imovel', 'ind_status', 'ind_tipo', 'cod_estado', 'geometry']]
        car_gdf = car_gdf[(car_gdf['ind_tipo'] == 'IRU') & (car_gdf['ind_status'].isin(['AT', 'PE']))]
        car_gdf = car_gdf.drop_duplicates()
        # For duplicates by cod_imovel, keep the first occurrence
        car_gdf = car_gdf.drop_duplicates(subset=['cod_imovel'], keep='first')
        car_gdf = car_gdf[car_gdf.geometry.is_valid]
        
        print(f"Starting preprocessing and loading CAR year {year} into PostGIS...")
        
        loader.load_car_data(car_gdf, year)

        end_time = time.time()
        
        print(f"Successfully preprocessed and loaded CAR data to PostGIS for year {year} in {end_time - start_time:.2f} seconds.")
        
        # Clear memory
        del car_gdf
        gc.collect()
        
    # Display summary of loaded data
    print("\nSummary of loaded CAR data:")
    summary = loader.get_year_summary()
    for row in summary:
        print(f"Year {row[0]}: {row[1]:,} records, {row[2]} states")

    # ##############################################
    # #       Preprocess and Load PRODES data      #
    # ##############################################

    print("\n Starting preprocessing and loading PRODES data into PostGIS...")

    prodes_folder = "./data/PRODES"
    prodes_file = os.path.join(prodes_folder, 'prodes_amazonia_nb.gpkg')

    if not os.path.exists(prodes_file):
        raise FileNotFoundError("PRODES file not found in the specified folder.")

    start_time = time.time()

    prodes_gdf = gpd.read_file(prodes_file)
    prodes_gdf = prodes_gdf[['uuid', 'geometry', 'area_km']]
    prodes_gdf['area_km'] = prodes_gdf['area_km'].round(3)
    prodes_gdf = prodes_gdf[prodes_gdf.geometry.is_valid]
    loader.load_prodes_data(prodes_gdf)

    end_time = time.time()

    print(f"Successfully preprocessed and loaded PRODES data to PostGIS in {end_time - start_time:.2f} seconds.")
    
    print("\nData loading completed successfully!")


if __name__ == "__main__":
    main()
