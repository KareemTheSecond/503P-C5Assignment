# 503P-C5Assignment

## 1. Environment setup

From the **project root** (folder that has `servers/`, `tests/`, `agent/`):

### 1.1 Create and activate venv

```bash
python -m venv .venv
```

**Activate the virtual environment:**

- **Windows (PowerShell):**

```bash
.\.venv\Scripts\Activate.ps1
```

- **macOS / Linux (bash/zsh):**

```bash
source .venv/bin/activate
```

(You should see `(.venv)` in the prompt.)

### 1.2 Install requirements

With the venv active:

```bash
pip install -r requirements.txt
```

## 2. OpenAI API key (`.env`)

In the project root, create a file named `.env`:

```text
OPENAI_API_KEY=YOUR_KEY_HERE
```

Replace `YOUR_KEY_HERE` with your actual key.

The agent will automatically load this via `python-dotenv` and `openai`.

## 3. Running the MCP server tests

Make sure the venv is active (`(.venv)`).

### 3.1 Test the maps server

```bash
python tests/test_maps_geo_server.py
```

This starts `servers/maps_geo_server.py` and calls:

- `geocodeAddress`
- `reverseGeocode`
- `searchPois`
- `basicRoute`

Results are printed as pretty JSON.

### 3.2 Test the tile catalog server

```bash
python tests/test_tile_catalog_server.py
```

This starts `servers/tile_catalog_server.py` and calls:

- `listTileProviders`
- `latLonToTile`
- `getOsmTileUrl`
- `getProviderTileUrl`
- `getMapLibreStyle`

## 4. Running the Assistant agent

To interact with the assistant that uses both MCP servers:

```bash
python agent/AssistantAgent.py
```

You get a simple chat loop:

- Type your question (e.g., “Geocode Hamra Street and give me a tile URL”).
- The agent calls MCP tools as needed and replies.
- Type `exit` to stop.

## 5. MCP servers – brief overview

### 5.1 `maps_geo_server.py` (`servers/maps_geo_server.py`)

Provides basic geospatial tools backed by OpenStreetMap APIs:

- `geocodeAddress(query, limit)` – name/address → coordinates.
- `reverseGeocode(lat, lon)` – coordinates → address.
- `searchPois(keyword, lat, lon, radiusM, maxResults)` – nearby POIs (e.g., cafés).
- `basicRoute(startLat, startLon, endLat, endLon, profile)` – distance, duration, simple steps.

### 5.2 `tile_catalog_server.py` (`servers/tile_catalog_server.py`)

Provides tile and map-style utilities:

- `listTileProviders()` – supported tile providers.
- `getOsmTileUrl(z, x, y)` – standard OSM tile URL.
- `getProviderTileUrl(provider, z, x, y, subdomain)` – provider-based tile URL.
- `latLonToTile(lat, lon, zoom)` – lat/lon → XYZ tile indices.
- `getMapLibreStyle(provider, centerLat, centerLon, zoom)` – minimal MapLibre style JSON for a raster basemap.

