"""
BlogImageAgent - AI Agent specialized in image generation and management
"""
import logging
from typing import Dict, Optional
import json
from ..fractal.base_agent import FractalAgent

logger = logging.getLogger(__name__)


class BlogImageAgent(FractalAgent):
    """
    AI Agent specializing in image generation for blog posts

    Capabilities:
    - Generate image prompts from content
    - Create cover images (via Stability AI or similar)
    - Suggest image placements
    - Generate alt text for accessibility
    """

    async def generate_cover_image_prompt(
        self,
        post_title: str,
        post_content: str,
        style: str = 'modern'
    ) -> Dict:
        """
        Generate image prompt for blog cover image

        Args:
            post_title: Blog post title
            post_content: Blog post content
            style: Image style ('modern', 'minimalist', 'illustrative', 'photographic')

        Returns:
            Dict with prompt, negative_prompt, alt_text
        """
        if not self._initialized:
            await self.initialize()

        prompt = f"""You are an AI image generation specialist. Create a detailed prompt for generating a blog post cover image.

BLOG TITLE: {post_title}

BLOG CONTENT:
{post_content[:1000]}...

DESIRED STYLE: {style}

Create:
1. Detailed image generation prompt (specific, visual, descriptive)
2. Negative prompt (what to avoid)
3. Alt text for accessibility
4. Color palette suggestions
5. Composition notes

Return JSON:
{{
    "image_prompt": "detailed prompt for image generation",
    "negative_prompt": "things to avoid in the image",
    "alt_text": "descriptive alt text for accessibility",
    "style_keywords": ["keyword1", "keyword2"],
    "color_palette": ["#color1", "#color2", "#color3"],
    "composition": "composition description",
    "aspect_ratio": "16:9 or 4:3 or 1:1"
}}

Return ONLY JSON."""

        try:
            response = self.anthropic.messages.create(
                model=self.data.get('model', 'claude-sonnet-4-20250514'),
                max_tokens=1500,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )

            result = self._extract_json(response.content[0].text)
            logger.info(f"Image prompt generated for: {post_title}")

            return result

        except Exception as e:
            logger.error(f"Image prompt generation failed: {e}")
            raise

    async def generate_image_with_stability(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 1024,
        height: int = 576
    ) -> Dict:
        """
        Generate image using Stability AI (placeholder - needs API key)

        Returns:
            Dict with image_url or image_data
        """
        # This is a placeholder implementation
        # In production, you would integrate with Stability AI API:
        # - Use stability-sdk
        # - Call image generation API
        # - Upload to S3 or similar storage
        # - Return public URL

        logger.warning("Image generation with Stability AI not yet implemented")

        return {
            'status': 'placeholder',
            'message': 'Stability AI integration pending',
            'prompt_used': prompt,
            'image_url': None
        }

    async def suggest_image_placements(
        self,
        content: str,
        num_images: int = 3
    ) -> List[Dict]:
        """
        Suggest where to place images in content

        Returns:
            List of image placement suggestions
        """
        if not self._initialized:
            await self.initialize()

        prompt = f"""Analyze this blog content and suggest {num_images} strategic image placements:

{content}

For each suggested image:
1. Where to place it (after which paragraph/section)
2. What the image should show
3. Purpose (illustration, example, break up text, etc.)
4. Alt text

Return JSON array:
[
    {{
        "placement": "After section X / paragraph Y",
        "description": "What image should show",
        "purpose": "Why this image here",
        "suggested_alt_text": "alt text",
        "image_type": "photo, illustration, diagram, screenshot"
    }}
]

Return ONLY JSON array."""

        try:
            response = self.anthropic.messages.create(
                model=self.data.get('model', 'claude-sonnet-4-20250514'),
                max_tokens=2000,
                temperature=0.6,
                messages=[{"role": "user", "content": prompt}]
            )

            placements = self._extract_json(response.content[0].text)

            if not isinstance(placements, list):
                placements = [placements]

            return placements[:num_images]

        except Exception as e:
            logger.error(f"Image placement suggestions failed: {e}")
            raise

    async def generate_alt_text(self, image_description: str, context: str = "") -> str:
        """
        Generate accessibility-friendly alt text for image

        Args:
            image_description: Description of the image
            context: Context where image appears

        Returns:
            Alt text string
        """
        if not self._initialized:
            await self.initialize()

        prompt = f"""Generate concise, descriptive alt text for accessibility:

IMAGE: {image_description}
CONTEXT: {context}

Requirements:
- Describe what's important in the image
- Keep it concise (125 chars or less)
- Focus on content, not aesthetics
- Include relevant context

Return just the alt text, no JSON."""

        try:
            response = self.anthropic.messages.create(
                model=self.data.get('model', 'claude-sonnet-4-20250514'),
                max_tokens=200,
                temperature=0.4,
                messages=[{"role": "user", "content": prompt}]
            )

            alt_text = response.content[0].text.strip()

            # Remove quotes if present
            alt_text = alt_text.strip('"\'')

            return alt_text[:125]  # Ensure max length

        except Exception as e:
            logger.error(f"Alt text generation failed: {e}")
            raise

    def _extract_json(self, text: str):
        """Extract JSON from response"""
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0].strip()
        elif '```' in text:
            text = text.split('```')[1].split('```')[0].strip()

        return json.loads(text)
