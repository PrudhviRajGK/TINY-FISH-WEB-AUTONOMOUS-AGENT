"""
Trend Analyzer
Ranks articles based on trending topics and virality potential
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any
import re
import logging

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """Analyzes and ranks articles based on trend score"""
    
    # Trending keywords with weights
    TRENDING_KEYWORDS = {
        # AI & Tech
        'ai': 10, 'artificial intelligence': 10, 'chatgpt': 9, 'openai': 9,
        'machine learning': 8, 'deeptech': 8, 'generative ai': 9,
        
        # Startups & Funding
        'startup': 8, 'unicorn': 9, 'funding': 8, 'series a': 7, 'series b': 7,
        'ipo': 9, 'valuation': 7, 'investment': 6,
        
        # Big Tech
        'google': 7, 'microsoft': 7, 'amazon': 7, 'meta': 7, 'apple': 7,
        'tesla': 8, 'nvidia': 8, 'openai': 9,
        
        # Stock Market
        'stock market': 7, 'sensex': 7, 'nifty': 7, 'shares': 6,
        'market crash': 9, 'bull run': 8, 'bear market': 8,
        
        # India Tech
        'india': 6, 'indian startup': 8, 'bangalore': 6, 'mumbai': 6,
        'digital india': 7, 'make in india': 7,
        
        # Business Impact
        'layoff': 8, 'acquisition': 8, 'merger': 7, 'bankruptcy': 8,
        'profit': 6, 'revenue': 6, 'growth': 5,
        
        # Viral Topics
        'controversy': 7, 'scandal': 8, 'breakthrough': 8, 'record': 7,
        'first time': 7, 'historic': 7, 'shocking': 8,
    }
    
    # Category weights
    CATEGORY_WEIGHTS = {
        'tech': 1.3,
        'startup': 1.4,
        'ai': 1.5,
        'business': 1.2,
        'market': 1.1,
        'general': 1.0,
    }
    
    def __init__(self):
        self.keyword_pattern = self._compile_keyword_pattern()
    
    def _compile_keyword_pattern(self):
        """Compile regex pattern for keyword matching"""
        keywords = '|'.join(re.escape(k) for k in self.TRENDING_KEYWORDS.keys())
        return re.compile(keywords, re.IGNORECASE)
    
    def rank_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rank articles by trend score
        
        Args:
            articles: List of article dictionaries
        
        Returns:
            Sorted list with trend scores
        """
        logger.info(f"Ranking {len(articles)} articles")
        
        scored_articles = []
        
        for article in articles:
            score = self._calculate_trend_score(article)
            article['trend_score'] = score
            article['trend_breakdown'] = self._get_score_breakdown(article)
            scored_articles.append(article)
        
        # Sort by trend score (highest first)
        scored_articles.sort(key=lambda x: x['trend_score'], reverse=True)
        
        logger.info(f"Top article: {scored_articles[0]['title']} (score: {scored_articles[0]['trend_score']:.2f})")
        
        return scored_articles
    
    def _calculate_trend_score(self, article: Dict[str, Any]) -> float:
        """Calculate overall trend score for an article"""
        
        # 1. Recency Score (0-30 points)
        recency_score = self._calculate_recency_score(article['published_time'])
        
        # 2. Keyword Score (0-40 points)
        keyword_score = self._calculate_keyword_score(article)
        
        # 3. Category Score (0-20 points)
        category_score = self._calculate_category_score(article['category'])
        
        # 4. Virality Potential (0-10 points)
        virality_score = self._calculate_virality_score(article)
        
        total_score = recency_score + keyword_score + category_score + virality_score
        
        return total_score
    
    def _calculate_recency_score(self, published_time: datetime) -> float:
        """Calculate score based on article recency"""
        now = datetime.now()
        age = now - published_time
        
        # Maximum 30 points for articles less than 1 hour old
        if age < timedelta(hours=1):
            return 30.0
        elif age < timedelta(hours=6):
            return 25.0
        elif age < timedelta(hours=12):
            return 20.0
        elif age < timedelta(days=1):
            return 15.0
        elif age < timedelta(days=2):
            return 10.0
        else:
            return 5.0
    
    def _calculate_keyword_score(self, article: Dict[str, Any]) -> float:
        """Calculate score based on trending keywords"""
        text = f"{article['title']} {article['summary']} {article['content'][:500]}"
        text = text.lower()
        
        score = 0.0
        matched_keywords = []
        
        for keyword, weight in self.TRENDING_KEYWORDS.items():
            if keyword.lower() in text:
                score += weight
                matched_keywords.append(keyword)
        
        # Cap at 40 points
        score = min(score, 40.0)
        
        article['matched_keywords'] = matched_keywords
        
        return score
    
    def _calculate_category_score(self, category: str) -> float:
        """Calculate score based on article category"""
        category = category.lower()
        
        for cat, weight in self.CATEGORY_WEIGHTS.items():
            if cat in category:
                return 20.0 * weight
        
        return 10.0  # Default score
    
    def _calculate_virality_score(self, article: Dict[str, Any]) -> float:
        """Calculate virality potential based on content characteristics"""
        score = 0.0
        
        title = article['title'].lower()
        
        # Viral indicators in title
        viral_words = ['shocking', 'breaking', 'exclusive', 'revealed', 'secret',
                      'you won\'t believe', 'just announced', 'major', 'huge']
        
        for word in viral_words:
            if word in title:
                score += 2.0
        
        # Numbers in title (data-driven)
        if re.search(r'\d+', title):
            score += 2.0
        
        # Question in title
        if '?' in title:
            score += 1.0
        
        # Exclamation in title
        if '!' in title:
            score += 1.0
        
        # Cap at 10 points
        return min(score, 10.0)
    
    def _get_score_breakdown(self, article: Dict[str, Any]) -> Dict[str, float]:
        """Get detailed score breakdown for debugging"""
        return {
            'recency': self._calculate_recency_score(article['published_time']),
            'keywords': self._calculate_keyword_score(article),
            'category': self._calculate_category_score(article['category']),
            'virality': self._calculate_virality_score(article),
        }
    
    def select_top_articles(self, articles: List[Dict[str, Any]], count: int = 3) -> List[Dict[str, Any]]:
        """
        Select top N trending articles
        
        Args:
            articles: List of articles
            count: Number of articles to select
        
        Returns:
            Top N articles
        """
        ranked = self.rank_articles(articles)
        selected = ranked[:count]
        
        logger.info(f"Selected top {len(selected)} articles:")
        for i, article in enumerate(selected, 1):
            logger.info(f"  {i}. {article['title']} (score: {article['trend_score']:.2f})")
        
        return selected
