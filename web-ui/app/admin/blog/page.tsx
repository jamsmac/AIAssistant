
"use client";

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface BlogPost {
  id: string;
  title: string;
  slug: string;
  author_name: string;
  category_name: string;
  status: string;
  published_at: string;
  view_count: number;
  like_count: number;
  ai_generated: boolean;
}

export default function BlogAdminPage() {
  const [posts, setPosts] = useState<BlogPost[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/blog/posts')
      .then(res => res.json())
      .then(data => { setPosts(data.posts || []); setLoading(false); })
      .catch(err => { console.error(err); setLoading(false); });
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold">Blog Administration</h1>
          <Link href="/admin/blog/new" className="px-4 py-2 bg-blue-600 text-white rounded-lg">+ New Post</Link>
        </div>

        {loading ? (
          <div className="bg-white rounded-lg p-12 text-center">Loading...</div>
        ) : posts.length === 0 ? (
          <div className="bg-white rounded-lg p-12 text-center">No posts found</div>
        ) : (
          <>
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <table className="min-w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs uppercase">Title</th>
                    <th className="px-6 py-3 text-left text-xs uppercase">Category</th>
                    <th className="px-6 py-3 text-left text-xs uppercase">Status</th>
                    <th className="px-6 py-3 text-left text-xs uppercase">Stats</th>
                    <th className="px-6 py-3 text-right text-xs uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {posts.map((post) => (
                    <tr key={post.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <Link href={`/blog/${post.slug}`} className="font-medium hover:text-blue-600">{post.title}</Link>
                      </td>
                      <td className="px-6 py-4 text-sm">{post.category_name}</td>
                      <td className="px-6 py-4"><span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800">{post.status}</span></td>
                      <td className="px-6 py-4 text-sm">Views: {post.view_count} | Likes: {post.like_count}</td>
                      <td className="px-6 py-4 text-right">
                        <Link href={`/admin/blog/edit/${post.id}`} className="text-blue-600 mr-3">Edit</Link>
                        <Link href={`/blog/${post.slug}`} className="text-gray-600">View</Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-6 grid grid-cols-4 gap-4">
              <div className="bg-white rounded-lg p-4 border">
                <p className="text-sm text-gray-600">Total Posts</p>
                <p className="text-2xl font-bold">{posts.length}</p>
              </div>
              <div className="bg-white rounded-lg p-4 border">
                <p className="text-sm text-gray-600">Total Views</p>
                <p className="text-2xl font-bold">{posts.reduce((sum, p) => sum + p.view_count, 0)}</p>
              </div>
              <div className="bg-white rounded-lg p-4 border">
                <p className="text-sm text-gray-600">Total Likes</p>
                <p className="text-2xl font-bold">{posts.reduce((sum, p) => sum + p.like_count, 0)}</p>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
