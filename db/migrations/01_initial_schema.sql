-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create tables for each year of CAR data
CREATE TABLE IF NOT EXISTS car_2024 (
    id SERIAL PRIMARY KEY,
    cod_imovel VARCHAR(255) UNIQUE NOT NULL,
    ind_status VARCHAR(10),
    ind_tipo VARCHAR(10),
    cod_estado VARCHAR(10),
    geometry GEOMETRY(MultiPolygon, 4674),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS car_2025 (
    id SERIAL PRIMARY KEY,
    cod_imovel VARCHAR(255) UNIQUE NOT NULL,
    ind_status VARCHAR(10),
    ind_tipo VARCHAR(10),
    cod_estado VARCHAR(10),
    geometry GEOMETRY(MultiPolygon, 4674),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create PRODES table
CREATE TABLE IF NOT EXISTS prodes (
    id SERIAL PRIMARY KEY,
    uuid VARCHAR(255) UNIQUE NOT NULL,
    num_corners INTEGER,
    geometry GEOMETRY(MultiPolygon, 4674),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create analysis results table
CREATE TABLE IF NOT EXISTS analysis_results (
    id SERIAL PRIMARY KEY,
    cod_imovel VARCHAR(255) NOT NULL,
    year_earlier INTEGER,
    year_later INTEGER,
    geometry_changed BOOLEAN,
    geodesic_distance FLOAT,
    intersects_prodes_earlier BOOLEAN,
    intersects_prodes_later BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(cod_imovel, year_earlier, year_later)
);

-- Create indexes for performance
CREATE INDEX idx_car_2024_geometry ON car_2024 USING GIST (geometry);
CREATE INDEX idx_car_2025_geometry ON car_2025 USING GIST (geometry);
CREATE INDEX idx_prodes_geometry ON prodes USING GIST (geometry);
CREATE INDEX idx_car_2024_cod_imovel ON car_2024 (cod_imovel);
CREATE INDEX idx_car_2025_cod_imovel ON car_2025 (cod_imovel);