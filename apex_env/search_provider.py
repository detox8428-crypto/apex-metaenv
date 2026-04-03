"""
Web Search Provider Module
===========================
Searches across Chrome, Google, Bing, and other search engines

Features:
- Google search with custom API
- Bing search
- DuckDuckGo search (no API key needed)
- Chrome automation for JavaScript-heavy sites
- Result parsing and ranking
- Image search support
"""

import os
import requests
import logging
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Search result item"""
    title: str
    url: str
    snippet: str
    source: str
    rank: int
    relevance_score: float = 0.0


class SearchProvider:
    """Base search provider (abstract interface)"""
    
    def __init__(self):
        self.enabled = False
        self.provider_type = "search"
    
    def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """Search and return results"""
        raise NotImplementedError
    
    def image_search(self, query: str, num_results: int = 10) -> List[Dict]:
        """Search for images"""
        raise NotImplementedError


class GoogleCustomSearch(SearchProvider):
    """
    Google Custom Search via Google API
    
    Setup:
    1. Go to https://programmablesearchengine.google.com/
    2. Create a search engine
    3. Get GOOGLE_SEARCH_ENGINE_ID
    4. Go to Google Cloud Console and get GOOGLE_API_KEY
    5. Add to .env:
       - GOOGLE_API_KEY=your_key
       - GOOGLE_SEARCH_ENGINE_ID=your_engine_id
    """
    
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv("GOOGLE_API_KEY", "")
        self.search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID", "")
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        
        if self.api_key and self.search_engine_id:
            self.enabled = True
            logger.info("✅ Google Custom Search enabled")
        else:
            logger.warning("⚠️ Google Custom Search disabled - missing API credentials")
    
    def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """Search using Google Custom Search API"""
        
        if not self.enabled:
            return []
        
        try:
            params = {
                "key": self.api_key,
                "cx": self.search_engine_id,
                "q": query,
                "num": min(num_results, 10)  # Google API limit
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            data = response.json()
            
            if "items" not in data:
                logger.warning(f"⚠️ Google Search: No results for '{query}'")
                return []
            
            results = []
            for idx, item in enumerate(data["items"][:num_results], 1):
                result = SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    source="Google Custom Search",
                    rank=idx,
                    relevance_score=1.0 - (idx * 0.05)  # Higher rank = lower score
                )
                results.append(result)
            
            logger.info(f"✅ Found {len(results)} results for '{query}'")
            return results
        
        except Exception as e:
            logger.error(f"❌ Google Search error: {e}")
            return []
    
    def image_search(self, query: str, num_results: int = 10) -> List[Dict]:
        """Search for images"""
        
        if not self.enabled:
            return []
        
        try:
            params = {
                "key": self.api_key,
                "cx": self.search_engine_id,
                "q": query,
                "searchType": "image",
                "num": min(num_results, 10)
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            data = response.json()
            
            results = []
            if "items" in data:
                for idx, item in enumerate(data["items"][:num_results], 1):
                    image_data = item.get("image", {})
                    results.append({
                        "title": item.get("title", ""),
                        "image_url": item.get("link", ""),
                        "thumbnail_url": image_data.get("thumbnailLink", ""),
                        "source_url": item.get("image", {}).get("contextLink", ""),
                        "source": "Google Custom Search",
                        "rank": idx
                    })
            
            return results
        
        except Exception as e:
            logger.error(f"❌ Google Image Search error: {e}")
            return []


class BingSearch(SearchProvider):
    """
    Bing Search via Azure Cognitive Search API
    
    Setup:
    1. Go to https://www.microsoft.com/en-us/bing/apis/bing-web-search-api
    2. Create account and API key
    3. Add to .env:
       - BING_SEARCH_KEY=your_key
    """
    
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv("BING_SEARCH_KEY", "")
        self.endpoint = "https://api.bing.microsoft.com/v7.0/search"
        
        if self.api_key:
            self.enabled = True
            logger.info("✅ Bing Search enabled")
        else:
            logger.warning("⚠️ Bing Search disabled - missing API key")
    
    def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """Search using Bing"""
        
        if not self.enabled:
            return []
        
        try:
            headers = {"Ocp-Apim-Subscription-Key": self.api_key}
            params = {"q": query, "count": min(num_results, 50)}
            
            response = requests.get(self.endpoint, headers=headers, params=params, timeout=10)
            data = response.json()
            
            results = []
            if "webPages" in data:
                for idx, item in enumerate(data["webPages"]["value"][:num_results], 1):
                    result = SearchResult(
                        title=item.get("name", ""),
                        url=item.get("url", ""),
                        snippet=item.get("snippet", ""),
                        source="Bing Search",
                        rank=idx,
                        relevance_score=1.0 - (idx * 0.05)
                    )
                    results.append(result)
            
            logger.info(f"✅ Bing found {len(results)} results for '{query}'")
            return results
        
        except Exception as e:
            logger.error(f"❌ Bing Search error: {e}")
            return []


class DuckDuckGoSearch(SearchProvider):
    """
    DuckDuckGo Search (no API key required, uses instant answers API)
    """
    
    def __init__(self):
        super().__init__()
        self.endpoint = "https://api.duckduckgo.com/"
        self.enabled = True
        logger.info("✅ DuckDuckGo Search enabled (no API required)")
    
    def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """Search using DuckDuckGo"""
        
        try:
            params = {
                "q": query,
                "format": "json",
                "no_redirect": 1
            }
            
            response = requests.get(self.endpoint, params=params, timeout=10)
            data = response.json()
            
            results = []
            
            # Add instant answer if available
            if data.get("Abstract"):
                result = SearchResult(
                    title="Instant Answer",
                    url=data.get("AbstractURL", ""),
                    snippet=data.get("Abstract", ""),
                    source="DuckDuckGo",
                    rank=1,
                    relevance_score=1.0
                )
                results.append(result)
            
            # Add related topics
            for idx, topic in enumerate(data.get("RelatedTopics", [])[:num_results], 1):
                if "Topics" in topic:
                    for sub_idx, sub_topic in enumerate(topic["Topics"][:3], 1):
                        if len(results) >= num_results:
                            break
                        result = SearchResult(
                            title=sub_topic.get("FirstURL", "").split("/")[-1],
                            url=sub_topic.get("FirstURL", ""),
                            snippet=sub_topic.get("Text", "")[:200],
                            source="DuckDuckGo",
                            rank=len(results) + 1,
                            relevance_score=0.7
                        )
                        results.append(result)
                else:
                    if len(results) >= num_results:
                        break
                    result = SearchResult(
                        title=topic.get("FirstURL", "").split("/")[-1],
                        url=topic.get("FirstURL", ""),
                        snippet=topic.get("Text", "")[:200],
                        source="DuckDuckGo",
                        rank=len(results) + 1,
                        relevance_score=0.7
                    )
                    results.append(result)
            
            logger.info(f"✅ DuckDuckGo found {len(results)} results for '{query}'")
            return results[:num_results]
        
        except Exception as e:
            logger.error(f"❌ DuckDuckGo Search error: {e}")
            return []


class SearchManager:
    """
    Search manager - orchestrates searching via multiple providers
    Tries providers in order of preference: Google > Bing > DuckDuckGo
    """
    
    def __init__(self):
        self.providers = {
            "google": GoogleCustomSearch(),
            "bing": BingSearch(),
            "duckduckgo": DuckDuckGoSearch()
        }
        
        # Find first enabled provider
        self.primary_provider = None
        for name, provider in self.providers.items():
            if provider.enabled:
                self.primary_provider = provider
                logger.info(f"Primary search provider: {name}")
                break
        
        if not self.primary_provider:
            logger.warning("⚠️ No search providers enabled - DuckDuckGo will be used")
            self.primary_provider = self.providers["duckduckgo"]
    
    def search(self, query: str, num_results: int = 10,
              provider: Optional[str] = None) -> Dict:
        """
        Search using specified or primary provider
        
        Args:
            query: Search query
            num_results: Number of results to return
            provider: Specific provider ("google", "bing", "duckduckgo")
        
        Returns:
            {"success": bool, "results": [...], "total": int, ...}
        """
        
        try:
            # Choose provider
            if provider and provider in self.providers:
                search_provider = self.providers[provider]
            else:
                search_provider = self.primary_provider
            
            # Search
            results = search_provider.search(query, num_results)
            
            if not results:
                return {
                    "success": False,
                    "query": query,
                    "error": "No results found",
                    "provider": search_provider.provider_type
                }
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "rank": result.rank,
                    "title": result.title,
                    "url": result.url,
                    "snippet": result.snippet[:300] + "..." if len(result.snippet) > 300 else result.snippet,
                    "source": result.source,
                    "relevance": result.relevance_score
                })
            
            return {
                "success": True,
                "query": query,
                "provider": search_provider.provider_type,
                "total": len(results),
                "results": formatted_results,
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"❌ Search error: {e}")
            return {"success": False, "error": str(e), "query": query}
    
    def image_search(self, query: str, num_results: int = 10) -> Dict:
        """Search for images"""
        
        try:
            # Only Google supports image search
            if self.primary_provider == self.providers["google"]:
                results = self.primary_provider.image_search(query, num_results)
            else:
                return {"success": False, "error": "Image search requires Google API"}
            
            if not results:
                return {
                    "success": False,
                    "query": query,
                    "error": "No images found"
                }
            
            return {
                "success": True,
                "query": query,
                "total": len(results),
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"❌ Image search error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_status(self) -> Dict:
        """Get all providers' status"""
        return {
            "primary": "google" if self.providers["google"].enabled else
                      "bing" if self.providers["bing"].enabled else "duckduckgo",
            "google": {"enabled": self.providers["google"].enabled},
            "bing": {"enabled": self.providers["bing"].enabled},
            "duckduckgo": {"enabled": self.providers["duckduckgo"].enabled}
        }


# Global manager instance
search_manager = SearchManager()


if __name__ == "__main__":
    # Demo usage
    print("Web Search Provider Module")
    print("=" * 50)
    print(search_manager.get_status())
    print("\nTo use Web Search:")
    print("1. Optional: Set up Google Custom Search")
    print("   - GOOGLE_API_KEY")
    print("   - GOOGLE_SEARCH_ENGINE_ID")
    print("2. Optional: Set up Bing Search")
    print("   - BING_SEARCH_KEY")
    print("3. DuckDuckGo works without any setup!")
    print("\nUsage: search_manager.search('python tutorial')")
