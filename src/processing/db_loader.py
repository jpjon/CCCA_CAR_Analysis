import geopandas as gpd
from sqlalchemy import create_engine, text
import pandas as pd
from datetime import datetime
import os

class PostGISLoader:
    def __init__(self, connection_string="postgresql://postgres:postgres@localhost:5432/geoanalytics"):
        self.engine = create_engine(connection_string)
        
    def load_car_data(self, gdf, year):
        """Load CAR data into year-specific table"""
        table_name = f"car_{year}"
        
        # Ensure geometry column is properly set
        if gdf.crs is None:
            gdf = gdf.set_crs("EPSG:4674")
        else:
            gdf = gdf.to_crs("EPSG:4674")
        
        # Load to PostGIS
        print(f"Loading {len(gdf)} records to {table_name}...")
        gdf.to_postgis(
            table_name, 
            self.engine, 
            if_exists='replace', 
            index=False,
            dtype={'geometry': 'geometry'}
        )
        print(f"Successfully loaded data to {table_name}")
        
    def load_prodes_data(self, gdf):
        """Load PRODES data"""
        if gdf.crs is None:
            gdf = gdf.set_crs("EPSG:4674")
        else:
            gdf = gdf.to_crs("EPSG:4674")
            
        print(f"Loading {len(gdf)} PRODES records...")
        gdf.to_postgis(
            "prodes", 
            self.engine, 
            if_exists='replace', 
            index=False,
            dtype={'geometry': 'geometry'}
        )
        print("Successfully loaded PRODES data")
        
    def save_analysis_results(self, results_df):
        """Save analysis results to database"""
        # Remove geometry columns for the analysis table
        results_df = results_df.drop(columns=[col for col in results_df.columns if 'geometry' in col or 'centroid' in col])
        
        print("Saving analysis results...")
        results_df.to_sql(
            "analysis_results",
            self.engine,
            if_exists='append',
            index=False
        )
        print("Analysis results saved")