# CCCA CAR Analysis Platform

A modern geospatial analysis platform for tracking changes in Brazilian CAR (Cadastro Ambiental Rural) property boundaries over time and their relationship to PRODES deforestation data. Built with Docker microservices architecture for scalable spatial analysis and interactive visualization.

![System Architecture](docs/architecture-diagram.png)

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose** (required)
- **npm** (for web development)
- **Git** (for repository management)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd CCCA_CAR_Analysis

# Install dependencies and start services
make setup
```

### 2. Load Data and Run Analysis

```bash
# Ingest CAR and PRODES data
make ingest-data

# Load data into PostGIS and run analysis
make load-data analyze

# Or run the full pipeline
make run-all
```

### 3. Start Web Interface

```bash
# Start development web server
make web

# Web interface available at http://localhost:5173
```

## 🏗️ System Architecture

The platform consists of four main services:

- **PostgreSQL/PostGIS** (`:5432`) - Spatial database for CAR and PRODES data
- **FastAPI Backend** (`:8000`) - RESTful API for data access and search
- **Martin Tile Server** (`:3000`) - High-performance vector tile serving
- **React Frontend** (`:5173`) - Interactive web interface with search and visualization

## 📊 Key Features

- **Temporal Analysis**: Compare CAR boundaries across multiple years
- **Spatial Search**: Trigram-based fuzzy search for property codes
- **Interactive Maps**: MapLibre GL-based visualization with vector tiles
- **Change Detection**: Identify geometry changes and PRODES intersections
- **Performance Optimized**: Spatial indexing and async operations

## 🔧 Common Commands

```bash
# Service Management
make start           # Start all Docker services
make stop            # Stop all services
make logs            # View service logs

# Data Pipeline
make ingest-data     # Download/ingest raw data
make load-data       # Load data into PostGIS
make analyze         # Run spatial analysis
make run-all         # Complete pipeline

# Web Development
make web-install     # Install npm dependencies
make web-dev         # Start development server
make web-build       # Build for production

# Database Access
make psql            # Access PostgreSQL CLI
make clean           # Remove all data and containers
```

## 📁 Project Structure

```
├── src/                 # Python source code
│   ├── ingestion/       # Data ingestion scripts
│   └── processing/      # Analysis and database loading
├── web/                 # React frontend application
├── docker/              # Docker configuration
├── docs/                # Detailed documentation
├── db/                  # Database migrations and SQL
├── data/                # Raw data storage
└── Makefile            # Automation commands
```

## 🗂️ Data Requirements

Place your data in the following structure:

```
data/
├── SICAR/
│   ├── 2023/           # CAR data for 2023
│   ├── 2024/           # CAR data for 2024
│   └── 2025/           # Latest year with state folders
│       ├── AC/         # Acre state data
│       ├── AM/         # Amazonas state data
│       └── ...
└── PRODES/
    └── prodes_amazonia_nb.gpkg  # PRODES deforestation data
```

## 📚 Documentation

- [**Installation Guide**](docs/installation.md) - Detailed setup and system requirements
- [**Development Guide**](docs/development.md) - Development environment and workflow  
- [**Architecture Overview**](docs/architecture.md) - Technical system architecture
- [**Data Pipeline**](docs/data-pipeline.md) - Data ingestion and processing workflow
- [**Makefile Reference**](docs/makefile-reference.md) - Complete command reference

## 🔍 Search Functionality

The platform includes advanced search capabilities:

- **Property Code Search**: Fuzzy search using PostgreSQL trigrams
- **Spatial Navigation**: Navigate to properties with geometry bounds
- **Year Comparison**: Toggle between different years for temporal analysis
- **Real-time Suggestions**: Debounced search with instant suggestions

## 🌍 Geographic Data

- **Coordinate System**: SIRGAS 2000 (EPSG:4674)
- **Coverage**: Amazon region of Brazil
- **Data Sources**: SICAR (CAR registry), PRODES (deforestation alerts)
- **Spatial Operations**: PostGIS-powered geometric analysis

## 🚧 Development

```bash
# Start development environment
make setup

# Run web development server with hot reload
make web-dev

# Access database for debugging
make psql

# View all service logs
make logs
```

## 📈 Performance Features

- **Vector Tiles**: Efficient map rendering with Martin tile server
- **Spatial Indexing**: GIST indexes for fast geometric queries
- **Connection Pooling**: Optimized database connections
- **Async Operations**: Non-blocking FastAPI endpoints

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Set up development environment with `make setup`
4. Make your changes
5. Test with `make run-all`
6. Submit a pull request

---

For detailed technical information, see the [System Architecture documentation](docs/architecture.md).