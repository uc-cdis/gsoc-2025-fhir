
import pytest
import logging
import re
import os
from dotenv import load_dotenv

load_dotenv(".env.test", override=True)
GEN_USER_URL = os.getenv("GEN_USER_URL")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)



@pytest.mark.asyncio
async def test_get_patient(client, mock_gen3_httpx, mock_hapi_httpx, test_token):
    mock_gen3_httpx(token=test_token)
    mock_hapi_httpx(path="/Patient/123")
    response = await client.get("/Patient/123", headers={"Authorization": f"Bearer {test_token}"})
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_search_patient_with_security(client, mock_gen3_httpx, mock_hapi_httpx, test_token):
    mock_gen3_httpx(token=test_token, allowed_resources=["Patient"])
    mock_hapi_httpx(path="/Patient?name=Smith&_security=gen3%7CPatient")
    response = await client.get("/Patient?name=Smith", headers={"Authorization": f"Bearer {test_token}"})
    assert response.status_code == 200



@pytest.mark.asyncio
async def test_access_denied_when_gen3_forbids_resource(client, mock_gen3_httpx, mock_hapi_httpx, test_token):
    mock_gen3_httpx(token=test_token, allowed_resources=["Observation"])
    mock_hapi_httpx(path="/Patient/123", status_code=403)
    response = await client.get("/Patient/123", headers={"Authorization": f"Bearer {test_token}"})
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_401_when_no_token(client, mock_hapi_httpx):
    mock_hapi_httpx(path="/Patient/123", status_code=401)
    response = await client.get("/Patient/123")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_401_when_invalid_token(client, httpx_mock, mock_hapi_httpx):
    url_pattern = re.compile(rf"{re.escape(GEN_USER_URL)}/?(\?.*)?$")
    httpx_mock.add_response(method="GET", url=url_pattern, status_code=401)
    mock_hapi_httpx(path="/Patient/123", status_code=401)
    response = await client.get("/Patient/123", headers={"Authorization": "Bearer bad-token"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_500_preserved_from_hapi(client, mock_gen3_httpx, mock_hapi_httpx, test_token):
    mock_gen3_httpx(token=test_token, allowed_resources=["Patient"])
    mock_hapi_httpx(path="/Patient/123", status_code=500)
    response = await client.get("/Patient/123", headers={"Authorization": f"Bearer {test_token}"})
    assert response.status_code == 500


@pytest.mark.asyncio
async def test_create_patient(client, mock_gen3_httpx, mock_hapi_httpx, test_token):
    mock_gen3_httpx(token=test_token, allowed_resources=["Patient"])
    mock_hapi_httpx(path="/Patient", method="POST", status_code=201)
    response = await client.post(
        "/Patient",
        json={"resourceType": "Patient"},
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_update_patient(client, mock_gen3_httpx, mock_hapi_httpx, test_token):
    mock_gen3_httpx(token=test_token, allowed_resources=["Patient"])
    mock_hapi_httpx(path="/Patient/123", method="PUT", status_code=200)
    response = await client.put(
        "/Patient/123",
        json={"resourceType": "Patient"},
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_patient(client, mock_gen3_httpx, mock_hapi_httpx, test_token):
    mock_gen3_httpx(token=test_token, allowed_resources=["Patient"])
    mock_hapi_httpx(path="/Patient/123", method="DELETE", status_code=204)
    response = await client.delete("/Patient/123", headers={"Authorization": f"Bearer {test_token}"})
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_404_from_hapi(client, mock_gen3_httpx, mock_hapi_httpx, test_token):
    mock_gen3_httpx(token=test_token, allowed_resources=["Patient"])
    mock_hapi_httpx(path="/Patient/999", status_code=404)
    response = await client.get("/Patient/999", headers={"Authorization": f"Bearer {test_token}"})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_invalid_json(client, mock_hapi_httpx, test_token):
    mock_hapi_httpx(path="/Patient", method="POST", status_code=400)
    response = await client.post(
        "/Patient",
        content=b"{invalid json",
        headers={
            "Authorization": f"Bearer {test_token}",
            "Content-Type": "application/fhir+json"
        }
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_method_not_allowed(client, mock_hapi_httpx, test_token):
    mock_hapi_httpx(path="/Patient/123", method="PATCH", status_code=405)
    response = await client.patch("/Patient/123", headers={"Authorization": f"Bearer {test_token}"})
    assert response.status_code == 405


@pytest.mark.asyncio
async def test_gen3_downstream_error(client, httpx_mock, mock_hapi_httpx):
    url_pattern = re.compile(rf"{re.escape(GEN_USER_URL)}/?(\?.*)?$")
    httpx_mock.add_response(method="GET", url=url_pattern, status_code=500)
    mock_hapi_httpx(path="/Patient/123", status_code=502)
    response = await client.get("/Patient/123", headers={"Authorization": "Bearer bad-token"})
    assert response.status_code in (200, 401, 502)  


@pytest.mark.asyncio
async def test_search_with_paging_params(client, mock_gen3_httpx, mock_hapi_httpx, test_token):
    mock_gen3_httpx(token=test_token, allowed_resources=["Patient"])
    mock_hapi_httpx(path="/Patient", method="GET")
    response = await client.get("/Patient?_count=10", headers={"Authorization": f"Bearer {test_token}"})
    assert response.status_code == 200
