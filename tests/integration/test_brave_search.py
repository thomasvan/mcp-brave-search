import os
import pytest
import asyncio
import logging
import sys

# Skip all tests if BRAVE_API_KEY_INTEGRATION isn't set
pytestmark = pytest.mark.skipif(
    "BRAVE_API_KEY_INTEGRATION" not in os.environ,
    reason="Integration tests require BRAVE_API_KEY_INTEGRATION environment variable"
)

# Set BRAVE_API_KEY from BRAVE_API_KEY_INTEGRATION before importing the server module
os.environ["BRAVE_API_KEY"] = os.environ.get("BRAVE_API_KEY_INTEGRATION", "")

# Now we can safely import the server
from src.mcp_brave_search.server import BraveSearchServer

# Set up logging for integration tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('integration-tests')

@pytest.fixture
def server():
    """Create a server instance with real API key."""
    api_key = os.environ.get("BRAVE_API_KEY_INTEGRATION")
    logger.info(f"Setting up integration test with API key length: {len(api_key)}")
    server = BraveSearchServer(api_key)
    return server

@pytest.mark.asyncio
async def test_real_web_search(server):
    """Test actual API call to Brave Search."""
    query = "Python programming language"
    logger.info(f"Testing web search with query: {query}")
    
    results = await server._get_web_results(query, 5)
    
    # Verify we got results
    assert len(results) > 0
    assert "Python" in str(results)
    
    # Log some result info for debugging
    logger.info(f"Received {len(results)} results from real API")
    if results:
        logger.info(f"First result title: {results[0].get('title', 'No title')}")

@pytest.mark.asyncio
async def test_real_local_search(server):
    """Test actual API call to Brave Search for local results."""
    query = "coffee shops in San Francisco"
    logger.info(f"Testing local search with query: {query}")
    
    # Extract locations IDs first
    response = await server.get_client().get(
        f"{server.base_url}/web/search",
        params={
            "q": query,
            "search_lang": "en",
            "result_filter": "locations",
            "count": 5
        }
    )
    data = response.json()
    location_ids = server._extract_location_ids(data)
    
    # Skip test if no location IDs found
    if not location_ids:
        pytest.skip("No location results found, skipping test")
        
    # Verify we have location IDs
    assert len(location_ids) > 0
    logger.info(f"Found {len(location_ids)} location IDs")
    
    # Test getting location details
    if location_ids:
        poi_details, desc_details = await server._get_location_details(location_ids[:2])
        assert poi_details or desc_details
        logger.info(f"Retrieved details for locations")

@pytest.mark.asyncio
async def test_rate_limit_handling(server):
    """Test that rate limiting works properly."""
    # Make multiple rapid requests to potentially trigger rate limiting
    # Note: This test may not actually trigger rate limiting if your account has high limits
    for i in range(3):
        query = f"test query {i}"
        logger.info(f"Making request {i+1}/3: {query}")
        results = await server._get_web_results(query, 2)
        # Small pause to avoid being too aggressive
        await asyncio.sleep(0.2)
        
    # Final request should still work if we haven't hit limits
    results = await server._get_web_results("final test query", 2)
    assert len(results) > 0
