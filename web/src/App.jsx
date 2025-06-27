import React, { useState, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import MapComponent from './components/MapComponent.jsx';
import YearToggleControls from './components/YearToggleControls.jsx';
import Navbar from './components/Navbar.jsx';
import Sidebar from './components/Sidebar.jsx';

export default function App() {
  // Track which year comparisons are visible (year-over-year view)
  const [visibleYearComparisons, setVisibleYearComparisons] = useState(new Set());
  
  // Track sidebar open/closed state
  const [sidebarOpen, setSidebarOpen] = useState(false);
  
  // Map instance reference
  const mapInstance = useRef(null);

  // Toggle function - toggles year-over-year comparison for a specific year
  const toggleYear = (comparisonYear) => {
    setVisibleYearComparisons(prev => {
      const newSet = new Set(prev);
      if (newSet.has(comparisonYear)) {
        newSet.delete(comparisonYear);
      } else {
        newSet.add(comparisonYear);
      }
      return newSet;
    });
  };

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const closeSidebar = () => {
    setSidebarOpen(false);
  };

  // Handle map ready
  const handleMapReady = (mapRef) => {
    mapInstance.current = mapRef;
  };

  // Navigate to property on map
  const handleNavigateToProperty = async (codImovel) => {
    if (!mapInstance.current) {
      console.warn('Map not ready yet');
      return;
    }

    try {
      // Get the active year from visibleYearComparisons
      const activeYear = Array.from(visibleYearComparisons)[0];
      
      // First, try to get geometry from the API
      const response = await fetch(`http://localhost:8000/api/property/${encodeURIComponent(codImovel)}/geometry/${activeYear}`);
      
      if (response.ok) {
        const geometries = await response.json();
        
        if (geometries.length > 0) {
          // Use the bounds from the API response
          const geometry = geometries[0];
          const [minLng, minLat, maxLng, maxLat] = geometry.bounds;
          
          // Create bounds and fit map
          const bounds = new maplibregl.LngLatBounds([minLng, minLat], [maxLng, maxLat]);
          
          mapInstance.current.fitBounds(bounds, {
            padding: 50,
            maxZoom: 16
          });

          console.log(`Navigated to cod_imovel: ${codImovel} using API`);
          return;
        }
      }
      
      // Fallback: Query the map tiles directly (original approach)
      console.log('API lookup failed, trying map tile query...');
      
      // Get all features from visible layers
      const allFeatures = mapInstance.current.querySourceFeatures(
        `geometry_changes_${activeYear}_view.1`,
        {
          filter: ['==', 'cod_imovel', codImovel]
        }
      );

      if (allFeatures.length > 0) {
        // Get the first feature to calculate bounds
        const feature = allFeatures[0];
        
        // Create bounds from the feature geometry
        const bounds = new maplibregl.LngLatBounds();
        
        if (feature.geometry.type === 'Polygon') {
          feature.geometry.coordinates[0].forEach(coord => {
            bounds.extend(coord);
          });
        } else if (feature.geometry.type === 'MultiPolygon') {
          feature.geometry.coordinates.forEach(polygon => {
            polygon[0].forEach(coord => {
              bounds.extend(coord);
            });
          });
        } else if (feature.geometry.type === 'Point') {
          bounds.extend(feature.geometry.coordinates);
          // For points, add some padding around the location
          const padding = 0.01; // roughly 1km at equator
          bounds.extend([
            feature.geometry.coordinates[0] - padding,
            feature.geometry.coordinates[1] - padding
          ]);
          bounds.extend([
            feature.geometry.coordinates[0] + padding,
            feature.geometry.coordinates[1] + padding
          ]);
        }

        // Fit the map to the feature bounds
        mapInstance.current.fitBounds(bounds, {
          padding: 50,
          maxZoom: 16
        });

        console.log(`Navigated to cod_imovel: ${codImovel} using map tiles`);
      } else {
        console.warn(`No features found for cod_imovel: ${codImovel}`);
        alert(`Property ${codImovel} not found in the selected year.`);
      }
    } catch (error) {
      console.error('Error navigating to property:', error);
      alert('Error finding the property. Please try again.');
    }
  };

  // Check if navigation is allowed (exactly one year selected)
  const canNavigate = visibleYearComparisons.size === 1;

  return (
    <div className="app">
      <div className={`app-container ${sidebarOpen ? 'sidebar-open' : ''}`}>
        <Sidebar isOpen={sidebarOpen} onClose={closeSidebar}>
          <div className="sidebar-placeholder">
            <h3>Sidebar Content</h3>
            <p>Placeholder for more controls, such as filtering by State</p>
          </div>
        </Sidebar>
        <div className="main-layout">
          <Navbar 
            onToggleSidebar={toggleSidebar}
            githubUrl="https://github.com/jpjon/CCCA_CAR_Analysis"
          />
          <div className="content-area">
            <YearToggleControls 
              visibleYearComparisons={visibleYearComparisons}
              onToggleYear={toggleYear}
              onNavigateToProperty={handleNavigateToProperty}
              canNavigate={canNavigate}
            />
            <div className="map-container">
              <MapComponent 
                visibleYearComparisons={visibleYearComparisons} 
                onMapReady={handleMapReady}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}