# Simple API Gateway (FastAPI)

## FastAPI API Gateway

A lightweight **API Gateway built with FastAPI** that routes requests to multiple backend services, aggregates their OpenAPI specifications, and provides a unified Swagger interface with a simple React-based UI.

The gateway dynamically loads services from `services.json`, forwards requests to backend APIs, and exposes combined OpenAPI documentation.

I just wanted a simple implementation where i could expose internal and external through one managed interface

This solution allows you to:

-   Route requests to multiple (micro) services
-   Enforce a global gateway_key
-   Merge Swagger/OpenAPI documentation
-   Provide per-service API Swagger/OpenAPI documentation
-   Provide unified API access
-   Dynamically update services
-   Allow local hosting of OpenAPI specification (where they dont exist or you need to modify)

------------------------------------------------------------------------

## Features

🚪 **API Gateway Routing**
Routes incoming requests to configured backend services.

📄 **Unified OpenAPI Documentation**
Combines OpenAPI specs from multiple services into one interface.

🧭 **Interactive Swagger UI**
View and test APIs directly through the gateway.

🔑 **Gateway API Key Security**
Global query parameter (`gateway_key`) required to access endpoints.

⚙️ **Service Registry UI**
Browser-based UI to add, edit, or remove services.

🔄 **Live Service Configuration**
Updates `services.json` dynamically via API.

📂 **Local OpenAPI Support**
Load OpenAPI specs from local JSON files.

🌐 **CORS Enabled**
Allows cross-origin access for development and UI integration.

------------------------------------------------------------------------

# Architecture

                ┌─────────────────────┐
                │     Web UI (React)  │
                │     index.js        │
                └─────────┬───────────┘
                          │
                          ▼
                ┌─────────────────────┐
                │   FastAPI Gateway   │
                │     gateway.py      │
                └─────────┬───────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
   Backend API       Backend API       Backend API
   Service 

------------------------------------------------------------------------

The gateway:

1. Loads services from `services.json`
2. Fetches each service’s OpenAPI specification
3. Combines them into a unified API documentation
4. Routes requests dynamically to the correct backend service

------------------------------------------------------------------------

## Project Structure

    project/
    │
    ├── gateway.py               # Main FastAPI gateway Python 3
    ├── services.json            # Services configuration JSON
    ├── api_key.txt              # Gateway API key Text
    ├── dockerfile               # Create docker image for Gateway
    ├── app.lo                   # Log all Gateway requests, info and issues
    ├── instructions.txt         # Scripts for environments and deployment
    ├── orig.py                  # original code by Franklyn Dunbar
    ├── versions.py              # Version definition
    │
    ├── templates/
    │   ├── index.html           # Default page
    │   ├── swagger.html         # Swagger for hosted api
    │   └── swaggerOpenAPI.html  # Swagger for passed openapi.json
    │
    ├── static/
    │   ├── OpenAPI Specifications
    │       ├── httpbin.json     # Worling example OpenAPI Spec
    │   ├── [images *.*]
    │   ├── javasript files      # The main page code source is index.js
    │   ├── CSS files
    │
    ├── app.log
    │
    └── README.md

------------------------------------------------------------------------

## Requirements

Python 3.9 or newer

Install dependencies:

pip install fastapi uvicorn httpx jinja2 python-multipart

------------------------------------------------------------------------

# Installation

## 1. Clone the Repository

```bash
git clone https://github.com/yourrepo/api-gateway.git
cd api-gateway
```

---

## 2. Install Dependencies

```bash
pip install fastapi uvicorn httpx requests jinja2
```

---

## 3. Create API Key

Create a file:

```
api_key.txt
```

Example:

```
apikey123
```

---

## 4. Configure Services

Edit:

```
services.json
```
Note: Use a local file where an OpenAPI specification is not exposed so you can host the OpenAPI locally, but access the API from the published endpoint 
(e.g. Traccar or httpbin (httpbin) bleow where I use the hoted OpenAPI and also the local OpenAPI (httpbinlocal) definitions


Example:

```
[
  {
    "name": "httpbin",
    "endpoint": "https://httpbin.org/",
    "swagger": "https://httpbin.org/spec.json",
    "config": {
      "gateway_api": {
        "name": "gateway_key",
        "in": "query",
        "required": true,
        "schema": {
          "type": "string",
          "default": "apikey123"
        },
        "description": "Gateway API key"
      }
    }
  },
  {
    "name": "httpbinlocal",
    "endpoint": "https://httpbin.org/",
    "swagger": "file://:httpbin.json",
    "config": {
      "gateway_api": {
        "name": "gateway_key",
        "in": "query",
        "required": true,
        "schema": {
          "type": "string",
          "default": "apikey123"
        },
        "description": "Gateway API key"
      }
    }
  }
]

```

# Access the Gateway

| URL                  | Description                 |
| -------------------- | --------------------------- |
| `/`                  | Gateway UI                  |
| `/docs`              | FastAPI OpenAPI docs        |
| `/swagger/{service}` | Service-specific Swagger UI |
| `/openapi/{service}` | Combined OpenAPI schema     |
| `/services`          | List configured services    |
| `/version`           | Application version info    |

Example:

```
http://localhost:8005/
```

------------------------------------------------------------------------

## Security

Uses gateway_key query parameter

Stored in api_key.txt

Example:

?gateway_key=my-secret-key

------------------------------------------------------------------------

## How It Works

    Client
    ↓
    Gateway
    ↓
    Validates gateway_key
    ↓
    Forwards request
    ↓
    Service
    ↓
    Response returned to client

------------------------------------------------------------------------

# Service Configuration

Each service supports:

| Field      | Description                   |
| ---------- | ----------------------------- |
| `name`     | Gateway route prefix          |
| `endpoint` | Backend service base URL      |
| `swagger`  | OpenAPI spec URL              |
| `config`   | Security and gateway settings |

---

# Gateway Security

The gateway requires a query parameter:

```
gateway_key
```

Example:

```
GET /service/path?gateway_key=apikey123
```

The key is read from:

```
api_key.txt
```

---

# UI Features

The React UI allows:

* View registered services
* Add new services
* Edit service configuration
* Delete services
* Test API endpoints
* View OpenAPI specs
* Check service availability

---

# Local OpenAPI Support

Place OpenAPI JSON files inside:

```
static/OpenAPI/
```

They will appear automatically in the UI.

Example:

```
static/OpenAPI/weather.json
```

Access:

```
/swaggerfile/weather
```

# Logging

Logs are written to:

```
app.log
```

## Logging

Saved in:

app.log

------------------------------------------------------------------------

## Static Files

Served from:

/static

------------------------------------------------------------------------

## Templates

Jinja2 templates:

templates/

------------------------------------------------------------------------

## CORS

Currently allows all origins

Production should restrict

------------------------------------------------------------------------

## Production Recommendations

Use HTTPS

Restrict CORS

Secure API keys

Use environment variables

Add authentication

------------------------------------------------------------------------

## Limitations

No rate limiting

No load balancing

Basic security

------------------------------------------------------------------------

# Future Improvements

Potential enhancements:

* JWT authentication support
* Rate limiting
* Service health monitoring
* Docker deployment
* Kubernetes support
* Service caching
* Load balancing
* Metrics & observability

---

# License

This project uses components under:

* FastAPI
* React
* httpx
* requests

Refer to their respective licenses.

---
