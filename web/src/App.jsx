import React, { useState } from 'react';
import MapComponent from './components/MapComponent.jsx';
import YearToggleControls from './components/YearToggleControls.jsx';
import Navbar from './components/Navbar.jsx';
import Sidebar from './components/Sidebar.jsx';

export default function App() {
  // Track which year comparisons are visible (year-over-year view)
  const [visibleYearComparisons, setVisibleYearComparisons] = useState(new Set());
  
  // Track sidebar open/closed state
  const [sidebarOpen, setSidebarOpen] = useState(false);

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
            />
            <div className="map-container">
              <MapComponent visibleYearComparisons={visibleYearComparisons} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}