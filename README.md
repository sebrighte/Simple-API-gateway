# API Gateway (FastAPI) -- Full Documentation

## Overview

This project is a FastAPI-based API Gateway that aggregates multiple
backend services into a single unified secured entry point.

It allows you to:

-   Route requests to multiple microservices
-   Enforce a global gateway securiyt (key)
-   Merge Swagger/OpenAPI documentation
-   Create bespoke swagger for each service
-   Provide unified API access
-   Dynamically update services

------------------------------------------------------------------------

## Features

-   Unified API Gateway endpoint
-   Reverse proxy for microservices
-   Gateway API key protection
-   Combined Swagger documentation
-   Dynamic services configuration
-   Swagger UI support
-   Website availability checker
-   Static file support
-   Template rendering
-   Logging

------------------------------------------------------------------------

## Project Structure

    project/
    │
    ├── gateway.py                 # Main FastAPI gateway
    ├── services.json              # Services configuration
    ├── api_key.txt                # Gateway API key
    │
    ├── templates/
    │   ├── index.html             # React site to manage services
    │   ├── swagger.html           # View orogonal swagger
    │   └── swaggerOpenAPI.html    #View gatway enabled swagger
    │
    ├── static/
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

## APIs

/: index.htlm (React UI to magae services, Return TemplateResponse)
/doc: Gateway API Swagger UI
/redoc: ateway API ReDoc UI
/openapi/{name}: Retuen the OpenAPI for named service (JSON file below, Return HTMLResponse)
/services: List the services managed in the gateway (Return services)
/update: Update a service in the gateway (Return updated services)
/check-website: Check to see if site is OK 200 (Return Treu of False)
/origswagger/{title}/{encoded_url:path}: Get original swagger of sevoce in gateway (Return HTMLResponse)
/swagger/{name}: Get the gateway enabled swagger page (Return HTML)
/{service}/{path:path}: back end to call service method (Return JSON)

------------------------------------------------------------------------

## Configuration

### services.json

This JSON file serves as a centralized configuration for multiple web services accessible through an API gateway or client application. It defines essential connection details, authentication parameters, and API documentation references for each service, enabling consistent and secure integration.

**Structure Overview:**

services: An array of service objects, where each object represents a distinct web service. Each service object typically includes:
- **name** – The identifier for the service.
- **endpoint** – The base URL for accessing the service API.
- **swagger/openapi** – URL pointing to the service’s OpenAPI or Swagger specification for documentation and automated client generation.
- **authentication details** – Information on required API keys or gateway keys, including location (query/header), whether it’s required, schema type, default value, and description.

**Key Features:**

- **Centralized Service Configuration** – Consolidates all service endpoints, API keys, and gateway settings into a single, maintainable file.
- **API Documentation Integration** – Includes OpenAPI/Swagger links to enable automated testing, client generation, and consistent integration.
- **Flexible Authentication Support** – Allows per-service and global gateway keys, providing layered security for different access levels.
- **Extensible Design** – Additional services can be added by appending new objects to the services array without impacting existing entries.
- **Machine-Readable Format** – JSON structure allows easy parsing and use by client applications, scripts, or integration tools.

        {
            "services": [
                {
                "name": "users",
                "endpoint": "http://localhost:8001",
                "swagger": "http://localhost:8001/openapi.json",
                "security": [],
                "securitySchemes": [],
                "gateway_api": {
                    "name": "gateway_key",
                    "in": "query",
                    "required": true,
                    "schema": {
                        "type": "string"
                        }
                    }
                }
            ]
        }

------------------------------------------------------------------------

## Running the Gateway

- python gateway.py
or
- uvicorn gateway:app --reload --port 8005

------------------------------------------------------------------------

## Security
- Uses gateway_key query parameter
- Stored in api_key.txt

Example: ?gateway_key=my-secret-key

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

## Logging

Saved in:
- app.log

------------------------------------------------------------------------

## Static Files

Served from:
- /static

------------------------------------------------------------------------

## Templates

Jinja2 templates:
- templates/

------------------------------------------------------------------------

## CORS

- Currently allows all origins
- Production should restrict

------------------------------------------------------------------------

## Production Recommendations

- Use HTTPS
- Restrict CORS
- Secure API keys
- Use environment variables
- Add authentication

------------------------------------------------------------------------

## Supported Methods

- GET
- POST
- PUT
- PATCH
- DELETE

------------------------------------------------------------------------

## Development

uvicorn gateway:app --reload

------------------------------------------------------------------------

## Limitations

- No rate limiting
- No load balancing
- Basic security

------------------------------------------------------------------------

## Future Improvements

- JWT auth
- Rate limiting
- Docker
- Kubernetes
- Monitoring

------------------------------------------------------------------------

## Summary

Provides:

- Unified gateway
- Swagger aggregation
- Security
- Routing
- Microservice support
