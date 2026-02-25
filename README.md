# Gen3 FHIR Server
Google Summer of Code 2025 – FHIR Proxy Project

This project implements a FHIR proxy on Gen3, supporting NCPI FHIR resources with secure access control.  
It provides a fully containerized FastAPI proxy, HAPI FHIR server, and Arborist authorization service for local or cloud deployment.


---

## Contributor Information
- **Name:** Andriana Sielli  
- **Organization:** Center for Translational Data Science, University of Chicago  
- **Mentors:** Alex Vantol, Kyle Burton  
- **GSoC Year:** 2025
  
---

## Table of Contents
1. [Contributor Information](#contributor-information)
2. [Environment Variables](#environment-variables)
3. [HAPI FHIR Server Setup](#hapi-fhir-server-setup)
4. [PostgreSQL Setup](#postgresql-setup)
5. [Data Ingestion](#data-ingestion)
   - [Synthea Data](#synthea-data)
   - [NCPI FHIR](#ncpi-fhir)
6. [Proxy & Authorization](#proxy--authorization)
7. [Dockerization](#dockerization)
8. [Unit Testing](#unit-testing)
9. [Useful Links / References](#useful-links--references)


---
## Environmental Variables  
 
### .env example  

```bash
AUTH_SERVER_URL=https://auth.example.com  
SECURITY_TAG_PREFIX=ncpi-security  
PROXY_TIMEOUT=3000  
ARBORIST_URL=https://arborist.example.com  
HAPI_FHIR_URL=https://fhir.example.com  
ARBORIST_TIMEOUT=5000  
```
## HAPI FHIR JPA SERVER:  
```bash
git clone https://github.com/hapifhir/hapi-fhir-jpaserver-starter.git  
cd hapi-fhir-jpaserver-starter
```
   
## PostgreSQL Setup (MacOS example): 

```bash
brew install postgresql  
brew services start postgresql  
```  
To test that it's running:  
```bash
brew services list | grep postgresql
```
If you want to connect, use:
```bash
psql postgres
```
Then, create the postgres superuser, the HAPI user, and the database:
```bash  
psql postgres -c "CREATE DATABASE hapi_database;"  
psql postgres -c "CREATE USER hapi_user WITH PASSWORD 'Password';"  
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE hapi_database TO hapi_user;"  
```
Now you can test the login:
```bash  
psql -U hapi_user -d hapi_database
```

In the hapi-fhir-jpaserver-starter folder there is a pom.xml.  
The following PostgreSQL dependency is present in pom.xml

```xml
<dependency>  
  <groupId>org.postgresql</groupId>  
  <artifactId>postgresql</artifactId>  
  <!-- <scope>runtime</scope> optional -->
</dependency>
```

Open the application.yaml in the following directory  

hapi-fhir-jpaserver-starter/src/main/resources/application.yaml  

Configure application.yaml:

Find section “B. Core Spring” and replace the following sections:
 

```yaml

  datasource:
    url: jdbc:postgresql://localhost:5432/hapi_database
    username: hapi_user
    password: Password
    driver-class-name: org.postgresql.Driver
    hikari:
      maximum-pool-size: 15

  jpa:
    properties:
      hibernate:
        format_sql: false
        show_sql: false
        # Hibernate dialect is auto-detected except for H2/Postgres.
        # If using H2:     ca.uhn.fhir.jpa.model.dialect.HapiFhirH2Dialect
        # If using Postgres: ca.uhn.fhir.jpa.model.dialect.HapiFhirPostgresDialect
        dialect: ca.uhn.fhir.jpa.model.dialect.HapiFhirPostgresDialect

        # --- Optional Hibernate DDL & tuning ---
        hbm2ddl:
          auto: update
        jdbc:
          batch_size: 20
        cache:
          use_query_cache: false
          use_second_level_cache: false
          use_structured_entries: false
          use_minimal_puts: false

        
```

Go to the hapi-fhir-jpaserver-starter that there is the pom.xml and then run: 
```bash 
mvn spring-boot:run
```
You can access the Swagger  UI at http://localhost:8080/fhir/swagger-ui/ 


## Data Ingestion
### Synthea Data 

```bash
git clone https://github.com/synthetichealth/synthea.git  
cd synthea  
```
for ten records: 
```bash
./gradlew build  
./run_synthea -p 10  
```
the default is FHIR json. 

Data output: synthea/output/fhir/

Ingestion order: 
1. Organization  
2. Location  
3. Practitioner  
4. PractitionerRole  
5. Patient  
6. Encounter  
7. Condition  
8. Observation  
9. Medication  
10. MedicationRequest  
11. CareTeam  
12. CarePlan  

### NCPI FHIR  
Prerequisites: sushi 

```bash
sushi  
npm install -g sushi  
sushi .  
```

```bash
git clone https://github.com/NIH-NCPI/ncpi-fhir-ig-2.git
cd ncpi-fhir-ig-2
./_updatePublisher.sh  
./_genonce.sh  
```


Ingest resources: 
```bash 
for file in *.json; do
  resource_type="${file%%-*}"
  resource_id="${file#*-}"
  resource_id="${resource_id%.json}"

  echo "Uploading $file to $resource_type/$resource_id ..."

  curl -X PUT "http://localhost:8080/fhir/${resource_type}/${resource_id}" \
       -H "Content-Type: application/fhir+json" \
       -d @"$file"

  echo ""


```
<img width="492" height="217" alt="Screenshot 2025-08-08 at 2 34 44 PM" src="https://github.com/user-attachments/assets/009a9b64-8201-4977-a3e1-d4b1b65bdba3" />

test ingestion:  
```bash
curl -X GET "http://localhost:8080/fhir/StructureDefinition?_summary=count" -H "Accept: application/fhir+json"
curl -X GET "http://localhost:8080/fhir/CodeSystem?_summary=count" -H "Accept: application/fhir+json"
curl -X GET "http://localhost:8080/fhir/ValueSet?_summary=count" -H "Accept: application/fhir+json"
curl -X GET "http://localhost:8080/fhir/Patient?_summary=count" -H "Accept: application/fhir+json"
```

## Proxy & Authorization:
Architecture Flow  

- Client → Proxy: Sends request with Bearer token
- Proxy → Arborist: Validates token + gets resources
- Proxy → FHIR: Forwards request with _security tags
- FHIR → Proxy: Returns filtered data
- Proxy → Client: Passes through response


<img width="826" height="546" alt="Screenshot 2025-08-02 at 6 08 52 PM" src="https://github.com/user-attachments/assets/0e02c1b1-0277-4b96-9b59-db25453d6e56" />

```bash
pip install poetry  
poetry install  
poetry run uvicorn app.main:app --reload --port 8082
```



Arborist setup

```bash
export OIDC_ISSUER=https://qa.planx-pla.net/user  
export JWKS_ENDPOINT=https://qa.planx-pla.net/user/.well-known/jwks  

./bin/arborist --port 8081  
```
##  Dockerization of the FHIR proxy  


Run the FHIR proxy locally using Docker Compose.

- **Stack Components:**
  - `fhir-proxy` – FastAPI service with Gunicorn, exposed on port 8888
  - `hapi-fhir` – HAPI FHIR server, exposed on port 8080
  - `arborist` – Authorization service, exposed on port 8081
- **Dependencies:** Python packages managed via Poetry
- **Configuration:** Environment variables control URLs, timeouts, and security tags
- **Functionality:** Proxy forwards requests to HAPI FHIR while enforcing security via Arborist

```bash
docker compose build --no-cache
docker compose up

```

## Unit Testing:  

The project includes unit tests to verify the FHIR proxy’s functionality and security.  

- **Tools:** `pytest`, `pytest-asyncio`, `pytest-httpx`  
- **What is tested:**  
  - Retrieval of individual FHIR resources  
  - Search queries with `_security` filters  
  - Enforcement of bearer token permissions

All external services (Gen3 authorization and HAPI FHIR server) are mocked so tests can run locally without a live server. 

To run the tests:

```bash
pytest -v tests/
```
 
Environment file: .env.test

GEN_USER_URL=https://qa.planx-pla.net/user/user  
FHIR_SERVER_URL=http://localhost:8080/fhir

## HELM:

### FOR PROXY 
Start Minikube
```bash
brew install minikube
minikube start
kubectl get nodes
```

Switch Docker to Minikube
```bash
eval $(minikube docker-env)
```

In the Docker folder, where the Dockerfile is run:
```bash
docker build -t fhir-proxy:latest .
```

In the Helm folder run: 

```bash
helm upgrade fhir-stack . -f values.yaml
kubectl get pods
minikube service fhir-proxy
```

### FOR HAPI FHIR SERVER

```bash
docker build -t hapi-fhir-server:latest .
```
```bash
helm upgrade hapi-fhir . -f values.yaml

```
```bash
minikube service hapi-fhir
```

# LINKS:
1. Create a FastAPI instance: https://fastapi.tiangolo.com/tutorial/first-steps/  
2. Async Support: https://www.python-httpx.org/async/  
3. URL Parse: https://docs.python.org/3/library/urllib.parse.html#urllib.parse.urlparse
4. FHIR Security: https://www.hl7.org/fhir/security.html
5. Bearer Token Usage: https://www.rfc-editor.org/rfc/rfc6750





