from fastapi import FastAPI, Request, Header, HTTPException  
from fastapi.responses import JSONResponse  
import httpx  
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse  
from .config import (
    ARBORIST_URL,
    ARBORIST_TIMEOUT,
    HAPI_FHIR_URL,
    SECURITY_TAG_PREFIX,
    PROXY_TIMEOUT,
    GEN_USER_URL  
)

app = FastAPI()  


################################################################################################


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_fhir(path: str, request: Request, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    
    token = authorization[len("Bearer "):]


    try:
        allowed_resources = await get_gen3_allowed_resources(token)
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=403, detail="Failed to fetch allowed resources from Gen3")

  
    original_url = f"{HAPI_FHIR_URL}/{path}"
    if request.query_params:
        original_url += "?" + str(request.query_params)

    rewritten_url = rewrite_fhir_url(original_url, allowed_resources)

    forward_headers = {k: v for k, v in request.headers.items() if k.lower() not in ["host", "content-length"]}
    forward_headers["Authorization"] = f"Bearer {token}"
    forward_headers["Accept"] = "application/fhir+json"
    forward_headers["Content-Type"] = "application/fhir+json"

    body = None
    if request.method in ("POST", "PUT"):
        body = await request.body()

    async with httpx.AsyncClient(timeout=PROXY_TIMEOUT) as client:
        try:
            resp = await client.request(
                method=request.method,
                url=rewritten_url,
                headers=forward_headers,
                content=body
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"FHIR server error: {e.response.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Error communicating with FHIR server: {str(e)}")

    data = resp.json()

###################################################################################################################################

    path_parts = path.strip("/").split("/")
    is_direct_read = len(path_parts) == 2  

    if is_direct_read and "meta" in data and "security" in data["meta"]:
        resource_codes = [sec.get("code") for sec in data["meta"]["security"]]
        if not any(code in allowed_resources for code in resource_codes):
            raise HTTPException(status_code=403, detail="Access denied for this resource")


####################################################################################################################################


    return JSONResponse(content=data, status_code=resp.status_code)
####################################################################################################################################
async def get_gen3_allowed_resources(token: str) -> list[str]:
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=ARBORIST_TIMEOUT) as client:
        resp = await client.get(GEN_USER_URL, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return data.get("resources", [])  

################################################################################################

def rewrite_fhir_url(original_url: str, resources: list[str]) -> str:
    parsed = urlparse(original_url)
    query_params = parse_qs(parsed.query)
    security_tags = [SECURITY_TAG_PREFIX + res for res in resources]
    query_params["_security"] = security_tags
    new_query = urlencode(query_params, doseq=True)
    return urlunparse(parsed._replace(query=new_query))

################################################################################################
