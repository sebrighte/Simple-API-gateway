# Simple API Gateway (FastAPI)

## Overview

This project is a FastAPI-based API Gateway that aggregates multiple
backend services into a single unified entry point. 

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
    ├── gateway.py             # Main FastAPI gateway Python 3
    ├── services.json          # Services configuration JSON
    ├── api_key.txt            # Gateway API key Text
    ├── dockerfile             # Create docker image for Gateway
    ├── app.lo                 # Log all Gateway requests, info and issues
    ├── instructions.txt       # Scripts for environments and deployment
    ├── orig.py                # original code by Franklyn Dunbar
    │
    ├── templates/
    │   ├── index.html         # Default page
    │   ├── swagger.html
    │   └── swaggerOpenAPI.html
    │
    ├── static/
    │   ├── OpenAPI Specifications
    │       ├── httpbin.json    # Worling example OpenAPI Spec
    │   ├── [images *.*]
    │   ├── javasript files
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

## Configuration

### services.json

Example:

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

python gateway.py

or

uvicorn gateway:app --reload --port 8005

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

## Supported Methods

GET

POST

PUT

PATCH

DELETE

------------------------------------------------------------------------

## Development

uvicorn gateway:app --reload

------------------------------------------------------------------------

## Limitations

No rate limiting

No load balancing

Basic security

------------------------------------------------------------------------

## Future Improvements

JWT auth

Rate limiting

Docker

Kubernetes

Monitoring

------------------------------------------------------------------------

## License

CC BY-SA 4.0

------------------------------------------------------------------------

## Summary

Provides:

Unified gateway

Swagger aggregation

Security

Routing

Microservice support
