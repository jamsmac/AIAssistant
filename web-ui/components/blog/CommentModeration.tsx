'use client'

import { useState, useEffect } from 'react'
import { Check, X, MessageSquare, User, Calendar, AlertCircle } from 'lucide-react'

interface Comment {
  id: string
  post_id: string
  post_title: string
  author_name: string
  author_email: string
  content: string
  status: 'pending' | 'approved' | 'rejected' | 'spam'
  created_at: string
}

export default function CommentModeration() {
  const [comments, setComments] = useState<Comment[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'pending' | 'approved' | 'rejected'>('pending')

  useEffect(() => {
    fetchComments()
  }, [filter])

  const fetchComments = async () => {
    try {
      const params = new URLSearchParams()
      if (filter !== 'all') params.set('status', filter)

      const response = await fetch(`/api/blog/comments?${params}`)
      if (response.ok) {
        const data = await response.json()
        setComments(data.comments || [])
      }
    } catch (error) {
      console.error('Failed to fetch comments:', error)
    } finally {
      setLoading(false)
    }
  }

  const moderateComment = async (commentId: string, action: 'approve' | 'reject' | 'spam') => {
    try {
      const response = await fetch(`/api/blog/comments/${commentId}/moderate`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action }),
      })

      if (response.ok) {
        setComments(comments.filter(c => c.id !== commentId))
      }
    } catch (error) {
      console.error('Moderation failed:', error)
      alert('Failed to moderate comment')
    }
  }

  const filteredComments = comments.filter(comment => {
    if (filter === 'all') return true
    return comment.status === filter
  })

  const pendingCount = comments.filter(c => c.status === 'pending').length

  return (
    <div className="bg-white rounded-xl shadow-md overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold flex items-center gap-2">
              <MessageSquare size={28} />
              Comment Moderation
            </h2>
            <p className="text-blue-100 mt-1">Review and moderate user comments</p>
          </div>
          {pendingCount > 0 && (
            <div className="flex items-center gap-2 bg-yellow-400 text-yellow-900 px-4 py-2 rounded-lg font-semibold">
              <AlertCircle size={20} />
              {pendingCount} Pending
            </div>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="p-4 bg-gray-50 border-b border-gray-200">
        <div className="flex gap-2">
          {(['all', 'pending', 'approved', 'rejected'] as const).map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                filter === status
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
              {status === 'pending' && pendingCount > 0 && (
                <span className="ml-2 bg-yellow-400 text-yellow-900 px-2 py-0.5 rounded-full text-xs">
                  {pendingCount}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Comments List */}
      <div className="divide-y divide-gray-200">
        {loading ? (
          <div className="p-12 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading comments...</p>
          </div>
        ) : filteredComments.length === 0 ? (
          <div className="p-12 text-center">
            <MessageSquare className="mx-auto text-gray-300" size={64} />
            <p className="mt-4 text-gray-600 text-lg">No comments to moderate</p>
            <p className="text-gray-500 text-sm mt-2">
              {filter === 'pending' ? 'All caught up!' : `No ${filter} comments found`}
            </p>
          </div>
        ) : (
          filteredComments.map((comment) => (
            <div key={comment.id} className="p-6 hover:bg-gray-50 transition-colors">
              {/* Comment Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center text-white font-semibold">
                    {comment.author_name.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="font-semibold text-gray-900">{comment.author_name}</h4>
                      <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                        comment.status === 'approved' ? 'bg-green-100 text-green-800' :
                        comment.status === 'rejected' ? 'bg-red-100 text-red-800' :
                        comment.status === 'spam' ? 'bg-orange-100 text-orange-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {comment.status}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600">{comment.author_email}</p>
                    <div className="flex items-center gap-4 mt-1 text-xs text-gray-500">
                      <span className="flex items-center gap-1">
                        <Calendar size={12} />
                        {new Date(comment.created_at).toLocaleString()}
                      </span>
                      <span>On: {comment.post_title}</span>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                {comment.status === 'pending' && (
                  <div className="flex gap-2">
                    <button
                      onClick={() => moderateComment(comment.id, 'approve')}
                      className="flex items-center gap-1 px-3 py-1.5 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors"
                      title="Approve"
                    >
                      <Check size={16} />
                      Approve
                    </button>
                    <button
                      onClick={() => moderateComment(comment.id, 'reject')}
                      className="flex items-center gap-1 px-3 py-1.5 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors"
                      title="Reject"
                    >
                      <X size={16} />
                      Reject
                    </button>
                    <button
                      onClick={() => moderateComment(comment.id, 'spam')}
                      className="px-3 py-1.5 bg-orange-100 text-orange-700 rounded-lg hover:bg-orange-200 transition-colors text-sm"
                      title="Mark as Spam"
                    >
                      Spam
                    </button>
                  </div>
                )}
              </div>

              {/* Comment Content */}
              <div className="ml-13 pl-6 border-l-2 border-gray-200">
                <p className="text-gray-700 whitespace-pre-wrap">{comment.content}</p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
