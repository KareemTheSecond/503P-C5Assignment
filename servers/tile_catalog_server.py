import json
import math

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("tile_catalog")

TILE_PROVIDERS = {
    "OpenStreetMap.Mapnik": {
        "urlTemplate": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        "subdomains": ["a", "b", "c"],
        "attribution": "© OpenStreetMap contributors",
        "description": "Standard OSM raster tiles (Mapnik style).",
    }
}


def get_provider_info(provider):
    """Return provider entry from TILE_PROVIDERS or raise ValueError."""
    if provider not in TILE_PROVIDERS:
        raise ValueError("Unknown tile provider: %s" % provider)
    return TILE_PROVIDERS[provider]


def build_tile_url_from_template(template, z, x, y, subdomain=None):
    """Fill {z}, {x}, {y}, {s} placeholders in a tile URL template."""
    url = (
        template.replace("{z}", str(z))
        .replace("{x}", str(x))
        .replace("{y}", str(y))
    )
    if "{s}" in url:
        if subdomain is None:
            subdomain = "a"
        url = url.replace("{s}", subdomain)
    return url


def lat_lon_to_tile_indices(lat_deg, lon_deg, zoom):
    """
    Convert latitude/longitude in degrees to Web Mercator XYZ tile indices.

    This uses the standard slippy-map formula.
    """
    lat_rad = math.radians(lat_deg)
    n = 2 ** zoom
    x_tile = n * ((lon_deg + 180.0) / 360.0)
    y_tile = n * (1.0 - (math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi)) / 2.0
    return int(x_tile), int(y_tile)


@mcp.tool()
async def listTileProviders():
    """
    List the available tile provider (only OpenStreetMap.Mapnik i guess for now).

    Returns:
        A JSON string with provider name, urlTemplate, description, attribution, subdomains.
    """
    providers_summary = []
    for name, info in TILE_PROVIDERS.items():
        providers_summary.append(
            {
                "name": name,
                "urlTemplate": info.get("urlTemplate"),
                "description": info.get("description"),
                "attribution": info.get("attribution"),
                "subdomains": info.get("subdomains"),
            }
        )

    payload = {"providers": providers_summary}
    return json.dumps(payload, ensure_ascii=False, indent=2)


@mcp.tool()
async def getOsmTileUrl(z, x, y):
    """
    Build a standard OpenStreetMap tile URL.

    Args:
        z: Zoom level.
        x: Tile X index.
        y: Tile Y index.

    Returns:
        A plain string with the full tile URL.
    """
    url = "https://tile.openstreetmap.org/%s/%s/%s.png" % (z, x, y)
    return url


@mcp.tool()
async def getProviderTileUrl(provider, z, x, y, subdomain=None):
    """
    Build a tile URL for the given provider.

    NOTE: In this server we only support "OpenStreetMap.Mapnik".

    Args:
        provider: Name of the provider (e.g., "OpenStreetMap.Mapnik").
        z: Zoom level.
        x: Tile X index.
        y: Tile Y index.
        subdomain: Optional subdomain for {s}, default is "a".

    Returns:
        A JSON string with provider name, generated URL, zoom and tile indices, attribution.
    """
    info = get_provider_info(provider)
    template = info["urlTemplate"]
    url = build_tile_url_from_template(template, z=z, x=x, y=y, subdomain=subdomain)

    payload = {
        "provider": provider,
        "z": z,
        "x": x,
        "y": y,
        "url": url,
        "attribution": info.get("attribution"),
        "description": info.get("description"),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


@mcp.tool()
async def latLonToTile(lat, lon, zoom):
    """
    Convert latitude/longitude to tile indices.

    Args:
        lat: Latitude in degrees.
        lon: Longitude in degrees.
        zoom: Zoom level.

    Returns:
        A JSON string with z (zoom), x, and y tile indices.
    """
    x, y = lat_lon_to_tile_indices(lat_deg=lat, lon_deg=lon, zoom=zoom)
    payload = {
        "z": zoom,
        "x": x,
        "y": y,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


@mcp.tool()
async def getMapLibreStyle(provider, centerLat, centerLon, zoom=12):
    """
    Create a minimal MapLibre style JSON using the given tile provider.

    In this server, provider should be "OpenStreetMap.Mapnik".

    Args:
        provider: Name of the provider.
        centerLat: Latitude of initial map center.
        centerLon: Longitude of initial map center.
        zoom: Initial zoom level.

    Returns:
        A JSON string representing a MapLibre style object.
    """
    info = get_provider_info(provider)
    template = info["urlTemplate"]

    # Keep {z}, {x}, {y} placeholders so MapLibre can request all tiles.
    tile_url = build_tile_url_from_template(
        template, z="{z}", x="{x}", y="{y}", subdomain="a"
    )

    style = {
        "version": 8,
        "name": "%s basemap" % provider,
        "sources": {
            "basemap": {
                "type": "raster",
                "tiles": [tile_url],
                "tileSize": 256,
                "attribution": info.get("attribution"),
            }
        },
        "layers": [
            {
                "id": "basemap",
                "type": "raster",
                "source": "basemap",
            }
        ],
        "center": [centerLon, centerLat],
        "zoom": zoom,
    }

    return json.dumps(style, ensure_ascii=False, indent=2)


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
