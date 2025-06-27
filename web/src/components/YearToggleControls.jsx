import React from 'react';
import { CONFIG } from '../config/config.js';
import { generateYearColors } from '../utils/colors.js';
import SearchComponent from './SearchComponent.jsx';
import '../styles/YearToggleComponent.css'; 

export default function YearToggleControls({ 
  visibleYearComparisons, 
  onToggleYear, 
  onNavigateToProperty, 
  canNavigate 
}) {
  const yearColors = generateYearColors(CONFIG.years);

  return (
    <div id="year-controls">
      <h3>Year-over-Year Comparisons</h3>
      {CONFIG.years.map(year => (
        <label key={year} className="year-toggle">
          <input
            type="checkbox"
            checked={visibleYearComparisons.has(year)}
            onChange={() => onToggleYear(year)}
          />
          <span> {year} YoY </span>
          <span style={{ marginLeft: '8px' }}>
            <span
              className="color-swatch"
              style={{ backgroundColor: yearColors[year].before }}
              title={`${year - 1} (before)`}
            />
            <span
              className="color-swatch"
              style={{
                backgroundColor: yearColors[year].after,
                marginLeft: '2px'
              }}
              title={`${year} (after)`}
            />
          </span>
        </label>
      ))}
      
      <div className="search-section">
        <h4>Search Property</h4>
        <SearchComponent
          onNavigateToProperty={onNavigateToProperty}
          visibleYearComparisons={visibleYearComparisons}
          canNavigate={canNavigate}
        />
      </div>
    </div>
  );
}
