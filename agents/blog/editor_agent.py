"""
BlogEditorAgent - AI Agent specialized in editing and improving blog content
"""
import logging
from typing import Dict, List
import json
from ..fractal.base_agent import FractalAgent

logger = logging.getLogger(__name__)


class BlogEditorAgent(FractalAgent):
    """
    AI Agent specializing in content editing and improvement

    Capabilities:
    - Grammar and spelling correction
    - Readability improvement
    - Structure optimization
    - Flow and transitions
    - Tone consistency
    """

    async def edit_post(self, content: str, title: str = "") -> Dict:
        """
        Comprehensive editing of blog post

        Returns:
            Dict with edited_content, changes_made, quality_score
        """
        if not self._initialized:
            await self.initialize()

        prompt = f"""You are a professional editor specializing in blog content.

ORIGINAL TITLE: {title}

ORIGINAL CONTENT:
{content}

Edit and improve this content focusing on:
1. Grammar, spelling, and punctuation
2. Sentence structure and clarity
3. Paragraph flow and transitions
4. Consistency in tone and style
5. Eliminating redundancy
6. Strengthening weak sections

Return JSON:
{{
    "edited_content": "improved content",
    "changes_made": ["list of key edits"],
    "quality_score": 0-10,
    "readability_grade": "grade level",
    "issues_fixed": ["issue 1", "issue 2"]
}}

Return ONLY JSON."""

        try:
            response = self.anthropic.messages.create(
                model=self.data.get('model', 'claude-sonnet-4-20250514'),
                max_tokens=8000,
                temperature=0.3,  # Lower temperature for editing
                messages=[{"role": "user", "content": prompt}]
            )

            result = self._extract_json(response.content[0].text)
            logger.info(f"Content edited: quality score {result.get('quality_score', 'N/A')}/10")

            return result

        except Exception as e:
            logger.error(f"Editing failed: {e}")
            raise

    async def check_readability(self, content: str) -> Dict:
        """
        Analyze readability of content

        Returns:
            Readability metrics and suggestions
        """
        if not self._initialized:
            await self.initialize()

        prompt = f"""Analyze the readability of this blog content:

{content}

Provide analysis on:
1. Reading level (Flesch-Kincaid grade)
2. Sentence complexity
3. Paragraph length
4. Use of jargon
5. Overall accessibility

Return JSON:
{{
    "readability_score": 0-100,
    "grade_level": "X grade",
    "avg_sentence_length": number,
    "complex_words_ratio": 0-1,
    "suggestions": ["suggestion 1", "suggestion 2"],
    "overall_assessment": "description"
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
            logger.error(f"Readability check failed: {e}")
            raise

    async def proofread(self, content: str) -> Dict:
        """
        Quick proofread for errors

        Returns:
            List of errors found and corrected content
        """
        if not self._initialized:
            await self.initialize()

        prompt = f"""Proofread this content and fix all errors:

{content}

Find and fix:
- Spelling errors
- Grammar mistakes
- Punctuation issues
- Typos
- Formatting inconsistencies

Return JSON:
{{
    "corrected_content": "fixed content",
    "errors_found": [
        {{"type": "error type", "original": "...", "fixed": "...", "location": "paragraph X"}}
    ],
    "error_count": number
}}

Return ONLY JSON."""

        try:
            response = self.anthropic.messages.create(
                model=self.data.get('model', 'claude-sonnet-4-20250514'),
                max_tokens=8000,
                temperature=0.1,  # Very low for proofreading
                messages=[{"role": "user", "content": prompt}]
            )

            return self._extract_json(response.content[0].text)

        except Exception as e:
            logger.error(f"Proofreading failed: {e}")
            raise

    def _extract_json(self, text: str) -> Dict:
        """Extract JSON from response"""
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0].strip()
        elif '```' in text:
            text = text.split('```')[1].split('```')[0].strip()

        return json.loads(text)
