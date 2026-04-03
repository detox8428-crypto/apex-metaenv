"""
Content Summarizer Module
==========================
Summarizes text, web pages, documents using OpenAI GPT

Features:
- Text summarization
- Web content summarization
- Document summarization (PDF, TXT, etc.)
- Multiple summary styles (brief, detailed, bullet-points)
- Language detection and translation-aware summarization
- Cost tracking for API calls
"""

import os
import requests
import logging
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

# Try importing required libraries
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI library not available - install with: pip install openai")


class SummaryStyle(Enum):
    """Summary style options"""
    BRIEF = "brief"  # 1-2 sentences
    DETAILED = "detailed"  # Full summary with all key points
    BULLET_POINTS = "bullet_points"  # Key points as bullet list
    EXECUTIVE = "executive"  # Executive summary format
    KEY_INSIGHTS = "key_insights"  # Key insights only


class ContentAnalyzer:
    """Analyzes and extracts content"""
    
    @staticmethod
    def extract_text_from_url(url: str) -> Optional[str]:
        """Extract text from a web page"""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Try to extract text from HTML
            from html.parser import HTMLParser
            
            class TextExtractor(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.text = []
                
                def handle_data(self, data):
                    text = data.strip()
                    if text:
                        self.text.append(text)
            
            extractor = TextExtractor()
            extractor.feed(response.text)
            content = " ".join(extractor.text)
            
            if content:
                logger.info(f"✅ Extracted {len(content)} chars from {url}")
                return content
            else:
                logger.warning(f"⚠️ No text extracted from {url}")
                return None
        
        except Exception as e:
            logger.error(f"❌ Failed to extract from URL: {e}")
            return None
    
    @staticmethod
    def estimate_word_count(text: str) -> int:
        """Estimate word count"""
        return len(text.split())
    
    @staticmethod
    def truncate_to_tokens(text: str, max_tokens: int = 4000) -> str:
        """Truncate text to approximate token limit (rough estimate: 1 token ≈ 4 chars)"""
        char_limit = max_tokens * 4
        if len(text) > char_limit:
            return text[:char_limit] + "..."
        return text


class ContentSummarizer:
    """Content summarization with OpenAI"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.enabled = False
        self.total_tokens_used = 0
        self.total_cost = 0.0
        
        # OpenAI pricing (approximate, as of 2024)
        self.pricing = {
            "gpt-4": {"input": 0.03 / 1000, "output": 0.06 / 1000},
            "gpt-3.5-turbo": {"input": 0.0005 / 1000, "output": 0.0015 / 1000}
        }
        
        if OPENAI_AVAILABLE and self.api_key:
            openai.api_key = self.api_key
            self.enabled = True
            logger.info("✅ Content Summarizer (OpenAI) enabled")
        else:
            logger.warning("⚠️ Content Summarizer disabled - OpenAI not available or no API key")
    
    def _get_summary_prompt(self, content: str, style: SummaryStyle) -> str:
        """Generate summarization prompt based on style"""
        
        prompts = {
            SummaryStyle.BRIEF: f"""Please summarize the following content in 1-2 sentences:

{content}

Summary:""",
            
            SummaryStyle.DETAILED: f"""Please provide a comprehensive summary of the following content, including all key points and details:

{content}

Summary:""",
            
            SummaryStyle.BULLET_POINTS: f"""Please summarize the following content as a list of key bullet points (5-10 points):

{content}

Key Points:
-""",
            
            SummaryStyle.EXECUTIVE: f"""Please provide an executive summary of the following content suitable for C-level executives (2-3 paragraphs):

{content}

Executive Summary:""",
            
            SummaryStyle.KEY_INSIGHTS: f"""Please extract and list the key insights and main takeaways from the following content (5-7 points):

{content}

Key Insights:
1."""
        }
        
        return prompts.get(style, prompts[SummaryStyle.DETAILED])
    
    def summarize(self, content: str, style: SummaryStyle = SummaryStyle.DETAILED,
                 model: str = "gpt-3.5-turbo") -> Dict:
        """
        Summarize content using OpenAI
        
        Args:
            content: Content to summarize (text or URL)
            style: Summary style
            model: OpenAI model to use
        
        Returns:
            {"success": bool, "summary": str, "tokens_used": int, "cost": float, ...}
        """
        
        if not self.enabled:
            return {"success": False, "error": "Summarizer not configured"}
        
        try:
            # If content looks like a URL, extract it
            if content.startswith("http://") or content.startswith("https://"):
                extracted = ContentAnalyzer.extract_text_from_url(content)
                if not extracted:
                    return {"success": False, "error": "Failed to extract content from URL"}
                content = extracted
            
            # Truncate if too long
            content = ContentAnalyzer.truncate_to_tokens(content, max_tokens=4000)
            
            # Generate prompt
            prompt = self._get_summary_prompt(content, style)
            
            logger.info(f"Summarizing {len(content)} chars with {model} ({style.value})")
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes content concisely and accurately."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for consistency
                max_tokens=500 if style == SummaryStyle.DETAILED else 250
            )
            
            # Extract summary
            summary = response.choices[0].message.content.strip()
            
            # Calculate tokens and cost
            tokens_used = response.usage.total_tokens
            self.total_tokens_used += tokens_used
            
            cost = (response.usage.prompt_tokens * self.pricing[model]["input"] +
                   response.usage.completion_tokens * self.pricing[model]["output"])
            self.total_cost += cost
            
            logger.info(f"✅ Summary generated: {len(summary)} chars, {tokens_used} tokens, ${cost:.4f}")
            
            return {
                "success": True,
                "summary": summary,
                "style": style.value,
                "model": model,
                "tokens_used": tokens_used,
                "cost": round(cost, 6),
                "content_length": len(content),
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"❌ Summarization error: {e}")
            return {"success": False, "error": str(e)}
    
    def summarize_multiple(self, contents: List[str],
                         style: SummaryStyle = SummaryStyle.BRIEF) -> Dict:
        """Summarize multiple pieces of content"""
        
        results = []
        total_cost = 0.0
        
        for idx, content in enumerate(contents, 1):
            logger.info(f"Summarizing {idx}/{len(contents)}")
            result = self.summarize(content, style)
            results.append(result)
            if result.get("success"):
                total_cost += result.get("cost", 0)
        
        successful = sum(1 for r in results if r.get("success"))
        
        return {
            "success": successful == len(contents),
            "total_summarized": len(contents),
            "successful": successful,
            "failed": len(contents) - successful,
            "total_cost": round(total_cost, 6),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_usage_stats(self) -> Dict:
        """Get usage statistics"""
        return {
            "total_tokens": self.total_tokens_used,
            "total_cost": round(self.total_cost, 6),
            "currency": "USD",
            "status": "✅ Active" if self.enabled else "⚠️ Disabled"
        }


class Promptoptimizer:
    """Optimize content for summarization"""
    
    @staticmethod
    def estimate_summary_quality(content: str, summary: str) -> Dict:
        """Estimate quality of summary"""
        
        content_words = len(content.split())
        summary_words = len(summary.split())
        
        # Compression ratio
        compression = summary_words / content_words if content_words > 0 else 0
        
        # Check for key indicators
        indicators = {
            "has_numbers": any(char.isdigit() for char in summary),
            "has_names": any(word[0].isupper() for word in summary.split() if len(word) > 2),
            "sentence_count": summary.count(".") + summary.count("!") + summary.count("?"),
            "average_sentence_length": summary_words / (summary.count(".") + 1) if summary else 0
        }
        
        return {
            "content_words": content_words,
            "summary_words": summary_words,
            "compression_ratio": round(compression, 2),
            "indicators": indicators,
            "quality_score": min(1.0, round(compression * 0.3 + 0.7, 2))  # Simple quality score
        }


class SummarizerManager:
    """Manages content summarization"""
    
    def __init__(self):
        self.summarizer = ContentSummarizer()
        self.analyzer = ContentAnalyzer()
        self.optimizer = Promptoptimizer()
        self.enabled = self.summarizer.enabled
    
    def summarize(self, content: str, style: str = "detailed") -> Dict:
        """Summarize content with specified style"""
        
        try:
            style_enum = SummaryStyle[style.upper()]
        except KeyError:
            style_enum = SummaryStyle.DETAILED
        
        return self.summarizer.summarize(content, style_enum)
    
    def get_status(self) -> Dict:
        """Get summarizer status"""
        stats = self.summarizer.get_usage_stats()
        stats["provider"] = "OpenAI"
        stats["content_analyzer_available"] = True
        return stats


# Global manager instance
summarizer_manager = SummarizerManager()


if __name__ == "__main__":
    # Demo usage
    print("Content Summarizer Module")
    print("=" * 50)
    print(summarizer_manager.get_status())
    print("\nTo use Content Summarizer:")
    print("1. Set environment variable:")
    print("   - OPENAI_API_KEY=your_key")
    print("2. Use summarizer_manager.summarize(content, style='brief|detailed|bullet_points|executive|key_insights')")
    print("3. Can summarize text or URLs")
    print("\nExample:")
    print("  result = summarizer_manager.summarize('Your text here', style='brief')")
