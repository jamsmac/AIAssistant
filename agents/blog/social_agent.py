"""
BlogSocialAgent - AI Agent specialized in social media content creation
"""
import logging
from typing import Dict, List
import json
from ..fractal.base_agent import FractalAgent

logger = logging.getLogger(__name__)


class BlogSocialAgent(FractalAgent):
    """
    AI Agent specializing in social media post creation

    Capabilities:
    - Create platform-specific posts (Twitter, LinkedIn, Facebook)
    - Generate engaging hooks
    - Suggest hashtags
    - Create post threads
    - Optimize for engagement
    """

    async def create_social_posts(
        self,
        blog_post: Dict,
        platforms: List[str] = None
    ) -> Dict:
        """
        Create optimized posts for social media platforms

        Args:
            blog_post: Dict with title, excerpt, content
            platforms: List of platforms ('twitter', 'linkedin', 'facebook', 'instagram')

        Returns:
            Dict with posts for each platform
        """
        if not self._initialized:
            await self.initialize()

        if platforms is None:
            platforms = ['twitter', 'linkedin', 'facebook']

        title = blog_post.get('title', '')
        excerpt = blog_post.get('excerpt', '')
        content = blog_post.get('content', '')[:1000]

        results = {}

        for platform in platforms:
            post = await self._create_platform_post(platform, title, excerpt, content)
            results[platform] = post

        return results

    async def _create_platform_post(
        self,
        platform: str,
        title: str,
        excerpt: str,
        content: str
    ) -> Dict:
        """Create post for specific platform"""

        platform_specs = {
            'twitter': {
                'max_length': 280,
                'style': 'concise and engaging, thread-friendly',
                'hashtags': '2-3 relevant hashtags',
                'emojis': 'optional, use sparingly'
            },
            'linkedin': {
                'max_length': 3000,
                'style': 'professional and insightful',
                'hashtags': '3-5 professional hashtags',
                'emojis': 'minimal, professional only'
            },
            'facebook': {
                'max_length': 5000,
                'style': 'conversational and engaging',
                'hashtags': '2-4 hashtags',
                'emojis': 'friendly and appropriate'
            },
            'instagram': {
                'max_length': 2200,
                'style': 'visual and story-driven',
                'hashtags': '5-10 relevant hashtags',
                'emojis': 'encouraged for personality'
            }
        }

        spec = platform_specs.get(platform, platform_specs['twitter'])

        prompt = f"""Create an engaging {platform} post to promote this blog article.

BLOG TITLE: {title}
EXCERPT: {excerpt}
CONTENT PREVIEW: {content}...

{platform.upper()} REQUIREMENTS:
- Max length: {spec['max_length']} characters
- Style: {spec['style']}
- Hashtags: {spec['hashtags']}
- Emojis: {spec['emojis']}

Create a post that:
1. Hooks the reader immediately
2. Highlights key value/insight
3. Creates curiosity
4. Includes clear call-to-action
5. Uses appropriate tone for {platform}

Return JSON:
{{
    "post_text": "the complete post",
    "hook": "opening line",
    "hashtags": ["hashtag1", "hashtag2"],
    "call_to_action": "CTA used",
    "char_count": number,
    "thread_parts": ["part1", "part2"] (if multi-part)
}}

Return ONLY JSON."""

        try:
            response = self.anthropic.messages.create(
                model=self.data.get('model', 'claude-sonnet-4-20250514'),
                max_tokens=2000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )

            result = self._extract_json(response.content[0].text)
            logger.info(f"Created {platform} post: {result.get('char_count', 'N/A')} chars")

            return result

        except Exception as e:
            logger.error(f"Failed to create {platform} post: {e}")
            raise

    async def create_thread(
        self,
        topic: str,
        key_points: List[str],
        platform: str = 'twitter'
    ) -> List[str]:
        """
        Create a social media thread

        Args:
            topic: Main topic
            key_points: List of key points to cover
            platform: Platform (twitter, linkedin)

        Returns:
            List of thread posts
        """
        if not self._initialized:
            await self.initialize()

        max_length = 280 if platform == 'twitter' else 1300

        prompt = f"""Create a {platform} thread about: {topic}

KEY POINTS TO COVER:
{chr(10).join(f'{i+1}. {point}' for i, point in enumerate(key_points))}

Requirements:
- Each post max {max_length} characters
- Engaging opening tweet/post
- Smooth flow between posts
- Clear numbering (1/X format)
- Strong closing with CTA
- Each post stands alone but connects to thread

Return JSON array of posts:
["post 1", "post 2", "post 3", ...]

Return ONLY JSON array."""

        try:
            response = self.anthropic.messages.create(
                model=self.data.get('model', 'claude-sonnet-4-20250514'),
                max_tokens=3000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )

            thread = self._extract_json(response.content[0].text)

            if not isinstance(thread, list):
                thread = [thread]

            logger.info(f"Created thread with {len(thread)} posts")

            return thread

        except Exception as e:
            logger.error(f"Thread creation failed: {e}")
            raise

    async def suggest_hashtags(
        self,
        content: str,
        platform: str = 'general',
        count: int = 5
    ) -> List[str]:
        """
        Suggest relevant hashtags

        Args:
            content: Content to analyze
            platform: Target platform
            count: Number of hashtags

        Returns:
            List of hashtags (without # symbol)
        """
        if not self._initialized:
            await self.initialize()

        prompt = f"""Suggest {count} effective hashtags for this content on {platform}:

{content[:500]}...

Requirements:
- Relevant to content
- Mix of popular and niche
- Platform-appropriate
- Not overly generic

Return JSON array (without # symbol):
["hashtag1", "hashtag2", ...]

Return ONLY JSON array."""

        try:
            response = self.anthropic.messages.create(
                model=self.data.get('model', 'claude-sonnet-4-20250514'),
                max_tokens=500,
                temperature=0.6,
                messages=[{"role": "user", "content": prompt}]
            )

            hashtags = self._extract_json(response.content[0].text)

            if not isinstance(hashtags, list):
                hashtags = [hashtags]

            # Remove # if present and limit count
            hashtags = [h.lstrip('#') for h in hashtags][:count]

            return hashtags

        except Exception as e:
            logger.error(f"Hashtag suggestion failed: {e}")
            raise

    def _extract_json(self, text: str):
        """Extract JSON from response"""
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0].strip()
        elif '```' in text:
            text = text.split('```')[1].split('```')[0].strip()

        return json.loads(text)
