'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface BlogPost {
  id: string;
  title: string;
  slug: string;
  excerpt: string;
  cover_image_url: string | null;
  category_name: string;
  category_slug: string;
  author_name: string;
  author_avatar: string | null;
  published_at: string;
  reading_time_minutes: number;
  view_count: number;
  is_featured: boolean;
}

interface Category {
  id: string;
  name: string;
  slug: string;
  post_count: number;
  color: string | null;
}

export default function BlogPage() {
  const [posts, setPosts] = useState<BlogPost[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    fetchCategories();
    fetchPosts();
  }, [selectedCategory, page]);

  const fetchCategories = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/blog/categories`);
      const data = await res.json();
      setCategories(data.categories || []);
    } catch (error) {
      console.error('Failed to fetch categories:', error);
    }
  };

  const fetchPosts = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        per_page: '9',
        status: 'published'
      });

      if (selectedCategory) {
        params.append('category', selectedCategory);
      }

      const res = await fetch(`${API_BASE}/api/blog/posts?${params}`);
      const data = await res.json();

      setPosts(data.posts || []);
      setTotalPages(data.pagination?.pages || 1);
    } catch (error) {
      console.error('Failed to fetch posts:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const featuredPost = posts.find(p => p.is_featured);
  const regularPosts = posts.filter(p => !p.is_featured);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b">
        <div className="container mx-auto px-4 py-8">
          <div className="max-w-6xl mx-auto">
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              AIAssistant Blog
            </h1>
            <p className="text-gray-600">
              Insights on AI, Automation & Enterprise Technology
            </p>
          </div>
        </div>
      </header>

      {/* Category Filter */}
      <div className="bg-white border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="max-w-6xl mx-auto">
            <div className="flex gap-2 overflow-x-auto">
              <button
                onClick={() => setSelectedCategory(null)}
                className={`px-4 py-2 rounded-full whitespace-nowrap transition-colors ${
                  !selectedCategory
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                All Posts
              </button>
              {categories.map(category => (
                <button
                  key={category.id}
                  onClick={() => setSelectedCategory(category.slug)}
                  className={`px-4 py-2 rounded-full whitespace-nowrap transition-colors ${
                    selectedCategory === category.slug
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  style={
                    selectedCategory === category.slug && category.color
                      ? { backgroundColor: category.color }
                      : {}
                  }
                >
                  {category.name} ({category.post_count})
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-12">
        <div className="max-w-6xl mx-auto">
          {/* Featured Post */}
          {featuredPost && (
            <Link
              href={`/blog/${featuredPost.slug}`}
              className="block mb-12 group"
            >
              <div className="relative rounded-2xl overflow-hidden shadow-2xl h-96 bg-gray-900">
                {featuredPost.cover_image_url && (
                  <img
                    src={featuredPost.cover_image_url}
                    alt={featuredPost.title}
                    className="absolute inset-0 w-full h-full object-cover opacity-60 group-hover:opacity-50 transition-opacity"
                  />
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent" />
                <div className="absolute bottom-0 left-0 right-0 p-8 text-white">
                  <div className="flex items-center gap-3 mb-3">
                    <span className="px-3 py-1 bg-blue-600 rounded-full text-sm font-semibold">
                      Featured
                    </span>
                    <span className="px-3 py-1 bg-white/20 rounded-full text-sm">
                      {featuredPost.category_name}
                    </span>
                  </div>
                  <h2 className="text-4xl font-bold mb-3 group-hover:text-blue-300 transition-colors">
                    {featuredPost.title}
                  </h2>
                  <p className="text-lg text-gray-200 mb-4 line-clamp-2">
                    {featuredPost.excerpt}
                  </p>
                  <div className="flex items-center gap-4 text-sm">
                    {featuredPost.author_avatar && (
                      <img
                        src={featuredPost.author_avatar}
                        alt={featuredPost.author_name}
                        className="w-10 h-10 rounded-full"
                      />
                    )}
                    <span className="font-medium">{featuredPost.author_name}</span>
                    <span>•</span>
                    <span>{formatDate(featuredPost.published_at)}</span>
                    <span>•</span>
                    <span>{featuredPost.reading_time_minutes} min read</span>
                  </div>
                </div>
              </div>
            </Link>
          )}

          {/* Posts Grid */}
          {loading ? (
            <div className="text-center py-12">
              <div className="inline-block w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
              <p className="mt-4 text-gray-600">Loading posts...</p>
            </div>
          ) : regularPosts.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-600">No posts found.</p>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                {regularPosts.map(post => (
                  <Link
                    key={post.id}
                    href={`/blog/${post.slug}`}
                    className="block group"
                  >
                    <article className="bg-white rounded-lg overflow-hidden shadow hover:shadow-xl transition-shadow h-full flex flex-col">
                      {/* Cover Image */}
                      {post.cover_image_url && (
                        <div className="relative h-48 overflow-hidden">
                          <img
                            src={post.cover_image_url}
                            alt={post.title}
                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                          />
                          <div className="absolute top-3 left-3">
                            <span
                              className="px-3 py-1 text-white rounded-full text-xs font-semibold"
                              style={{
                                backgroundColor: categories.find(c => c.slug === post.category_slug)?.color || '#3B82F6'
                              }}
                            >
                              {post.category_name}
                            </span>
                          </div>
                        </div>
                      )}

                      <div className="p-6 flex-1 flex flex-col">
                        <h3 className="font-bold text-xl mb-2 group-hover:text-blue-600 transition-colors line-clamp-2">
                          {post.title}
                        </h3>

                        <p className="text-gray-600 text-sm mb-4 line-clamp-3 flex-1">
                          {post.excerpt}
                        </p>

                        <div className="flex items-center justify-between text-sm text-gray-500 mt-auto">
                          <div className="flex items-center gap-2">
                            {post.author_avatar && (
                              <img
                                src={post.author_avatar}
                                alt={post.author_name}
                                className="w-8 h-8 rounded-full"
                              />
                            )}
                            <span className="font-medium">{post.author_name}</span>
                          </div>
                          <div className="flex items-center gap-3">
                            <span>{post.reading_time_minutes} min</span>
                            <span>•</span>
                            <span>{post.view_count} views</span>
                          </div>
                        </div>
                      </div>
                    </article>
                  </Link>
                ))}
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex justify-center gap-2 mt-12">
                  <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="px-4 py-2 rounded-lg bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>

                  {Array.from({ length: totalPages }, (_, i) => i + 1).map(p => (
                    <button
                      key={p}
                      onClick={() => setPage(p)}
                      className={`px-4 py-2 rounded-lg transition-colors ${
                        page === p
                          ? 'bg-blue-600 text-white'
                          : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      {p}
                    </button>
                  ))}

                  <button
                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                    className="px-4 py-2 rounded-lg bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Newsletter Signup */}
      <div className="bg-blue-50 py-16">
        <div className="container mx-auto px-4">
          <div className="max-w-2xl mx-auto text-center">
            <h2 className="text-3xl font-bold mb-3">Subscribe to our newsletter</h2>
            <p className="text-gray-600 mb-6">
              Get the latest articles and insights delivered to your inbox weekly
            </p>
            <form className="flex gap-3">
              <input
                type="email"
                placeholder="Enter your email"
                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <button
                type="submit"
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
              >
                Subscribe
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
