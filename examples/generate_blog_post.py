#!/usr/bin/env python3
"""
Example: Generate AI-powered blog post
Demonstrates complete blog post creation workflow
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.postgres_db import init_db, close_db
from agents.blog import BlogWriterAgent, BlogSEOAgent, BlogImageAgent, BlogSocialAgent
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Generate complete blog post with AI"""
    print("=" * 60)
    print("AI Blog Post Generation Example")
    print("=" * 60 + "\n")

    # Get topic from user
    topic = input("Enter blog post topic (or press Enter for default): ").strip()
    if not topic:
        topic = "Introduction to AI Agents and Automation"

    print(f"\nGenerating blog post about: {topic}\n")

    try:
        # Initialize database
        db = await init_db()
        logger.info("✓ Connected to database")

        # Create temporary agents (in production, these would be persistent)
        writer = BlogWriterAgent("temp-writer", db)
        seo = BlogSEOAgent("temp-seo", db)
        image = BlogImageAgent("temp-image", db)
        social = BlogSocialAgent("temp-social", db)

        # Step 1: Generate blog post
        print("Step 1: Generating content with Writer Agent...")
        post_data = await writer.write_blog_post(
            topic=topic,
            category='tutorial',
            style='professional',
            target_length=1500,
            organization_id='demo'
        )

        print(f"✓ Generated: {post_data['title']}")
        print(f"  Word count: {post_data['word_count']}")
        print(f"  Reading time: {post_data['reading_time']} minutes")
        print(f"  Tags: {', '.join(post_data['suggested_tags'])}")

        # Step 2: SEO Optimization
        print("\nStep 2: Optimizing for SEO...")
        seo_data = await seo.optimize_for_seo(
            title=post_data['title'],
            content=post_data['content'],
            target_keywords=post_data['suggested_tags']
        )

        print(f"✓ SEO Score: {seo_data['seo_score']}/100")
        print(f"  Optimized title: {seo_data['optimized_title']}")
        print(f"  Meta description: {seo_data['meta_description'][:80]}...")

        # Step 3: Generate image prompt
        print("\nStep 3: Generating cover image concept...")
        image_data = await image.generate_cover_image_prompt(
            post_title=post_data['title'],
            post_content=post_data['content']
        )

        print(f"✓ Image prompt: {image_data['image_prompt'][:100]}...")
        print(f"  Alt text: {image_data['alt_text']}")
        print(f"  Colors: {', '.join(image_data['color_palette'])}")

        # Step 4: Create social media posts
        print("\nStep 4: Creating social media posts...")
        social_posts = await social.create_social_posts(
            blog_post=post_data,
            platforms=['twitter', 'linkedin']
        )

        print(f"✓ Created posts for {len(social_posts)} platforms")
        for platform, post in social_posts.items():
            print(f"  {platform.capitalize()}: {post['post_text'][:60]}...")

        # Show final summary
        print("\n" + "=" * 60)
        print("GENERATION COMPLETE!")
        print("=" * 60)

        print(f"\n📝 Blog Post: {post_data['title']}")
        print(f"   Length: {post_data['word_count']} words")
        print(f"   SEO Score: {seo_data['seo_score']}/100")
        print(f"   Tags: {', '.join(post_data['suggested_tags'])}")

        print(f"\n🖼️  Cover Image:")
        print(f"   Prompt: {image_data['image_prompt'][:80]}...")

        print(f"\n📱 Social Posts:")
        for platform in social_posts:
            print(f"   {platform.capitalize()}: Ready")

        print(f"\n💾 Content Preview:")
        print("-" * 60)
        print(post_data['content'][:500])
        print("...")
        print("-" * 60)

        # Ask if user wants to save
        save = input("\nSave to database? (y/n): ").strip().lower()

        if save == 'y':
            # In production, you would save to blog_posts table here
            print("\n✓ Post would be saved to database")
            print("  (Database save not implemented in this example)")

        print("\n" + "=" * 60)
        print("Example completed successfully!")
        print("=" * 60 + "\n")

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await close_db()


if __name__ == '__main__':
    asyncio.run(main())
