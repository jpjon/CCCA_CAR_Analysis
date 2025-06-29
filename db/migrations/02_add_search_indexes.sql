-- Add text search indexes for cod_imovel search functionality for frontend

-- GIN index for fast prefix matching on cod_imovel
CREATE INDEX IF NOT EXISTS idx_car_data_cod_imovel_gin 
ON car_data USING GIN (cod_imovel gin_trgm_ops);

-- Add trigram index for fuzzy text search
CREATE INDEX IF NOT EXISTS idx_car_data_cod_imovel_trgm 
ON car_data USING GIN (cod_imovel gin_trgm_ops);

-- Composite index for year-specific searches
CREATE INDEX IF NOT EXISTS idx_car_data_year_cod_imovel_trgm 
ON car_data (year, cod_imovel text_pattern_ops);

-- Index for the geometry changes views
CREATE INDEX IF NOT EXISTS idx_car_changed_cod_imovel_trgm 
ON car_changed_to_exclude_prodes USING GIN (cod_imovel gin_trgm_ops);