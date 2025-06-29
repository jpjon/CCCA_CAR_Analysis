-- this worked, is this viable? can do in the beginning
DROP TABLE IF EXISTS prodes_subdivided;
EXPLAIN ANALYZE CREATE TABLE prodes_subdivided AS
SELECT 
    -- Subdivide into max 256 vertices per geometry
    ST_Subdivide(p.geometry, 256) as geometry
FROM prodes p;

-- Create spatial index on subdivided geometries
CREATE INDEX idx_prodes_subdivided_geom ON prodes_subdivided USING GIST (geometry);
