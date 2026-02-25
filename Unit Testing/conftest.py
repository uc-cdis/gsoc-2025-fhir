import re
import pytest
import logging
import os
from httpx import AsyncClient, ASGITransport
from pytest_httpx import HTTPXMock
from fhir_proxy.app import app
from dotenv import load_dotenv
import pytest_asyncio

FHIR_SERVER_URL = os.getenv("FHIR_SERVER_URL", "http://localhost:8080/fhir")
# -----------------------------
# Logging for debugging
# -----------------------------
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv(".env.test", override=True)
GEN_USER_URL = os.getenv("GEN_USER_URL")
FHIR_SERVER_URL = os.getenv("FHIR_SERVER_URL")

# -----------------------------
# Mock Gen3 allowed resources
# -----------------------------
@pytest.fixture
def mock_gen3_httpx(httpx_mock: HTTPXMock):
    """Mock Gen3 /user/user endpoint for allowed resources"""
    def _mock(token="test-token", allowed_resources=None):
        if allowed_resources is None:
            allowed_resources = ["Patient", "Observation"]

        url_pattern = re.compile(rf"{re.escape(GEN_USER_URL)}/?(\?.*)?$")
        httpx_mock.add_response(
            method="GET",
            url=url_pattern,
            json={"resources": allowed_resources},
            status_code=200,
        )
        logger.debug(
            f"Mocked Gen3 response for token={token}, "
            f"allowed_resources={allowed_resources}, url_pattern={url_pattern.pattern}"
        )

    return _mock

# ----------------------------- -----------------------------



# -----------------------------
# Async TestClient fixture
# -----------------------------
@pytest_asyncio.fixture
async def client():
    """Async client for testing FastAPI endpoints"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=FHIR_SERVER_URL) as c:
        yield c

# -----------------------------
# Mock Gen3 allowed resources
# -----------------------------
@pytest.fixture
def mock_hapi_httpx(httpx_mock: HTTPXMock):
    """Mock HAPI FHIR server responses"""
    def _mock(path="/Patient/123", method="GET", response_data=None, status_code=200):
        if response_data is None:
            response_data = {
                "resourceType": "Patient",
                "id": "123",
                "meta": {
                    "security": [
                        {"system": "https://example.org/fhir/security", "code": "Patient"}
                    ]
                },
            }

        
        if path.startswith("/fhir/"):
            path = path[len("/fhir/"):]
        elif path.startswith("/"):
            path = path[1:]

        full_url = f"{FHIR_SERVER_URL.rstrip('/')}/fhir/{path.lstrip('/')}"


       
        if "?" in full_url:
            base_path = full_url.split("?")[0]
            path_regex = rf"{re.escape(base_path)}\?.*$"
        else:
            path_regex = re.escape(full_url)

        url_pattern = re.compile(path_regex)

        httpx_mock.add_response(
            method=method,
            url=url_pattern,
            json=response_data,
            status_code=status_code,
        )
        logger.debug(
            f"Mocked HAPI FHIR response for pattern: {path_regex}, "
            f"data={response_data}"
        )

    return _mock

# -----------------------------
# Test bearer token fixture
# -----------------------------
@pytest.fixture
def test_token():
    return "test-token"
