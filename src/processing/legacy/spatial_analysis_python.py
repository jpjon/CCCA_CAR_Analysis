from utils import rename_car_data
import dask_geopandas as dgpd
import geopandas as gpd
import pandas as pd
from geopy.distance import geodesic
from shapely.geometry import LineString
from datetime import datetime
import sys
from dask.diagnostics import ProgressBar
from tqdm import tqdm
import time
import os


from db_loader import PostGISLoader

import warnings

warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message="Geometry is in a geographic CRS. Results from 'centroid' are likely incorrect.*")
# ... (keep your existing processing logic until the save section)
##############################################
#              Load SICAR data               #
##############################################

year1 = sys.argv[1]
year2 = sys.argv[2]
latest_year = sys.argv[3]

# Determine which year is earlier/later
if int(year1) < int(year2):
    earlier_year = year1
    later_year = year2
else:
    earlier_year = year2
    later_year = year1

# Define the path to the SICAR folders
sicar_folders = {
    year1: f"./data/SICAR/{year1}",
    year2: f"./data/SICAR/{year2}",
}

# Dictionary to store GeoDataFrames per year
car_gdfs = {}

print("Loading SICAR data...")

for year, CAR_yearly_data in sicar_folders.items():
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
    else:
        shp_files = [f for f in os.listdir(CAR_yearly_data) if f.endswith(".shp")]
        for file in shp_files:
            file_path = os.path.join(CAR_yearly_data, file)
            car_gdf = gpd.read_file(file_path)
    end_time = time.time()
    print(f"Loaded SICAR data for {year} in {end_time - start_time:.2f} seconds.")

    # Rename and filter CAR data
    car_gdf = rename_car_data(car_gdf)
    car_gdf = car_gdf[['cod_imovel', 'ind_status', 'ind_tipo', 'cod_estado', 'geometry']]
    car_gdf = car_gdf[(car_gdf['ind_tipo'] == 'IRU') & (car_gdf['ind_status'].isin(['AT', 'PE']))]
    car_gdf = car_gdf.drop_duplicates()
    car_gdf = car_gdf[car_gdf.geometry.is_valid]

    # Store the processed GeoDataFrame
    car_gdfs[year] = car_gdf

car_gdf_earlier_year = car_gdfs[earlier_year]
car_gdf_later_year = car_gdfs[later_year]

##############################################
#              Load PRODES data              #
##############################################

print("Loading PRODES data...")

prodes_folder = "./data/PRODES"
prodes_file = os.path.join(prodes_folder, 'prodes_amazonia_nb.gpkg')

if not os.path.exists(prodes_file):
    raise FileNotFoundError("PRODES file not found in the specified folder.")

start_time = time.time()
prodes_gdf = gpd.read_file(prodes_file)
end_time = time.time()

print(f"Loaded PRODES data in {end_time - start_time:.2f} seconds.")
prodes_gdf = prodes_gdf[['uuid', 'geometry']]
prodes_gdf = prodes_gdf.to_crs(car_gdf_later_year.crs)

def count_corners(geom):
    if geom.geom_type == 'Polygon':
        return len(geom.exterior.coords)
    elif geom.geom_type == 'MultiPolygon':
        return sum(len(poly.exterior.coords) for poly in geom.geoms)
    else:
        return 0

prodes_gdf['num_prodes_corners'] = prodes_gdf.geometry.apply(count_corners)

# # Simplify PRODES geometries (tolerance can be adjusted as needed)
# simplify_tolerance = 0.0005
# prodes_gdf['geometry'] = prodes_gdf['geometry'].simplify(simplify_tolerance, preserve_topology=True)


##############################################
#     Data Processing -- ArcGIS Analysis     #
##############################################

print("Performing spatial join to find intersections between earlier CAR year and PRODES data...")

# Spatial join to identify earlier-year CAR parcels intersecting PRODES areas

# Using Dask for parallel processing to reduce runtime
car_ddf = dgpd.from_geopandas(car_gdf_earlier_year, npartitions=12)
prodes_ddf = dgpd.from_geopandas(prodes_gdf, npartitions=12)

sjoin_ddf = car_ddf.sjoin(prodes_ddf, how="inner", predicate="intersects")

start_time = time.time()
with ProgressBar():
    car_earlier_year_prodes_intersection_gdf = sjoin_ddf.compute().drop(columns=["index_right"])
end_time = time.time()

print(f"Spatial join completed in {end_time - start_time:.2f} seconds.")

# Drop duplicates where one geometry intersects multiple PRODES features. Keep the largest intersect by number of corners.
car_earlier_year_prodes_intersection_gdf = car_earlier_year_prodes_intersection_gdf.sort_values('num_prodes_corners', ascending=False)
car_earlier_year_prodes_intersection_gdf = car_earlier_year_prodes_intersection_gdf.drop_duplicates(
    subset=['cod_imovel'], keep="first"
)

# Join later-year CAR data to earlier-year intersected parcels
car_later_year_car_early_year_prodes_intersect = car_earlier_year_prodes_intersection_gdf.merge(
    car_gdf_later_year,
    on="cod_imovel",
    how="inner",
    suffixes=(f"_{earlier_year}", f"_{later_year}")
)

# Handle cases where duplicates exist due to multiple statuses or geometries
car_later_year_car_early_year_prodes_intersect = car_later_year_car_early_year_prodes_intersect.drop_duplicates(
    subset=['cod_imovel'], keep="first"
)

amount_of_CAR_parcels_intersecting_PRODES_in_early_year = len(car_later_year_car_early_year_prodes_intersect)

# Ensure we can safely create a new column
car_later_year_car_early_year_prodes_intersect = car_later_year_car_early_year_prodes_intersect.copy()

# Identify parcels whose geometry changed from earlier to later year
car_later_year_car_early_year_prodes_intersect['geometry_changed'] = \
    car_later_year_car_early_year_prodes_intersect.apply(
        lambda row: not row[f'geometry_{earlier_year}'].equals(row[f'geometry_{later_year}']),
        axis=1
    )

car_later_year_car_early_year_prodes_intersect = car_later_year_car_early_year_prodes_intersect[
    car_later_year_car_early_year_prodes_intersect['geometry_changed']
]

amount_of_CAR_parcels_with_geometry_changed = len(car_later_year_car_early_year_prodes_intersect.geometry_changed)

print("Starting process of finding later-year geometries changed to longer intersect with PRODES...")

# Join PRODES geometries to eventually find later-year CAR parcels that no longer intersect PRODES
car_later_year_car_early_year_prodes_intersect = car_later_year_car_early_year_prodes_intersect.set_geometry(f'geometry_{later_year}')

start_time = time.time()
car_later_year_car_early_year_prodes_intersect = car_later_year_car_early_year_prodes_intersect.sjoin(prodes_gdf, how = "left", predicate="intersects")
end_time = time.time()

print(f"Spatial join to find later-year geometries that do not intersect with PRODES completed in {end_time - start_time:.2f} seconds.")

# Filter for later-year CAR parcels that do not intersect with PRODE
car_later_year_car_early_year_prodes_intersect_result = car_later_year_car_early_year_prodes_intersect[car_later_year_car_early_year_prodes_intersect['uuid_right'].isna()].copy()\
    .drop(columns=['uuid_right', 'num_prodes_corners_right', 'index_right'])

amount_of_CAR_later_year_parcels_changed_to_no_longer_intersect_PRODES = len(car_later_year_car_early_year_prodes_intersect_result)

# Renaming columns for clarity post-join
car_later_year_car_early_year_prodes_intersect_result = car_later_year_car_early_year_prodes_intersect_result.rename(
    columns={
        'uuid_left': 'uuid',
        'num_prodes_corners_left': 'num_prodes_corners',
    }
)

# Add PRODES geometry to the result
car_later_year_car_early_year_prodes_intersect_result = car_later_year_car_early_year_prodes_intersect_result.merge(
    prodes_gdf[['uuid', 'geometry']],
    on='uuid',
    how='left'
).rename(
    columns={
        'geometry': 'geometry_prodes',}
)

##############################################
#     Data Processing -- Distance Analysis   #
##############################################

print("Running distance analysis...")

def calculate_geodesic_distance(row):
    coord_earlier_year = (row[f'centroid_{earlier_year}'].y, row[f'centroid_{earlier_year}'].x)
    coord_later_year = (row[f'centroid_{later_year}'].y, row[f'centroid_{later_year}'].x)
    return geodesic(coord_earlier_year, coord_later_year).meters

# Compute centroids and distances
car_later_year_car_early_year_prodes_intersect_result[f'centroid_{earlier_year}'] = \
    car_later_year_car_early_year_prodes_intersect_result[f'geometry_{earlier_year}'].centroid

car_later_year_car_early_year_prodes_intersect_result[f'centroid_{later_year}'] = \
    car_later_year_car_early_year_prodes_intersect_result[f'geometry_{later_year}'].centroid

car_later_year_car_early_year_prodes_intersect_result['geodesic_distance'] = \
    car_later_year_car_early_year_prodes_intersect_result.apply(calculate_geodesic_distance, axis=1)

car_later_year_car_early_year_prodes_intersect_result['distance_line'] = \
    car_later_year_car_early_year_prodes_intersect_result.apply(
        lambda row: LineString([row[f'geometry_{earlier_year}'].centroid,
                                row[f'geometry_{later_year}'].centroid]),
        axis=1
    )

print("\n" + "="*50)
print("SUMMARY OF PROCESSING STATISTICS")
print("="*50)
print(f"Years analyzed: {earlier_year} (earlier), {later_year} (later)")
print(f"SICAR parcels loaded for {earlier_year}: {len(car_gdf_earlier_year)}")
print(f"SICAR parcels loaded for {later_year}: {len(car_gdf_later_year)}")
print(f"PRODES polygons loaded: {len(prodes_gdf)}")
print(f"CAR parcels from {earlier_year} intersecting PRODES: {amount_of_CAR_parcels_intersecting_PRODES_in_early_year}")
print(f"CAR parcels with geometry changed from {earlier_year} to {later_year}: {amount_of_CAR_parcels_with_geometry_changed}")
print(f"CAR parcels whose geometry changed in {latest_year} and no longer intersect PRODES: {amount_of_CAR_later_year_parcels_changed_to_no_longer_intersect_PRODES}")
print("="*50 + "\n")

##############################################
#        Save to PostGIS Instead            #
##############################################

print("Loading data into PostGIS...")

# Initialize loader
loader = PostGISLoader()

# Load CAR data for both years
loader.load_car_data(car_gdf_earlier_year, earlier_year)
loader.load_car_data(car_gdf_later_year, later_year)

# Load PRODES data
prodes_to_load = prodes_gdf[['uuid', 'num_prodes_corners', 'geometry']].copy()
loader.load_prodes_data(prodes_to_load)

# Prepare analysis results for database
analysis_results = pd.DataFrame({
    'cod_imovel': car_later_year_car_early_year_prodes_intersect_result['cod_imovel'],
    'year_earlier': int(earlier_year),
    'year_later': int(later_year),
    'geometry_changed': car_later_year_car_early_year_prodes_intersect_result['geometry_changed'],
    'geodesic_distance': car_later_year_car_early_year_prodes_intersect_result['geodesic_distance'],
    'intersects_prodes_earlier': True,  # They all intersected in earlier year
    'intersects_prodes_later': False    # These are the ones that no longer intersect
})

loader.save_analysis_results(analysis_results)

print("Data successfully loaded to PostGIS!")