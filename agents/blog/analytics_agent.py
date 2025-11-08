"""
Blog Analytics Agent
Analyzes blog performance, provides insights, and generates recommendations
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class BlogAnalyticsAgent:
    """
    Specialized agent for blog analytics and insights
    Analyzes performance metrics and provides actionable recommendations
    """

    def __init__(self, db, anthropic_client=None):
        """
        Initialize the analytics agent

        Args:
            db: Database connection (PostgresDB instance)
            anthropic_client: Anthropic client for AI analysis
        """
        self.db = db
        self.anthropic = anthropic_client

    async def analyze_post_performance(
        self,
        post_id: str,
        time_period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze individual post performance

        Returns:
            {
                'post_id': str,
                'metrics': {...},
                'trends': {...},
                'insights': [str],
                'recommendations': [str]
            }
        """
        # Get post info
        post = await self.db.fetchrow("""
            SELECT
                p.*,
                a.name as author_name,
                c.name as category_name
            FROM blog_posts p
            LEFT JOIN blog_authors a ON p.author_id = a.id
            LEFT JOIN blog_categories c ON p.category_id = c.id
            WHERE p.id = $1
        """, post_id)

        if not post:
            raise ValueError(f"Post {post_id} not found")

        # Get analytics data
        since_date = datetime.now() - timedelta(days=time_period_days)

        analytics = await self.db.fetch("""
            SELECT
                event_type,
                COUNT(*) as count,
                AVG(time_on_page_seconds) as avg_time_on_page,
                AVG(scroll_depth_percent) as avg_scroll_depth,
                COUNT(*) FILTER (WHERE bounce = true)::FLOAT / COUNT(*) * 100 as bounce_rate
            FROM blog_analytics
            WHERE post_id = $1
              AND created_at >= $2
            GROUP BY event_type
        """, post_id, since_date)

        # Calculate engagement metrics
        views = next((a['count'] for a in analytics if a['event_type'] == 'view'), 0)
        likes = post['like_count']
        comments = post['comment_count']
        shares = post['share_count']

        engagement_rate = 0
        if views > 0:
            engagement_rate = ((likes + comments * 2 + shares * 3) / views) * 100

        # Get traffic sources
        traffic_sources = await self.db.fetch("""
            SELECT
                COALESCE(utm_source, 'direct') as source,
                COUNT(*) as visits,
                AVG(time_on_page_seconds) as avg_time
            FROM blog_analytics
            WHERE post_id = $1
              AND created_at >= $2
              AND event_type = 'view'
            GROUP BY source
            ORDER BY visits DESC
            LIMIT 10
        """, post_id, since_date)

        # Get daily views trend
        daily_views = await self.db.fetch("""
            SELECT
                event_date,
                SUM(count) as views
            FROM blog_analytics
            WHERE post_id = $1
              AND event_type = 'view'
              AND created_at >= $2
            GROUP BY event_date
            ORDER BY event_date
        """, post_id, since_date)

        # Generate insights
        insights = []
        recommendations = []

        # Engagement analysis
        if engagement_rate > 15:
            insights.append(f"Excellent engagement rate ({engagement_rate:.1f}%) - well above average")
        elif engagement_rate > 5:
            insights.append(f"Good engagement rate ({engagement_rate:.1f}%)")
        else:
            insights.append(f"Low engagement rate ({engagement_rate:.1f}%) - needs improvement")
            recommendations.append("Add more engaging CTAs and interactive elements")

        # Bounce rate analysis
        bounce_rate = next((a['bounce_rate'] for a in analytics if a['event_type'] == 'view'), 0)
        if bounce_rate > 70:
            insights.append(f"High bounce rate ({bounce_rate:.1f}%) indicates content may not match expectations")
            recommendations.append("Review meta description and title to better match content")
            recommendations.append("Improve content introduction to hook readers faster")

        # Scroll depth analysis
        avg_scroll = next((a['avg_scroll_depth'] for a in analytics if a['event_type'] == 'view'), 0)
        if avg_scroll < 50:
            insights.append(f"Low scroll depth ({avg_scroll:.1f}%) - readers not finishing content")
            recommendations.append("Break up long paragraphs with subheadings and images")
            recommendations.append("Add a compelling hook in the first paragraph")
        elif avg_scroll > 80:
            insights.append(f"Excellent scroll depth ({avg_scroll:.1f}%) - engaging content")

        # Social sharing analysis
        if shares > 0 and views > 0:
            share_rate = (shares / views) * 100
            if share_rate > 5:
                insights.append(f"High share rate ({share_rate:.1f}%) - highly shareable content")
            elif share_rate < 1:
                recommendations.append("Add social share buttons more prominently")
                recommendations.append("Create more shareable quotes/insights in content")

        # Traffic source insights
        if traffic_sources:
            top_source = traffic_sources[0]
            insights.append(f"Top traffic source: {top_source['source']} ({top_source['visits']} visits)")

            # Check if organic traffic is low
            organic = next((s for s in traffic_sources if 'google' in s['source'].lower() or 'search' in s['source'].lower()), None)
            if not organic or organic['visits'] < views * 0.3:
                recommendations.append("Improve SEO to increase organic search traffic")
                recommendations.append("Add more relevant keywords and internal links")

        return {
            'post_id': post_id,
            'post_title': post['title'],
            'post_status': post['status'],
            'published_at': post['published_at'].isoformat() if post['published_at'] else None,
            'metrics': {
                'views': views,
                'likes': likes,
                'comments': comments,
                'shares': shares,
                'engagement_rate': round(engagement_rate, 2),
                'bounce_rate': round(bounce_rate, 2),
                'avg_scroll_depth': round(avg_scroll, 2),
                'avg_time_on_page': round(next((a['avg_time_on_page'] for a in analytics if a['event_type'] == 'view'), 0) or 0, 2)
            },
            'traffic_sources': [
                {
                    'source': s['source'],
                    'visits': s['visits'],
                    'avg_time': round(s['avg_time'] or 0, 2)
                }
                for s in traffic_sources
            ],
            'daily_trend': [
                {
                    'date': d['event_date'].isoformat(),
                    'views': d['views']
                }
                for d in daily_views
            ],
            'insights': insights,
            'recommendations': recommendations
        }

    async def analyze_category_performance(
        self,
        category_id: str,
        time_period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze category performance

        Returns category metrics and top performing posts
        """
        category = await self.db.fetchrow("""
            SELECT * FROM blog_categories WHERE id = $1
        """, category_id)

        if not category:
            raise ValueError(f"Category {category_id} not found")

        since_date = datetime.now() - timedelta(days=time_period_days)

        # Category-wide metrics
        metrics = await self.db.fetchrow("""
            SELECT
                COUNT(DISTINCT p.id) as total_posts,
                SUM(p.view_count) as total_views,
                SUM(p.like_count) as total_likes,
                SUM(p.comment_count) as total_comments,
                AVG(p.seo_score) as avg_seo_score
            FROM blog_posts p
            WHERE p.category_id = $1
              AND p.status = 'published'
        """, category_id)

        # Top posts in category
        top_posts = await self.db.fetch("""
            SELECT
                id,
                title,
                slug,
                view_count,
                like_count,
                engagement_rate
            FROM post_analytics_summary
            WHERE category_name = $1
            ORDER BY view_count DESC
            LIMIT 10
        """, category['name'])

        return {
            'category_id': category_id,
            'category_name': category['name'],
            'metrics': dict(metrics),
            'top_posts': [dict(p) for p in top_posts]
        }

    async def analyze_author_performance(
        self,
        author_id: str,
        time_period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze author performance

        Returns author metrics and insights
        """
        author = await self.db.fetchrow("""
            SELECT * FROM blog_authors WHERE id = $1
        """, author_id)

        if not author:
            raise ValueError(f"Author {author_id} not found")

        # Author metrics
        metrics = await self.db.fetchrow("""
            SELECT
                COUNT(*) as total_posts,
                SUM(view_count) as total_views,
                SUM(like_count) as total_likes,
                SUM(comment_count) as total_comments,
                AVG(seo_score) as avg_seo_score,
                AVG(engagement_rate) as avg_engagement_rate
            FROM post_analytics_summary
            WHERE author_name = $1
        """, author['name'])

        # Best performing posts
        best_posts = await self.db.fetch("""
            SELECT
                id,
                title,
                slug,
                view_count,
                engagement_rate
            FROM post_analytics_summary
            WHERE author_name = $1
            ORDER BY engagement_rate DESC
            LIMIT 5
        """, author['name'])

        return {
            'author_id': author_id,
            'author_name': author['name'],
            'metrics': dict(metrics),
            'best_posts': [dict(p) for p in best_posts]
        }

    async def get_platform_overview(
        self,
        time_period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Get overall platform analytics

        Returns:
            Comprehensive platform statistics
        """
        since_date = datetime.now() - timedelta(days=time_period_days)

        # Overall metrics
        overall = await self.db.fetchrow("""
            SELECT
                COUNT(DISTINCT id) as total_posts,
                SUM(view_count) as total_views,
                SUM(like_count) as total_likes,
                SUM(comment_count) as total_comments,
                SUM(share_count) as total_shares
            FROM blog_posts
            WHERE status = 'published'
              AND published_at >= $1
        """, since_date)

        # Top performing posts
        top_posts = await self.db.fetch("""
            SELECT
                id,
                title,
                slug,
                view_count,
                engagement_rate,
                published_at
            FROM post_analytics_summary
            ORDER BY view_count DESC
            LIMIT 10
        """)

        # Category breakdown
        category_stats = await self.db.fetch("""
            SELECT
                c.name,
                COUNT(p.id) as post_count,
                SUM(p.view_count) as total_views
            FROM blog_categories c
            LEFT JOIN blog_posts p ON c.id = p.category_id AND p.status = 'published'
            WHERE c.is_active = true
            GROUP BY c.name
            ORDER BY total_views DESC
        """)

        # Daily trend
        daily_trend = await self.db.fetch("""
            SELECT
                event_date,
                SUM(count) FILTER (WHERE event_type = 'view') as views,
                SUM(count) FILTER (WHERE event_type = 'like') as likes,
                SUM(count) FILTER (WHERE event_type = 'comment') as comments
            FROM blog_analytics
            WHERE created_at >= $1
            GROUP BY event_date
            ORDER BY event_date
        """, since_date)

        return {
            'time_period_days': time_period_days,
            'overall_metrics': dict(overall),
            'top_posts': [dict(p) for p in top_posts],
            'category_breakdown': [dict(c) for c in category_stats],
            'daily_trend': [
                {
                    'date': t['event_date'].isoformat(),
                    'views': t['views'] or 0,
                    'likes': t['likes'] or 0,
                    'comments': t['comments'] or 0
                }
                for t in daily_trend
            ]
        }

    async def generate_content_recommendations(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Generate AI-powered content recommendations

        Returns:
            List of content ideas based on performance data
        """
        # Find trending topics
        trending = await self.db.fetch("""
            SELECT
                unnest(tags) as tag,
                COUNT(*) as post_count,
                AVG(engagement_rate) as avg_engagement
            FROM post_analytics_summary
            WHERE published_at >= NOW() - INTERVAL '30 days'
            GROUP BY tag
            HAVING COUNT(*) >= 2
            ORDER BY avg_engagement DESC
            LIMIT $1
        """, limit)

        recommendations = []

        for topic in trending:
            recommendations.append({
                'type': 'trending_topic',
                'topic': topic['tag'],
                'reason': f"High engagement ({topic['avg_engagement']:.1f}%) in recent posts",
                'suggestion': f"Create more content about '{topic['tag']}'"
            })

        # Find underperforming categories
        underperforming = await self.db.fetch("""
            SELECT
                name,
                post_count
            FROM blog_categories
            WHERE post_count < 5
              AND is_active = true
            ORDER BY post_count
            LIMIT 5
        """)

        for category in underperforming:
            recommendations.append({
                'type': 'content_gap',
                'category': category['name'],
                'reason': f"Only {category['post_count']} posts in this category",
                'suggestion': f"Add more content to '{category['name']}' category"
            })

        return recommendations


# Export
__all__ = ['BlogAnalyticsAgent']
