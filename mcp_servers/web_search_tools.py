"""MCP Server for Web Search: Tavily AI Integration.

This is a 🟢 Green Tool (Read-Only, Safe, High-Value).
Provides up-to-date information beyond LLM knowledge cutoff.
"""

from typing import Dict, Any, Optional
import os
import requests


# Removed duplicate function definition - see below


def web_search(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    Search the web for current information.
    
    Use this tool to find information about:
    - Current events and news
    - Latest software versions and releases
    - Recent documentation updates
    - Facts beyond knowledge cutoff (March 2024)
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return (default: 5)
    
    Returns:
        Dict with status, answer, sources, and content
    """
    # Privacy Filter: Block searches for secrets
    blocked_keywords = [
        "password", "secret", "api key", "access key", "private key",
        "token", "credential", "auth", "login", "ssh key"
    ]
    
    query_lower = query.lower()
    for keyword in blocked_keywords:
        if keyword in query_lower:
            return {
                "status": "error",
                "message": "Search query blocked for security reasons",
                "reason": f"Query contains blocked keyword: {keyword}"
            }
    
    # Check for Tavily API key
    tavily_key = os.getenv("TAVILY_API_KEY")
    if tavily_key:
        return _search_tavily(query, tavily_key, max_results)
    
    # Fallback to Serper.dev
    serper_key = os.getenv("SERPER_API_KEY")
    if serper_key:
        return _search_serper(query, serper_key, max_results)
    
    # No API keys configured
    return {
        "status": "error",
        "message": "Web search not configured. Please set TAVILY_API_KEY or SERPER_API_KEY environment variable.",
        "hint": "Get API key from https://tavily.com or https://serper.dev"
    }


def _search_tavily(query: str, api_key: str, max_results: int) -> Dict[str, Any]:
    """Search using Tavily AI (preferred - built for agents)."""
    try:
        url = "https://api.tavily.com/search"
        headers = {
            "Content-Type": "application/json"
        }
        payload = {
            "api_key": api_key,
            "query": query,
            "search_depth": "advanced",
            "max_results": max_results,
            "include_answer": True,
            "include_raw_content": False
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract answer and sources
        answer = data.get("answer", "")
        results = data.get("results", [])
        
        sources = [r.get("url", "") for r in results]
        content_snippets = [r.get("content", "") for r in results]
        
        return {
            "status": "success",
            "answer": answer,
            "sources": sources,
            "content": "\n\n---\n\n".join(content_snippets),
            "provider": "tavily"
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": f"Tavily API error: {str(e)}",
            "provider": "tavily"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
            "provider": "tavily"
        }


def _search_serper(query: str, api_key: str, max_results: int) -> Dict[str, Any]:
    """Search using Serper.dev (fallback)."""
    try:
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "q": query,
            "num": max_results
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract organic results
        organic = data.get("organic", [])
        sources = [r.get("link", "") for r in organic]
        snippets = [r.get("snippet", "") for r in organic]
        
        # Try to get answer box
        answer_box = data.get("answerBox", {})
        answer = answer_box.get("answer", "") or answer_box.get("snippet", "")
        
        return {
            "status": "success",
            "answer": answer or "See sources below",
            "sources": sources,
            "content": "\n\n---\n\n".join(snippets),
            "provider": "serper"
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": f"Serper API error: {str(e)}",
            "provider": "serper"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
            "provider": "serper"
        }


# Tool registry
WEB_SEARCH_TOOLS = {
    "web_search": web_search,
}


def init_web_search_client():
    """Initialize web search client."""
    tavily_key = os.getenv("TAVILY_API_KEY")
    serper_key = os.getenv("SERPER_API_KEY")
    
    if tavily_key:
        return {"provider": "tavily", "configured": True}
    elif serper_key:
        return {"provider": "serper", "configured": True}
    else:
        return {"provider": None, "configured": False}

