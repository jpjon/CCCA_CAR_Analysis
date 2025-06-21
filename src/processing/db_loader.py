import geopandas as gpd
from sqlalchemy import create_engine, text
import pandas as pd
from datetime import datetime
import os

class PostGISLoader:
    def __init__(self, connection_string="postgresql://postgres:postgres@localhost:5432/geoanalytics"):
        self.engine = create_engine(connection_string)
        
    def load_car_data(self, gdf, year):
        """Load CAR data into unified table with year column"""
        
        # Add year column to the dataframe
        gdf['year'] = year
        
        # Ensure geometry column is properly set
        if gdf.crs is None:
            gdf = gdf.set_crs("EPSG:4674")
        else:
            gdf = gdf.to_crs("EPSG:4674")
        
        # Load to PostGIS
        print(f"Loading {len(gdf)} records for year {year}...")
        
        # First time loading? Use 'replace'. Otherwise 'append'
        # Check if table exists and has data
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'car_data'
                );
            """)).scalar()
            
            table_exists = result
            
            if table_exists:
                # Check if this year's data already exists
                year_exists = conn.execute(
                    text("SELECT EXISTS(SELECT 1 FROM car_data WHERE year = :year LIMIT 1);"),
                    {"year": year}
                ).scalar()
                
                if year_exists:
                    # Delete existing data for this year before inserting
                    print(f"Removing existing data for year {year}...")
                    conn.execute(text("DELETE FROM car_data WHERE year = :year;"), {"year": year})
                    conn.commit()
        
        # Load the data
        gdf.to_postgis(
            "car_data", 
            self.engine, 
            if_exists='append' if table_exists else 'replace', 
            index=False,
            dtype={'geometry': 'geometry'}
        )
        
        print(f"Successfully loaded {len(gdf)} records for year {year}")
        
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
        
    def execute_sql(self, sql_query):
        """Execute a SQL query"""
        with self.engine.connect() as conn:
            conn.execute(text(sql_query))
            conn.commit()
            
    def get_year_summary(self):
        """Get summary of loaded CAR data by year"""
        query = """
        SELECT 
            year,
            COUNT(*) as record_count,
            COUNT(DISTINCT cod_imovel) as unique_properties,
            COUNT(DISTINCT cod_estado) as states_count
        FROM car_data
        GROUP BY year
        ORDER BY year;
        """
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query))
            return result.fetchall()