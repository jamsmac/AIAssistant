-- ============================================
-- BLOG PLATFORM SCHEMA
-- AIAssistant v4.5 - AI-Powered Content Platform
-- ============================================

-- Enable UUID extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- 1. BLOG CATEGORIES
-- ============================================
CREATE TABLE IF NOT EXISTS blog_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Identity
    name VARCHAR(100) UNIQUE NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,

    -- Styling
    color VARCHAR(7),  -- hex color like #FF5733
    icon VARCHAR(50),  -- icon name/emoji

    -- SEO
    meta_title VARCHAR(255),
    meta_description TEXT,

    -- Stats
    post_count INTEGER DEFAULT 0,
    view_count INTEGER DEFAULT 0,

    -- Display
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_categories_slug ON blog_categories(slug);
CREATE INDEX IF NOT EXISTS idx_categories_active ON blog_categories(is_active);
CREATE INDEX IF NOT EXISTS idx_categories_order ON blog_categories(display_order);

-- ============================================
-- 2. BLOG AUTHORS
-- ============================================
CREATE TABLE IF NOT EXISTS blog_authors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Identity (link to existing users table if needed)
    user_id VARCHAR(255),  -- Link to main users table
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,

    -- Profile
    bio TEXT,
    avatar_url VARCHAR(500),

    -- Contact & Social
    email VARCHAR(255),
    twitter VARCHAR(100),
    linkedin VARCHAR(100),
    github VARCHAR(100),
    website VARCHAR(500),

    -- Stats
    post_count INTEGER DEFAULT 0,
    total_views INTEGER DEFAULT 0,
    total_likes INTEGER DEFAULT 0,
    followers INTEGER DEFAULT 0,

    -- Settings
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    email_notifications BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_authors_slug ON blog_authors(slug);
CREATE INDEX IF NOT EXISTS idx_authors_user ON blog_authors(user_id);
CREATE INDEX IF NOT EXISTS idx_authors_active ON blog_authors(is_active);
CREATE INDEX IF NOT EXISTS idx_authors_verified ON blog_authors(is_verified);

-- ============================================
-- 3. BLOG POSTS
-- ============================================
CREATE TABLE IF NOT EXISTS blog_posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id VARCHAR(255),  -- For multi-tenant

    -- Content
    title VARCHAR(500) NOT NULL,
    slug VARCHAR(500) UNIQUE NOT NULL,
    excerpt TEXT,  -- Short description
    content TEXT NOT NULL,  -- Full Markdown/HTML content
    content_format VARCHAR(20) DEFAULT 'markdown',  -- 'markdown', 'html', 'rich'

    -- Media
    cover_image_url VARCHAR(500),
    cover_image_alt TEXT,
    images JSONB DEFAULT '[]'::jsonb,  -- Additional images with metadata

    -- Categorization
    category_id UUID REFERENCES blog_categories(id) ON DELETE SET NULL,
    tags TEXT[],  -- Array of tags

    -- Author
    author_id UUID REFERENCES blog_authors(id) ON DELETE SET NULL,
    co_authors UUID[],  -- Multiple authors support

    -- Publishing
    status VARCHAR(50) DEFAULT 'draft',
    -- Statuses: 'draft', 'published', 'scheduled', 'archived', 'unlisted'
    published_at TIMESTAMP,
    scheduled_for TIMESTAMP,
    archived_at TIMESTAMP,

    -- SEO
    meta_title VARCHAR(255),
    meta_description TEXT,
    meta_keywords TEXT[],
    og_image_url VARCHAR(500),  -- Open Graph image
    canonical_url VARCHAR(500),  -- Canonical URL for SEO

    -- Engagement
    view_count INTEGER DEFAULT 0,
    unique_views INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    share_count INTEGER DEFAULT 0,
    bookmark_count INTEGER DEFAULT 0,

    -- Reading metrics
    reading_time_minutes INTEGER,
    word_count INTEGER,

    -- Featured
    is_featured BOOLEAN DEFAULT FALSE,
    featured_order INTEGER,
    featured_until TIMESTAMP,

    -- AI Generation (if created by AI)
    ai_generated BOOLEAN DEFAULT FALSE,
    ai_agent_id UUID,  -- Reference to fractal_agents(id)
    generation_prompt TEXT,
    ai_metadata JSONB DEFAULT '{}'::jsonb,

    -- Version control
    version INTEGER DEFAULT 1,
    last_edited_by UUID REFERENCES blog_authors(id),

    -- Settings
    allow_comments BOOLEAN DEFAULT TRUE,
    is_premium BOOLEAN DEFAULT FALSE,  -- Premium content
    requires_auth BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_status CHECK (status IN ('draft', 'published', 'scheduled', 'archived', 'unlisted')),
    CONSTRAINT valid_content_format CHECK (content_format IN ('markdown', 'html', 'rich'))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_posts_org ON blog_posts(organization_id);
CREATE INDEX IF NOT EXISTS idx_posts_slug ON blog_posts(slug);
CREATE INDEX IF NOT EXISTS idx_posts_category ON blog_posts(category_id);
CREATE INDEX IF NOT EXISTS idx_posts_author ON blog_posts(author_id);
CREATE INDEX IF NOT EXISTS idx_posts_status ON blog_posts(status);
CREATE INDEX IF NOT EXISTS idx_posts_published ON blog_posts(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_posts_featured ON blog_posts(is_featured);
CREATE INDEX IF NOT EXISTS idx_posts_tags ON blog_posts USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_posts_created ON blog_posts(created_at DESC);

-- Full-text search index
CREATE INDEX IF NOT EXISTS idx_posts_search ON blog_posts USING GIN(
    to_tsvector('english', title || ' ' || COALESCE(excerpt, '') || ' ' || content)
);

-- ============================================
-- 4. BLOG POST VERSIONS (version history)
-- ============================================
CREATE TABLE IF NOT EXISTS blog_post_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    post_id UUID NOT NULL REFERENCES blog_posts(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,

    -- Snapshot of content
    title VARCHAR(500),
    content TEXT,
    excerpt TEXT,
    tags TEXT[],

    -- Who made changes
    changed_by UUID REFERENCES blog_authors(id),
    change_description TEXT,
    change_type VARCHAR(50),  -- 'created', 'content_update', 'seo_update', etc.

    -- Diff information (optional)
    diff_summary JSONB,

    -- Timestamp
    created_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_post_version UNIQUE(post_id, version)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_versions_post ON blog_post_versions(post_id);
CREATE INDEX IF NOT EXISTS idx_versions_created ON blog_post_versions(created_at DESC);

-- ============================================
-- 5. BLOG COMMENTS
-- ============================================
CREATE TABLE IF NOT EXISTS blog_comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    post_id UUID NOT NULL REFERENCES blog_posts(id) ON DELETE CASCADE,

    -- Author (can be authenticated user or guest)
    user_id VARCHAR(255),  -- Authenticated user
    author_name VARCHAR(255),  -- Guest name
    author_email VARCHAR(255),  -- Guest email
    author_avatar VARCHAR(500),

    -- Content
    content TEXT NOT NULL,
    content_html TEXT,  -- Rendered HTML

    -- Threading (nested comments)
    parent_comment_id UUID REFERENCES blog_comments(id) ON DELETE CASCADE,
    thread_level INTEGER DEFAULT 0,  -- 0 = top-level, 1 = reply, etc.

    -- Moderation
    status VARCHAR(50) DEFAULT 'pending',
    -- Statuses: 'pending', 'approved', 'rejected', 'spam', 'deleted'
    moderated_by UUID REFERENCES blog_authors(id),
    moderated_at TIMESTAMP,
    moderation_reason TEXT,

    -- Engagement
    like_count INTEGER DEFAULT 0,
    reply_count INTEGER DEFAULT 0,

    -- Spam detection
    is_spam BOOLEAN DEFAULT FALSE,
    spam_score FLOAT DEFAULT 0.0,

    -- Technical
    ip_address INET,
    user_agent TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_comment_status CHECK (status IN ('pending', 'approved', 'rejected', 'spam', 'deleted')),
    CONSTRAINT valid_spam_score CHECK (spam_score >= 0 AND spam_score <= 1)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_comments_post ON blog_comments(post_id);
CREATE INDEX IF NOT EXISTS idx_comments_parent ON blog_comments(parent_comment_id);
CREATE INDEX IF NOT EXISTS idx_comments_status ON blog_comments(status);
CREATE INDEX IF NOT EXISTS idx_comments_user ON blog_comments(user_id);
CREATE INDEX IF NOT EXISTS idx_comments_created ON blog_comments(created_at DESC);

-- ============================================
-- 6. BLOG SUBSCRIPTIONS (newsletter)
-- ============================================
CREATE TABLE IF NOT EXISTS blog_subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),

    -- Preferences
    categories UUID[],  -- Which categories to follow
    frequency VARCHAR(50) DEFAULT 'weekly',
    -- Frequencies: 'instant', 'daily', 'weekly', 'monthly'

    -- Status
    status VARCHAR(50) DEFAULT 'active',
    -- Statuses: 'active', 'paused', 'unsubscribed', 'bounced'
    confirmed BOOLEAN DEFAULT FALSE,
    confirmation_token VARCHAR(255) UNIQUE,
    unsubscribe_token VARCHAR(255) UNIQUE,

    -- Tracking
    last_email_sent_at TIMESTAMP,
    open_count INTEGER DEFAULT 0,
    click_count INTEGER DEFAULT 0,
    total_emails_sent INTEGER DEFAULT 0,

    -- Source tracking
    source VARCHAR(100),  -- Where they subscribed from
    referrer VARCHAR(500),
    utm_source VARCHAR(100),
    utm_medium VARCHAR(100),
    utm_campaign VARCHAR(100),

    -- Timestamps
    subscribed_at TIMESTAMP DEFAULT NOW(),
    confirmed_at TIMESTAMP,
    unsubscribed_at TIMESTAMP,
    last_activity_at TIMESTAMP,

    -- Constraints
    CONSTRAINT valid_subscription_status CHECK (status IN ('active', 'paused', 'unsubscribed', 'bounced')),
    CONSTRAINT valid_frequency CHECK (frequency IN ('instant', 'daily', 'weekly', 'monthly'))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_subscriptions_email ON blog_subscriptions(email);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON blog_subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_confirmed ON blog_subscriptions(confirmed);
CREATE INDEX IF NOT EXISTS idx_subscriptions_categories ON blog_subscriptions USING GIN(categories);

-- ============================================
-- 7. BLOG SOCIAL SHARES (tracking)
-- ============================================
CREATE TABLE IF NOT EXISTS blog_social_shares (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    post_id UUID NOT NULL REFERENCES blog_posts(id) ON DELETE CASCADE,

    platform VARCHAR(50) NOT NULL,
    -- Platforms: 'twitter', 'linkedin', 'facebook', 'email', 'copy_link', 'reddit', etc.

    -- User who shared
    user_id VARCHAR(255),

    -- Tracking
    ip_address INET,
    user_agent TEXT,
    referrer VARCHAR(500),

    -- UTM parameters (for tracking clicks back)
    utm_source VARCHAR(100),
    utm_medium VARCHAR(100),
    utm_campaign VARCHAR(100),

    -- Click tracking
    clicks_back INTEGER DEFAULT 0,

    -- Timestamp
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_shares_post ON blog_social_shares(post_id);
CREATE INDEX IF NOT EXISTS idx_shares_platform ON blog_social_shares(platform);
CREATE INDEX IF NOT EXISTS idx_shares_user ON blog_social_shares(user_id);
CREATE INDEX IF NOT EXISTS idx_shares_created ON blog_social_shares(created_at DESC);

-- ============================================
-- 8. BLOG ANALYTICS (detailed tracking)
-- ============================================
CREATE TABLE IF NOT EXISTS blog_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    post_id UUID REFERENCES blog_posts(id) ON DELETE CASCADE,
    category_id UUID REFERENCES blog_categories(id) ON DELETE SET NULL,

    -- Event
    event_type VARCHAR(50) NOT NULL,
    -- Types: 'view', 'like', 'share', 'comment', 'bookmark', 'click', 'scroll', 'time_spent'
    event_value FLOAT,  -- For numeric events

    -- User
    user_id VARCHAR(255),
    session_id VARCHAR(255),
    is_unique BOOLEAN DEFAULT TRUE,

    -- Context
    referrer VARCHAR(500),
    utm_source VARCHAR(100),
    utm_medium VARCHAR(100),
    utm_campaign VARCHAR(100),
    utm_content VARCHAR(100),

    -- Technical
    ip_address INET,
    user_agent TEXT,
    device_type VARCHAR(50),  -- 'desktop', 'mobile', 'tablet'
    browser VARCHAR(50),
    os VARCHAR(50),

    -- Location (can be enriched later)
    country VARCHAR(2),
    city VARCHAR(100),
    latitude FLOAT,
    longitude FLOAT,

    -- Reading behavior
    scroll_depth INTEGER,  -- Percentage scrolled
    time_spent INTEGER,  -- Seconds

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamp
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_analytics_post ON blog_analytics(post_id);
CREATE INDEX IF NOT EXISTS idx_analytics_category ON blog_analytics(category_id);
CREATE INDEX IF NOT EXISTS idx_analytics_event ON blog_analytics(event_type);
CREATE INDEX IF NOT EXISTS idx_analytics_user ON blog_analytics(user_id);
CREATE INDEX IF NOT EXISTS idx_analytics_session ON blog_analytics(session_id);
CREATE INDEX IF NOT EXISTS idx_analytics_timestamp ON blog_analytics(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_analytics_device ON blog_analytics(device_type);
CREATE INDEX IF NOT EXISTS idx_analytics_unique ON blog_analytics(is_unique);

-- Partitioning by time (optional, for large scale)
-- CREATE TABLE blog_analytics_2025_01 PARTITION OF blog_analytics
-- FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

-- ============================================
-- HELPER FUNCTIONS & TRIGGERS
-- ============================================

-- Function to update post counts
CREATE OR REPLACE FUNCTION update_post_counts()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        -- Update category post count
        IF NEW.category_id IS NOT NULL AND NEW.status = 'published' THEN
            UPDATE blog_categories
            SET post_count = post_count + 1
            WHERE id = NEW.category_id;
        END IF;

        -- Update author post count
        IF NEW.author_id IS NOT NULL AND NEW.status = 'published' THEN
            UPDATE blog_authors
            SET post_count = post_count + 1
            WHERE id = NEW.author_id;
        END IF;

    ELSIF TG_OP = 'UPDATE' THEN
        -- Handle status changes
        IF OLD.status != 'published' AND NEW.status = 'published' THEN
            -- Post was published
            IF NEW.category_id IS NOT NULL THEN
                UPDATE blog_categories
                SET post_count = post_count + 1
                WHERE id = NEW.category_id;
            END IF;
            IF NEW.author_id IS NOT NULL THEN
                UPDATE blog_authors
                SET post_count = post_count + 1
                WHERE id = NEW.author_id;
            END IF;

        ELSIF OLD.status = 'published' AND NEW.status != 'published' THEN
            -- Post was unpublished
            IF NEW.category_id IS NOT NULL THEN
                UPDATE blog_categories
                SET post_count = post_count - 1
                WHERE id = NEW.category_id AND post_count > 0;
            END IF;
            IF NEW.author_id IS NOT NULL THEN
                UPDATE blog_authors
                SET post_count = post_count - 1
                WHERE id = NEW.author_id AND post_count > 0;
            END IF;
        END IF;

    ELSIF TG_OP = 'DELETE' THEN
        -- Update category post count
        IF OLD.category_id IS NOT NULL AND OLD.status = 'published' THEN
            UPDATE blog_categories
            SET post_count = post_count - 1
            WHERE id = OLD.category_id AND post_count > 0;
        END IF;

        -- Update author post count
        IF OLD.author_id IS NOT NULL AND OLD.status = 'published' THEN
            UPDATE blog_authors
            SET post_count = post_count - 1
            WHERE id = OLD.author_id AND post_count > 0;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for post counts
DROP TRIGGER IF EXISTS trigger_update_post_counts ON blog_posts;
CREATE TRIGGER trigger_update_post_counts
    AFTER INSERT OR UPDATE OR DELETE ON blog_posts
    FOR EACH ROW
    EXECUTE FUNCTION update_post_counts();

-- Function to create post version on update
CREATE OR REPLACE FUNCTION create_post_version()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'UPDATE' AND (
        OLD.title != NEW.title OR
        OLD.content != NEW.content OR
        OLD.excerpt != NEW.excerpt
    ) THEN
        INSERT INTO blog_post_versions (
            post_id,
            version,
            title,
            content,
            excerpt,
            tags,
            changed_by,
            change_type
        ) VALUES (
            NEW.id,
            NEW.version,
            OLD.title,
            OLD.content,
            OLD.excerpt,
            OLD.tags,
            NEW.last_edited_by,
            'content_update'
        );

        NEW.version := NEW.version + 1;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for versioning
DROP TRIGGER IF EXISTS trigger_create_post_version ON blog_posts;
CREATE TRIGGER trigger_create_post_version
    BEFORE UPDATE ON blog_posts
    FOR EACH ROW
    EXECUTE FUNCTION create_post_version();

-- Function to update comment counts
CREATE OR REPLACE FUNCTION update_comment_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' AND NEW.status = 'approved' THEN
        UPDATE blog_posts
        SET comment_count = comment_count + 1
        WHERE id = NEW.post_id;

        IF NEW.parent_comment_id IS NOT NULL THEN
            UPDATE blog_comments
            SET reply_count = reply_count + 1
            WHERE id = NEW.parent_comment_id;
        END IF;

    ELSIF TG_OP = 'DELETE' AND OLD.status = 'approved' THEN
        UPDATE blog_posts
        SET comment_count = comment_count - 1
        WHERE id = OLD.post_id AND comment_count > 0;

        IF OLD.parent_comment_id IS NOT NULL THEN
            UPDATE blog_comments
            SET reply_count = reply_count - 1
            WHERE id = OLD.parent_comment_id AND reply_count > 0;
        END IF;

    ELSIF TG_OP = 'UPDATE' THEN
        IF OLD.status != 'approved' AND NEW.status = 'approved' THEN
            UPDATE blog_posts
            SET comment_count = comment_count + 1
            WHERE id = NEW.post_id;
        ELSIF OLD.status = 'approved' AND NEW.status != 'approved' THEN
            UPDATE blog_posts
            SET comment_count = comment_count - 1
            WHERE id = NEW.post_id AND comment_count > 0;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for comment counts
DROP TRIGGER IF EXISTS trigger_update_comment_count ON blog_comments;
CREATE TRIGGER trigger_update_comment_count
    AFTER INSERT OR UPDATE OR DELETE ON blog_comments
    FOR EACH ROW
    EXECUTE FUNCTION update_comment_count();

-- ============================================
-- VIEWS FOR EASY QUERYING
-- ============================================

-- View: Published posts with full details
CREATE OR REPLACE VIEW v_published_posts AS
SELECT
    p.*,
    c.name as category_name,
    c.slug as category_slug,
    c.color as category_color,
    a.name as author_name,
    a.slug as author_slug,
    a.avatar_url as author_avatar,
    a.bio as author_bio
FROM blog_posts p
LEFT JOIN blog_categories c ON p.category_id = c.id
LEFT JOIN blog_authors a ON p.author_id = a.id
WHERE p.status = 'published'
ORDER BY p.published_at DESC;

-- View: Popular posts
CREATE OR REPLACE VIEW v_popular_posts AS
SELECT
    p.id,
    p.title,
    p.slug,
    p.excerpt,
    p.cover_image_url,
    p.view_count,
    p.like_count,
    p.comment_count,
    p.share_count,
    p.published_at,
    c.name as category_name,
    a.name as author_name,
    a.avatar_url as author_avatar,
    (p.view_count * 1 + p.like_count * 5 + p.comment_count * 10 + p.share_count * 15) as popularity_score
FROM blog_posts p
LEFT JOIN blog_categories c ON p.category_id = c.id
LEFT JOIN blog_authors a ON p.author_id = a.id
WHERE p.status = 'published'
ORDER BY popularity_score DESC;

-- View: Category statistics
CREATE OR REPLACE VIEW v_category_stats AS
SELECT
    c.*,
    COUNT(p.id) as actual_post_count,
    SUM(p.view_count) as total_views,
    SUM(p.like_count) as total_likes,
    AVG(p.view_count) as avg_views_per_post
FROM blog_categories c
LEFT JOIN blog_posts p ON c.id = p.category_id AND p.status = 'published'
GROUP BY c.id
ORDER BY c.display_order, c.name;

-- View: Author statistics
CREATE OR REPLACE VIEW v_author_stats AS
SELECT
    a.*,
    COUNT(p.id) as actual_post_count,
    SUM(p.view_count) as total_views,
    SUM(p.like_count) as total_likes,
    SUM(p.comment_count) as total_comments,
    AVG(p.view_count) as avg_views_per_post,
    MAX(p.published_at) as last_published_at
FROM blog_authors a
LEFT JOIN blog_posts p ON a.id = p.author_id AND p.status = 'published'
GROUP BY a.id
ORDER BY total_views DESC;

-- ============================================
-- INITIAL SEED DATA (optional)
-- ============================================

-- Insert default categories
INSERT INTO blog_categories (name, slug, description, color, display_order) VALUES
    ('Tutorial', 'tutorial', 'Step-by-step guides and tutorials', '#3B82F6', 1),
    ('Insight', 'insight', 'Industry insights and analysis', '#8B5CF6', 2),
    ('Research', 'research', 'Research findings and technical deep-dives', '#10B981', 3),
    ('News', 'news', 'Latest news and updates', '#F59E0B', 4),
    ('Case Study', 'case-study', 'Real-world case studies', '#EF4444', 5)
ON CONFLICT (slug) DO NOTHING;

-- ============================================
-- SCHEMA COMPLETE
-- ============================================

-- Grant permissions (adjust as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_app_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO your_app_user;
