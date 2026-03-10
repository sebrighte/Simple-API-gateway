# Source - https://stackoverflow.com/q
# Posted by Franklyn Dunbar, modified by community
# Retrieved 2026-01-22, License - CC BY-SA 4.0

from fastapi import FastAPI, HTTPException, Request, Query, Depends, status
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from urllib.parse import unquote
from pathlib import Path

import httpx
import uvicorn
import json
import logging
import requests

from versions import *

SERVICES_FILE = "services.json"
API_KEY_FILE = "api_key.txt"
LOCAL_OPENAPI_DIR = "static/OpenAPI"


# ------------------------------------------------
# Utility functions
# ------------------------------------------------

def loadServices():
    with open(SERVICES_FILE) as f:
        return json.load(f)["services"]


def getAPIKey():
    with open(API_KEY_FILE) as f:
        return f.read().strip()


def getLocalSpecs():
    folder = Path(LOCAL_OPENAPI_DIR)
    return [f.stem for f in folder.glob("*.json")]


def url_exists(url):
    try:
        r = requests.head(url, timeout=1)
        return r.status_code == 200
    except requests.RequestException:
        return False


async def fetch_openapi(swagger):

    if swagger.startswith("file://"):
        file_path = f"{LOCAL_OPENAPI_DIR}/{swagger.replace('file://','')}"
        with open(file_path) as f:
            return json.load(f)

    async with httpx.AsyncClient(verify=False) as client:
        r = await client.get(swagger)
        r.raise_for_status()
        return r.json()


# ------------------------------------------------
# Inject query parameters into OpenAPI operations
# ------------------------------------------------

def inject_parameters(methods, gateway_api=None, api_key=None):

    for operation in methods.values():

        params = operation.setdefault("parameters", [])

        if gateway_api and not any(
            p.get("name") == "gateway_key" and p.get("in") == "query"
            for p in params
        ):
            gateway_api["schema"]["default"] = getAPIKey() or False
            params.append(gateway_api)

        if api_key and not any(
            p.get("name") == "api_key" and p.get("in") == "query"
            for p in params
        ):
            params.append(api_key)


# ------------------------------------------------
# Service Swagger Builder
# ------------------------------------------------

async def serviceSwagger(name):

    services = loadServices()

    service = next((s for s in services if s["name"] == name), None)

    if service is None and name == "gateway":
        return get_openapi(
            title="API Gateway",
            version="1.0.0",
            description="Gateway API",
            routes=app.routes
        )

    combined_paths = {}
    combined_components = {
        "schemas": {},
        "responses": {},
        "parameters": {},
        "requestBodies": {},
    }

    combined_tags = []

    swagger = service.get("swagger")

    config = service.get("config", {})

    security = config.get("security")
    securitySchemes = config.get("securitySchemes")
    gateway_api = config.get("gateway_api")
    api_key = config.get("api_key")

    try:

        openapi_schema = await fetch_openapi(swagger)

        for path, methods in openapi_schema.get("paths", {}).items():

            new_path = f"/{service['name']}{path}"

            inject_parameters(methods, gateway_api, api_key)

            combined_paths[new_path] = methods

        components = openapi_schema.get("components", {})

        for comp_type, comp_value in components.items():
            combined_components.setdefault(comp_type, {})
            combined_components[comp_type].update(comp_value)

        for tag in openapi_schema.get("tags", []):
            if tag not in combined_tags:
                combined_tags.append(tag)

    except Exception as e:
        print(f"Error fetching OpenAPI schema from {service['name']}: {e}")

    def custom_openapi():

        openapi_schema = get_openapi(
            title="API Gateway",
            version="1.0.0",
            description="API Gateway for API Services",
            routes=None,
        )

        if security:
            openapi_schema["security"] = security

        if combined_tags:
            openapi_schema["tags"] = combined_tags

        openapi_schema["paths"] = combined_paths
        openapi_schema["components"] = combined_components

        if securitySchemes:
            openapi_schema["components"]["securitySchemes"] = securitySchemes

        return openapi_schema

    return custom_openapi()


# ------------------------------------------------
# Gateway OpenAPI builder (startup)
# ------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):

    combined_paths = {}
    combined_components = {
        "schemas": {},
        "responses": {},
        "parameters": {},
        "requestBodies": {},
    }

    combined_tags = []

    for service in loadServices():

        try:

            openapi_schema = await fetch_openapi(service["swagger"])

            for path, methods in openapi_schema.get("paths", {}).items():

                new_path = f"/{service['name']}{path}"

                combined_paths[new_path] = methods

            components = openapi_schema.get("components", {})

            for comp_type, comp_val in components.items():
                combined_components.setdefault(comp_type, {})
                combined_components[comp_type].update(comp_val)

            for tag in openapi_schema.get("tags", []):
                if tag not in combined_tags:
                    combined_tags.append(tag)

            print(f"Loaded OpenAPI for {service['name']}")

        except Exception as e:
            print(f"Error loading {service['name']}: {e}")

    def custom_openapi():

        openapi_schema = get_openapi(
            title="API Gateway",
            version="1.0.0",
            description="API Gateway for API Services",
            routes=app.routes,
        )

        openapi_schema["paths"] = combined_paths
        openapi_schema["components"] = combined_components
        openapi_schema["tags"] = combined_tags

        app.openapi_schema = openapi_schema
        return openapi_schema

    app.openapi = custom_openapi

    yield


# ------------------------------------------------
# Security
# ------------------------------------------------

def require_gateway_key(request: Request):

    gateway_key = request.query_params.get("gateway_key")

    if not gateway_key or gateway_key != getAPIKey():
        raise HTTPException(status_code=401, detail="gateway_key invalid")

    return gateway_key


# ------------------------------------------------
# FastAPI App
# ------------------------------------------------

app = FastAPI(lifespan=lifespan)

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------
# UI Routes
# ------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/services")
def services():
    return loadServices()


@app.get("/version")
def version():
    return {
        "app": appVersion,
        "json": jsonVersion,
        "UI": uiVersion
    }


@app.get("/files")
async def files():
    return getLocalSpecs()


# ------------------------------------------------
# Swagger Routes
# ------------------------------------------------

# @app.get("/openapi/{name}")
# async def getopenapi(name):
#     return await serviceSwagger(name)


@app.get("/swagger/{name}", response_class=HTMLResponse)
async def swagger_ui(name: str, request: Request):

    openapi_schema = await serviceSwagger(name)

    html = templates.get_template("ServiceSwagger.html").render(
        request=request,
        name=f"/openapi/{name}",
        openapi=json.dumps(openapi_schema)   # important
    )
    return html


@app.get("/swaggerfile/{name}", response_class=HTMLResponse)
async def swagger_file(name: str, request: Request):

    with open(f"{LOCAL_OPENAPI_DIR}/{name}.json") as f:
        data = json.load(f)

    html = templates.get_template("ServiceSwagger.html").render(
        name=name,
        request=request,
        openapi=json.dumps(data)
    )

    return HTMLResponse(content=html)


@app.get("/origswagger/{title}/{encoded_url:path}")
async def origswagger(title: str, encoded_url: str, request: Request):

    url = unquote(encoded_url)

    async with httpx.AsyncClient(verify=False) as client:
        r = await client.get(url)
        r.raise_for_status()

    html = templates.get_template("swaggerOpenAPI.html").render(
        name=title,
        request=request,
        openapi=json.dumps(r.json())
    )

    return HTMLResponse(content=html)


# ------------------------------------------------
# Forward Requests
# ------------------------------------------------

async def forward_request(service_url, method, path, body=None, headers=None):

    url = f"{service_url.rstrip('/')}/{path.lstrip('/')}"

    headers = dict(headers)
    headers.pop("host", None)

    async with httpx.AsyncClient() as client:

        response = await client.request(
            method=method,
            url=url,
            headers=headers,
            json=body
        )

    return response


# ------------------------------------------------
# Gateway Proxy
# ------------------------------------------------

@app.api_route(
    "/{service}/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    dependencies=[Depends(require_gateway_key)]
)
async def gateway(service: str, path: str, request: Request):

    service_obj = next((s for s in loadServices() if s["name"] == service), None)

    if not service_obj:
        raise HTTPException(status_code=404, detail="Service not found")

    body = None

    if request.method in ["POST", "PUT", "PATCH"]:
        body = await request.json()

    headers = dict(request.headers)

    if "authorization" in headers:
        headers["Authorization"] = headers.pop("authorization")

    response = await forward_request(
        service_obj["endpoint"],
        request.method,
        f"{path}?{request.url.query}",
        body,
        headers
    )

    try:
        data = response.json()
    except Exception:
        data = {
            "url": f"{request.method} {service_obj['endpoint']}/{path}",
            "response": response.text
        }

    return JSONResponse(status_code=response.status_code, content=data)


# ------------------------------------------------
# Logging
# ------------------------------------------------

logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


# ------------------------------------------------
# Run
# ------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        "gateway:app",
        host="0.0.0.0",
        port=8005,
        reload=True,
        log_level="debug"
    )