import asyncio
import json
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def pretty_print_result(tool_name, result):
    text_parts = []
    if result.content:
        for item in result.content:
            text = getattr(item, "text", None)
            if text is not None:
                text_parts.append(text)

    print("\n" + "=" * 80)
    print("Result from tool:", tool_name)
    print("-" * 80)

    if not text_parts:
        print("[No text content]")
        return

    full_text = "\n".join(text_parts)

    try:
        parsed = json.loads(full_text)
        print(json.dumps(parsed, ensure_ascii=False, indent=2))
    except json.JSONDecodeError:
        print(full_text)


def extract_json(result):
    """
    Helper to parse the first JSON payload from a tool result.
    Returns a Python object or None if parsing fails.
    """
    text_parts = []
    if result.content:
        for item in result.content:
            text = getattr(item, "text", None)
            if text is not None:
                text_parts.append(text)

    if not text_parts:
        return None

    full_text = "\n".join(text_parts)
    try:
        return json.loads(full_text)
    except json.JSONDecodeError:
        return None


async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "servers.tile_catalog_server"],
        env=os.environ,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Available tools:")
            for tool in tools.tools:
                print(" -", tool.name)

            list_result = await session.call_tool("listTileProviders", {})
            pretty_print_result("listTileProviders", list_result)

            # the hamra location we got from the prev unittest. 
            latlon_args = {"lat": 33.895, "lon": 35.478, "zoom": 14}
            latlon_result = await session.call_tool("latLonToTile", latlon_args)
            pretty_print_result("latLonToTile", latlon_result)

            latlon_json = extract_json(latlon_result)
            if latlon_json is not None:
                z = latlon_json.get("z")
                x = latlon_json.get("x")
                y = latlon_json.get("y")
            else:
                # Fallback values if parsing fails
                z, x, y = 14, 9093, 5749


            osm_args = {"z": z, "x": x, "y": y}
            osm_result = await session.call_tool("getOsmTileUrl", osm_args)
            pretty_print_result("getOsmTileUrl", osm_result)

            provider_args = {
                "provider": "OpenStreetMap.Mapnik",
                "z": z,
                "x": x,
                "y": y,
            }
            provider_result = await session.call_tool("getProviderTileUrl", provider_args)
            pretty_print_result("getProviderTileUrl", provider_result)

            style_args = {
                "provider": "OpenStreetMap.Mapnik",
                "centerLat": 33.895,
                "centerLon": 35.478,
                "zoom": 14,
            }
            style_result = await session.call_tool("getMapLibreStyle", style_args)
            pretty_print_result("getMapLibreStyle", style_result)

    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())

