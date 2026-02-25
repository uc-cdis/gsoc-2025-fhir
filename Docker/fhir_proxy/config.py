from starlette.config import Config

config = Config(".env")

class Settings:

    ARBORIST_URL = config("ARBORIST_URL", default="http://localhost:8081/auth/r$
    ARBORIST_TIMEOUT = config("ARBORIST_TIMEOUT", cast=int, default=5)


    HAPI_FHIR_URL = config("HAPI_FHIR_URL", default="http://localhost:8080/fhir$

    SECURITY_TAG_PREFIX = config("SECURITY_TAG_PREFIX", default="gen3|")


    PROXY_TIMEOUT = config("PROXY_TIMEOUT", cast=float, default=30.0)


    GEN_USER_URL = config("GEN3_USER_URL", default="https://qa.planx-pla.net/us$

settings = Settings()

ARBORIST_URL = settings.ARBORIST_URL
ARBORIST_TIMEOUT = settings.ARBORIST_TIMEOUT
HAPI_FHIR_URL = settings.HAPI_FHIR_URL
SECURITY_TAG_PREFIX = settings.SECURITY_TAG_PREFIX
PROXY_TIMEOUT = settings.PROXY_TIMEOUT
GEN_USER_URL = settings.GEN_USER_URL

