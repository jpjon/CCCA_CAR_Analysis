-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create single CAR table with year column
CREATE TABLE IF NOT EXISTS car_data (
    id SERIAL PRIMARY KEY,
    cod_imovel VARCHAR(255) NOT NULL,
    year INTEGER NOT NULL,
    ind_status VARCHAR(10),
    ind_tipo VARCHAR(10),
    cod_estado VARCHAR(10),
    geometry GEOMETRY(Geometry, 4674),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Ensure unique cod_imovel per year
    UNIQUE(cod_imovel, year)
);

-- Create PRODES table
CREATE TABLE IF NOT EXISTS prodes (
    id SERIAL PRIMARY KEY,
    uuid VARCHAR(255) UNIQUE NOT NULL,
    num_corners INTEGER,
    geometry GEOMETRY(MultiPolygon, 4674),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create comprehensive indexes for performance
-- Spatial index (critical for ST_Intersects and other spatial operations)
CREATE INDEX idx_car_data_geometry ON car_data USING GIST (geometry);

-- Compound index for year + cod_imovel lookups (very important for joins)
CREATE INDEX idx_car_data_year_cod_imovel ON car_data (year, cod_imovel);

-- Individual indexes for filtering
CREATE INDEX idx_car_data_year ON car_data (year);
CREATE INDEX idx_car_data_cod_imovel ON car_data (cod_imovel);

-- Index for status filtering
CREATE INDEX idx_car_data_ind_status ON car_data (ind_status);

-- Index for tipo filtering
CREATE INDEX idx_car_data_ind_tipo ON car_data (ind_tipo);

-- Compound index for your typical WHERE clause pattern
CREATE INDEX idx_car_data_tipo_status_year ON car_data (ind_tipo, ind_status, year) 
WHERE ind_tipo = 'IRU' AND ind_status IN ('AT', 'PE');

-- PRODES indexes (unchanged)
CREATE INDEX idx_prodes_geometry ON prodes USING GIST (geometry);
CREATE INDEX idx_prodes_uuid ON prodes (uuid);