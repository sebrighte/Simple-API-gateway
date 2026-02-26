# Source - https://stackoverflow.com/q
# Posted by Franklyn Dunbar, modified by community. See post 'Timeline' for change history
# Retrieved 2026-01-22, License - CC BY-SA 4.0

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
import httpx
import os
import time
from contextlib import asynccontextmanager

# APP_A_URL/APP_B_URL are made available via a docker bridge network
APPA = os.getenv("APP_A_URL", "localhost")
APPB = os.getenv("APP_B_URL", "localhost")

# By defining the respective ports for each microservice app 
# and using a bridge network the gateway app can "reach" the microservice apps.
SERVICES = {
    "app_a": f"http://{APPA}:8001",
    "app_b": f"http://{APPB}:8002",
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    time.sleep(10)  # Delay to allow services to start
    combined_paths = {}
    combined_components = {
        "schemas": {},
        "responses": {},
        "parameters": {},
        "requestBodies": {},
    }
    combined_tags = []

    async with httpx.AsyncClient(verify=False) as client:
        for name, url in SERVICES.items():
            try:
                # Fetch the OpenAPI schema from the service
                response = await client.get(url + "/openapi.json")
                response.raise_for_status()
                openapi_schema = response.json()

                # Merge paths
                for path, methods in openapi_schema.get("paths", {}).items():
                    new_path = f"/{name}{path}/"
                    combined_paths[new_path] = methods

                # Merge components
                components = openapi_schema.get("components", {})
                for comp_type, comp_value in components.items():
                    if comp_type in combined_components:
                        combined_components[comp_type].update(comp_value)

                # Merge tags (avoid duplicates)
                if "tags" in openapi_schema:
                    for tag in openapi_schema["tags"]:
                        if tag not in combined_tags:
                            combined_tags.append(tag)

            except Exception as e:
                print(f"Error fetching OpenAPI schema from {name}: {e}")

    # Define a custom OpenAPI schema
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title="API Gateway",
            version="1.0.0",
            description="API Gateway for Microservices",
            routes=app.routes,
        )
        openapi_schema["paths"] = combined_paths
        openapi_schema["components"] = combined_components
        openapi_schema["tags"] = combined_tags
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    # Assign the custom OpenAPI schema
    app.openapi = custom_openapi
    yield

async def forward_request(service_url: str, method: str, path: str, body=None, headers=None):
    async with httpx.AsyncClient() as client:
        url = f"{service_url}/{path}"
        response = await client.request(method, url, json=body, headers=headers)
        return response

app = FastAPI(lifespan=lifespan)

@app.api_route("/{service}/{path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def gateway(service: str, path: str, request: Request):
    if service not in SERVICES:
        raise HTTPException(status_code=404, detail="Service not found")

    service_url = SERVICES[service]
    body = await request.json() if request.method in ["POST", "PUT", "PATCH"] else None
    headers = dict(request.headers)

    response = await forward_request(service_url, request.method, f"{path}", body, headers)
    return JSONResponse(status_code=response.status_code, content=response.json())
