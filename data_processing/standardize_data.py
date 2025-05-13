import geopandas as gpd
import pandas as pd

def standardize_car_data(car_gdf):
    """
    Standardizes the CAR data by renaming columns.
    
    Parameters:
    car_gdf (GeoDataFrame): The GeoDataFrame containing CAR data.
    
    Returns:
    GeoDataFrame: The standardized GeoDataFrame.
    """
    
    
    # Define raw-to-standard column name mapping
    rename_map = {
        'COD_IMOVEL': 'cod_imovel',
        'COD_ESTADO': 'cod_estado',
        'TIPO_IMOVE': 'ind_tipo',
        'SITUACAO': 'ind_status'
    }

    # Filter the rename map to only include keys that exist in the GeoDataFrame
    safe_rename_map = {k: v for k, v in rename_map.items() if k in car_gdf.columns}

    # Perform the renaming
    car_gdf = car_gdf.rename(columns=safe_rename_map)

    
    return car_gdf