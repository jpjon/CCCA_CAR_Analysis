from standardize_data import standardize_car_data
import geopandas as gpd
import pandas as pd
from geopy.distance import geodesic
from shapely.geometry import LineString
from datetime import datetime
import sys
import os

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
    latest_year: f"./data/SICAR/{latest_year}"
}

# Dictionary to store GeoDataFrames per year
car_gdfs = {}

print("Loading SICAR data...")

for year, CAR_yearly_data in sicar_folders.items():
    if year == latest_year:
        # Data from the latest year must be concatenated across all states
        sicar_dataframes = []
        for state_folder in os.listdir(CAR_yearly_data):
            state_path = os.path.join(CAR_yearly_data, state_folder)
            if os.path.isdir(state_path):
                for file in os.listdir(state_path):
                    if file.endswith(".shp"):
                        file_path = os.path.join(state_path, file)
                        gdf = gpd.read_file(file_path)
                        sicar_dataframes.append(gdf)
        car_gdf = gpd.GeoDataFrame(pd.concat(sicar_dataframes, ignore_index=True))
    else:
        shp_files = [f for f in os.listdir(CAR_yearly_data) if f.endswith(".shp")]
        file_path = os.path.join(CAR_yearly_data, shp_files[0])
        car_gdf = gpd.read_file(file_path)

    # Standardize and filter CAR data
    car_gdf = standardize_car_data(car_gdf)
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

prodes_gdf = gpd.read_file(prodes_file)
prodes_gdf = prodes_gdf[['uuid', 'geometry']]
prodes_gdf = prodes_gdf.to_crs(car_gdf_later_year.crs)

##############################################
#     Data Processing -- ArcGIS Analysis     #
##############################################

print("Performing spatial join to find intersections between earlier CAR year and PRODES data...")

# Spatial join to identify earlier-year CAR parcels intersecting PRODES areas
car_earlier_year_prodes_intersection_gdf = gpd.sjoin(
    car_gdf_earlier_year, prodes_gdf, how="inner", predicate="intersects"
).drop(columns=["index_right"])

# Drop duplicates where one geometry intersects multiple PRODES features
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

# Ensure we can safely create a new column
car_later_year_car_early_year_prodes_intersect = car_later_year_car_early_year_prodes_intersect.copy()

# Identify parcels whose geometry changed from earlier to later year
car_later_year_car_early_year_prodes_intersect['geometry_changed'] = \
    car_later_year_car_early_year_prodes_intersect.apply(
        lambda row: not row[f'geometry_{earlier_year}'].equals(row[f'geometry_{later_year}']),
        axis=1
    )

# Merge PRODES geometry for filtering
car_later_year_car_early_year_prodes_intersect_with_prodes = car_later_year_car_early_year_prodes_intersect.merge(
    prodes_gdf[['uuid', 'geometry']],
    on='uuid',
    how='inner'
).rename(columns={'geometry': 'geometry_prodes'})

# Filter to find cases where geometry changed and no longer intersects PRODES
filtered_indexes = [
    row.Index for row in car_later_year_car_early_year_prodes_intersect_with_prodes.itertuples()
    if row.geometry_changed and not row.__getattribute__(f'geometry_{later_year}').intersects(row.geometry_prodes)
]

car_later_year_car_early_year_prodes_intersect_with_prodes = \
    car_later_year_car_early_year_prodes_intersect_with_prodes.loc[filtered_indexes]

##############################################
#     Data Processing -- Distance Analysis   #
##############################################

def calculate_geodesic_distance(row):
    coord_earlier_year = (row[f'centroid_{earlier_year}'].y, row[f'centroid_{earlier_year}'].x)
    coord_later_year = (row[f'centroid_{later_year}'].y, row[f'centroid_{later_year}'].x)
    return geodesic(coord_earlier_year, coord_later_year).meters

# Compute centroids and distances
car_later_year_car_early_year_prodes_intersect_with_prodes[f'centroid_{earlier_year}'] = \
    car_later_year_car_early_year_prodes_intersect_with_prodes[f'geometry_{earlier_year}'].centroid

car_later_year_car_early_year_prodes_intersect_with_prodes[f'centroid_{later_year}'] = \
    car_later_year_car_early_year_prodes_intersect_with_prodes[f'geometry_{later_year}'].centroid

car_later_year_car_early_year_prodes_intersect_with_prodes['geodesic_distance'] = \
    car_later_year_car_early_year_prodes_intersect_with_prodes.apply(calculate_geodesic_distance, axis=1)

car_later_year_car_early_year_prodes_intersect_with_prodes['distance_line'] = \
    car_later_year_car_early_year_prodes_intersect_with_prodes.apply(
        lambda row: LineString([row[f'geometry_{earlier_year}'].centroid,
                                row[f'geometry_{later_year}'].centroid]),
        axis=1
    )

##############################################
#             Save Output Files              #
##############################################

print("Successfully processed data. Saving files as GeoJSON...")

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_dir = f'./outputs/{timestamp}'
os.makedirs(output_dir, exist_ok=True)

fields_to_keep = [
    'cod_imovel', f'ind_status_{later_year}', f'cod_estado_{later_year}',
    'geodesic_distance'
]

geometry_columns = {
    f"geometry_{earlier_year}": f"geometry_{earlier_year}.geojson",
    f"geometry_{later_year}": f"geometry_{later_year}.geojson",
    "geometry_prodes": "geometry_prodes.geojson",
    "distance_line": "distance_lines.geojson"
}

for geom_col, filename in geometry_columns.items():
    gdf_out = car_later_year_car_early_year_prodes_intersect_with_prodes[fields_to_keep + [geom_col]].copy()
    gdf_out = gdf_out.set_geometry(geom_col)
    gdf_out.to_file(os.path.join(output_dir, filename), driver="GeoJSON")
