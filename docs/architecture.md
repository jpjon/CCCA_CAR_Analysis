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