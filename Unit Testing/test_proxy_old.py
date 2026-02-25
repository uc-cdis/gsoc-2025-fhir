import pytest
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# -----------------------------
# Test: GET single Patient
# -----------------------------

@pytest.mark.asyncio
@pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
async def test_get_patient(client, mock_gen3_httpx, mock_hapi_httpx, test_token):
    """Test retrieving a single Patient from the proxy"""
    mock_gen3_httpx(token=test_token)
    mock_hapi_httpx(path="/Patient/123")

    logger.debug("Making GET request to /Patient/123")
    response = await client.get("/Patient/123", headers={"Authorization": f"Bearer {test_token}"})
    logger.debug(f"Received response: {response.json()}")

    assert response.status_code == 200
    assert response.json()["resourceType"] == "Patient"
    assert response.json()["id"] == "123"

# -----------------------------
# Test: Search Patients with security
# -----------------------------
@pytest.mark.asyncio
@pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
async def test_search_patient_with_security(client, mock_gen3_httpx, mock_hapi_httpx, test_token):
    """Test searching for patients with security parameters"""
    mock_gen3_httpx(token=test_token, allowed_resources=["Patient"])
    mock_hapi_httpx(path="/Patient?name=Smith&_security=gen3%7CPatient", response_data={
        "resourceType": "Bundle",
        "entry": [
            {"resource": {"resourceType": "Patient", "id": "123"}},
            {"resource": {"resourceType": "Patient", "id": "456"}},
        ]
    })

    logger.debug("Making GET request to /Patient?name=Smith")
    response = await client.get("/Patient?name=Smith", headers={"Authorization": f"Bearer {test_token}"})
    logger.debug(f"Received response: {response.json()}")

    assert response.status_code == 200
    bundle = response.json()
    assert bundle["resourceType"] == "Bundle"
    assert len(bundle["entry"]) == 2
    assert {entry["resource"]["id"] for entry in bundle["entry"]} == {"123", "456"}
