// Initialize the map
const map = new maplibregl.Map({
    container: 'map',
    style: {
        version: 8,
        sources: {
            'carto-light': {
                type: 'raster',
                tiles: ['https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png'],
                tileSize: 256,
                attribution: '© CARTO'
            },
            'car_changed_to_exclude_prodes': {
                type: 'vector',
                tiles: ['http://localhost:3000/car_changed_to_exclude_prodes.3/{z}/{x}/{y}']
            },
            'prodes': {
                type: 'vector',
                tiles: ['http://localhost:3000/prodes/{z}/{x}/{y}']
            }
        },
        layers: [{
            id: 'carto-base',
            type: 'raster',
            source: 'carto-light'
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
        id: 'car-fill',
        type: 'fill',
        source: 'car_changed_to_exclude_prodes.3',
        'source-layer': 'car_changed_to_exclude_prodes.3',
        paint: {
            'fill-color': '#0000FF',
            'fill-opacity': 0.5
        }
    });
    // Add PRODES data
    map.addLayer({
        id: 'prodes-fill',
        type: 'fill',
        source: 'prodes',
        'source-layer': 'prodes',
        paint: {
            'fill-color': '#FFD93D',
            'fill-opacity': 0.5
        }
    });

    console.log('Map loaded with all layers!');
});