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
            'car-2024': {
                type: 'vector',
                tiles: ['http://localhost:3000/car_2024/{z}/{x}/{y}']
            },
            'car-2025': {
                type: 'vector',
                tiles: ['http://localhost:3000/car_2025/{z}/{x}/{y}']
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
    // Add 2024 CAR data
    map.addLayer({
        id: 'car-2024-fill',
        type: 'fill',
        source: 'car-2024',
        'source-layer': 'car_2024',
        paint: {
            'fill-color': '#FF6B6B',
            'fill-opacity': 0.6
        }
    });

    // Add 2025 CAR data
    map.addLayer({
        id: 'car-2025-fill',
        type: 'fill',
        source: 'car-2025',
        'source-layer': 'car_2025',
        paint: {
            'fill-color': '#4ECDC4',
            'fill-opacity': 0.6
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