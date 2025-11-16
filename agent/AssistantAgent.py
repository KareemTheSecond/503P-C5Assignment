import asyncio
import os
from dotenv import load_dotenv
from agents import Agent, Runner, trace, set_default_openai_key
from agents.mcp import MCPServerStdio

load_dotenv(override=True)
set_default_openai_key(os.getenv("OPENAI_API_KEY"))


async def main():
    mapsGeoParams = {"command": "python", "args": ["-m", "servers.maps_geo_server"]}
    tileCatalogParams = {"command": "python", "args": ["-m", "servers.tile_catalog_server"]}

    async with MCPServerStdio(name="maps_geo", params=mapsGeoParams, client_session_timeout_seconds=60) as mapsGeoServer:
        mapsGeoTools = await mapsGeoServer.list_tools()
        print("maps_geo tools:", [t.name for t in mapsGeoTools])

        async with MCPServerStdio(name="tile_catalog", params=tileCatalogParams, client_session_timeout_seconds=60) as tileCatalogServer:
            tileTools = await tileCatalogServer.list_tools()
            print("tile_catalog tools:", [t.name for t in tileTools])

            instructions = (
                "You are a helpful map assistant. Use tools from 'maps_geo' for geocoding, reverse geocoding, "
                "POI search, and routing. Use tools from 'tile_catalog' for tile URLs and MapLibre styles. "
                "When the user asks for a map, map view, tile, or zoom level, "
                "you MUST call a tile_catalog tool (for example getOsmTileForLocation, "
                "getOsmTileUrl, getProviderTileUrl, or getMapLibreStyle) and include "
                "the resulting URL or JSON in your answer. Do not invent tools."
            )

            agent = Agent(
                name="MapAssistant",
                instructions=instructions,
                model="gpt-4",
                mcp_servers=[mapsGeoServer, tileCatalogServer],
            )

            history = []

            while True:
                userInput = input("Ask a map question (or 'exit'): ").strip()
                if not userInput or userInput.lower() == "exit":
                    print("Exiting.")
                    break

                runInput = history + [{"role": "user", "content": userInput}]

                with trace("map-assistant-run"):
                    result = await Runner.run(agent, input=runInput)

                print("\n=== Agent answer ===")
                print(result.final_output)
                print()

                history = result.to_input_list()


if __name__ == "__main__":
    asyncio.run(main())
