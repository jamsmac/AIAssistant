"""
BlogSEOAgent - AI Agent specialized in SEO optimization
"""
import logging
from typing import Dict, List
import json
from ..fractal.base_agent import FractalAgent

logger = logging.getLogger(__name__)


class BlogSEOAgent(FractalAgent):
    """
    AI Agent specializing in SEO optimization

    Capabilities:
    - Keyword research and optimization
    - Meta tag generation
    - Content structure for SEO
    - Internal linking suggestions
    - SEO scoring
    """

    async def optimize_for_seo(
        self,
        title: str,
        content: str,
        target_keywords: List[str] = None
    ) -> Dict:
        """
        Complete SEO optimization

        Returns:
            Optimized meta data and suggestions
        """
        if not self._initialized:
            await self.initialize()

        keywords_str = ', '.join(target_keywords) if target_keywords else 'auto-detect'

        prompt = f"""You are an SEO specialist. Optimize this blog post for search engines.

TITLE: {title}

CONTENT:
{content[:2000]}...

TARGET KEYWORDS: {keywords_str}

Provide SEO optimization:
1. Optimized title (50-60 chars, includes main keyword)
2. Meta description (150-160 chars, compelling, includes keyword)
3. Suggested meta keywords (5-8 keywords)
4. URL slug (SEO-friendly)
5. Content improvements for SEO
6. Header structure recommendations
7. Internal linking opportunities
8. SEO score (0-100)

Return JSON:
{{
    "optimized_title": "SEO title",
    "meta_description": "description",
    "meta_keywords": ["keyword1", "keyword2"],
    "url_slug": "seo-friendly-slug",
    "h1_heading": "main heading",
    "content_improvements": ["improvement 1", "improvement 2"],
    "header_structure": ["H1: ...", "H2: ...", "H2: ..."],
    "internal_links_suggestions": ["link to related topic 1", "link to topic 2"],
    "keyword_density": {{"keyword": 0.02}},
    "seo_score": 0-100,
    "optimization_notes": ["note 1", "note 2"]
}}

Return ONLY JSON."""

        try:
            response = self.anthropic.messages.create(
                model=self.data.get('model', 'claude-sonnet-4-20250514'),
                max_tokens=3000,
                temperature=0.4,
                messages=[{"role": "user", "content": prompt}]
            )

            result = self._extract_json(response.content[0].text)
            logger.info(f"SEO optimized: score {result.get('seo_score', 'N/A')}/100")

            return result

        except Exception as e:
            logger.error(f"SEO optimization failed: {e}")
            raise

    async def generate_keywords(self, content: str, count: int = 10) -> List[str]:
        """
        Extract and suggest relevant keywords

        Returns:
            List of SEO keywords
        """
        if not self._initialized:
            await self.initialize()

        prompt = f"""Extract the {count} most relevant SEO keywords from this content:

{content[:1500]}...

Consider:
- Main topics and themes
- Search intent
- Long-tail keywords
- Related terms

Return JSON array of keywords:
["keyword1", "keyword2", ...]

Return ONLY JSON array."""

        try:
            response = self.anthropic.messages.create(
                model=self.data.get('model', 'claude-sonnet-4-20250514'),
                max_tokens=500,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )

            keywords = self._extract_json(response.content[0].text)

            if not isinstance(keywords, list):
                keywords = [keywords]

            return keywords[:count]

        except Exception as e:
            logger.error(f"Keyword generation failed: {e}")
            raise

    async def analyze_seo_score(self, title: str, content: str, meta_description: str = "") -> Dict:
        """
        Analyze SEO score of content

        Returns:
            Detailed SEO analysis with score
        """
        if not self._initialized:
            await self.initialize()

        prompt = f"""Analyze the SEO quality of this blog post:

TITLE: {title}
META DESCRIPTION: {meta_description}

CONTENT:
{content[:1500]}...

Evaluate:
1. Title optimization (keyword placement, length)
2. Meta description quality
3. Content structure (H1, H2, H3 usage)
4. Keyword optimization
5. Content length
6. Readability for search engines
7. Internal/external link potential

Return JSON:
{{
    "overall_score": 0-100,
    "title_score": 0-100,
    "meta_description_score": 0-100,
    "content_structure_score": 0-100,
    "keyword_score": 0-100,
    "readability_score": 0-100,
    "strengths": ["strength 1", "strength 2"],
    "weaknesses": ["weakness 1", "weakness 2"],
    "quick_wins": ["easy improvement 1", "easy improvement 2"],
    "detailed_feedback": "comprehensive feedback"
}}

Return ONLY JSON."""

        try:
            response = self.anthropic.messages.create(
                model=self.data.get('model', 'claude-sonnet-4-20250514'),
                max_tokens=2000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )

            return self._extract_json(response.content[0].text)

        except Exception as e:
            logger.error(f"SEO analysis failed: {e}")
            raise

    def _extract_json(self, text: str) -> Dict:
        """Extract JSON from response"""
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0].strip()
        elif '```' in text:
            text = text.split('```')[1].split('```')[0].strip()

        return json.loads(text)
