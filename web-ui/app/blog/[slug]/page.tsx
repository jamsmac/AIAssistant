"use client";

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';

interface BlogPost {
  id: string;
  title: string;
  slug: string;
  content: string;
  excerpt: string;
  cover_image_url?: string;
  author_name: string;
  category_name: string;
  category_color: string;
  published_at: string;
  reading_time_minutes: number;
  view_count: number;
  like_count: number;
  tags: string[];
  ai_generated: boolean;
}

export default function BlogPostPage() {
  const params = useParams();
  const slug = params.slug as string;

  const [post, setPost] = useState<BlogPost | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [liked, setLiked] = useState(false);

  useEffect(() => {
    if (slug) {
      fetchPost();
    }
  }, [slug]);

  const fetchPost = async () => {
    try {
      setLoading(true);
      const res = await fetch(`/api/blog/posts/${slug}`);
      if (!res.ok) {
        setError(res.status === 404 ? 'Post not found' : 'Failed to fetch post');
        return;
      }
      const data = await res.json();
      setPost(data);
    } catch (err) {
      console.error(err);
      setError('Failed to load post');
    } finally {
      setLoading(false);
    }
  };

  const handleLike = async () => {
    if (!post || liked) return;
    try {
      await fetch(`/api/blog/posts/${slug}/like`, { method: 'POST' });
      setLiked(true);
      setPost({ ...post, like_count: post.like_count + 1 });
    } catch (err) {
      console.error('Failed to like post:', err);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-white p-8">
        <div className="max-w-4xl mx-auto animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-3/4 mb-6"></div>
          <div className="h-64 bg-gray-200 rounded mb-6"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !post) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center p-8">
        <div className="text-center">
          <h1 className="text-4xl font-bold mb-4">{error || 'Post not found'}</h1>
          <Link href="/blog" className="text-blue-600 hover:text-blue-700">
            ← Back to blog
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <Link href="/blog" className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900 mb-6">
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to blog
        </Link>

        <div className="flex items-center gap-4 mb-4">
          <span className="px-3 py-1 text-sm font-medium rounded-full" style={{
            backgroundColor: post.category_color + '20',
            color: post.category_color
          }}>
            {post.category_name}
          </span>
          <span className="text-sm text-gray-600">{post.reading_time_minutes} min read</span>
          {post.ai_generated && (
            <span className="px-2 py-1 text-xs bg-purple-100 text-purple-800 rounded">AI Generated</span>
          )}
        </div>

        <h1 className="text-4xl sm:text-5xl font-bold mb-6">{post.title}</h1>

        <div className="flex items-center gap-4 text-sm text-gray-600 mb-8">
          <p className="font-medium text-gray-900">{post.author_name}</p>
          <p>{new Date(post.published_at).toLocaleDateString('en-US', {
            year: 'numeric', month: 'long', day: 'numeric'
          })}</p>
        </div>

        {post.cover_image_url && (
          <img src={post.cover_image_url} alt={post.title} className="w-full h-96 object-cover rounded-lg mb-8" />
        )}

        <div className="prose prose-lg max-w-none mb-12">
          <div dangerouslySetInnerHTML={{ __html: post.content }} />
        </div>

        {post.tags && post.tags.length > 0 && (
          <div className="mb-8 pt-8 border-t">
            <h3 className="text-sm font-medium mb-4">Tags</h3>
            <div className="flex flex-wrap gap-2">
              {post.tags.map((tag, idx) => (
                <span key={idx} className="px-3 py-1 text-sm bg-gray-100 rounded-full">#{tag}</span>
              ))}
            </div>
          </div>
        )}

        <div className="pt-8 border-t">
          <div className="flex items-center gap-4">
            <button
              onClick={handleLike}
              disabled={liked}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg ${
                liked ? 'bg-red-100 text-red-700' : 'bg-gray-100 hover:bg-gray-200'
              }`}
            >
              <svg className="w-5 h-5" fill={liked ? 'currentColor' : 'none'} stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
              </svg>
              <span>{post.like_count}</span>
            </button>
            <div className="flex items-center gap-2 px-4 py-2 bg-gray-100 rounded-lg">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
              <span>{post.view_count}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
