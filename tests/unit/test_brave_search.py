import os
import sys
import pytest
import asyncio
from unittest.mock import patch, MagicMock

# Add the parent directory to the Python path for importing
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set environment variable for testing
os.environ['BRAVE_API_KEY'] = 'test_api_key_for_testing'

# Import after setting the environment variable
from src.mcp_brave_search.server import BraveSearchServer, RateLimitError


class MockResponse:
    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code
    
    def json(self):
        return self.json_data
    
    def raise_for_status(self):
        if self.status_code != 200:
            raise Exception(f"HTTP Error: {self.status_code}")


@pytest.fixture
def server():
    """Create a server instance with a mock API key."""
    # Use the environment variable already set at module import
    server = BraveSearchServer(os.environ['BRAVE_API_KEY'])
    return server


@pytest.mark.asyncio
async def test_web_search_success(server):
    """Test that web search returns properly formatted results."""
    # Mock response data
    mock_data = {
        "web": {
            "results": [
                {
                    "title": "Test Result 1",
                    "description": "Description 1",
                    "url": "https://example.com/1"
                },
                {
                    "title": "Test Result 2",
                    "description": "Description 2",
                    "url": "https://example.com/2",
                    "extra_snippets": ["Extra info 1", "Extra info 2"]
                }
            ]
        }
    }
    
    # Mock httpx.AsyncClient.get
    with patch('httpx.AsyncClient.get', return_value=MockResponse(mock_data)):
        # Call the brave_web_search tool directly
        results = await server._get_web_results("test query", 2)
        
        # Verify results
        assert len(results) == 2
        assert results[0]['title'] == "Test Result 1"
        assert results[1]['title'] == "Test Result 2"


@pytest.mark.asyncio
async def test_web_search_error_handling(server):
    """Test that web search handles errors gracefully."""
    # Mock an HTTP error
    with patch('httpx.AsyncClient.get', side_effect=Exception("Connection error")):
        # Call the method directly
        results = await server._get_web_results("test query", 2)
        
        # Verify error handling (should return empty list)
        assert results == []


@pytest.mark.asyncio
async def test_rate_limit_handling(server):
    """Test that rate limit errors are handled properly."""
    # Mock a rate limit error with the correct RateLimitError class
    with patch.object(server.rate_limit, 'check', side_effect=RateLimitError("Rate limit exceeded")):
        # Call the method directly
        results = await server._get_web_results("test query", 2)
        
        # Verify proper error handling response
        assert len(results) == 1
        assert "Rate Limit" in results[0]['title']


def test_format_results(server):
    """Test formatting of search results."""
    mock_data = {
        "web": {
            "results": [
                {
                    "title": "Test Result",
                    "description": "Test Description",
                    "url": "https://example.com",
                    "meta_url": "example.com",
                    "age": "2d",
                    "language": "en"
                }
            ]
        }
    }
    
    formatted = server._format_web_results(mock_data, 1)
    
    # Check formatting includes all expected fields
    assert "Title: Test Result" in formatted
    assert "Description: Test Description" in formatted
    assert "URL: https://example.com" in formatted
    assert "Source: example.com" in formatted
    assert "Age: 2d" in formatted
    assert "Language: en" in formatted
