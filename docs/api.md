# FRIDAY OS - API Documentation

## Overview
The FRIDAY OS backend exposes a REST API via FastAPI. This API allows external clients and internal components to interact with the OS.

### Base URL
`http://localhost:8000/`

## Endpoints

### 1. Health Check
- **Endpoint**: `GET /health`
- **Description**: Returns the operational status of the OS.
- **Response**:
  ```json
  {
    "status": "online",
    "app": "FRIDAY OS",
    "version": "0.1.0",
    "environment": "development"
  }
  ```

*(Additional endpoints for Conversations, Agents, and Tasks will be documented here as they are implemented in Phase 5).*
