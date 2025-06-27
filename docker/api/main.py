from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import Column, Integer, String, Numeric
from geoalchemy2 import Geometry
from geoalchemy2.functions import ST_AsGeoJSON, ST_Envelope, ST_AsText
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import os
import json

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgis:5432/geoanalytics")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Pydantic models
class CodImovelSuggestion(BaseModel):
    cod_imovel: str
    year: int
    state: Optional[str] = None
    tipo: Optional[str] = None

class PropertyDetails(BaseModel):
    cod_imovel: str
    year: int
    ind_status: Optional[str]
    ind_tipo: Optional[str]
    cod_estado: Optional[str]

class PropertyGeometry(BaseModel):
    cod_imovel: str
    year: int
    state: str
    geometry: Dict[str, Any]
    bounds: List[float]

# SQLAlchemy models
class CarData(Base):
    __tablename__ = "car_data"
    
    id = Column(Integer, primary_key=True)
    cod_imovel = Column(String(255), nullable=False)
    year = Column(Integer, nullable=False)
    ind_status = Column(String(10))
    ind_tipo = Column(String(10))
    cod_estado = Column(String(10))
    geometry = Column(Geometry('GEOMETRY', srid=4674))

class CarChangedToExcludeProdes(Base):
    __tablename__ = "car_changed_to_exclude_prodes"
    
    id = Column(Integer, primary_key=True)
    cod_imovel = Column(String(255))
    year_earlier = Column(Integer)
    year_later = Column(Integer)
    ind_status = Column(String(10))
    ind_tipo = Column(String(10))
    cod_estado = Column(String(10))
    geometry_earlier = Column(Geometry('GEOMETRY', srid=4674))
    geometry_later = Column(Geometry('GEOMETRY', srid=4674))
    geodesic_distance = Column(Numeric)

app = FastAPI(title="CCCA CAR Analysis API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def root():
    return {"message": "CCCA CAR Analysis API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/search/cod_imovel/{query}/{year}", response_model=List[CodImovelSuggestion])
async def search_cod_imovel(query: str, year: int, limit: int = 10, db: Session = Depends(get_db)):
    """
    Search for cod_imovel suggestions from geometry_changes view for specific year
    """
    if len(query) < 2:
        return []
    
    try:
        # Search in geometry_changes_{year}_view for properties visible on the map
        results = db.execute(
            text(f"""
                SELECT DISTINCT cod_imovel, year, ind_status, ind_tipo
                FROM geometry_changes_{year}_view 
                WHERE cod_imovel ILIKE :query 
                ORDER BY cod_imovel
                LIMIT :limit
            """),
            {"query": f"%{query}%", "limit": limit}
        ).fetchall()
        
        suggestions = []
        for row in results:
            suggestions.append(CodImovelSuggestion(
                cod_imovel=row.cod_imovel,
                year=row.year,
                state=row.ind_status,
                tipo=row.ind_tipo
            ))
        
        return suggestions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/property/{cod_imovel}", response_model=List[PropertyDetails])
async def get_property_details(cod_imovel: str, db: Session = Depends(get_db)):
    """
    Get property details for all available years
    """
    try:
        results = db.execute(
            text("""
                SELECT cod_imovel, year, ind_status, ind_tipo, cod_estado
                FROM car_data 
                WHERE cod_imovel = :cod_imovel
                ORDER BY year
            """),
            {"cod_imovel": cod_imovel}
        ).fetchall()
        
        if not results:
            raise HTTPException(status_code=404, detail="Property not found")
        
        details = []
        for row in results:
            details.append(PropertyDetails(
                cod_imovel=row.cod_imovel,
                year=row.year,
                ind_status=row.ind_status,
                ind_tipo=row.ind_tipo,
                cod_estado=row.cod_estado
            ))
        
        return details
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/property/{cod_imovel}/geometry/{year}", response_model=List[PropertyGeometry])
async def get_property_geometry(cod_imovel: str, year: int, db: Session = Depends(get_db)):
    """
    Get property geometry for a specific year, checking both comparison views and car_data
    """
    try:
        # First, try to get from geometry comparison view if it exists
        comparison_results = db.execute(
            text(f"""
                SELECT 
                    cod_imovel,
                    year,
                    state,
                    ST_AsGeoJSON(geometry) as geometry_json,
                    ST_AsText(ST_Envelope(geometry)) as bounds_wkt
                FROM geometry_changes_{year}_view 
                WHERE cod_imovel = :cod_imovel
            """),
            {"cod_imovel": cod_imovel}
        ).fetchall()
        
        if comparison_results:
            geometries = []
            for row in comparison_results:
                # Parse bounds from WKT envelope
                bounds = parse_envelope_to_bounds(row.bounds_wkt)
                
                geometries.append(PropertyGeometry(
                    cod_imovel=row.cod_imovel,
                    year=row.year,
                    state=row.state,
                    geometry=json.loads(row.geometry_json),
                    bounds=bounds
                ))
            return geometries
        
        # If not in comparison view, get from car_data directly
        car_data_results = db.execute(
            text("""
                SELECT 
                    cod_imovel,
                    year,
                    ST_AsGeoJSON(geometry) as geometry_json,
                    ST_AsText(ST_Envelope(geometry)) as bounds_wkt
                FROM car_data 
                WHERE cod_imovel = :cod_imovel AND year = :year
            """),
            {"cod_imovel": cod_imovel, "year": year}
        ).fetchall()
        
        if not car_data_results:
            raise HTTPException(status_code=404, detail=f"Property {cod_imovel} not found for year {year}")
        
        geometries = []
        for row in car_data_results:
            bounds = parse_envelope_to_bounds(row.bounds_wkt)
            
            geometries.append(PropertyGeometry(
                cod_imovel=row.cod_imovel,
                year=row.year,
                state="current",
                geometry=json.loads(row.geometry_json),
                bounds=bounds
            ))
        
        return geometries
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/property/{cod_imovel}/years")
async def get_property_years(cod_imovel: str, db: Session = Depends(get_db)):
    """
    Get all available years for a property
    """
    try:
        results = db.execute(
            text("""
                SELECT DISTINCT year
                FROM car_data 
                WHERE cod_imovel = :cod_imovel
                ORDER BY year
            """),
            {"cod_imovel": cod_imovel}
        ).fetchall()
        
        if not results:
            raise HTTPException(status_code=404, detail="Property not found")
        
        return {"cod_imovel": cod_imovel, "years": [row.year for row in results]}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

def parse_envelope_to_bounds(envelope_wkt: str) -> List[float]:
    """
    Parse PostGIS envelope WKT to [minLng, minLat, maxLng, maxLat] bounds
    Example: POLYGON((minX minY,maxX minY,maxX maxY,minX maxY,minX minY))
    """
    try:
        # Extract coordinate pairs from the WKT
        coords_str = envelope_wkt.replace("POLYGON((", "").replace("))", "")
        coord_pairs = coords_str.split(",")
        
        # Parse the first coordinate pair to get minX, minY
        min_coords = coord_pairs[0].strip().split()
        min_x, min_y = float(min_coords[0]), float(min_coords[1])
        
        # Parse the third coordinate pair to get maxX, maxY  
        max_coords = coord_pairs[2].strip().split()
        max_x, max_y = float(max_coords[0]), float(max_coords[1])
        
        return [min_x, min_y, max_x, max_y]
    except Exception as e:
        print(f"Error parsing envelope: {e}")
        return [-180, -90, 180, 90]  # Default world bounds

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)