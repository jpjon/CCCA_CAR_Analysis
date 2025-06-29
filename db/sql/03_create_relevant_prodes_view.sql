-- Add relevant prodes geometry for visualization
UPDATE relevant_prodes rp
SET geometry = p.geometry
FROM prodes p
WHERE rp.uuid = p.uuid
  AND rp.geometry IS NULL;

-- Create subdivided relevant prodes for better load on visualization
INSERT INTO relevant_prodes_subdivided (uuid, geometry)
SELECT 
    rp.uuid,
    ST_Subdivide(rp.geometry, 256) AS geometry
FROM relevant_prodes rp;


-- Create spatial index on subdivided geometries
CREATE INDEX idx_relevant_prodes_subdivided_geom ON relevant_prodes_subdivided USING GIST (geometry);