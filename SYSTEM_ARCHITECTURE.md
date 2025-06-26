# CCCA CAR Analysis System Architecture

## Overview

The CCCA CAR Analysis application is a modern geospatial analysis platform designed to track changes in Brazilian CAR (Cadastro Ambiental Rural) property boundaries over time and their relationship to PRODES deforestation data. This document provides a comprehensive overview of the system architecture, design decisions, and implementation details.

## System Architecture Diagram

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React Frontend │    │   FastAPI Backend │    │ PostgreSQL/PostGIS │
│   (Port 5173)    │◄──►│   (Port 8000)     │◄──►│   (Port 5432)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         │              ┌─────────▼─────────┐              │
         │              │  Martin Tile Server │              │
         └──────────────►│   (Port 3000)      │◄─────────────┘
                        └───────────────────┘
```

## Technology Stack & Rationale

### 1. FastAPI Backend Framework

**Choice Rationale:**
- **Modern Async Support**: Native async/await for database operations and concurrent request handling
- **Automatic API Documentation**: Built-in OpenAPI/Swagger documentation generation
- **Type Safety**: Pydantic models provide runtime validation and IDE support
- **SQLAlchemy Integration**: Excellent ORM support with async capabilities
- **Performance**: Among the fastest Python web frameworks (comparable to Node.js)

**Key Implementation Details:**
```python
# Async database operations for better concurrency
async def search_cod_imovel(query: str, limit: int = 10, db: Session = Depends(get_db)):
    # Non-blocking database queries
    results = db.execute(text("""
        SELECT DISTINCT cod_imovel, year, ind_status, ind_tipo
        FROM car_data 
        WHERE cod_imovel ILIKE :query 
        ORDER BY cod_imovel, year DESC
        LIMIT :limit
    """), {"query": f"%{query}%", "limit": limit})
```

### 2. PostgreSQL with PostGIS Extension

**Choice Rationale:**
- **Spatial Capabilities**: Native support for geographic data types and operations
- **ACID Compliance**: Critical for data integrity in analysis workflows
- **Advanced Indexing**: GIST indexes for spatial queries, trigram indexes for text search
- **Mature Ecosystem**: Extensive documentation and community support

**Spatial Indexing Strategy:**
```sql
-- GIST indexes for efficient spatial operations
CREATE INDEX idx_car_data_geometry ON car_data USING GIST (geometry);

-- Trigram indexes for fuzzy text search on cod_imovel
CREATE INDEX idx_car_data_cod_imovel_trgm ON car_data USING GIN (cod_imovel gin_trgm_ops);

-- Compound indexes for temporal queries
CREATE INDEX idx_car_data_year_cod_imovel ON car_data (year, cod_imovel);
```

### 3. Martin Tile Server

**Choice Rationale:**
- **High Performance**: Rust-based implementation optimized for vector tile serving
- **PostGIS Integration**: Direct connection to PostgreSQL without data duplication
- **Automatic Discovery**: Auto-detects spatial tables and creates tile endpoints
- **MVT Standard**: Serves Mapbox Vector Tiles for efficient client-side rendering

**Configuration:**
```yaml
# martin/config.yaml
sources:
  # Auto-discover PostGIS tables
  postgres:
    connection_string: "postgresql://postgres:postgres@postgis:5432/geoanalytics"
    auto_publish:
      tables: true
      views: true
```

### 4. React with MapLibre GL

**Choice Rationale:**
- **Modern Development**: Component-based architecture with hooks
- **WebGL Performance**: Hardware-accelerated rendering for smooth map interactions
- **Vector Tiles**: Efficient data transfer and client-side styling
- **Open Source**: MapLibre provides OSS alternative to Mapbox GL

## Data Flow Architecture

### 1. Data Ingestion Pipeline

```
Raw CAR Data → PostgreSQL → Spatial Analysis → Materialized Views → Vector Tiles
```

**Process:**
1. **Raw Data Import**: CAR shapefiles imported with year-based partitioning
2. **Geometry Processing**: Coordinates transformed to SIRGAS 2000 (EPSG:4674)
3. **Analysis Execution**: SQL-based geometry change detection between years
4. **View Materialization**: Results stored in optimized views for visualization

### 2. Search Functionality Flow

```
User Input → Frontend Debounce → API Request → Database Query → Trigram Search → Results
```

**Implementation:**
```javascript
// Frontend: Debounced search with 300ms delay
const fetchSuggestions = async (term) => {
  const response = await fetch(
    `http://localhost:8000/api/search/cod_imovel/${encodeURIComponent(term)}?limit=10`
  );
  const data = await response.json();
  setSuggestions([...new Set(data.map(item => item.cod_imovel))]);
};
```

### 3. Map Navigation Strategy

**Dual-Strategy Approach:**
1. **Primary**: API-based geometry lookup with pre-calculated bounds
2. **Fallback**: Direct tile querying for real-time feature access

```javascript
// API-first approach with fallback
const handleNavigateToProperty = async (codImovel) => {
  try {
    // Try API first (faster, pre-calculated bounds)
    const response = await fetch(`/api/property/${codImovel}/geometry/${year}`);
    if (response.ok) {
      const geometries = await response.json();
      const [minLng, minLat, maxLng, maxLat] = geometries[0].bounds;
      map.fitBounds([minLng, minLat], [maxLng, maxLat]);
      return;
    }
    
    // Fallback to tile querying
    const features = map.querySourceFeatures(sourceId, {
      filter: ['==', 'cod_imovel', codImovel]
    });
    // Handle different geometry types...
  } catch (error) {
    console.error('Navigation failed:', error);
  }
};
```

## Database Design & Optimization

### 1. Schema Design

**Core Tables:**
- `car_data`: Unified temporal storage with (cod_imovel, year) composite key
- `prodes`: PRODES deforestation polygons with spatial indexing
- `car_changed_to_exclude_prodes`: Analysis results with geometry pairs
- `relevant_prodes_subdivided`: Optimized PRODES data for visualization

**Temporal Data Handling:**
```sql
CREATE TABLE car_data (
    id SERIAL PRIMARY KEY,
    cod_imovel VARCHAR(255) NOT NULL,
    year INTEGER NOT NULL,
    geometry GEOMETRY(Geometry, 4674),
    UNIQUE(cod_imovel, year)  -- Prevents duplicate entries
);
```

### 2. Trigram Search Implementation

**Why Trigrams for cod_imovel Search:**
- **Brazilian Property Codes**: Often contain mixed alphanumeric patterns
- **Typo Tolerance**: Handles user input errors gracefully
- **Partial Matching**: Efficient prefix and substring searches
- **Performance**: GIN indexes provide sub-millisecond search times

**Technical Implementation:**
```sql
-- Enable trigram extension
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Create trigram index
CREATE INDEX idx_car_data_cod_imovel_trgm 
ON car_data USING GIN (cod_imovel gin_trgm_ops);

-- Search query with similarity ranking
SELECT cod_imovel, similarity(cod_imovel, 'search_term') as rank
FROM car_data 
WHERE cod_imovel % 'search_term'  -- Trigram operator
ORDER BY rank DESC;
```

### 3. Spatial Analysis Approach

**Geometry Change Detection:**
```sql
-- Identify changed geometries between years
SELECT 
    e.cod_imovel,
    e.geometry as geometry_earlier,
    l.geometry as geometry_later,
    NOT ST_Equals(e.geometry, l.geometry) as geometry_changed
FROM car_data e
JOIN car_data l ON e.cod_imovel = l.cod_imovel
WHERE e.year = 2024 AND l.year = 2025;
```

**PRODES Intersection Analysis:**
```sql
-- Find properties that intersect with deforestation
SELECT DISTINCT c.cod_imovel
FROM car_geom_changed c
JOIN prodes_subdivided p ON c.geometry_later && p.geometry 
WHERE ST_Intersects(c.geometry_later, p.geometry);
```

## Performance Optimization Strategies

### 1. Database Level

**Indexing Strategy:**
- **Spatial Indexes**: GIST for geometry operations
- **Text Search**: GIN trigram for fuzzy matching
- **Composite Indexes**: Year + cod_imovel for temporal queries
- **Materialized Views**: Pre-computed analysis results

**Query Optimization:**
```sql
-- Bounding box pre-filtering (&&) before expensive ST_Intersects
SELECT * FROM geometries 
WHERE geometry && ST_MakeEnvelope(xmin, ymin, xmax, ymax, 4674)
AND ST_Intersects(geometry, search_polygon);
```

### 2. Application Level

**Caching Strategy:**
- **Frontend**: LocalStorage for search history
- **API**: Connection pooling for database access
- **Tiles**: Browser caching of vector tile data

**Async Operations:**
```python
# Async database session management
async with SessionLocal() as db:
    result = await db.execute(query)
    return result.fetchall()
```

### 3. Network Level

**Data Transfer Optimization:**
- **Vector Tiles**: Compressed binary format vs. GeoJSON
- **API Responses**: Minimal JSON with only required fields
- **Debouncing**: Reduces API calls during user typing

## Frontend Architecture

### 1. Component Design Pattern

**Separation of Concerns:**
```javascript
// App.jsx - State management and business logic
const [visibleYearComparisons, setVisibleYearComparisons] = useState(new Set());
const canNavigate = visibleYearComparisons.size === 1;

// SearchComponent.jsx - UI logic and user interactions
export default function SearchComponent({ onNavigateToProperty, canNavigate }) {
  // Component-specific state and effects
}

// MapComponent.jsx - Map rendering and spatial operations
export default function MapComponent({ visibleYearComparisons, onMapReady }) {
  // MapLibre GL integration
}
```

### 2. State Management Strategy

**Local State with Hooks:**
- **Year Selection**: Set-based tracking for efficient operations
- **Search State**: Component-local with history persistence
- **Map State**: Ref-based for imperative map operations

**Props Pattern:**
```javascript
// Unidirectional data flow
<SearchComponent
  onNavigateToProperty={handleNavigateToProperty}  // Callback up
  visibleYearComparisons={visibleYearComparisons}  // State down
  canNavigate={canNavigate}                        // Derived state
/>
```

### 3. Error Handling & UX

**Progressive Enhancement:**
- **API Failure**: Graceful fallback to tile querying
- **Loading States**: User feedback during async operations
- **Input Validation**: Client-side validation before API calls

## Docker Microservices Architecture

### 1. Service Isolation

**Container Responsibilities:**
```yaml
services:
  postgis:     # Data persistence and spatial operations
  api:         # Business logic and data access layer  
  martin:      # High-performance tile serving
  db-init:     # Database initialization and migrations
```

### 2. Service Communication

**Network Architecture:**
- **Frontend → API**: HTTP REST for data operations
- **Frontend → Martin**: HTTP for vector tiles
- **API → PostgreSQL**: TCP connection pooling
- **Martin → PostgreSQL**: Direct PostGIS queries

### 3. Development Workflow

**Hot Reloading:**
```yaml
api:
  volumes:
    - ./api:/app  # Live code reloading
  command: ["uvicorn", "main:app", "--reload"]
```

## Security Considerations

### 1. Data Access Control

**SQL Injection Prevention:**
```python
# Parameterized queries prevent injection
db.execute(text("""
    SELECT * FROM car_data 
    WHERE cod_imovel ILIKE :query
"""), {"query": f"%{user_input}%"})
```

### 2. CORS Configuration

**Development vs. Production:**
```python
# Development: Permissive for local development
app.add_middleware(CORSMiddleware, allow_origins=["*"])

# Production: Restrict to specific domains
app.add_middleware(CORSMiddleware, allow_origins=["https://yourdomain.com"])
```

## Future Enhancements

### 1. Scalability Improvements

**Horizontal Scaling:**
- **Read Replicas**: For read-heavy workloads
- **Caching Layer**: Redis for frequently accessed data
- **CDN Integration**: For static tile delivery

### 2. Advanced Features

**Analytics Enhancement:**
- **Time Series Analysis**: Temporal change patterns
- **Machine Learning**: Anomaly detection in geometry changes
- **Real-time Updates**: WebSocket integration for live data

### 3. Performance Monitoring

**Observability Stack:**
- **Database Monitoring**: pg_stat_statements for query analysis
- **API Metrics**: Request latency and error rates
- **Frontend Analytics**: User interaction patterns

## Conclusion

This architecture balances performance, maintainability, and scalability while providing a rich user experience for geospatial analysis. The microservices approach enables independent scaling and development of components, while the spatial database foundation provides the analytical power needed for complex geographic operations.

The search functionality demonstrates how modern web technologies can provide responsive, intelligent interfaces for large spatial datasets, combining the power of PostGIS spatial analysis with the performance of vector tile rendering and the user experience of modern React applications.