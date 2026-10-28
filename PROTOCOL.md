# PROTOCOL.md — Portal Investigation and Solution Process

## 1. Objective

The goal of this assignment was to understand how the Urja Meter Ops portal exposes operational data and build a small, documented API that makes the useful read operations accessible through a cleaner interface.

There was no official API specification available during our investigation. Instead of guessing how the portal worked, we explored the application through normal use, observed its network traffic, reproduced requests, and used the evidence to design the wrapper API.

This document explains:

1. What we discovered while exploring the portal.
2. How we organized those discoveries to identify a practical solution.
3. How we implemented and validated that solution.
4. What remains unknown and could be investigated further.

## 2. How We Investigated the Portal

### Step 1 — Explore the Application as a Real User

We first signed in to the portal and explored its available workflows instead of immediately writing API code. We focused on searching for meters, opening meter information, viewing energy history, and browsing distribution transformers.

This helped us identify the main operational resources and understand which user actions caused the application to request data.

**Engineering reasoning:** Before building an integration, we need to understand what the existing application does and which information the new solution must provide.

### Step 2 — Inspect Browser Network Activity

We opened the browser's Developer Tools Network panel while performing the relevant actions.

For each request, we inspected the HTTP method, request path, query parameters, headers, response status, and response body.

The Network panel helped us understand how the user interface communicated with the backend. It also revealed requests that were not immediately visible from the portal's interface.

**Engineering reasoning:** An undocumented application can still expose useful technical evidence through its normal network traffic. Observing actual requests is more reliable than guessing endpoint paths or response structures.

### Step 3 — Record the Useful Requests

During the investigation, we identified the following requests.

#### Sign In
- **Observed request:** `POST /login`
- **Purpose:** Authenticate the user before accessing protected information.
- **Finding:** The login flow required the appropriate request headers and session handling.

#### Search Meters
- **Observed request:** `GET /portal/meters/search?q=...&page=...`
- **Purpose:** Search for meters and retrieve matching records.
- **Finding:** The response provided meter information and pagination metadata.

#### Read Meter Location
- **Observed request:** `GET /portal/meters/{meter_id}/geo`
- **Purpose:** Retrieve geographic information for a selected meter.
- **Finding:** The response included geographic fields such as latitude and longitude.

#### Read Meter Energy History
- **Observed request:** `GET /portal/meters/{meter_id}/energy`
- **Purpose:** Retrieve energy readings and historical information for a selected meter.
- **Finding:** The response contained energy-related records.

#### List Transformers
- **Observed request:** `GET /portal/dts?page=...`
- **Purpose:** Retrieve distribution-transformer records.
- **Finding:** The response included transformer information and pagination metadata.

We also encountered `/portal/geo`, `/portal/energy`, `/portal/export`, and `/portal/keys` while inspecting network activity. We did not establish the complete contracts of all these endpoints, so they were not included as dependencies of the core wrapper API.

## 3. What Information We Learned

### 3.1 Authentication and Session Behavior

The portal used `POST /login` with email and password form fields.

The observed browser request included application-related headers. While reproducing the login request with Python, including the expected `Origin` header was necessary for a successful login. The observed request also included `Referer` and `X-Sveltekit-Action: true`.

After successful authentication, subsequent requests reused session state carried in cookies.

This finding influenced our implementation: the API client needed to preserve the authenticated session across requests rather than create a new unauthenticated session for every operation.

We did not establish the portal's exact session lifetime, refresh behavior, or complete logout and revocation rules.

Credentials, cookies, and signing material are sensitive and must not be included in source code, documentation, or Git commits.

### 3.2 Meter Records and Search

The meter-search response contained the following fields:

- `data`: the returned meter records.
- `page`: the current page.
- `pageSize`: the number of records per page.
- `total`: the reported total number of matching records.

Observed meter fields included:

- `meterId`
- `serialNo`
- `make`
- `phaseType`
- `installStatus`
- `dtCode`

The tested page size was 20, and one response reported 403 total meter records. These are observations from the investigation, not permanent constants.

The search operation also revealed a useful workflow: first locate a meter, then use its identifier to request additional information.

### 3.3 Meter Location and Energy History

The meter geography endpoint returned geographic information, including latitude and longitude. Exact coordinates are intentionally excluded from this document.

The energy endpoint returned reading and history data. Fields observed during schema investigation included:

- `timestamp`
- `kwh`
- `kvah`
- `voltR`

One test request returned 337 energy records for a meter. This was one observed response and does not establish a guaranteed history length or retention period.

We did not conclusively establish coordinate accuracy, timestamp timezone, sampling guarantees, or energy-data retention rules.

### 3.4 Transformer Records

The transformer-list response included fields such as:

- `code`
- `name`
- `feederCode`
- `capacityKva`

The response also contained pagination metadata. During the investigation, one response reported 40 total transformer records with a page size of 20.

Meter records also contained a `dtCode` field. This suggested a possible reference between meter records and transformer records. However, we did not reconstruct or verify the complete electrical network hierarchy.

### 3.5 Export-Related Behavior

An export-related request included `X-Timestamp` and `X-Signature` headers. We also encountered `/portal/keys`, which appeared to involve signing-related material.

We did not verify the complete signature algorithm, key lifecycle, or intended security model. Therefore, the core wrapper API does not depend on these operations.

No signing secret or sensitive key material is recorded in this document.

## 4. How We Structured the Findings

After collecting evidence, we organized the observations by resource and responsibility instead of treating every discovered request as an unrelated coding task.

### 4.1 Authentication

**Evidence collected:** Login request, relevant headers, and cookie-based session behavior.

**Design decision:** Put login and session reuse in a shared portal client.

This avoids duplicating authentication logic across multiple API endpoints.

### 4.2 Meter Collection

**Evidence collected:** Search parameters, meter fields, and pagination metadata.

**Design decision:** Provide a meter-search route and preserve the portal's pagination information.

This allows callers to search for meter records without needing to understand the original portal interface.

### 4.3 Meter Location

**Evidence collected:** Meter identifier in the request path and geographic fields in the response.

**Design decision:** Create a separate API route for retrieving location information for a selected meter.

Separating this operation keeps the API responsibilities clear.

### 4.4 Energy History

**Evidence collected:** Meter-specific requests returning energy reading records.

**Design decision:** Create a separate route for retrieving a meter's energy history.

This provides a clear boundary between meter search and historical measurement retrieval.

### 4.5 Transformers

**Evidence collected:** Transformer-list requests, transformer fields, and pagination metadata.

**Design decision:** Create a transformer-list route that exposes the relevant records and pagination.

### 4.6 Unclear or Sensitive Operations

**Evidence collected:** Export-related headers and the `/portal/keys` endpoint.

**Design decision:** Document these findings, but keep them outside the core implementation until their behavior and security requirements can be established.

This prevents the solution from depending on mechanisms that we have not fully understood.

## 5. How We Distinguished Facts from Assumptions

A key part of the investigation was distinguishing direct observations from engineering decisions and unresolved questions.

### Observed

These are findings directly visible in browser requests or responses, or reproduced successfully through the Python client.

Examples include the login path, meter-search parameters, response fields, pagination metadata, and the need to include the expected `Origin` header during login.

### Inferred for Design

These are reasonable implementation choices based on the observations.

For example, because authenticated requests reused session cookies, we chose a persistent HTTP client to maintain session state.

### Unknown

These are behaviors we did not verify.

Examples include session expiry, rate limits, timestamp timezone, and the complete export-signing mechanism.

Keeping these categories separate prevents us from treating a single successful request as proof of the portal's complete behavior.

## 6. How We Identified the Solution

The portal already exposed read operations for the core data we needed. The practical solution was therefore to build a wrapper around those requests rather than recreate the user interface or introduce an unrelated data source.

We selected a small set of operations:

- Search and paginate meter records.
- Retrieve geographic information for a meter.
- Retrieve energy history for a meter.
- List and paginate transformer records.
- Provide a health endpoint for the wrapper service.

The purpose of the wrapper was to offer a cleaner, documented interface while reusing the existing portal data.

The API was versioned under `/api/v1` to separate our public interface from the portal's internal request paths.

## 7. How We Built the Solution

### Step 1 — Reproduce the Request Outside the Browser

We implemented the login flow in Python using `httpx`.

The first challenge was reproducing the browser's login behavior, including the relevant headers and session handling. We found that the expected `Origin` header was necessary for successful login.

After authentication, the same client was reused for protected requests so that the session cookies remained available.

This step demonstrated that the observed request flow could be reproduced programmatically rather than only through the browser.

### Step 2 — Centralize Portal Communication

We implemented a `PortalClient` to handle portal-specific HTTP operations.

Its responsibilities include:

- Logging in to the portal.
- Reusing authenticated session state.
- Sending requests to the observed endpoint paths.
- Parsing JSON responses.
- Managing the HTTP client's lifecycle.

Centralizing this behavior avoids duplicating authentication and request-handling logic in individual API routes. It also provides a single location for improving timeout handling and upstream error handling.

### Step 3 — Create FastAPI Routes

We used FastAPI to expose a simpler API over the portal operations.

The wrapper provides the following routes.

#### Search Meters

`GET /api/v1/meters?q=...&page=...`

Wraps the portal's meter-search operation and returns meter records with pagination metadata.

#### Read Meter Location

`GET /api/v1/meters/{meter_id}/geo`

Wraps the portal's geographic-information endpoint for a selected meter.

#### Read Meter Energy History

`GET /api/v1/meters/{meter_id}/energy`

Wraps the portal's energy-history endpoint for a selected meter.

#### List Transformers

`GET /api/v1/transformers?page=...`

Wraps the portal's transformer-list operation.

#### Health Check

`GET /health`

Provides a health endpoint for the wrapper service.

A successful response from `/health` should not automatically be interpreted as proof that the upstream portal is available or that the authenticated session remains valid unless the implementation explicitly performs those checks.

### Step 4 — Separate Responsibilities

The project structure separates application entry-point logic, portal communication, API routers, and response schemas.

- `app/main.py`: Creates the FastAPI application and registers routers.
- `app/clients/portal_client.py`: Handles the upstream portal session and requests.
- `app/routers/`: Defines the routes exposed by our API.
- `app/schemas/`: Defines structured response models where applicable.
- `tests/`: Contains automated tests for expected API behavior.
- `openapi.json`: Describes the public API contract.
- `README.md`: Explains project setup and usage.
- `PROTOCOL.md`: Records how the portal was investigated and how the findings informed the solution.

This structure makes the code easier to understand, test, and debug. For example, upstream request handling can be investigated in the client layer without mixing it into route definitions.

### Step 5 — Validate the Implementation

We tested the wrapper routes through the FastAPI Swagger UI and observed successful `200 OK` responses for the core routes we exercised.

We also ran the project's pytest command. The exact test count and coverage are not recorded here, so no numerical coverage claim is made.

The generated `openapi.json` describes the wrapper's exposed endpoints and schemas. It should remain consistent with the implementation and be updated whenever the public API contract changes.

## 8. Engineering Decisions and Why They Matter

### 8.1 Use Evidence Instead of Guessing

Browser Network inspection provided concrete request paths, headers, parameters, and response structures. This gave us a reliable starting point for implementation.

### 8.2 Reuse an Authenticated Session

Since protected requests relied on session cookies, a persistent HTTP client was a suitable way to reproduce the observed behavior.

### 8.3 Keep the API Focused

The wrapper concentrates on the core read operations needed for the assignment. It avoids depending on incompletely understood export and signing functionality.

### 8.4 Preserve Pagination

The original portal returned paginated data. Preserving page information and record totals makes the wrapper more useful and helps callers understand which part of the data they have received.

### 8.5 Separate the Public API from the Portal

The FastAPI routes provide a versioned interface for API consumers. This separates our API contract from the portal's internal paths and makes future changes easier to manage.

### 8.6 Document Unknowns Honestly

Session lifetime, rate limits, timestamp timezone, and some endpoint behaviors remain unresolved. Recording these gaps helps prevent unsupported assumptions from becoming hidden dependencies.

### 8.7 Protect Sensitive Information

Credentials, session cookies, signing material, and sensitive raw responses must not be committed, logged unnecessarily, or included in documentation.

## 9. Remaining Unknowns and Future Investigation

The investigation did not conclusively establish the following:

- How long a login session remains valid or how re-authentication should be handled.
- Exact error response formats for invalid meter identifiers, empty searches, invalid page values, and server failures.
- Rate limits, concurrency limits, or production availability expectations.
- The timezone, sampling interval, and retention policy for energy timestamps.
- Whether coordinates and transformer references are populated for every record.
- The supported purpose and complete security contract of export/signing-related endpoints.
- Whether `/health` checks only the local process or also upstream reachability in every running configuration.

These questions should be verified through authorized testing or clarified with the portal owner before the integration is treated as production-ready.

## 10. End-to-End Engineering Workflow

The solution followed an evidence-led process.

1. **Explore:** Use the portal's normal workflows to discover which information users can access.
2. **Observe:** Inspect Network requests to identify methods, paths, parameters, headers, authentication behavior, and JSON responses.
3. **Record:** Document the useful requests and fields returned by the portal.
4. **Organize:** Group findings by authentication and business resource, and identify pagination and session requirements.
5. **Evaluate:** Separate verified facts, implementation assumptions, and unresolved behavior.
6. **Design:** Select a small set of useful read operations and define a cleaner, versioned API.
7. **Implement:** Reproduce the authenticated session through a shared `httpx` client and expose the selected operations through FastAPI routers.
8. **Validate:** Test the routes through Swagger, run automated tests, and maintain the OpenAPI specification.
9. **Document:** Explain what was verified, why the design decisions were made, and what still needs investigation.

## Conclusion

The main engineering outcome was not only an API wrapper. It was a repeatable method for turning an undocumented web application's observed behavior into a small, testable, documented integration.

By exploring the portal, examining network traffic, recording response structures, separating observations from assumptions, and validating requests programmatically, we developed an implementation grounded in evidence rather than guesswork.

The remaining unknowns are documented explicitly so that future work can focus on verified gaps instead of relying on unsupported assumptions.
