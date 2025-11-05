"""
BlogWriterAgent - AI Agent specialized in writing blog posts
"""
import logging
from typing import Dict, List, Optional
import json
from ..fractal.base_agent import FractalAgent

logger = logging.getLogger(__name__)


class BlogWriterAgent(FractalAgent):
    """
    AI Agent specializing in blog post writing

    Capabilities:
    - Write complete blog posts from topics
    - Adapt writing style (professional, casual, technical, etc.)
    - Control content length
    - Generate compelling titles and excerpts
    - Suggest relevant tags
    - Calculate reading time
    """

    def __init__(self, agent_id: str, db, anthropic_api_key: Optional[str] = None):
        super().__init__(agent_id, db, anthropic_api_key)

    async def write_blog_post(
        self,
        topic: str,
        category: str = 'general',
        style: str = 'professional',
        target_length: int = 1500,
        audience: str = 'general',
        tone: str = 'informative',
        include_examples: bool = True,
        organization_id: Optional[str] = None
    ) -> Dict:
        """
        Write complete blog post

        Args:
            topic: Topic to write about
            category: Blog category
            style: Writing style
            target_length: Target word count
            audience: Target audience
            tone: Tone of writing
            include_examples: Whether to include practical examples
            organization_id: Organization ID for memory access

        Returns:
            Dict with title, excerpt, content, tags, reading_time
        """
        if not self._initialized:
            await self.initialize()

        logger.info(f"Writing blog post about: {topic}")

        # Check collective memory for similar posts
        similar_posts = await self._query_similar_posts(topic, category, organization_id)

        # Build writing prompt
        prompt = self._build_writing_prompt(
            topic=topic,
            category=category,
            style=style,
            target_length=target_length,
            audience=audience,
            tone=tone,
            include_examples=include_examples,
            similar_posts=similar_posts
        )

        try:
            # Generate content
            response = self.anthropic.messages.create(
                model=self.data.get('model', 'claude-sonnet-4-20250514'),
                max_tokens=8000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text

            # Extract JSON from response
            post_data = self._extract_json(response_text)

            # Calculate reading time if not provided
            if 'reading_time' not in post_data:
                word_count = len(post_data.get('content', '').split())
                post_data['reading_time'] = max(1, word_count // 200)

            if 'word_count' not in post_data:
                post_data['word_count'] = len(post_data.get('content', '').split())

            logger.info(
                f"Blog post written: {post_data.get('title', 'Untitled')} "
                f"({post_data.get('word_count', 0)} words)"
            )

            # Store in memory
            await self._store_writing_in_memory(topic, category, post_data, organization_id)

            return post_data

        except Exception as e:
            logger.error(f"Failed to write blog post: {e}")
            raise

    async def improve_content(
        self,
        content: str,
        improvement_type: str = 'general',
        organization_id: Optional[str] = None
    ) -> Dict:
        """
        Improve existing content

        Args:
            content: Existing content
            improvement_type: Type of improvement ('clarity', 'engagement', 'structure', 'general')
            organization_id: Organization ID

        Returns:
            Dict with improved_content and changes_made
        """
        if not self._initialized:
            await self.initialize()

        prompt = f"""You are a professional content improvement specialist.

Improve this blog content focusing on {improvement_type}:

ORIGINAL CONTENT:
{content}

Tasks:
1. Improve {improvement_type}
2. Maintain the original message and key points
3. Enhance readability and flow
4. Fix any awkward phrasing
5. Add transitions if needed

Return a JSON object with:
{{
    "improved_content": "...",
    "changes_made": ["list of key improvements"],
    "improvement_score": 0-10
}}

Return ONLY the JSON, no other text."""

        try:
            response = self.anthropic.messages.create(
                model=self.data.get('model', 'claude-sonnet-4-20250514'),
                max_tokens=8000,
                temperature=0.5,
                messages=[{"role": "user", "content": prompt}]
            )

            result = self._extract_json(response.content[0].text)

            logger.info(f"Content improved: score {result.get('improvement_score', 'N/A')}/10")

            return result

        except Exception as e:
            logger.error(f"Failed to improve content: {e}")
            raise

    async def generate_title_options(
        self,
        content: str,
        num_options: int = 5,
        style: str = 'engaging'
    ) -> List[str]:
        """
        Generate multiple title options for content

        Args:
            content: Blog content
            num_options: Number of title options to generate
            style: Title style ('engaging', 'descriptive', 'seo', 'creative')

        Returns:
            List of title options
        """
        if not self._initialized:
            await self.initialize()

        prompt = f"""Generate {num_options} {style} title options for this blog content.

CONTENT:
{content[:1000]}...

Requirements:
- Titles should be compelling and {style}
- 40-60 characters ideal length
- Capture the main value/insight
- Make readers want to click

Return a JSON array of title strings:
["title 1", "title 2", ...]

Return ONLY the JSON array."""

        try:
            response = self.anthropic.messages.create(
                model=self.data.get('model', 'claude-sonnet-4-20250514'),
                max_tokens=1000,
                temperature=0.8,
                messages=[{"role": "user", "content": prompt}]
            )

            titles = self._extract_json(response.content[0].text)

            if not isinstance(titles, list):
                titles = [titles]

            return titles

        except Exception as e:
            logger.error(f"Failed to generate titles: {e}")
            raise

    def _build_writing_prompt(
        self,
        topic: str,
        category: str,
        style: str,
        target_length: int,
        audience: str,
        tone: str,
        include_examples: bool,
        similar_posts: List[Dict]
    ) -> str:
        """Build comprehensive writing prompt"""

        prompt = f"""You are an expert blog content writer specializing in creating high-quality, engaging blog posts.

ASSIGNMENT:
Write a comprehensive blog post about: {topic}

SPECIFICATIONS:
- Category: {category}
- Style: {style}
- Target length: ~{target_length} words
- Audience: {audience}
- Tone: {tone}
- Include practical examples: {'Yes' if include_examples else 'No'}

STRUCTURE:
1. Compelling title (engaging, clear, SEO-friendly)
2. Engaging introduction (hook the reader, explain value)
3. Well-organized body with clear sections/subheadings
4. Practical examples and actionable insights
5. Strong conclusion with key takeaways
6. Call-to-action

QUALITY REQUIREMENTS:
- Original, well-researched content
- Clear, concise, and engaging writing
- Proper flow and transitions
- Actionable insights
- Value-driven content
"""

        if similar_posts:
            prompt += f"\n\nSIMILAR SUCCESSFUL POSTS (for inspiration, don't copy):\n"
            for i, post in enumerate(similar_posts[:3], 1):
                prompt += f"{i}. {post.get('solution_summary', '')}...\n"

        prompt += """
Return a JSON object with this exact structure:
{
    "title": "Compelling blog post title",
    "excerpt": "Brief description (150-200 chars) that summarizes the post and entices readers",
    "content": "Full blog post content in Markdown format with proper headings, lists, code blocks if needed, etc.",
    "suggested_tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
    "key_takeaways": ["takeaway 1", "takeaway 2", "takeaway 3"],
    "reading_time": estimated_minutes,
    "target_audience": "description of ideal reader",
    "seo_keywords": ["keyword1", "keyword2", "keyword3"]
}

IMPORTANT: Return ONLY the JSON object, no other text before or after."""

        return prompt

    async def _query_similar_posts(
        self,
        topic: str,
        category: str,
        organization_id: Optional[str]
    ) -> List[Dict]:
        """Query collective memory for similar blog posts"""
        if not organization_id:
            return []

        try:
            similar = await self.db.fetch("""
                SELECT *
                FROM agent_collective_memory
                WHERE task_type = 'blog_writing'
                AND task_category = $1
                AND organization_id = $2
                AND success = TRUE
                ORDER BY confidence_score DESC, created_at DESC
                LIMIT 5
            """, category, organization_id)

            return similar

        except Exception as e:
            logger.warning(f"Failed to query similar posts: {e}")
            return []

    async def _store_writing_in_memory(
        self,
        topic: str,
        category: str,
        post_data: Dict,
        organization_id: Optional[str]
    ):
        """Store writing task in collective memory"""
        if not organization_id:
            return

        try:
            await self.db.execute("""
                INSERT INTO agent_collective_memory (
                    organization_id,
                    task_type,
                    task_category,
                    input_context,
                    solution_approach,
                    solution_summary,
                    participating_agents,
                    primary_agent_id,
                    success,
                    confidence_score
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
            organization_id,
            'blog_writing',
            category,
            f"Write blog post about: {topic}",
            post_data.get('content', '')[:5000],
            f"Title: {post_data.get('title', 'N/A')}, Words: {post_data.get('word_count', 0)}",
            [self.agent_id],
            self.agent_id,
            True,
            0.85
            )

        except Exception as e:
            logger.warning(f"Failed to store in memory: {e}")

    def _extract_json(self, text: str) -> Dict:
        """Extract JSON from LLM response"""
        # Remove markdown code blocks
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0].strip()
        elif '```' in text:
            text = text.split('```')[1].split('```')[0].strip()

        # Try to parse
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.error(f"Text: {text[:500]}")
            raise ValueError(f"Invalid JSON response from LLM: {e}")
