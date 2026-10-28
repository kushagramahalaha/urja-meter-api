# Urja Meter Ops API

A documented REST API built with **FastAPI** that wraps selected read operations from the Urja Meter Ops portal. It provides a structured interface for searching meters, retrieving meter location and energy history, and listing distribution transformers.

The project demonstrates how to investigate an existing web application, reproduce its authenticated HTTP requests, and expose useful operations through a clean, testable API.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Installation and Configuration](#installation-and-configuration)
- [Running the Application](#running-the-application)
- [API Endpoints](#api-endpoints)
- [Example Request](#example-request)
- [Architecture and Design Decisions](#architecture-and-design-decisions)
- [Assumptions and Limitations](#assumptions-and-limitations)
- [Intentionally Skipped Features](#intentionally-skipped-features)
- [Testing](#testing)
- [Future Improvements](#future-improvements)
- [Documentation](#documentation)
- [Security Notes](#security-notes)

## Overview

The Urja Meter Ops portal provides operational information about meters, their geographic locations, energy readings, and distribution transformers.

The assignment involved exploring the existing portal, identifying its useful backend requests, understanding authentication and response structures, and building a small API around the relevant operations.

The solution uses Python, `httpx`, and FastAPI. The portal remains the upstream data source; this project does not create a separate database or independently store the portal's operational records.

## Features

- **Meter Search:** Search meter records using a query and page number.
- **Meter Location:** Retrieve geographic information for a specific meter.
- **Energy History:** Retrieve energy readings for a specific meter.
- **Transformer Listing:** Retrieve paginated distribution-transformer records.
- **Session Management:** Authenticate with the portal and reuse the authenticated HTTP session.
- **Interactive API Documentation:** Explore and execute API requests through Swagger UI.
- **Automated Tests:** Validate expected API behavior through pytest.

## Project Structure

The project separates HTTP communication, API routing, response schemas, and application initialization.

```text
API_urja_meter/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── clients/
│   │   └── portal_client.py
│   ├── routers/
│   │   ├── meters.py
│   │   └── transformers.py
│   └── schemas/
│       ├── meter.py
│       ├── energy.py
│       └── transformer.py
├── tests/
│   └── test_api.py
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
├── PROTOCOL.md
└── openapi.json
```

**Component responsibilities**

- `app/main.py` initializes FastAPI and registers the API routers.
- `app/config.py` loads application configuration.
- `app/clients/portal_client.py` handles portal authentication, session reuse, and upstream HTTP requests.
- `app/routers/meters.py` exposes meter search, location, and energy-history routes.
- `app/routers/transformers.py` exposes transformer-listing functionality.
- `app/schemas/` defines structured request or response models where applicable.
- `tests/` contains automated tests.
- `.env.example` documents the required environment variables without storing actual credentials.
- `PROTOCOL.md` records the portal investigation and the reasoning behind the implementation.
- `openapi.json` provides the OpenAPI specification for the wrapper API.

The tree above represents the intended layout. If your local repository differs, adjust the paths to match the actual files.

## Requirements

- Python 3.10 or later; Python 3.11 is a suitable choice.
- Access to the Urja Meter Ops portal.
- Valid portal credentials authorized for the required operations.
- Network connectivity to the configured portal URL.
- Dependencies listed in `requirements.txt`.

## Installation and Configuration

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd API_urja_meter
```

Replace the placeholder with your repository's actual URL.

### 2. Create a virtual environment

On macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example configuration file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Configure the following values in `.env`:

```dotenv
PORTAL_BASE_URL=https://urja-ops.flockenergy.tech
PORTAL_EMAIL=your_authorized_portal_email
PORTAL_PASSWORD=your_authorized_portal_password
REQUEST_TIMEOUT_SECONDS=15
```

Use the correct portal base URL and credentials provided for your environment. Do not commit the populated `.env` file to Git.

The timeout value is a configurable request timeout, not a guarantee that every portal operation will complete within that duration.

## Running the Application

From the repository root, activate the virtual environment and run:

```bash
uvicorn app.main:app --reload
```

The local API should be accessible at:

- **Base URL:** `http://127.0.0.1:8000`
- **Swagger UI:** `http://127.0.0.1:8000/docs`
- **ReDoc:** `http://127.0.0.1:8000/redoc`
- **OpenAPI JSON:** `http://127.0.0.1:8000/openapi.json`

The documentation interfaces are provided by FastAPI.

A successful startup means the application has started. It does not by itself guarantee that the upstream portal is reachable or that authentication will continue to work for every request.

## API Endpoints

### 1. Health Check

`GET /health`

Provides a health endpoint for the wrapper application.

Example:

```bash
curl http://127.0.0.1:8000/health
```

The health endpoint should be interpreted according to the checks implemented in the application. Do not assume it verifies upstream portal availability unless it explicitly performs that check.

### 2. Search Meters

`GET /api/v1/meters`

**Query parameters**

- `q`: Search query.
- `page`: Page number.

Example:

```bash
curl --get "http://127.0.0.1:8000/api/v1/meters" \
  --data-urlencode "q=J100004" \
  --data-urlencode "page=1"
```

The endpoint wraps the portal's meter-search operation and returns matching meter records with pagination information.

Observed meter fields included `meterId`, `serialNo`, `make`, `phaseType`, `installStatus`, and `dtCode`.

### 3. Retrieve Meter Location

`GET /api/v1/meters/{meter_id}/geo`

Example:

```bash
curl "http://127.0.0.1:8000/api/v1/meters/J100000/geo"
```

Replace `J100000` with the identifier of a meter you are authorized to query.

This endpoint retrieves geographic information for the selected meter.

### 4. Retrieve Meter Energy History

`GET /api/v1/meters/{meter_id}/energy`

Example:

```bash
curl "http://127.0.0.1:8000/api/v1/meters/J100000/energy"
```

This endpoint retrieves energy-history records for the selected meter.

Observed energy-related fields included `timestamp`, `kwh`, `kvah`, and `voltR`. The actual response depends on the upstream portal data and the implemented response model.

### 5. List Transformers

`GET /api/v1/transformers`

**Query parameters**

- `page`: Page number.

Example:

```bash
curl "http://127.0.0.1:8000/api/v1/transformers?page=1"
```

This endpoint retrieves transformer records with pagination metadata. Observed transformer fields included `code`, `name`, `feederCode`, and `capacityKva`.

For exact response models and parameter constraints, use the running Swagger UI or consult `openapi.json`.

## Example Request

The following example demonstrates how a client can request meter search results from the wrapper API without directly handling the portal's login process.

**Request**

```http
GET /api/v1/meters?q=J100004&page=1 HTTP/1.1
Host: 127.0.0.1:8000
```

**Illustrative response structure**

```json
{
  "data": [
    {
      "meterId": "J100004",
      "serialNo": "EXAMPLE_SERIAL",
      "make": "EXAMPLE_MAKE",
      "phaseType": "EXAMPLE_PHASE",
      "installStatus": "EXAMPLE_STATUS",
      "dtCode": "EXAMPLE_DT"
    }
  ],
  "page": 1,
  "pageSize": 20,
  "total": 1
}
```

This JSON illustrates the observed meter-search structure; the values and total are examples, not a claim about the live response. Use the actual response schema returned by your running implementation as the authoritative contract.

## Architecture and Design Decisions

### Investigation-Driven Development

The portal did not provide a complete API specification for this assignment. We explored the portal's normal workflows and inspected browser Network requests to discover relevant HTTP methods, paths, headers, authentication behavior, and response fields.

The findings are documented in `PROTOCOL.md`.

### Shared Portal Client

Authentication and upstream request handling are centralized in `PortalClient`.

This reduces duplicated code and provides a single location for session management, request timeouts, response parsing, and upstream error handling.

### HTTPX for Upstream Communication

`httpx` was selected to make HTTP requests from Python and preserve session state through a reusable client.

During investigation, we found that the login flow required appropriate request headers, including the expected `Origin` header. Reproducing the login behavior programmatically was an important step in validating the approach.

### FastAPI for the Wrapper API

FastAPI provides a simple way to expose HTTP endpoints, validate parameters, organize routers, and publish an OpenAPI specification.

Its interactive documentation also makes manual evaluation easier.

### Versioned API Routes

The public wrapper routes use the `/api/v1` prefix. This separates our API interface from the original portal's internal routes and gives the interface a clear place for future evolution.

### Preserve Upstream Pagination

The meter and transformer endpoints expose pagination information observed in the original portal.

Preserving this information helps callers understand whether a response represents one page or the whole dataset. Values such as total records and page size should be treated as dynamic upstream data rather than hard-coded constants.

### Keep Unverified Features Out of the Core Scope

Export-related requests and signing headers were observed during investigation, but their complete behavior was not verified.

The implementation therefore focuses on the core read operations rather than building dependencies on an incompletely understood signing mechanism.

## Assumptions and Limitations

The implementation is based on the following findings and assumptions:

- The portal is the upstream source of truth for meter, energy, geographic, and transformer data.
- The selected portal routes are available to the account used to run the application.
- The login flow and cookie-based session behavior observed during investigation remain applicable to the configured environment.
- Portal records and pagination totals can change over time.
- A meter may not necessarily have every optional geographic or energy field populated.
- The exact behavior of session expiry, API rate limits, and some error responses was not fully established.
- Timestamp timezone and energy-history retention rules were not conclusively verified.
- The complete contract of the export/signing-related operations remains outside the verified scope.

These limitations should be revisited before using the service as a production integration.

## Intentionally Skipped Features

To keep the solution focused on the assignment, the following were not included in the core scope:

- Recreating the portal's user interface.
- Building a separate database or independent data warehouse.
- Implementing write operations that modify portal records.
- Integrating the export and signing-related workflow whose full behavior was not verified.
- Adding a separate API authentication layer for external consumers beyond the authentication behavior actually implemented.
- Adding caching, background synchronization, or a scheduled ingestion pipeline.
- Claiming production-grade monitoring, availability, or performance guarantees without supporting tests.

These are scope decisions, not claims that the portal lacks these capabilities.

## Testing

Run the automated test suite from the repository root:

```bash
python -m pytest -q
```

The tests should verify the behavior implemented in `tests/`, including route responses and relevant error handling.

Manual validation can be performed through Swagger UI at:

```text
http://127.0.0.1:8000/docs
```

Use the documented endpoints to inspect the actual response structures and status codes.

The existence of a passing test run does not by itself demonstrate complete coverage of every upstream portal behavior. Record the actual test result when evaluating the submission.

## Future Improvements

Given additional time, the following improvements would make the integration more robust:

1. **Stronger Error Handling:** Define consistent error responses for authentication failures, upstream timeouts, invalid identifiers, and unexpected portal responses.
2. **Session Recovery:** Detect expired sessions and implement safe re-authentication where supported by the portal.
3. **More Comprehensive Tests:** Add tests for empty results, invalid pagination, missing data, upstream failures, and session-expiry scenarios.
4. **Response Contract Verification:** Validate every response schema against representative upstream responses and improve schema documentation.
5. **Operational Observability:** Add structured logging, request correlation, and basic health checks without exposing credentials or sensitive response data.
6. **Pagination Validation:** Confirm the portal's pagination conventions and define explicit validation rules for the wrapper.
7. **Configuration and Deployment:** Add deployment guidance, environment-specific configuration, and production server recommendations.
8. **Performance Evaluation:** Measure upstream latency and determine whether caching or bounded concurrency would help without violating portal usage policies.

These improvements should be prioritized according to verified requirements and the portal's supported behavior.

## Documentation

The repository contains the following supporting documentation:

- **`README.md`** — Installation, configuration, run instructions, example requests, architecture, and design decisions.
- **`PROTOCOL.md`** — Investigation notes describing what was discovered in the portal, how evidence was collected, and how that evidence informed the implementation.
- **`openapi.json`** — Machine-readable API specification for the wrapper service.

FastAPI also serves interactive API documentation at `/docs` and ReDoc at `/redoc` while the application is running.

Keep `openapi.json` synchronized with the actual routes and schemas whenever the API contract changes.

## Security Notes

- Store portal credentials in environment variables or an appropriate secret manager.
- Never commit `.env`, session cookies, passwords, or signing secrets.
- Do not log authentication headers or sensitive raw responses.
- Use only accounts and portal operations you are authorized to access.
- Review `.gitignore` and inspect staged files before committing changes.
- If credentials or session tokens are accidentally exposed, follow the portal owner's revocation and rotation process.

## Conclusion

This project turns a set of useful operations discovered in the Urja Meter Ops portal into a documented API interface.

The workflow combines browser-based investigation, evidence-driven design, authenticated HTTP communication, FastAPI route development, and API testing. The result provides a focused starting point for accessing meter and transformer information while documenting the assumptions and unresolved questions that matter for future development.
