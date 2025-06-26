import { useState, useEffect, useRef } from 'react';
import { FaSearch, FaHistory, FaTimes } from 'react-icons/fa';
import '../styles/SearchComponent.css';

export default function SearchComponent({ 
  onNavigateToProperty, 
  visibleYearComparisons, 
  canNavigate 
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [searchHistory, setSearchHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const dropdownRef = useRef(null);
  const inputRef = useRef(null);

  // Load search history from localStorage
  useEffect(() => {
    const savedHistory = localStorage.getItem('cod_imovel_search_history');
    if (savedHistory) {
      setSearchHistory(JSON.parse(savedHistory));
    }
  }, []);

  // Save search history to localStorage
  const saveSearchHistory = (newHistory) => {
    localStorage.setItem('cod_imovel_search_history', JSON.stringify(newHistory));
    setSearchHistory(newHistory);
  };

  // Add to search history
  const addToHistory = (codImovel) => {
    const newHistory = [codImovel, ...searchHistory.filter(item => item !== codImovel)].slice(0, 10);
    saveSearchHistory(newHistory);
  };

  // Clear search history
  const clearHistory = () => {
    saveSearchHistory([]);
  };

  // API call for cod_imovel suggestions
  const fetchSuggestions = async (term) => {
    if (!term || term.length < 2) {
      setSuggestions([]);
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/api/search/cod_imovel/${encodeURIComponent(term)}?limit=10`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      // Extract unique cod_imovel values from the response
      const uniqueSuggestions = [...new Set(data.map(item => item.cod_imovel))];
      
      setSuggestions(uniqueSuggestions);
    } catch (error) {
      console.error('Error fetching suggestions:', error);
      setSuggestions([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle input change
  const handleInputChange = (e) => {
    const value = e.target.value;
    setSearchTerm(value);
    setShowHistory(false);
    
    if (value.trim()) {
      fetchSuggestions(value);
      setShowDropdown(true);
    } else {
      setSuggestions([]);
      setShowDropdown(false);
    }
  };

  // Handle suggestion selection
  const handleSuggestionSelect = (codImovel) => {
    setSearchTerm(codImovel);
    setShowDropdown(false);
    setShowHistory(false);
    addToHistory(codImovel);
    
    if (canNavigate) {
      onNavigateToProperty(codImovel);
    }
  };

  // Handle history item selection
  const handleHistorySelect = (codImovel) => {
    setSearchTerm(codImovel);
    setShowHistory(false);
    setShowDropdown(false);
    
    if (canNavigate) {
      onNavigateToProperty(codImovel);
    }
  };

  // Handle search submit
  const handleSubmit = (e) => {
    e.preventDefault();
    if (searchTerm.trim() && canNavigate) {
      addToHistory(searchTerm);
      onNavigateToProperty(searchTerm);
      setShowDropdown(false);
      setShowHistory(false);
    }
  };

  // Handle clicking outside dropdown
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
        setShowHistory(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Show history when input is focused and empty
  const handleInputFocus = () => {
    if (!searchTerm && searchHistory.length > 0) {
      setShowHistory(true);
      setShowDropdown(false);
    }
  };

  const getStatusMessage = () => {
    const yearCount = visibleYearComparisons.size;
    if (yearCount === 0) {
      return "Select a year to enable search";
    } else if (yearCount > 1) {
      return "Select only one year to enable search";
    }
    return "Search for cod_imovel";
  };

  return (
    <div className="search-component" ref={dropdownRef}>
      <form onSubmit={handleSubmit} className="search-form">
        <div className="search-input-container">
          <FaSearch className="search-icon" />
          <input
            ref={inputRef}
            type="text"
            value={searchTerm}
            onChange={handleInputChange}
            onFocus={handleInputFocus}
            placeholder={getStatusMessage()}
            className={`search-input ${!canNavigate ? 'disabled' : ''}`}
            disabled={!canNavigate}
          />
          {searchHistory.length > 0 && (
            <FaHistory 
              className="history-icon" 
              onClick={() => {
                setShowHistory(!showHistory);
                setShowDropdown(false);
              }}
              title="Search History"
            />
          )}
        </div>
      </form>

      {/* Suggestions Dropdown */}
      {showDropdown && suggestions.length > 0 && (
        <div className="dropdown suggestions-dropdown">
          <div className="dropdown-header">Suggestions</div>
          {isLoading ? (
            <div className="dropdown-item loading">Loading...</div>
          ) : (
            suggestions.map((suggestion, index) => (
              <div
                key={index}
                className="dropdown-item"
                onClick={() => handleSuggestionSelect(suggestion)}
              >
                <FaSearch className="item-icon" />
                {suggestion}
              </div>
            ))
          )}
        </div>
      )}

      {/* History Dropdown */}
      {showHistory && searchHistory.length > 0 && (
        <div className="dropdown history-dropdown">
          <div className="dropdown-header">
            <span>Recent Searches</span>
            <FaTimes 
              className="clear-history" 
              onClick={clearHistory}
              title="Clear History"
            />
          </div>
          {searchHistory.map((item, index) => (
            <div
              key={index}
              className="dropdown-item"
              onClick={() => handleHistorySelect(item)}
            >
              <FaHistory className="item-icon" />
              {item}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}