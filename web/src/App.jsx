import React, { useState } from 'react';
import MapComponent from './components/MapComponent.jsx';
import YearToggleControls from './components/YearToggleControls.jsx';

export default function App() {
  // Track which year comparisons are visible (year-over-year view)
  const [visibleYearComparisons, setVisibleYearComparisons] = useState(new Set());

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

  return (
    <div className="app">
      <MapComponent visibleYearComparisons={visibleYearComparisons} />
      <YearToggleControls 
        visibleYearComparisons={visibleYearComparisons}
        onToggleYear={toggleYear}
      />
    </div>
  );
}