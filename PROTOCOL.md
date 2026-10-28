PROTOCOL.md — Portal Investigation and Solution Process

1. Objective
The goal of this assignment was to understand how the Urja Meter Ops portal exposes operational data and build a small, documented API that makes the useful read operations accessible through a cleaner interface.

There was no official API specification available during our investigation. Instead of guessing how the portal worked, we explored the application through normal use, observed its network traffic, reproduced requests, and used the evidence to design the wrapper API.

This document records three things:
1. What we discovered while exploring the portal.
2. How we organized those discoveries to identify a practical solution.
3. How we implemented and checked that solution.
2. How We Investigated the Portal

Step 1 — Use the application as a real user
We first signed in to the portal and explored the main workflows instead of starting by writing API code. We looked at the actions used to search for meters, open meter information, view energy history, and browse distribution transformers.

This helped identify the actual operational resources the application works with and the user actions that trigger data requests.

Step 2 — Observe browser Network requests
We used the browser's Developer Tools Network panel while carrying out those workflows. For each relevant action, we inspected the request method, path, query parameters, request headers, response status, and response body.

This was important because the portal's visible pages did not, by themselves, explain the complete data interface. The Network panel showed which HTTP requests the browser made to retrieve the information.

Step 3 — Record the request and response evidence
We recorded the useful requests and the fields visible in their responses. We treated those records as observations from the portal rather than assuming they formed a complete or officially supported API specification.



3. What Information I Learned
Authentication and session behavior

- The portal login used POST /login with email and password form fields.
- The browser request included application/browser headers. While reproducing the request with Python, including the expected Origin header was necessary for a successful login. The observed browser request also included Referer and X-Sveltekit-Action: true.
- After login, subsequent requests reused session state carried in cookies.
- This meant the API client needed to preserve the authenticated session between requests instead of issuing every request with a new, unauthenticated HTTP session.
We did not establish the portal's exact session lifetime, refresh behavior, or full logout/revocation rules. Credentials and cookies are secrets and must not be written into this file or committed to the repository.
Meter records and search
The meter-search response contained data, page, pageSize, and total. Meter fields observed in the returned records included meterId, serialNo, make, phaseType, installStatus, and dtCode.

The tested page size was 20. One response reported 403 total meter records. These numbers describe what we observed during the investigation; they are not permanent constants.

The search operation also provided a practical entry point into the data model: find a meter first, use its identifier, and then request additional information for that meter.
Meter location and energy history
- The geo endpoint returned geographic fields such as latitude and longitude. Exact coordinates are intentionally omitted from this document.
- The energy endpoint returned reading/history data. Fields seen during schema investigation included timestamp, kwh, kvah, and voltR.
- One test request returned 337 energy records for a meter. This is a single observation, not a guarantee about history length or retention.
We did not conclusively establish coordinate accuracy, timestamp timezone, sampling guarantees, or energy-data retention rules.
Transformer records
The transformer-list response included fields such as code, name, feederCode, and capacityKva, along with pagination metadata. During the investigation, the response reported 40 total records with a page size of 20.

Meter records also included a dtCode field. This suggested a useful reference between meter and transformer data, but we did not reconstruct or verify the complete network hierarchy.
Export-related behavior

An export-related request included X-Timestamp and X-Signature headers. We also encountered /portal/keys, which appeared to involve signing-related material. We did not verify the complete signature algorithm, key lifecycle, or intended security model. The wrapper therefore does not depend on this path, and no signing secret or signing procedure is recorded here.

4. How We Structured the Findings to Identify a Solution
Rather than treating every observed request as a separate coding task, we grouped the evidence by resource and responsibility.
A. Group requests by resource
Resource or concern	Evidence gathered	Design implication
Authentication	Login request, required headers, cookie-based session	Put login and session reuse in one shared portal client.
Meter collection	Search query, meter fields, page metadata	Provide a meter-search route and preserve pagination information.
Meter location	Meter identifier in the path and geo response	Provide a separate route to retrieve a meter's geographic information.
Energy history	Meter identifier and time-series-like reading records	Provide a separate route for a meter's energy history.
Transformers	Paged list and transformer fields	Provide a transformer-list route with pagination.
Unclear or sensitive operations	Export/signature headers and /portal/keys observation	Record as an investigation finding, but exclude from the core implementation until better understood.


B. Separate facts from assumptions
We used three categories when interpreting the evidence:
- Observed: directly visible in a browser request/response or reproduced successfully by the Python client.
- Inferred for design: a practical engineering choice based on observations, such as using a persistent HTTP session because cookies were reused.
- Unknown: behavior that we did not verify, such as session expiry, rate limits, timestamp timezone, or the complete export-signing mechanism.
This separation prevents us from turning a single successful request into an unsupported claim about the portal's complete behavior.
C. Identify the smallest useful API surface
The portal already had read operations for the core data we needed. The practical solution was therefore to build a wrapper around those requests, rather than reproduce the portal's UI or invent a new data source.

The initial API surface was kept intentionally small:
- Search and paginate meter records.
- Retrieve location information for a meter.
- Retrieve energy history for a meter.
- List and paginate transformer records.
- Provide a health endpoint for the wrapper process.
The goal was to make the existing data easier to consume without pretending that the wrapper had discovered every feature of the portal.

5. How We Built the Solution
Step 1 — Reproduce the portal request outside the browser
We implemented the login flow in Python using httpx. The first challenge was to match the browser's login behavior, including the relevant headers and session handling. Once login succeeded, we reused the same client for protected requests so that cookies from the login response remained available.

This step validated that the observed request flow could be called from our own program, not only from the browser.
Step 2 — Centralize upstream communication
We placed portal-specific HTTP behavior in PortalClient. This client is responsible for logging in, reusing session state, making requests to the observed paths, parsing JSON responses, and managing the HTTP client's lifecycle.

Centralizing this logic avoids duplicating login and cookie handling inside each API route. It also gives us one place to improve timeout handling, authentication error handling, and upstream request behavior.
Step 3 — Add a versioned FastAPI interface
We added FastAPI routes that map to the core portal operations:
Our API route	Portal request it wraps	Responsibility
GET /api/v1/meters?q=...&page=...	GET /portal/meters/search?q=...&page=...	Search meter records and return pagination metadata.
GET /api/v1/meters/{meter_id}/geo	GET /portal/meters/{meter_id}/geo	Retrieve geographic information for a meter.
GET /api/v1/meters/{meter_id}/energy	GET /portal/meters/{meter_id}/energy	Retrieve energy history for a meter.
GET /api/v1/transformers?page=...	GET /portal/dts?page=...	List transformer records.
GET /health	No portal-data request is implied	Check whether the wrapper process is responding.


The API is versioned under /api/v1 so its public routes are distinct from the portal's internal paths. The health endpoint should not be treated as proof that the upstream portal is available or that the authenticated session is still valid unless the implementation explicitly checks those conditions.
Step 4 — Keep responsibilities separate
The project structure separates application entry point, portal communication, API routers, and response schemas. Conceptually, responsibilities are divided as follows:
- app/main.py: creates the FastAPI application and registers routers.
- app/clients/portal_client.py: handles the upstream portal session and requests.
- app/routers/: defines the API routes exposed to callers.
- app/schemas/: describes structured response data where models are used.
- tests/: checks expected API behavior.
- openapi.json: records the public API contract.
- README.md: explains setup and usage.
- PROTOCOL.md: records the portal investigation and how those findings led to the solution.
This separation makes the integration easier to debug: a portal request problem can be investigated in the client layer without mixing it into route definitions.
Step 5 — Validate with real requests and API documentation
We exercised the wrapper routes through the FastAPI Swagger UI and observed successful 200 OK responses for the core routes we tested. We also ran the project's pytest command. The exact test count and coverage are not recorded in this document, so no numerical test-coverage claim is made here.

The generated openapi.json describes the wrapper's exposed endpoints and schemas. The API contract should be kept aligned with the implementation and verified responses whenever either changes.
6. Engineering Decisions and Why They Matter

1. Use observed requests rather than guessing. Browser Network inspection supplied concrete paths, headers, parameters, and response shapes to reproduce.
2. Reuse an authenticated session. Since protected requests relied on session cookies, a persistent HTTP client matches the observed behavior more closely than unrelated one-off requests.
3. Keep the wrapper read-only and focused. The core solution uses the data-retrieval operations needed for the assignment and avoids depending on incompletely understood export/signing functionality.
4. Preserve pagination metadata. The observed lists were paginated, so callers should be able to tell which page they received and how many records the portal reported.
5. Separate internal and public interfaces. FastAPI route names are designed for the wrapper's consumers; they do not expose the portal's internal paths as the public contract.
6. Document uncertainty. Session lifetime, rate limits, timestamp timezone, and some endpoint behaviors remain open questions. A good integration should make those gaps visible instead of silently assuming answers.
7. Protect secrets. Credentials, cookies, signing material, and raw sensitive responses should not be committed, logged, or included in documentation.


7. Remaining Unknowns
The investigation did not conclusively establish:
- How long a login session remains valid or how re-authentication should be handled.
- Exact error response formats for invalid meter identifiers, empty search results, invalid page values, and server failures.
- Rate limits, concurrency limits, or production availability expectations.
- The timezone, sampling interval, and retention policy for energy timestamps.
- Whether coordinates and transformer references are populated for every record.
- The supported purpose and complete security contract of export/signing-related endpoints.
- Whether /health checks only the local process or also upstream reachability in every running configuration.
These items should be verified through authorized testing or clarified with the portal owner before the integration is treated as production-ready.


8. End-to-End Reasoning Summary
The solution followed an evidence-led sequence:
1. Explore: use the portal's normal workflows to discover which information users can access.
2. Observe: inspect Network requests to identify methods, paths, parameters, headers, authentication behavior, and JSON responses.
3. Organize: group findings by authentication and business resource; record response fields and pagination; label uncertain behavior explicitly.
4. Choose: select a small set of useful, read-only operations and define a cleaner versioned API for them.
5. Implement: reproduce the portal session in a shared httpx client, then expose the operations through FastAPI routers.
6. Validate: test real calls through Swagger, run automated tests, and keep openapi.json and the README consistent with the code.
7. Document: preserve what was verified, why design choices were made, and what still needs investigation.
The main engineering outcome was not only an API wrapper. It was a repeatable method for turning an undocumented web application's observed behavior into a small, testable, documented integration—without claiming knowledge that the investigation did not establish.