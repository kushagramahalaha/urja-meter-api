# Urja Meter API

A clean, documented FastAPI service over the Urja Meter Ops legacy portal. The service provides programmatic access to meter search, geographic coordinates, consumption history, and distribution transformer records.

## Problem Statement

Urja Meter Ops provides meter and network information through a web portal designed for human users. This project adds a structured HTTP API so another engineer or application can retrieve that information without manually navigating the original portal.

## Features

- Portal login and HTTP session management.
- Meter search with query and page parameters.
- Meter-specific geographic information.
- Meter consumption history.
- Paginated distribution transformer records.
- Pydantic response validation.
- Interactive API documentation through Swagger UI.
- Automated tests using mocked portal responses.

## Technology Stack

- Python
- FastAPI
- HTTPX
- Pydantic
- python-dotenv
- pytest
- respx

## Project Structure

```text
app/
  main.py
  config.py
  clients/
    portal_client.py
  routers/
    meters.py
    transformers.py
  schemas/
    meter.py
    energy.py
    transformer.py
tests/
requirements.txt
.env.example
.gitignore
PROTOCOL.md
openapi.json
README.md
REFLECTION.md
```

## Requirements

- Python installed locally.
- Network access to the Urja Meter Ops portal.
- Authorized portal credentials supplied for the assignment.

## Installation and Configuration

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Create a local configuration file:

```bash
cp .env.example .env
```

Set the following variables in `.env` using the authorized assignment credentials:

```dotenv
PORTAL_BASE_URL=https://urja-ops.flockenergy.tech
PORTAL_EMAIL=
PORTAL_PASSWORD=
REQUEST_TIMEOUT_SECONDS=15
```

Keep `.env` private. Never commit passwords, session cookies, signing secrets, or other credentials to the repository.

## Running the API

From the project root, run:

```bash
uvicorn app.main:app --reload
```

Interactive API documentation:

- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`
- Health check: `http://127.0.0.1:8000/health`

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/meters?q=J100000&page=1` | Search meters |
| GET | `/api/v1/meters/{meter_id}/geo` | Get meter coordinates |
| GET | `/api/v1/meters/{meter_id}/energy` | Get meter consumption history |
| GET | `/api/v1/transformers?page=1` | List distribution transformers |
| GET | `/health` | Basic service health check |

## Example Request

Search for a meter:

```bash
curl "http://127.0.0.1:8000/api/v1/meters?q=J100000&page=1"
```

Example response structure:

```json
{
  "data": [
    {
      "meterId": "EXAMPLE-METER",
      "serialNo": "EXAMPLE-SERIAL",
      "make": "Example Manufacturer",
      "phaseType": "single",
      "installStatus": "Installed",
      "dtCode": "DT-001"
    }
  ],
  "total": 1,
  "page": 1,
  "pageSize": 20
}
```

The example values are illustrative. Actual responses depend on the portal data available to the configured account.

## Error Handling

- Invalid query parameters are rejected by FastAPI validation.
- Portal HTTP failures and invalid responses are handled by the portal client.
- Upstream failures are exposed by the relevant routes as HTTP 502 responses.
- Configuration must include the portal login credentials before the application starts.

## Design Decisions and Trade-offs

- **FastAPI:** Provides validation, route registration, automatic OpenAPI generation, and interactive documentation.
- **HTTPX client:** Maintains an HTTP session so the service does not need to log in for every incoming request.
- **Pydantic models:** Define response contracts and validate returned data.
- **No database initially:** The service retrieves data directly from the portal. This avoids maintaining a second copy of the dataset.
- **Mocked tests:** Exercise API behavior without depending on live portal availability.
- **Read-only scope:** The service is designed for data retrieval, not modification of portal records.

## Assumptions

- The supplied portal login is intended for this assignment's read-only exploration.
- The currently observed portal endpoints and response formats may change because the original portal is a legacy application.
- Portal availability, authentication state, and underlying data can affect live API responses.
- The initial implementation retrieves data on demand and does not promise cached or historical snapshots.

## Intentionally Not Implemented

- Data modification or administrative operations.
- A separate database or persistent cache.
- A frontend dashboard.
- Optional network-hierarchy analytics and geospatial search.
- Bulk export through the service, pending further integration and validation.

## Future Improvements

- Add authentication and access control for consumers of the new API.
- Improve session expiry handling and safe reauthentication.
- Add more detailed response models and consistent error schemas.
- Add integration tests for portal failures and authentication expiry.
- Evaluate caching and bulk retrieval if performance requirements justify them.
- Expand network hierarchy and geospatial query capabilities.
- Add monitoring, logging, and deployment configuration.

## Documentation

- [Portal protocol and investigation findings](PROTOCOL.md)
- [OpenAPI specification](openapi.json)
- [Reflection](REFLECTION.md)

## Running Tests

Run the automated test suite:

```bash
python -m pytest -q
```

The tests use mocked portal responses and should not require live portal access.

## Reflection

See [REFLECTION.md](REFLECTION.md) for assumptions, the most difficult part of the investigation, mistakes made, and possible improvements.
