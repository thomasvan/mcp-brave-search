import asyncio
import logging
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from rich.console import Console
from rich.logging import RichHandler
from typing import Optional, Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler()]
)

class BraveSearchClient:
    def __init__(
        self,
        server_path: str,
        api_key: str,
        console: Optional[Console] = None
    ):
        self.server_params = StdioServerParameters(
            command="python",
            args=[server_path],
            env={"BRAVE_API_KEY": api_key}
        )
        self.console = console or Console()
        self.logger = logging.getLogger("brave-search-client")

    def _is_complex_query(self, query: str) -> bool:
        """Determine if a query is complex based on its characteristics"""
        indicators = [
            " and ", " or ", " why ", " how ", " what ", " explain ",
            "compare", "difference", "analysis", "describe"
        ]
        return any(indicator in query.lower() for indicator in indicators) or len(query.split()) > 5

    async def _execute_search(
        self,
        session: ClientSession,
        tool: str,
        params: Dict[str, Any]
    ) -> str:
        try:
            # Adjust count based on query complexity
            if "query" in params:
                is_complex = self._is_complex_query(params["query"])
                params["count"] = 20 if is_complex else 10

            result = await session.call_tool(tool, params)
            if result.is_error:
                raise Exception(result.content[0].text)
            return result.content[0].text
        except Exception as e:
            self.logger.error(f"Search failed: {str(e)}")
            return f"Error: {str(e)}"

    async def run_interactive(self):
        """Run interactive search client"""
        try:
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    
                    self.console.print(
                        "Available tools:",
                        ", ".join(tool.name for tool in tools)
                    )

                    while True:
                        query = self.console.input("\nSearch query (or 'quit'): ")
                        if query.lower() == "quit":
                            break

                        # Default to web search as it's used for answer formulation
                        search_type = "web"
                        
                        is_complex = self._is_complex_query(query)
                        count = 20 if is_complex else 10
                        
                        tool = "brave_web_search"
                        
                        with self.console.status(f"Searching with {'complex' if is_complex else 'standard'} query..."):
                            result = await self._execute_search(
                                session,
                                tool,
                                {"query": query, "count": count}
                            )
                        
                        self.console.print("\nResults:", style="bold green")
                        self.console.print(result)

        except Exception as e:
            self.logger.error(f"Client error: {str(e)}")
            raise

if __name__ == "__main__":
    import os
    import sys

    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server.py>")
        sys.exit(1)

    api_key = os.getenv("BRAVE_API_KEY")
    if not api_key:
        print("Error: BRAVE_API_KEY environment variable required")
        sys.exit(1)

    client = BraveSearchClient(sys.argv[1], api_key)
    asyncio.run(client.run_interactive())