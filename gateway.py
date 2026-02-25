# Source - https://stackoverflow.com/q
# Posted by Franklyn Dunbar, modified by community. See post 'Timeline' for change history
# Retrieved 2026-01-22, License - CC BY-SA 4.0

from fastapi import FastAPI, HTTPException, Request, Query, Response, APIRouter, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic
from urllib.parse import quote, unquote
import httpx
import time
from contextlib import asynccontextmanager
import uvicorn
import json
import logging

def loadServices():
    with open("services.json") as f:
        return json.load(f)["services"]

def getAPIKey():
    with open("api_key.txt") as f:
        return f.read().strip()

def getLocalSpecs():
    from pathlib import Path
    folder = Path("static/OpenAPI/")
    json_files = list(folder.glob("*.json"))
    return [x.stem for x in json_files]
    #for file in json_files:
    #    print(file.stem)

async def serviceSwagger(name):
    time.sleep(5)  # Delay to allow services_json to start
    combined_paths = {}
    combined_components = {
        "schemas": {},
        "responses": {},
        "parameters": {},
        "requestBodies": {},
    }
    combined_tags = []

    async with httpx.AsyncClient(verify=False) as client:
        service = next((s for s in loadServices() if s["name"] == name), None)
        name = service.get("name")
        endpoint = service.get("endpoint")
        swagger = service.get("swagger")
        security = service.get("security") 
        securitySchemes = service.get("securitySchemes")
        gateway_api = service.get("gateway_api") 
        api_key = service.get("api_key") 

        try:
            # Fetch the OpenAPI schema from the service
            response = await client.get(swagger)  #+ "/openapi.json")
            response.raise_for_status()
            openapi_schema = response.json()

            for path, methods in openapi_schema.get("paths", {}).items():
                new_path = f"/{service['name']}{path}"

                for operation in methods.values():
                    params = operation.setdefault("parameters", [])

                    # avoid duplicates
                    if gateway_api and not any(p["name"] == "gateway_key" and p["in"] == "query" for p in params):
                        gateway_api['schema']['default'] = getAPIKey() or False
                        params.append(gateway_api)
                    if api_key and not any(p["name"] == "api_key" and p["in"] == "query" for p in params):
                        params.append(api_key)

                combined_paths[new_path] = methods
                
            components = openapi_schema.get("components", {})

            for comp_type, comp_value in components.items():
                combined_components.setdefault(comp_type, {})
                combined_components[comp_type].update(comp_value)

            # Merge tags (avoid duplicates)
            if "tags" in openapi_schema:
                for tag in openapi_schema["tags"]:
                    if tag not in combined_tags:
                        combined_tags.append(tag)

        except Exception as e:
            print(f"Error fetching OpenAPI schema from {service["name"]}: {e}")

    # Define a custom OpenAPI schema
    def custom_openapi():
        openapi_schema = get_openapi(
            title="API Gateway",
            version="1.0.0",
            description=f"API Gateway for API Services<br>Develeoped By Sebright Software<br>Version 1.0.1 <br><br><b><u>OpenAPI Details</u></b><ul><li><b>Security:</b> {security}</li><li><b>Security Scheme:</b> {securitySchemes}</li><li><b>Global ApiKey:</b> {gateway_api}</li></ul>",
            routes=app.routes,
        )
        if security: openapi_schema["security"] = security
        if combined_tags: openapi_schema["tags"] = combined_tags
        if combined_paths: openapi_schema["paths"] = combined_paths
        if combined_components: openapi_schema["components"] = combined_components
        if securitySchemes: openapi_schema["components"]["securitySchemes"] = securitySchemes
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    print(f"Created local OpenAPI for {service["name"]}")
    # Assign the custom OpenAPI schema
    return custom_openapi()


@asynccontextmanager
async def lifespan(app: FastAPI):

    time.sleep(5)  # Delay to allow services_json to start
    combined_paths = {}
    combined_components = {
        "schemas": {},
        "responses": {},
        "parameters": {},
        "requestBodies": {},
    }
    combined_tags = []

    #https://sebright.uksouth.cloudapp.azure.com:443/api/TidesSDK/swagger/docs/v1
    async with httpx.AsyncClient(verify=False) as client:
        for service in loadServices():
            name = service.get("name")
            endpoint = service.get("endpoint")
            swagger = service.get("swagger")
            security = service.get("security") 
            securitySchemes = service.get("securitySchemes")
            gateway_api = service.get("gateway_api") 

            try:
                #print(url)
                # Fetch the OpenAPI schema from the service
                response = await client.get(swagger)
                response.raise_for_status()
                openapi_schema = response.json()

                security = security

                global_query_param = gateway_api

                # Merge paths
                for path, methods in openapi_schema.get("paths", {}).items():
                    new_path = f"/{service["name"]}{path}"
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

                print(f"Loaded OpenAPI for {service["name"]}")

            except Exception as e:
                print(f"Error fetching OpenAPI schema from {service["name"]}: {e}")

    # Define a custom OpenAPI schema
    def custom_openapi():
        openapi_schema = get_openapi(
            title="API Gateway",
            version="1.0.0",
            description="API Gateway for API Services<br><br>Develeoped By Sebright Software<br><br>Version 1.0.1",
            routes=app.routes,
        )
        openapi_schema["paths"] = combined_paths
        openapi_schema["components"] = combined_components
        openapi_schema["tags"] = combined_tags
        
        openapi_schema["components"]["securitySchemes"] = securitySchemes

        #Apply to ALL endpoints
        openapi_schema["security"] = security

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

    yield

# Global dependency: validates gateway_key
def require_gateway_key(request: Request):
    gateway_key = request.query_params.get("gateway_key")
    if not gateway_key:
        raise HTTPException(status_code=400, detail="gateway_key query parameter is required")
    return gateway_key

app = FastAPI(lifespan=lifespan)

router = APIRouter(dependencies=[Depends(require_gateway_key)])
app.include_router(router)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # OK for local dev
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/openapi/{name}")
async def getopenapi(name):
    return await serviceSwagger(name)

@app.get("/services")
def services():
    return loadServices()

@app.post("/update")
async def update_gateway(request: Request):
    global services_json
    payload = await request.json()
    with open("services.json", "w") as f:
        json.dump(payload, f, indent=4)
    return loadServices()

@app.get("/check-website")
async def check_website(url: str = Query(...)):
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.head(url)
            return {"exists": r.status_code < 400}
    except Exception:
        return {"exists": False}

@app.get("/origswagger/{title}/{encoded_url:path}")
async def get_swagger(title: str, encoded_url: str, request: Request):
    url = unquote(encoded_url)
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.get(url)
        response.raise_for_status()
    template = templates.get_template("swaggerOpenAPI.html")
    html = template.render(
        name = title,
        request=request,                 # important for Jinja2
        openapi=json.dumps(response.json())
    )
    return HTMLResponse(content=html, status_code=response.status_code)

@app.get("/swagger/{name}", response_class=HTMLResponse)
async def get_swagger1(name: str, request: Request):
    #print(name)
    template = templates.get_template("swagger.html")
    html = template.render(
        request=request,
        #name=f("/openapi/{name}?gateway_key={getAPIKey()}")
        name=f"/openapi/{name}"
    )
    return html

@app.get("/files")
async def files():
    #getLocalSpecs()
    return getLocalSpecs()

@app.get("/swaggerfile/{name}", response_class=HTMLResponse)
async def get_swagger1(name: str, request: Request):

    template = templates.get_template("swaggerOpenAPI.html")

    with open(f"static/OpenAPI/{name}.json") as f:
        data = json.load(f)

    html = template.render(
        name=name,
        request=request,
        openapi=json.dumps(data)
    )

    return HTMLResponse(content=html, status_code=200)

async def forward_request(service_url: str, method: str, path: str, body=None, headers=None):
    import httpx

    url = f"{service_url.rstrip('/')}/{path.lstrip('/')}"

    async with httpx.AsyncClient() as client:

        headers = dict(headers)
        for k in list(headers.keys()):
            if k.lower() == "host":
                headers.pop(k)

        response = await client.request(
            method=method,
            url=url,
            headers=headers,
            json=body
        )
    return response  # return the httpx.Response, not FastAPI Response

#security = HTTPBasic()

@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
#async def gateway(service: str, path: str, request: Request, credentials = Depends(security)):
async def gateway(service: str, path: str, request: Request):
    services = loadServices()
    service_obj = next((s for s in services if s["name"] == service), None)
    if not service_obj:
        return JSONResponse(status_code=404, content={"error": "Service not found"})

    print(service_obj.get("securitySchemes"))

    if 'basic' in service_obj.get("securitySchemes", []):
        if credentials is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Basic"}
            )

    service_url = service_obj.get("endpoint") or ""

    body = await request.json() if request.method in ["POST", "PUT", "PATCH"] else None
    headers = dict(request.headers)

    response = await forward_request(
        service_url,
        request.method,
        f"{path}?{request.url.query}",
        body,
        headers
    )

    valid_key = getAPIKey()
    gateway_key = request.query_params.get("gateway_key")  # safe, returns None if missing

    if not gateway_key or gateway_key != valid_key:
        raise HTTPException(status_code=401, detail="gateway_key query parameter is invlaid")

    try:
        data = response.json()
    except (json.JSONDecodeError, ValueError):
        data = {
            "error": "Upstream did not return valid JSON",
            "status": getattr(response, "status_code", None),
        }

    return JSONResponse(status_code=response.status_code, content=data)

logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

if __name__ == "__main__":
    uvicorn.run("gateway:app",
                reload="true",
                host="0.0.0.0",
                port=8005,
                log_level="debug")
