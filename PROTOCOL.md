# PROTOCOL.md — Portal Investigation

## 1. Portal Overview

I explored the Urja Meter Ops portal to understand how meter and transformer information is organized and retrieved.

The Meters page shows 403 meters with details such as meter ID, serial number, manufacturer, phase type, installation status, and transformer code. The Transformers page provides transformer names, feeder codes, and capacity.

## 2. Data Access

I used Chrome DevTools and the Network tab with the Fetch/XHR filter to inspect the requests made by the portal.

The request `search?q=&page=1` returned JSON data containing meter records and pagination fields (`page`, `pageSize`, and `total`). The observed page size was 20, with 403 total records.

Opening a meter shows its nameplate details, geographical coordinates, distribution network hierarchy, and consumption history. A request named `energy` returned consumption-related records containing fields such as `timestamp`, `kwh`, `kvah`, and `voltR`.

## 3. Access and Authentication

I accessed the portal through its login interface. The request-level authentication mechanism has not yet been verified. I still need to inspect the request headers to understand how access is handled.

## 4. Observations and Open Questions

The portal uses browser requests to retrieve structured JSON data. The meter listing is paginated, and consumption data is available through a separate observed request.

I have not yet confirmed the full request URLs, HTTP methods, authentication details, or the exact purpose of every request. These will be checked before implementation.

## 5. Next Steps

I will inspect the relevant request headers and responses, verify how meter IDs relate to consumption data, and use the findings to plan the integration for the assignment API.
### Energy Data Request

I selected the `energy` request in Chrome DevTools and inspected its Headers tab.

- **Request URL:** `/portal/meters/J100000/energy`
- **HTTP method:** GET
- **Status code:** 200 OK
- **Response type:** JSON
- **Meter ID:** Included in the URL path (`J100000`)

The response contains consumption records with fields such as `timestamp`, `kwh`, `kvah`, and `voltR`.

The request includes a session cookie. I have not yet confirmed the complete authentication mechanism or whether the same session is required for every request.

**Next:** I will check the `geo` request and compare the energy request for another meter to understand how location data is retrieved and whether the endpoint changes with the meter ID.

### Geographic Data Request

I inspected the `geo` request in Chrome DevTools.

- **Endpoint:** `/portal/meters/J100000/geo`
- **HTTP method:** GET
- **Status code:** 200 OK
- **Response type:** JSON

The request is associated with the selected meter ID. The meter details page displays latitude and longitude coordinates.

I will inspect the response body to confirm the exact fields returned by this endpoint.

### Geographic Data Response

The `geo` endpoint returns the selected meter's geographical coordinates in JSON format.

- **Response fields:** `data.latitude`, `data.longitude`
- **Data type:** Both values are strings.
- **Status:** 200 OK

I compared the response with the meter details page and confirmed that the coordinates match the displayed location.

This endpoint can be used to retrieve location information for a meter.

### Meter Listing and Pagination

I inspected the meter search request using Chrome DevTools.

- **Endpoint:** `/portal/meters/search?q=&page=1`
- **Method:** GET
- **Status:** 200 OK
- **Response format:** JSON

The response contains a `data` array of meter records and pagination fields: `page`, `pageSize`, and `total`. The observed response shows 20 records per page and 403 meters in total.

Meter records include fields such as `meterId`, `serialNo`, `make`, `phaseType`, `dtCode`, and `installStatus`.

The search query is empty in the observed request. I will test the search and pagination controls to understand how the results change.

### 4. Meter Search API

I tested the meter search feature using the browser's Network tab in DevTools.

- **Endpoint:** `GET /portal/meters/search`
- **Search parameters:** `q` is used to search for a meter, and `page` specifies the page number.
- **Response format:** JSON.
- **Available data:** Meter ID, serial number, manufacturer, phase type, and installation status.
- **Pagination:** The response includes `page`, `pageSize`, and `total`. The general search returned 403 meters, with 20 records per page.
- **Testing:** I searched for meter `J100004`. The API returned one matching record with serial number `SE65293`, manufacturer `Genus`, phase type `single`, and status `Faulty`.

**Observation:** The search results displayed in the portal match the data returned by the API. This confirms that the search feature uses a backend endpoint rather than filtering only the currently visible table rows.

### 5. Distribution Transformers API

I opened the Transformers section and checked the Network tab in browser DevTools to identify the API used to load the data.

- **Endpoint:** `GET /portal/dts?page=1`
- **Response format:** JSON.
- **Available data:** Transformer code, name, feeder code, and capacity in KVA.
- **Pagination:** The response contains `page`, `pageSize`, and `total`.
- **Observed result:** The API returned 40 transformers, with 20 records per page.
- **Testing:** I compared the API response with the transformer table displayed on the portal. The transformer codes, names, feeder codes, and capacities matched.

**Observation:** The Transformers page loads its data through a separate API endpoint from the Meter search page. The response provides structured JSON data that can be used to understand the records displayed in the table.