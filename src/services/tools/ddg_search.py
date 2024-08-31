from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchResults


@tool
async def ddg_search(query: str) -> str:
    """Searches DuckDuckGo for a query and returns the results."""
    search = DuckDuckGoSearchResults()
    return search.invoke(query)
