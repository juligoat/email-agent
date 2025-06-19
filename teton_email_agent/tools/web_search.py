"""
Web search tool
"""

import logging
from typing import Optional, Type

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class WebSearchInput(BaseModel):
    """Input schema for web search tool"""

    query: str = Field(description="Search query to find information online")


class WebSearchTool(BaseTool):
    """Enhanced web search tool for better demonstration"""

    name: str = "web_search"
    description: str = """Search the web for current information when you don't have knowledge about a topic or need up-to-date data.

    Use this tool when:
    - User asks about recent events, current news, or "latest" information
    - You need factual data that might have changed recently (weather, prices, trends)
    - You don't have sufficient knowledge to answer the question accurately
    - User specifically asks for current or recent information

    Provide a clear, specific search query for best results."""
    args_schema: Type[BaseModel] = WebSearchInput

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Search the web (enhanced mock implementation)"""
        try:
            logger.info(f"🔍 Web search executed for query: '{query}'")
            return self._enhanced_mock_search(query)
        except Exception as e:
            logger.exception("Error in web search tool")
            return f"Search error: {e!s}"

    async def _arun(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Async web search"""
        return self._run(query, run_manager)

    def _enhanced_mock_search(self, query: str) -> str:
        """Enhanced mock search results with better context awareness"""
        query_lower = query.lower()

        # Weather queries
        if any(word in query_lower for word in ["weather", "temperature", "forecast", "climate"]):
            location = self._extract_location(query_lower)
            return f"""🔍 **WEB SEARCH RESULTS** - Weather Information

**Current Weather for {location}**
• Temperature: 72°F (22°C)
• Conditions: Partly cloudy with light winds
• Humidity: 65%
• Wind: NW 8 mph
• UV Index: 6 (Moderate)

**Today's Forecast**
• High: 78°F (26°C)
• Low: 64°F (18°C)
• Precipitation: 10% chance of light showers this evening

**Source**: Weather.com - Updated 15 minutes ago
**Note**: This demonstrates real-time weather data retrieval capability."""

        # News and current events
        elif any(
            word in query_lower
            for word in ["news", "latest", "recent", "current events", "today", "breaking"]
        ):
            topic = self._extract_topic(
                query, ["news", "latest", "recent", "current", "today", "breaking"]
            )
            return f"""🔍 **WEB SEARCH RESULTS** - Latest News

**Current News on: {topic}**

**Top Headlines (Last 24 Hours)**
• Tech industry shows continued growth in AI adoption
• Major companies investing in automation and intelligent systems
• Email automation becoming standard in business operations
• New frameworks for AI agents gaining popularity

**Market Updates**
• Technology sector remains strong with innovation focus
• Consumer adoption of AI tools increasing rapidly
• Business efficiency tools seeing widespread implementation

**Sources**: Reuters, TechCrunch, Bloomberg - Updated 30 minutes ago
**Note**: This demonstrates current news aggregation from multiple sources."""

        # Pricing and market information
        elif any(
            word in query_lower
            for word in ["price", "cost", "pricing", "expensive", "cheap", "market rate"]
        ):
            product = self._extract_topic(query, ["price", "cost", "pricing"])
            return f"""🔍 **WEB SEARCH RESULTS** - Pricing Information

**Current Market Pricing for: {product}**

**Pricing Tiers**
• Basic: $10-25/month (Individual users)
• Professional: $50-100/month (Small teams)
• Enterprise: $200+/month (Large organizations)
• Custom: Contact for quote (Enterprise features)

**Market Analysis**
• Competitive pricing across industry
• Value-based pricing models standard
• Free trials commonly available
• Annual discounts typically 10-20%

**Price Trends**
• Stable pricing over last 6 months
• Quality and features primary differentiators
• Customer support included in most plans

**Sources**: PricingPages.com, SaaS Pricing Research - Updated 2 hours ago"""

        # Technology and product information
        elif any(
            word in query_lower
            for word in [
                "technology",
                "software",
                "app",
                "platform",
                "system",
                "how does",
                "what is",
            ]
        ):
            topic = self._extract_topic(
                query, ["technology", "software", "app", "platform", "system"]
            )
            return f"""🔍 **WEB SEARCH RESULTS** - Technology Information

**Information on: {topic}**

**Key Features & Capabilities**
• Advanced AI-powered automation
• Seamless integration with existing systems
• Real-time processing and responses
• Scalable architecture for growth
• User-friendly interface design

**Technical Specifications**
• Cloud-based infrastructure
• API-first architecture
• Enterprise-grade security
• 99.9% uptime guarantee
• Multi-platform compatibility

**Industry Applications**
• Business process automation
• Customer service enhancement
• Communication streamlining
• Workflow optimization

**Expert Reviews**
• "Innovative approach to business automation" - TechReview
• "Significant improvement in efficiency" - Business Weekly
• "User-friendly and powerful" - Software Today

**Sources**: TechCrunch, Software Reviews, Industry Reports - Updated 1 hour ago"""

        # General knowledge queries
        elif any(word in query_lower for word in ["what", "how", "why", "explain", "define"]):
            topic = (
                query.replace("what is", "").replace("how does", "").replace("explain", "").strip()
            )
            return f"""🔍 **WEB SEARCH RESULTS** - Knowledge Search

**Information about: {topic}**

**Overview**
Based on current authoritative sources, here's comprehensive information about {topic}:

**Key Points**
• Well-established concept with proven applications
• Multiple approaches and methodologies available
• Active research and development in this area
• Practical implementations across various industries

**Current Trends**
• Growing adoption and implementation
• Integration with modern technologies
• Focus on user experience and efficiency
• Continuous improvement and innovation

**Expert Insights**
• Industry leaders recommend thoughtful implementation
• Best practices emphasize gradual adoption
• Success depends on proper planning and execution
• ROI typically seen within 3-6 months

**Sources**: Wikipedia, Academic Papers, Industry Whitepapers - Updated today
**Note**: Information compiled from multiple authoritative sources."""

        # Fallback for any other queries
        else:
            return f"""🔍 **WEB SEARCH RESULTS** - General Search

**Search Results for: "{query}"**

**Summary**
Current web sources provide comprehensive information about your query. Based on recent data and expert analysis:

**Key Findings**
• Multiple reliable sources confirm current information
• Recent updates and developments available
• Practical applications and use cases documented
• Industry trends and expert opinions accessible

**Current Status**
• Active development and research in this area
• Multiple perspectives and approaches available
• Growing interest and adoption trends
• Positive outlook for future developments

**Data Quality**
• Information verified from multiple sources
• Recent updates within last 24-48 hours
• Expert analysis and peer review available
• Continuing monitoring for changes

**Sources**: Multiple verified sources including academic, industry, and news outlets
**Last Updated**: Within last 24 hours

💡 **Demo Note**: This shows web search capability. In production, this would integrate with real search APIs like Google Search, Bing, or specialized search services for live data."""

    def _extract_location(self, query: str) -> str:
        """Extract location from weather query"""
        # Simple location extraction
        locations = ["san francisco", "new york", "london", "tokyo", "paris", "sydney"]
        for location in locations:
            if location in query:
                return location.title()
        return "your location"

    def _extract_topic(self, query: str, exclude_words: list) -> str:
        """Extract main topic from query by removing common words"""
        words = query.lower().split()
        # Remove common words and exclude words
        common_words = [
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "what",
            "how",
            "when",
            "where",
            "why",
        ]
        filtered_words = [w for w in words if w not in common_words and w not in exclude_words]

        if filtered_words:
            return " ".join(filtered_words[:3])  # Take first 3 meaningful words
        return "the requested topic"
