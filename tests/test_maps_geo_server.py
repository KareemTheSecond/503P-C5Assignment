import asyncio
import os
import json

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def pretty_print_tool_result(tool_name, result):

    print("\n" + "=" * 80)
    print(f"Result from tool: {tool_name}")
    print("-" * 80)

    if not result.content:
        print("[No content returned]")
        return

    text_parts = []
    for item in result.content:

        text = getattr(item, "text", None)
        if text is not None:
            text_parts.append(text)

    if not text_parts:
        print("[No text content in result]")
        return

    full_text = "\n".join(text_parts)


    try:
        parsed = json.loads(full_text)
        print(json.dumps(parsed, ensure_ascii=False, indent=2))
    except json.JSONDecodeError:
        print(full_text)


async def main():


    server_params = StdioServerParameters(
        command="python",
        args=["-m", "servers.maps_geo_server"],
        env=os.environ,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            print("Initializing MCP session...")
            await session.initialize()

            print("\nListing available tools from maps_geo_server:")
            tools_response = await session.list_tools()
            for tool in tools_response.tools:
                print(f" - {tool.name}: {tool.description}")

            geocode_args = {
                "query": "Hamra Street, Beirut",
                "limit": 2,
            }
            print("\nCalling geocodeAddress with:", geocode_args)
            geocode_result = await session.call_tool("geocodeAddress", geocode_args)
            pretty_print_tool_result("geocodeAddress", geocode_result)

            reverse_args = {
                "lat": 33.895,
                "lon": 35.478,
            }
            print("\nCalling reverseGeocode with:", reverse_args)
            reverse_result = await session.call_tool("reverseGeocode", reverse_args)
            pretty_print_tool_result("reverseGeocode", reverse_result)

            search_pois_args = {
                "keyword": "cafe",
                "lat": 33.895,
                "lon": 35.478,
                "radiusM": 800,
                "maxResults": 5,
            }
            print("\nCalling searchPois with:", search_pois_args)
            pois_result = await session.call_tool("searchPois", search_pois_args)
            pretty_print_tool_result("searchPois", pois_result)

            route_args = {
                "startLat": 33.895,
                "startLon": 35.478,
                "endLat": 33.820,
                "endLon": 35.490,
                "profile": "driving",
            }
            print("\nCalling basicRoute with:", route_args)
            route_result = await session.call_tool("basicRoute", route_args)
            pretty_print_tool_result("basicRoute", route_result)

    print("\nAll tests completed.")


if __name__ == "__main__":
    asyncio.run(main())
