"""
Blog Platform API Router
Complete REST API for blog operations
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import sys
from pathlib import Path

# Add agents to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.postgres_db import get_db
from agents.blog import BlogWriterAgent, BlogEditorAgent, BlogSEOAgent, BlogImageAgent, BlogSocialAgent
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/blog", tags=["blog"])

# ============================================
# Pydantic Models
# ============================================

class PostCreate(BaseModel):
    title: str
    content: str
    excerpt: Optional[str] = None
    category_id: Optional[str] = None
    tags: List[str] = []
    use_ai: bool = False
    ai_improve: bool = False
    auto_seo: bool = False

class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    category_id: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None

class AIGenerateRequest(BaseModel):
    topic: str
    category: str = 'general'
    style: str = 'professional'
    target_length: int = 1500
    auto_seo: bool = True
    generate_image: bool = False

class CategoryCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    color: Optional[str] = None

# ============================================
# Helper Functions
# ============================================

async def get_author_id(user_id: str, db) -> str:
    """Get or create blog author for user"""
    author = await db.fetchrow("""
        SELECT id FROM blog_authors WHERE user_id = $1
    """, user_id)

    if author:
        return str(author['id'])

    # Create author
    author_id = await db.fetchval("""
        INSERT INTO blog_authors (user_id, name, slug, email)
        VALUES ($1, $2, $3, $4)
        RETURNING id
    """, user_id, f"User {user_id}", f"user-{user_id}", f"{user_id}@example.com")

    return str(author_id)

def slugify(text: str) -> str:
    """Simple slugify function"""
    import re
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

# ============================================
# Posts Endpoints
# ============================================

@router.get("/posts")
async def list_posts(
    category: Optional[str] = None,
    author: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    status: str = 'published',
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50)
):
    """List blog posts with filtering and pagination"""
    db = get_db()
    await db.connect()

    query = """
        SELECT
            p.*,
            c.name as category_name,
            c.slug as category_slug,
            a.name as author_name,
            a.avatar_url as author_avatar
        FROM blog_posts p
        LEFT JOIN blog_categories c ON p.category_id = c.id
        LEFT JOIN blog_authors a ON p.author_id = a.id
        WHERE p.status = $1
    """

    params = [status]
    param_count = 1

    if category:
        param_count += 1
        query += f" AND c.slug = ${param_count}"
        params.append(category)

    if author:
        param_count += 1
        query += f" AND a.slug = ${param_count}"
        params.append(author)

    if tag:
        param_count += 1
        query += f" AND ${param_count} = ANY(p.tags)"
        params.append(tag)

    if search:
        param_count += 1
        query += f" AND (p.title ILIKE ${param_count} OR p.content ILIKE ${param_count})"
        params.append(f"%{search}%")

    # Get total count - Use CTE to safely count with parameterized query
    count_query = f"""
        WITH filtered_posts AS (
            {query}
        )
        SELECT COUNT(*) FROM filtered_posts
    """
    total = await db.fetchval(count_query, *params)

    # Add pagination
    query += f" ORDER BY p.published_at DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
    params.extend([per_page, (page - 1) * per_page])

    posts = await db.fetch(query, *params)

    return {
        'posts': posts,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page if total > 0 else 0
        }
    }

@router.get("/posts/{slug}")
async def get_post(slug: str):
    """Get single blog post by slug"""
    db = get_db()
    await db.connect()

    post = await db.fetchrow("""
        SELECT
            p.*,
            c.name as category_name,
            c.slug as category_slug,
            a.name as author_name,
            a.bio as author_bio,
            a.avatar_url as author_avatar
        FROM blog_posts p
        LEFT JOIN blog_categories c ON p.category_id = c.id
        LEFT JOIN blog_authors a ON p.author_id = a.id
        WHERE p.slug = $1
    """, slug)

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Increment view count
    await db.execute("""
        UPDATE blog_posts
        SET view_count = view_count + 1, unique_views = unique_views + 1
        WHERE id = $1
    """, post['id'])

    # Track analytics
    await db.execute("""
        INSERT INTO blog_analytics (post_id, event_type, is_unique)
        VALUES ($1, 'view', TRUE)
    """, post['id'])

    return post

@router.post("/posts")
async def create_post(
    post_data: PostCreate,
    user_id: str = "demo-user"  # TODO: Get from auth
):
    """Create new blog post"""
    db = get_db()
    await db.connect()

    author_id = await get_author_id(user_id, db)
    organization_id = "default"  # TODO: Get from user

    # AI enhancement if requested
    title = post_data.title
    content = post_data.content
    excerpt = post_data.excerpt
    tags = post_data.tags
    cover_image_url = None

    if post_data.use_ai or post_data.ai_improve:
        logger.info("Using AI to enhance post...")

        # Initialize Writer Agent
        # TODO: Get agent_id from database or create on-the-fly
        writer_agent = BlogWriterAgent(
            agent_id="temp-writer",
            db=db
        )

        if post_data.use_ai:
            # Generate from scratch
            result = await writer_agent.write_blog_post(
                topic=post_data.title,
                category=post_data.category_id or 'general',
                target_length=len(content.split()) if content else 1500,
                organization_id=organization_id
            )

            title = result.get('title', title)
            content = result.get('content', content)
            excerpt = result.get('excerpt', excerpt)
            tags = result.get('suggested_tags', tags)

        # SEO optimization if requested
        if post_data.auto_seo:
            seo_agent = BlogSEOAgent(agent_id="temp-seo", db=db)
            seo_data = await seo_agent.optimize_for_seo(title, content, tags)

            title = seo_data.get('optimized_title', title)
            excerpt = seo_data.get('meta_description', excerpt)
            tags = seo_data.get('meta_keywords', tags)

    # Generate slug
    slug = slugify(title)

    # Calculate reading time
    word_count = len(content.split())
    reading_time = max(1, word_count // 200)

    # Create post
    post_id = await db.fetchval("""
        INSERT INTO blog_posts (
            organization_id, title, slug, excerpt, content,
            category_id, author_id, tags, reading_time_minutes,
            word_count, cover_image_url, ai_generated, status
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, 'draft')
        RETURNING id
    """,
    organization_id, title, slug, excerpt, content,
    post_data.category_id, author_id, tags, reading_time,
    word_count, cover_image_url, post_data.use_ai
    )

    return {'post_id': str(post_id), 'slug': slug, 'status': 'draft'}

@router.put("/posts/{post_id}")
async def update_post(post_id: str, updates: PostUpdate):
    """Update blog post"""
    db = get_db()
    await db.connect()

    # Build dynamic update query
    set_clauses = []
    params = [post_id]
    param_count = 1

    for field, value in updates.dict(exclude_unset=True).items():
        if value is not None:
            param_count += 1
            set_clauses.append(f"{field} = ${param_count}")
            params.append(value)

    if not set_clauses:
        return {'message': 'No updates provided'}

    set_clauses.append("updated_at = NOW()")

    query = f"""
        UPDATE blog_posts
        SET {', '.join(set_clauses)}
        WHERE id = $1
    """

    await db.execute(query, *params)

    return {'message': 'Post updated successfully'}

@router.put("/posts/{post_id}/publish")
async def publish_post(
    post_id: str,
    publish_to_social: bool = False
):
    """Publish blog post"""
    db = get_db()
    await db.connect()

    await db.execute("""
        UPDATE blog_posts
        SET status = 'published', published_at = NOW()
        WHERE id = $1
    """, post_id)

    # Generate social posts if requested
    social_posts = None
    if publish_to_social:
        post = await db.fetchrow("SELECT * FROM blog_posts WHERE id = $1", post_id)

        social_agent = BlogSocialAgent(agent_id="temp-social", db=db)
        social_posts = await social_agent.create_social_posts(
            blog_post=dict(post),
            platforms=['twitter', 'linkedin']
        )

    return {
        'status': 'published',
        'social_posts': social_posts
    }

# ============================================
# AI Content Generation Endpoints
# ============================================

@router.post("/ai/generate")
async def ai_generate_post(request: AIGenerateRequest):
    """Generate complete blog post using AI"""
    db = get_db()
    await db.connect()

    logger.info(f"AI generating post about: {request.topic}")

    # Initialize agents
    writer = BlogWriterAgent(agent_id="temp-writer", db=db)

    # Generate content
    post_data = await writer.write_blog_post(
        topic=request.topic,
        category=request.category,
        style=request.style,
        target_length=request.target_length,
        organization_id="default"
    )

    # SEO optimization
    if request.auto_seo:
        seo = BlogSEOAgent(agent_id="temp-seo", db=db)
        seo_data = await seo.optimize_for_seo(
            post_data['title'],
            post_data['content'],
            post_data.get('suggested_tags', [])
        )

        post_data['seo'] = seo_data

    # Generate image prompt
    if request.generate_image:
        image = BlogImageAgent(agent_id="temp-image", db=db)
        image_data = await image.generate_cover_image_prompt(
            post_data['title'],
            post_data['content']
        )

        post_data['image'] = image_data

    return post_data

@router.post("/ai/improve")
async def ai_improve_content(
    content: str,
    improvement_type: str = 'general'
):
    """Improve existing content using AI"""
    db = get_db()
    await db.connect()

    editor = BlogEditorAgent(agent_id="temp-editor", db=db)
    result = await editor.edit_post(content)

    return result

@router.post("/ai/seo-optimize")
async def ai_seo_optimize(
    title: str,
    content: str,
    keywords: List[str] = []
):
    """SEO optimize content"""
    db = get_db()
    await db.connect()

    seo = BlogSEOAgent(agent_id="temp-seo", db=db)
    result = await seo.optimize_for_seo(title, content, keywords)

    return result

# ============================================
# Categories Endpoints
# ============================================

@router.get("/categories")
async def list_categories():
    """List all blog categories"""
    db = get_db()
    await db.connect()

    categories = await db.fetch("""
        SELECT c.*, COUNT(p.id) as post_count
        FROM blog_categories c
        LEFT JOIN blog_posts p ON c.id = p.category_id AND p.status = 'published'
        GROUP BY c.id
        ORDER BY c.display_order, c.name
    """)

    return {'categories': categories}

@router.post("/categories")
async def create_category(category: CategoryCreate):
    """Create blog category"""
    db = get_db()
    await db.connect()

    category_id = await db.fetchval("""
        INSERT INTO blog_categories (name, slug, description, color)
        VALUES ($1, $2, $3, $4)
        RETURNING id
    """, category.name, category.slug, category.description, category.color)

    return {'category_id': str(category_id)}

# ============================================
# Analytics Endpoints
# ============================================

@router.get("/analytics/overview")
async def get_analytics_overview():
    """Get blog analytics overview"""
    db = get_db()
    await db.connect()

    stats = await db.fetchrow("""
        SELECT
            COUNT(*) as total_posts,
            COUNT(*) FILTER (WHERE status = 'published') as published_posts,
            SUM(view_count) as total_views,
            SUM(like_count) as total_likes,
            SUM(comment_count) as total_comments
        FROM blog_posts
    """)

    return dict(stats)

@router.get("/posts/{post_id}/analytics")
async def get_post_analytics(post_id: str):
    """Get detailed analytics for a post"""
    db = get_db()
    await db.connect()

    # Views by day (last 30 days)
    views_by_day = await db.fetch("""
        SELECT
            DATE(timestamp) as date,
            COUNT(*) as views
        FROM blog_analytics
        WHERE post_id = $1 AND event_type = 'view'
        AND timestamp > NOW() - INTERVAL '30 days'
        GROUP BY DATE(timestamp)
        ORDER BY date DESC
    """, post_id)

    # Device breakdown
    devices = await db.fetch("""
        SELECT device_type, COUNT(*) as count
        FROM blog_analytics
        WHERE post_id = $1 AND event_type = 'view'
        GROUP BY device_type
    """, post_id)

    return {
        'views_by_day': views_by_day,
        'devices': devices
    }
