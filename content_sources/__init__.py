"""
Content Sources Module
Article trend scoring utilities.
Note: Live web content is now exclusively fetched via TinyFish Web Agent
(app/services/web_agent_news_service.py). EconomicTimesFetcher is retained
for reference only and is no longer used by the automation pipeline.
"""
from .trend_analyzer import TrendAnalyzer

__all__ = ['TrendAnalyzer']
