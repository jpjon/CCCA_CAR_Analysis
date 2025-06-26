import { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import '../styles/MapComponent.css';
import { CONFIG } from '../config/config.js';
import { generateYearColors } from '../utils/colors.js';

export default function MapComponent({ visibleYearComparisons  }) {
  const mapContainerRef = useRef(null);
  const map = useRef(null);
  const mapLoaded = useRef(false);
  const yearColors = generateYearColors(CONFIG.years);

  useEffect(() => {
    // Initialize the map
    map.current = new maplibregl.Map({
      container: mapContainerRef.current,
      style: {
        version: 8,
        sources: {
          'osm': {
            type: 'raster',
            tiles: [
              'https://a.tile.openstreetmap.org/{z}/{x}/{y}.png',
              'https://b.tile.openstreetmap.org/{z}/{x}/{y}.png',
              'https://c.tile.openstreetmap.org/{z}/{x}/{y}.png'
            ],
            tileSize: 256,
            attribution: '© OpenStreetMap contributors'
          },
          'relevant_prodes_subdivided': {
            type: 'vector',
            tiles: ['http://localhost:3000/relevant_prodes_subdivided/{z}/{x}/{y}']
          }
        },
        layers: [{
          id: 'osm-base',
          type: 'raster',
          source: 'osm'
        }]
      },
      center: [-55.0217, -8.1190], // Centered on Manaus
      zoom: 4
    });

    // Add navigation controls
    map.current.addControl(new maplibregl.NavigationControl());

    // When the map is fully loaded
    map.current.on('load', () => {

      // Add sources and layers for each table
      CONFIG.years.forEach(tableYear => {
        const sourceId = `geometry_changes_${tableYear}_view.1`;
            
        // Add source
        map.current.addSource(sourceId, {
          type: 'vector',
          tiles: [`http://localhost:3000/geometry_changes_${tableYear}_view.1/{z}/{x}/{y}`]
        });
        console.log(sourceId)
        // Add "before" layer (shows geometries from tableYear-1)
        map.current.addLayer({
          id: `table-${tableYear}-before`,
          type: 'fill',
          filter: ['==', 'state', 'before'],
          source: sourceId,
          'source-layer': sourceId,
          paint: {
            'fill-color': yearColors[tableYear]?.before || '#999999',
            'fill-opacity': 0.7
          },
          layout: {
            // 'visibility': 'none'
          }
        });

        // Add "after" layer (shows geometries from tableYear)
        map.current.addLayer({
          id: `table-${tableYear}-after`,
          type: 'fill',
          filter: ['==', 'state', 'after'],
          source: sourceId,
          'source-layer': sourceId,
          paint: {
            'fill-color': yearColors[tableYear]?.after || '#666666',
            'fill-opacity': 0.7
          },
          layout: {
            // 'visibility': 'none'
          }
        });
      });


      // Add relevant_prodes_subdivided layer
      map.current.addLayer({
        id: 'relevant_prodes_subdivided-fill',
        type: 'fill',
        source: 'relevant_prodes_subdivided',
        'source-layer': 'relevant_prodes_subdivided',
        paint: {
          'fill-color': '#6E260E',
          'fill-opacity': 0.5,
          'fill-outline-color': 'transparent'
        }
      });

      // Mark the map as loaded
      mapLoaded.current = true;

      // Add popup functionality
      const popup = new maplibregl.Popup({
        closeButton: true,
        closeOnClick: true
      });

      // Add click event listener
      map.current.on('click', (e) => {
          const allLayerIds = CONFIG.years.flatMap(tableYear => 
            [`table-${tableYear}-before`, `table-${tableYear}-after`]
          );
          
        const features = map.current.queryRenderedFeatures(e.point, { layers: allLayerIds });

        if (!features.length) return;

        const feature = features[0];
        const { cod_imovel, state } = feature.properties;
        console.log(feature)
        // Determine which table this came from and what actual year it represents
        const layerId = feature.layer.id;
        const tableYear = parseInt(layerId.match(/table-(\d+)-/)[1]);
        const actualYear = state === 'before' ? tableYear - 1 : tableYear;

        popup.setLngLat(e.lngLat)
          .setHTML(`
              <strong>Actual Year:</strong> ${actualYear}<br>
              <strong>State:</strong> ${state}<br>
              <strong>cod_imovel:</strong> ${cod_imovel}<br>
              <small>From table: ${tableYear}</small>
          `)
          .addTo(map.current);
      });

      console.log('Map loaded with all layers!');
    });

    // Cleanup on unmount
    return () => {
      map.current?.remove();
    };
  }, []);

  // Update layer visibility when visibleYearComparisons changes
  useEffect(() => {
    if (!map.current || !mapLoaded.current) return;

    try {
      CONFIG.years.forEach(tableYear => {
        const beforeLayerId = `table-${tableYear}-before`;
        const afterLayerId = `table-${tableYear}-after`;
        
        // Check if layers exist before trying to modify them
        if (map.current.getLayer(beforeLayerId) && map.current.getLayer(afterLayerId)) {
          const showComparison = visibleYearComparisons.has(tableYear);
          map.current.setLayoutProperty(beforeLayerId, 'visibility', showComparison ? 'visible' : 'none');
          map.current.setLayoutProperty(afterLayerId, 'visibility', showComparison ? 'visible' : 'none');
        }
      });
    } catch (error) {
      console.error('MapComponent: Error updating layer visibility:', error);
    }
  }, [visibleYearComparisons]);

  console.log('MapComponent: Rendering map container');

  return (
    <div className="map-wrap">
      <div ref={mapContainerRef} className="map" />
    </div>
  );
}
