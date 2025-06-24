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
    UNIQUE(cod_imovel, year)
);

-- Spatial index (critical for ST_Intersects and other spatial operations)
CREATE INDEX idx_car_data_geometry ON car_data USING GIST (geometry);
-- Compound index for year + cod_imovel lookups (very important for joins)
CREATE INDEX idx_car_data_year_cod_imovel ON car_data (year, cod_imovel);
-- Individual indexes for filtering by cod_imovel
CREATE INDEX idx_car_data_cod_imovel ON car_data (cod_imovel);

-- Create PRODES table
CREATE TABLE IF NOT EXISTS prodes (
    id SERIAL PRIMARY KEY,
    uuid VARCHAR(255) UNIQUE NOT NULL,
    num_corners INTEGER,
    area_km NUMERIC(10, 2) NOT NULL,
    geometry GEOMETRY(MultiPolygon, 4674)
);

-- PRODES indexes
CREATE INDEX idx_prodes_geometry ON prodes USING GIST (geometry);
CREATE INDEX idx_prodes_uuid ON prodes (uuid);

CREATE TABLE car_changed_to_exclude_prodes (
    id SERIAL PRIMARY KEY,
    cod_imovel VARCHAR(255),
    year_earlier INTEGER,
    year_later INTEGER,
    ind_status VARCHAR(10),
    ind_tipo VARCHAR(10),
    cod_estado VARCHAR(10),
    geometry_earlier GEOMETRY(Geometry, 4674),
    geometry_later GEOMETRY(Geometry, 4674),
    centroid_earlier GEOMETRY(Point, 4674),
    centroid_later GEOMETRY(Point, 4674),
    geodesic_distance DOUBLE PRECISION,
    distance_line GEOMETRY(LineString, 4674)
);

CREATE INDEX idx_changed_year_pair ON car_changed_to_exclude_prodes(year_earlier, year_later);
CREATE INDEX idx_changed_cod_imovel ON car_changed_to_exclude_prodes(cod_imovel);
CREATE INDEX idx_changed_geodesic_distance ON car_changed_to_exclude_prodes(geodesic_distance);

-- PRODES table with only relevant geometries post analysis
CREATE TABLE IF NOT EXISTS relevant_prodes (
    uuid VARCHAR(255) UNIQUE NOT NULL,
    geometry GEOMETRY(MultiPolygon, 4674)
);

-- Subdivided PRODES table with only relevant geometries post analysis
CREATE TABLE IF NOT EXISTS relevant_prodes_subdivided (
    uuid VARCHAR(255),
    geometry GEOMETRY(MultiPolygon, 4674)
);