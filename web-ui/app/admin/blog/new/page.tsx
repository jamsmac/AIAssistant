'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import RichTextEditor from '@/components/blog/RichTextEditor'
import { Save, Sparkles, Eye, FileText } from 'lucide-react'
import DOMPurify from 'dompurify'

export default function NewBlogPost() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [aiLoading, setAiLoading] = useState(false)
  const [showPreview, setShowPreview] = useState(false)

  const [formData, setFormData] = useState({
    title: '',
    excerpt: '',
    content: '',
    category: '',
    tags: '',
    coverImage: '',
    status: 'draft' as 'draft' | 'published',
    metaTitle: '',
    metaDescription: '',
    metaKeywords: '',
  })

  const handleChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const generateWithAI = async () => {
    if (!formData.title) {
      alert('Please enter a title first')
      return
    }

    setAiLoading(true)
    try {
      const response = await fetch('/api/blog/ai/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: formData.title,
          style: 'professional',
          target_length: 1500,
          auto_seo: true,
        }),
      })

      if (response.ok) {
        const data = await response.json()
        setFormData(prev => ({
          ...prev,
          content: data.content || prev.content,
          excerpt: data.excerpt || prev.excerpt,
          tags: data.suggested_tags?.join(', ') || prev.tags,
          metaTitle: data.seo?.optimized_title || prev.metaTitle,
          metaDescription: data.seo?.meta_description || prev.metaDescription,
          metaKeywords: data.seo?.keywords?.join(', ') || prev.metaKeywords,
        }))
      }
    } catch (error) {
      console.error('AI generation failed:', error)
      alert('Failed to generate content with AI')
    } finally {
      setAiLoading(false)
    }
  }

  const saveDraft = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/blog/posts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          tags: formData.tags.split(',').map(t => t.trim()).filter(Boolean),
          status: 'draft',
        }),
      })

      if (response.ok) {
        const data = await response.json()
        alert('Draft saved successfully!')
        router.push(`/admin/blog/edit/${data.post_id}`)
      }
    } catch (error) {
      console.error('Save failed:', error)
      alert('Failed to save draft')
    } finally {
      setLoading(false)
    }
  }

  const publish = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/blog/posts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          tags: formData.tags.split(',').map(t => t.trim()).filter(Boolean),
          status: 'published',
        }),
      })

      if (response.ok) {
        const data = await response.json()

        // Publish with social media
        await fetch(`/api/blog/posts/${data.post_id}/publish?publish_to_social=true`, {
          method: 'PUT',
        })

        alert('Post published successfully!')
        router.push('/blog')
      }
    } catch (error) {
      console.error('Publish failed:', error)
      alert('Failed to publish post')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 p-8">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Create New Blog Post
            </h1>
            <p className="text-gray-600 mt-2">Write and publish your content with AI assistance</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => setShowPreview(!showPreview)}
              className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50"
            >
              <Eye size={18} />
              {showPreview ? 'Edit' : 'Preview'}
            </button>
            <button
              onClick={generateWithAI}
              disabled={aiLoading || !formData.title}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:shadow-lg disabled:opacity-50"
            >
              <Sparkles size={18} />
              {aiLoading ? 'Generating...' : 'Generate with AI'}
            </button>
          </div>
        </div>

        {/* Main Content */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          {!showPreview ? (
            <>
              {/* Title */}
              <div className="mb-6">
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Post Title *
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => handleChange('title', e.target.value)}
                  placeholder="Enter a compelling title..."
                  className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-lg"
                />
              </div>

              {/* Excerpt */}
              <div className="mb-6">
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Excerpt
                </label>
                <textarea
                  value={formData.excerpt}
                  onChange={(e) => handleChange('excerpt', e.target.value)}
                  placeholder="Brief summary of your post..."
                  rows={3}
                  className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Content Editor */}
              <div className="mb-6">
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Content *
                </label>
                <RichTextEditor
                  content={formData.content}
                  onChange={(content) => handleChange('content', content)}
                  placeholder="Start writing your amazing content..."
                />
              </div>

              {/* Metadata Grid */}
              <div className="grid grid-cols-2 gap-6 mb-6">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Category
                  </label>
                  <input
                    type="text"
                    value={formData.category}
                    onChange={(e) => handleChange('category', e.target.value)}
                    placeholder="e.g., Technology, Tutorial"
                    className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Tags (comma separated)
                  </label>
                  <input
                    type="text"
                    value={formData.tags}
                    onChange={(e) => handleChange('tags', e.target.value)}
                    placeholder="ai, machine-learning, tutorial"
                    className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>

              {/* Cover Image */}
              <div className="mb-6">
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Cover Image URL
                </label>
                <input
                  type="text"
                  value={formData.coverImage}
                  onChange={(e) => handleChange('coverImage', e.target.value)}
                  placeholder="https://example.com/image.jpg"
                  className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* SEO Section */}
              <div className="border-t pt-6 mt-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <FileText size={20} />
                  SEO Settings
                </h3>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Meta Title
                    </label>
                    <input
                      type="text"
                      value={formData.metaTitle}
                      onChange={(e) => handleChange('metaTitle', e.target.value)}
                      placeholder="SEO optimized title"
                      className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Meta Description
                    </label>
                    <textarea
                      value={formData.metaDescription}
                      onChange={(e) => handleChange('metaDescription', e.target.value)}
                      placeholder="SEO meta description (150-160 characters)"
                      rows={2}
                      className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Keywords (comma separated)
                    </label>
                    <input
                      type="text"
                      value={formData.metaKeywords}
                      onChange={(e) => handleChange('metaKeywords', e.target.value)}
                      placeholder="keyword1, keyword2, keyword3"
                      className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex justify-end gap-4 mt-8 pt-6 border-t">
                <button
                  onClick={() => router.back()}
                  className="px-6 py-3 border border-gray-200 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={saveDraft}
                  disabled={loading || !formData.title || !formData.content}
                  className="flex items-center gap-2 px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50"
                >
                  <Save size={18} />
                  Save Draft
                </button>
                <button
                  onClick={publish}
                  disabled={loading || !formData.title || !formData.content}
                  className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:shadow-lg disabled:opacity-50"
                >
                  <Sparkles size={18} />
                  Publish
                </button>
              </div>
            </>
          ) : (
            /* Preview */
            <div className="prose prose-lg max-w-none">
              <h1>{formData.title || 'Untitled Post'}</h1>
              {formData.excerpt && <p className="lead">{formData.excerpt}</p>}
              {formData.coverImage && (
                <img src={formData.coverImage} alt="Cover" className="rounded-lg" />
              )}
              <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(formData.content || '<p>No content yet...</p>') }} />
              {formData.tags && (
                <div className="flex gap-2 mt-8">
                  {formData.tags.split(',').map((tag, i) => (
                    <span key={i} className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                      {tag.trim()}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
