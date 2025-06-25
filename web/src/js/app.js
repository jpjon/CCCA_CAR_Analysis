// Initialize the map
const map = new maplibregl.Map({
    container: 'map',
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
            'geometry_changes_2025_view.1': {
                type: 'vector',
                tiles: ['http://localhost:3000/geometry_changes_2025_view.1/{z}/{x}/{y}']
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
    center: [-50.5, -5.5], // Centered on Pará
    zoom: 8
});

// Add navigation controls
map.addControl(new maplibregl.NavigationControl());

// Add layers when map loads
map.on('load', () => {

    // Add CAR data
    map.addLayer({
        id: 'before-geometries',
        type: 'fill',
        filter: ['==', 'state', 'before'],
        source: 'geometry_changes_2025_view.1',
        'source-layer': 'geometry_changes_2025_view.1',
        paint: {
            'fill-color': '#165fc9',
            'fill-opacity': 0.5
        }
    });

    // Add CAR data
    map.addLayer({
        id: 'after-geometries',
        type: 'fill',
        filter: ['==', 'state', 'after'],
        source: 'geometry_changes_2025_view.1',
        'source-layer': 'geometry_changes_2025_view.1',
        paint: {
            'fill-color': '#c91616',
            'fill-opacity': 0.5
        }
    });

    // Add relevant_prodes_subdivided data
    map.addLayer({
        id: 'relevant_prodes_subdivided-fill',
        type: 'fill',
        source: 'relevant_prodes_subdivided',
        'source-layer': 'relevant_prodes_subdivided',
        paint: {
            'fill-color': '#6E260E',
            'fill-opacity': 0.5,
            'fill-outline-color': 'transparent' // This removes the outline
        }
    });

    // Create a popup instance (but don't add it to the map yet)
    const popup = new maplibregl.Popup({
        closeButton: true,
        closeOnClick: true
    });

    // Add click event on the map
    map.on('click', (e) => {
        const features = map.queryRenderedFeatures(e.point, {
            layers: ['before-geometries', 'after-geometries']
        });

        if (!features.length) return;

        const feature = features[0];

        // Extract properties you want
        const { cod_imovel, year } = feature.properties;

        // Set the popup content
        popup.setLngLat(e.lngLat)
            .setHTML(`
                <strong>cod_imovel:</strong> ${cod_imovel}<br>
                <strong>year:</strong> ${year}
            `)
            .addTo(map);
    });


    console.log('Map loaded with all layers!');
});