-- Blog Platform Schema
-- Version: 1.0.0
-- Description: Complete blog platform with AI-powered content creation

-- ============================================
-- 1. BLOG CATEGORIES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS blog_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    color VARCHAR(7), -- Hex color code for UI
    icon VARCHAR(50), -- Icon name or emoji
    parent_category_id UUID REFERENCES blog_categories(id) ON DELETE SET NULL,

    -- SEO
    meta_title VARCHAR(255),
    meta_description TEXT,

    -- Stats
    post_count INTEGER DEFAULT 0 NOT NULL,
    view_count INTEGER DEFAULT 0 NOT NULL,

    -- Display order
    display_order INTEGER DEFAULT 0,
    is_featured BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true NOT NULL,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_blog_categories_slug ON blog_categories(slug);
CREATE INDEX idx_blog_categories_parent ON blog_categories(parent_category_id);
CREATE INDEX idx_blog_categories_active ON blog_categories(is_active) WHERE is_active = true;
CREATE INDEX idx_blog_categories_featured ON blog_categories(is_featured) WHERE is_featured = true;
CREATE INDEX idx_blog_categories_order ON blog_categories(display_order);

-- ============================================
-- 2. BLOG AUTHORS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS blog_authors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255),
    bio TEXT,
    avatar_url TEXT,

    -- Social links
    twitter_handle VARCHAR(100),
    linkedin_url TEXT,
    github_url TEXT,
    website_url TEXT,

    -- Stats
    post_count INTEGER DEFAULT 0 NOT NULL,
    total_views INTEGER DEFAULT 0 NOT NULL,
    total_likes INTEGER DEFAULT 0 NOT NULL,

    -- AI Settings
    writing_style VARCHAR(100), -- professional, casual, technical, creative
    default_tone VARCHAR(100), -- informative, persuasive, entertaining
    ai_assistance_enabled BOOLEAN DEFAULT true,

    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_blog_authors_user ON blog_authors(user_id);
CREATE INDEX idx_blog_authors_slug ON blog_authors(slug);
CREATE INDEX idx_blog_authors_active ON blog_authors(is_active) WHERE is_active = true;

-- ============================================
-- 3. BLOG POSTS TABLE (Main)
-- ============================================
CREATE TABLE IF NOT EXISTS blog_posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    author_id UUID REFERENCES blog_authors(id) ON DELETE SET NULL NOT NULL,
    category_id UUID REFERENCES blog_categories(id) ON DELETE SET NULL,

    -- Content
    title VARCHAR(500) NOT NULL,
    slug VARCHAR(500) UNIQUE NOT NULL,
    excerpt TEXT,
    content TEXT NOT NULL, -- Markdown format
    content_html TEXT, -- Rendered HTML (cached)

    -- Media
    cover_image_url TEXT,
    cover_image_alt TEXT,
    cover_image_caption TEXT,

    -- SEO
    meta_title VARCHAR(255),
    meta_description TEXT,
    meta_keywords TEXT[],
    canonical_url TEXT,
    seo_score INTEGER DEFAULT 0 CHECK (seo_score >= 0 AND seo_score <= 100),

    -- Publishing
    status VARCHAR(50) DEFAULT 'draft' NOT NULL, -- draft, review, scheduled, published, archived
    published_at TIMESTAMP WITH TIME ZONE,
    scheduled_for TIMESTAMP WITH TIME ZONE,

    -- Engagement metrics
    view_count INTEGER DEFAULT 0 NOT NULL,
    like_count INTEGER DEFAULT 0 NOT NULL,
    comment_count INTEGER DEFAULT 0 NOT NULL,
    share_count INTEGER DEFAULT 0 NOT NULL,
    reading_time_minutes INTEGER,

    -- AI metadata
    ai_generated BOOLEAN DEFAULT false,
    ai_assisted BOOLEAN DEFAULT false,
    ai_model_used VARCHAR(100),
    ai_generation_prompt TEXT,
    ai_improvement_applied BOOLEAN DEFAULT false,

    -- Features
    is_featured BOOLEAN DEFAULT false,
    is_pinned BOOLEAN DEFAULT false,
    allow_comments BOOLEAN DEFAULT true,
    tags TEXT[],

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    last_edited_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_blog_posts_author ON blog_posts(author_id);
CREATE INDEX idx_blog_posts_category ON blog_posts(category_id);
CREATE INDEX idx_blog_posts_slug ON blog_posts(slug);
CREATE INDEX idx_blog_posts_status ON blog_posts(status);
CREATE INDEX idx_blog_posts_published ON blog_posts(published_at DESC) WHERE status = 'published';
CREATE INDEX idx_blog_posts_featured ON blog_posts(is_featured) WHERE is_featured = true;
CREATE INDEX idx_blog_posts_tags ON blog_posts USING GIN(tags);
CREATE INDEX idx_blog_posts_views ON blog_posts(view_count DESC);
CREATE INDEX idx_blog_posts_created ON blog_posts(created_at DESC);

-- Full-text search index
CREATE INDEX idx_blog_posts_search ON blog_posts USING GIN(
    to_tsvector('english', COALESCE(title, '') || ' ' || COALESCE(excerpt, '') || ' ' || COALESCE(content, ''))
);

-- ============================================
-- 4. BLOG POST VERSIONS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS blog_post_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id UUID REFERENCES blog_posts(id) ON DELETE CASCADE NOT NULL,
    version_number INTEGER NOT NULL,

    -- Content snapshot
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    excerpt TEXT,

    -- Metadata
    changed_by UUID REFERENCES blog_authors(id) ON DELETE SET NULL,
    change_summary TEXT,
    changes_json JSONB, -- Detailed diff of changes

    -- AI involvement
    ai_changes_applied BOOLEAN DEFAULT false,
    ai_improvement_type VARCHAR(100), -- grammar, style, seo, structure, etc.

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

    UNIQUE(post_id, version_number)
);

CREATE INDEX idx_post_versions_post ON blog_post_versions(post_id);
CREATE INDEX idx_post_versions_created ON blog_post_versions(created_at DESC);

-- ============================================
-- 5. BLOG COMMENTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS blog_comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id UUID REFERENCES blog_posts(id) ON DELETE CASCADE NOT NULL,
    parent_comment_id UUID REFERENCES blog_comments(id) ON DELETE CASCADE,

    -- Author info
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    author_name VARCHAR(255) NOT NULL,
    author_email VARCHAR(255),
    author_url TEXT,
    author_ip INET,

    -- Content
    content TEXT NOT NULL,
    content_html TEXT,

    -- Moderation
    status VARCHAR(50) DEFAULT 'pending' NOT NULL, -- pending, approved, spam, deleted
    spam_score FLOAT DEFAULT 0,
    moderated_by UUID REFERENCES blog_authors(id) ON DELETE SET NULL,
    moderated_at TIMESTAMP WITH TIME ZONE,
    moderation_reason TEXT,

    -- Engagement
    like_count INTEGER DEFAULT 0 NOT NULL,
    reply_count INTEGER DEFAULT 0 NOT NULL,

    -- AI moderation
    ai_moderated BOOLEAN DEFAULT false,
    ai_sentiment VARCHAR(50), -- positive, negative, neutral
    ai_toxicity_score FLOAT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_blog_comments_post ON blog_comments(post_id);
CREATE INDEX idx_blog_comments_parent ON blog_comments(parent_comment_id);
CREATE INDEX idx_blog_comments_user ON blog_comments(user_id);
CREATE INDEX idx_blog_comments_status ON blog_comments(status);
CREATE INDEX idx_blog_comments_created ON blog_comments(created_at DESC);

-- ============================================
-- 6. BLOG SUBSCRIPTIONS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS blog_subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255),

    -- Subscription preferences
    subscription_type VARCHAR(50) DEFAULT 'all' NOT NULL, -- all, weekly, category, author
    category_id UUID REFERENCES blog_categories(id) ON DELETE CASCADE,
    author_id UUID REFERENCES blog_authors(id) ON DELETE CASCADE,
    frequency VARCHAR(50) DEFAULT 'immediate', -- immediate, daily, weekly, monthly

    -- Status
    status VARCHAR(50) DEFAULT 'pending' NOT NULL, -- pending, active, unsubscribed, bounced
    confirmed_at TIMESTAMP WITH TIME ZONE,
    unsubscribed_at TIMESTAMP WITH TIME ZONE,

    -- Verification
    confirmation_token VARCHAR(255) UNIQUE,
    confirmation_sent_at TIMESTAMP WITH TIME ZONE,
    unsubscribe_token VARCHAR(255) UNIQUE,

    -- Engagement
    emails_sent INTEGER DEFAULT 0 NOT NULL,
    emails_opened INTEGER DEFAULT 0 NOT NULL,
    links_clicked INTEGER DEFAULT 0 NOT NULL,
    last_email_sent_at TIMESTAMP WITH TIME ZONE,

    -- Source tracking
    source VARCHAR(100), -- popup, footer, post, landing_page
    referrer TEXT,
    utm_source VARCHAR(100),
    utm_medium VARCHAR(100),
    utm_campaign VARCHAR(100),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_blog_subscriptions_email ON blog_subscriptions(email);
CREATE INDEX idx_blog_subscriptions_status ON blog_subscriptions(status);
CREATE INDEX idx_blog_subscriptions_type ON blog_subscriptions(subscription_type);
CREATE INDEX idx_blog_subscriptions_category ON blog_subscriptions(category_id);
CREATE INDEX idx_blog_subscriptions_author ON blog_subscriptions(author_id);
CREATE INDEX idx_blog_subscriptions_token ON blog_subscriptions(confirmation_token);

-- ============================================
-- 7. BLOG SOCIAL SHARES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS blog_social_shares (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id UUID REFERENCES blog_posts(id) ON DELETE CASCADE NOT NULL,

    -- Platform
    platform VARCHAR(50) NOT NULL, -- twitter, linkedin, facebook, reddit, etc.
    share_url TEXT,
    share_text TEXT,

    -- Generated by AI
    ai_generated BOOLEAN DEFAULT false,
    ai_optimized_text TEXT,
    hashtags TEXT[],

    -- Tracking
    shared_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    shared_by UUID REFERENCES blog_authors(id) ON DELETE SET NULL,

    -- Engagement (if trackable)
    clicks INTEGER DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    engagement_rate FLOAT,

    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_social_shares_post ON blog_social_shares(post_id);
CREATE INDEX idx_social_shares_platform ON blog_social_shares(platform);
CREATE INDEX idx_social_shares_date ON blog_social_shares(shared_at DESC);

-- ============================================
-- 8. BLOG ANALYTICS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS blog_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id UUID REFERENCES blog_posts(id) ON DELETE CASCADE,
    category_id UUID REFERENCES blog_categories(id) ON DELETE CASCADE,
    author_id UUID REFERENCES blog_authors(id) ON DELETE CASCADE,

    -- Event tracking
    event_type VARCHAR(50) NOT NULL, -- view, like, share, comment, click
    event_date DATE NOT NULL,
    event_hour INTEGER CHECK (event_hour >= 0 AND event_hour <= 23),

    -- User context
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    session_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    device_type VARCHAR(50), -- desktop, mobile, tablet
    browser VARCHAR(100),
    os VARCHAR(100),

    -- Location (if available)
    country_code VARCHAR(2),
    city VARCHAR(255),
    timezone VARCHAR(100),

    -- Traffic source
    referrer TEXT,
    utm_source VARCHAR(100),
    utm_medium VARCHAR(100),
    utm_campaign VARCHAR(100),
    utm_content VARCHAR(100),
    utm_term VARCHAR(100),

    -- Behavior
    time_on_page_seconds INTEGER,
    scroll_depth_percent INTEGER CHECK (scroll_depth_percent >= 0 AND scroll_depth_percent <= 100),
    bounce BOOLEAN DEFAULT false,

    -- Aggregation helper
    count INTEGER DEFAULT 1,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

    -- Prevent duplicate entries for unique views
    UNIQUE(post_id, user_id, session_id, event_type, event_date)
);

CREATE INDEX idx_blog_analytics_post ON blog_analytics(post_id);
CREATE INDEX idx_blog_analytics_category ON blog_analytics(category_id);
CREATE INDEX idx_blog_analytics_author ON blog_analytics(author_id);
CREATE INDEX idx_blog_analytics_event ON blog_analytics(event_type, event_date DESC);
CREATE INDEX idx_blog_analytics_date ON blog_analytics(event_date DESC);
CREATE INDEX idx_blog_analytics_source ON blog_analytics(utm_source, utm_medium);

-- ============================================
-- TRIGGERS
-- ============================================

CREATE TRIGGER update_blog_categories_updated_at
    BEFORE UPDATE ON blog_categories
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_blog_authors_updated_at
    BEFORE UPDATE ON blog_authors
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_blog_posts_updated_at
    BEFORE UPDATE ON blog_posts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_blog_comments_updated_at
    BEFORE UPDATE ON blog_comments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_blog_subscriptions_updated_at
    BEFORE UPDATE ON blog_subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- HELPER FUNCTIONS
-- ============================================

-- Update post metrics
CREATE OR REPLACE FUNCTION update_post_metrics(p_post_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE blog_posts
    SET
        comment_count = (
            SELECT COUNT(*)
            FROM blog_comments
            WHERE post_id = p_post_id AND status = 'approved'
        ),
        share_count = (
            SELECT COUNT(*)
            FROM blog_social_shares
            WHERE post_id = p_post_id
        ),
        view_count = (
            SELECT COALESCE(SUM(count), 0)
            FROM blog_analytics
            WHERE post_id = p_post_id AND event_type = 'view'
        ),
        updated_at = NOW()
    WHERE id = p_post_id;
END;
$$ LANGUAGE plpgsql;

-- Update category post count
CREATE OR REPLACE FUNCTION update_category_post_count(p_category_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE blog_categories
    SET
        post_count = (
            SELECT COUNT(*)
            FROM blog_posts
            WHERE category_id = p_category_id AND status = 'published'
        ),
        updated_at = NOW()
    WHERE id = p_category_id;
END;
$$ LANGUAGE plpgsql;

-- Update author metrics
CREATE OR REPLACE FUNCTION update_author_metrics(p_author_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE blog_authors
    SET
        post_count = (
            SELECT COUNT(*)
            FROM blog_posts
            WHERE author_id = p_author_id AND status = 'published'
        ),
        total_views = (
            SELECT COALESCE(SUM(view_count), 0)
            FROM blog_posts
            WHERE author_id = p_author_id AND status = 'published'
        ),
        total_likes = (
            SELECT COALESCE(SUM(like_count), 0)
            FROM blog_posts
            WHERE author_id = p_author_id AND status = 'published'
        ),
        updated_at = NOW()
    WHERE id = p_author_id;
END;
$$ LANGUAGE plpgsql;

-- Calculate reading time based on word count
CREATE OR REPLACE FUNCTION calculate_reading_time(p_content TEXT)
RETURNS INTEGER AS $$
DECLARE
    word_count INTEGER;
    words_per_minute INTEGER := 200;
BEGIN
    -- Count words (simplified)
    word_count := array_length(regexp_split_to_array(p_content, '\s+'), 1);
    RETURN GREATEST(1, CEIL(word_count::FLOAT / words_per_minute));
END;
$$ LANGUAGE plpgsql;

-- Auto-calculate reading time on insert/update
CREATE OR REPLACE FUNCTION auto_calculate_reading_time()
RETURNS TRIGGER AS $$
BEGIN
    NEW.reading_time_minutes := calculate_reading_time(NEW.content);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER blog_posts_reading_time
    BEFORE INSERT OR UPDATE OF content ON blog_posts
    FOR EACH ROW
    EXECUTE FUNCTION auto_calculate_reading_time();

-- ============================================
-- VIEWS
-- ============================================

-- Published posts with full details
CREATE OR REPLACE VIEW published_posts AS
SELECT
    p.*,
    a.name as author_name,
    a.slug as author_slug,
    a.avatar_url as author_avatar,
    c.name as category_name,
    c.slug as category_slug,
    c.color as category_color
FROM blog_posts p
LEFT JOIN blog_authors a ON p.author_id = a.id
LEFT JOIN blog_categories c ON p.category_id = c.id
WHERE p.status = 'published'
  AND p.published_at <= NOW()
  AND p.deleted_at IS NULL
ORDER BY p.published_at DESC;

-- Post analytics summary
CREATE OR REPLACE VIEW post_analytics_summary AS
SELECT
    p.id,
    p.title,
    p.slug,
    p.status,
    p.published_at,
    p.view_count,
    p.like_count,
    p.comment_count,
    p.share_count,
    COALESCE(
        (p.like_count::FLOAT + p.comment_count * 2 + p.share_count * 3) /
        NULLIF(p.view_count, 0) * 100,
        0
    )::DECIMAL(5,2) as engagement_rate,
    (
        SELECT COUNT(DISTINCT DATE(created_at))
        FROM blog_analytics
        WHERE post_id = p.id AND event_type = 'view'
    ) as days_with_views,
    a.name as author_name,
    c.name as category_name
FROM blog_posts p
LEFT JOIN blog_authors a ON p.author_id = a.id
LEFT JOIN blog_categories c ON p.category_id = c.id
WHERE p.status = 'published';

-- ============================================
-- SEED DATA
-- ============================================

-- Default category
INSERT INTO blog_categories (name, slug, description, color, is_active)
VALUES
    ('General', 'general', 'General articles and updates', '#3B82F6', true),
    ('Tutorial', 'tutorial', 'Step-by-step guides and tutorials', '#10B981', true),
    ('News', 'news', 'Latest news and announcements', '#F59E0B', true),
    ('Technical', 'technical', 'Technical deep dives and analysis', '#8B5CF6', true)
ON CONFLICT (slug) DO NOTHING;

-- ============================================
-- COMMENTS
-- ============================================

COMMENT ON TABLE blog_categories IS 'Blog post categories with hierarchical support';
COMMENT ON TABLE blog_authors IS 'Blog authors with AI writing preferences';
COMMENT ON TABLE blog_posts IS 'Main blog posts table with AI generation support';
COMMENT ON TABLE blog_post_versions IS 'Version history for blog posts';
COMMENT ON TABLE blog_comments IS 'Comments with AI moderation';
COMMENT ON TABLE blog_subscriptions IS 'Newsletter subscriptions and preferences';
COMMENT ON TABLE blog_social_shares IS 'Social media shares with AI-optimized content';
COMMENT ON TABLE blog_analytics IS 'Detailed analytics and tracking';

-- Migration complete
SELECT 'Blog Platform schema created successfully' AS status;
