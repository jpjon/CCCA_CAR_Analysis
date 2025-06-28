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
  
  // Track selected properties for distance lines (per year)
  const [selectedProperties, setSelectedProperties] = useState({});
  
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
          
          // Add property to selected properties for distance line display
          addSelectedProperty(codImovel, activeYear);
          
          return;
        }
      }
      
      // Fallback: Query the map tiles directly (original approach)
      console.warn(`No geometry found for cod_imovel: ${codImovel}`);
      alert(`Property ${codImovel} not found in the selected year.`);
      
    } catch (error) {
      console.error('Error navigating to property:', error);
      alert('Error finding the property. Please try again.');
    }
  };

  // Add property to selected properties for distance line display
  const addSelectedProperty = (codImovel, year) => {
    setSelectedProperties(prev => {
      const newSelected = { ...prev };
      if (!newSelected[year]) {
        newSelected[year] = new Set();
      } else {
        newSelected[year] = new Set(newSelected[year]);
      }
      newSelected[year].add(codImovel);
      return newSelected;
    });
  };

  // Clear all selected properties (for clear lines button)
  const clearAllSelectedProperties = () => {
    setSelectedProperties({});
  };

  // Check if navigation is allowed (exactly one year selected)
  const canNavigate = visibleYearComparisons.size === 1;

  return (
    <div className="app">
      <div className={`app-container ${sidebarOpen ? 'sidebar-open' : ''}`}>
        <Sidebar isOpen={sidebarOpen} onClose={closeSidebar}>
          <div className="sidebar-placeholder">
            <h3>Sidebar Content</h3>
            <p>Placeholder for data visualization</p>
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
              onClearLines={clearAllSelectedProperties}
            />
            <div className="map-container">
              <MapComponent 
                visibleYearComparisons={visibleYearComparisons} 
                onMapReady={handleMapReady}
                selectedProperties={selectedProperties}
                onPropertyClick={addSelectedProperty}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}