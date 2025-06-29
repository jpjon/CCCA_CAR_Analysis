import React from 'react';
import { FaTrash } from 'react-icons/fa';
import { CONFIG } from '../config/config.js';
import { generateYearColors } from '../utils/colors.js';
import SearchComponent from './SearchComponent.jsx';
import '../styles/YearToggleComponent.css'; 

export default function YearToggleControls({ 
  visibleYearComparisons, 
  onToggleYear, 
  onNavigateToProperty, 
  canNavigate,
  onClearLines
}) {
  const yearColors = generateYearColors(CONFIG.years);

  return (
    <div id="year-controls">
      <div className="legend-section">
        <h3>Deforested Areas</h3>
        <div className="legend-item">
          <span
            className="color-swatch"
            style={{ backgroundColor: "#6E260E" }}
            title="Deforested areas (PRODES data)"
          />
          <span className="legend-label">PRODES Data</span>
        </div>
      </div>
      
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
      
      <div className="clear-lines-section">
        <button className="clear-lines-button" onClick={onClearLines}>
          <FaTrash className="clear-lines-icon" />
          Clear Lines
        </button>
      </div>
      
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
