'use client'

import { useState, useEffect } from 'react'
import { Loader2, Zap, TrendingDown, Database, Activity, CheckCircle, XCircle } from 'lucide-react'

interface Skill {
  name: string
  description: string
  category: string
  level: number
  triggers: string[]
  active: boolean
  estimated_tokens: number
}

interface SkillsStats {
  total_skills: number
  active_skills: number
  level_2_loaded: number
  level_3_loaded: number
  context_saved: number
}

export default function SkillsPage() {
  const [skills, setSkills] = useState<Skill[]>([])
  const [stats, setStats] = useState<SkillsStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    loadSkills()
  }, [])

  const loadSkills = async () => {
    try {
      // TODO: Implement actual API calls when backend endpoints are ready
      // For now, using mock data
      const mockSkills: Skill[] = [
        {
          name: 'backend-development',
          description: 'Backend development and API design',
          category: 'development',
          level: 1,
          triggers: ['backend', 'api', 'server'],
          active: true,
          estimated_tokens: 50
        },
        {
          name: 'frontend-development',
          description: 'Frontend development and UI design',
          category: 'development',
          level: 1,
          triggers: ['frontend', 'ui', 'react'],
          active: false,
          estimated_tokens: 50
        },
        {
          name: 'database-design',
          description: 'Database schema design and optimization',
          category: 'data',
          level: 1,
          triggers: ['database', 'sql', 'schema'],
          active: true,
          estimated_tokens: 50
        }
      ]

      const mockStats: SkillsStats = {
        total_skills: 20,
        active_skills: 5,
        level_2_loaded: 3,
        level_3_loaded: 1,
        context_saved: 85
      }

      setSkills(mockSkills)
      setStats(mockStats)
      setLoading(false)
    } catch (error) {
      console.error('Failed to load skills:', error)
      setLoading(false)
    }
  }

  const toggleSkill = async (skillName: string) => {
    // TODO: Implement actual API call
    setSkills(skills.map(s => 
      s.name === skillName ? { ...s, active: !s.active } : s
    ))
  }

  const categories = ['all', ...Array.from(new Set(skills.map(s => s.category)))]
  const filteredSkills = selectedCategory === 'all' 
    ? skills 
    : skills.filter(s => s.category === selectedCategory)

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 p-8 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-16 w-16 animate-spin text-blue-600 mx-auto" />
          <p className="mt-4 text-gray-600">Loading skills...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Skills Manager
          </h1>
          <p className="text-gray-600 mt-2">
            Progressive Disclosure System - Manage skill loading and context optimization
          </p>
        </div>

        {/* Statistics Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-5 gap-6 mb-8">
            <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-blue-500">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-600 text-sm">Total Skills</p>
                  <p className="text-3xl font-bold text-gray-800">{stats.total_skills}</p>
                </div>
                <Database className="text-blue-500" size={32} />
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-green-500">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-600 text-sm">Active Skills</p>
                  <p className="text-3xl font-bold text-gray-800">{stats.active_skills}</p>
                </div>
                <Activity className="text-green-500" size={32} />
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-purple-500">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-600 text-sm">Level 2 Loaded</p>
                  <p className="text-3xl font-bold text-gray-800">{stats.level_2_loaded}</p>
                </div>
                <Zap className="text-purple-500" size={32} />
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-yellow-500">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-600 text-sm">Level 3 Loaded</p>
                  <p className="text-3xl font-bold text-gray-800">{stats.level_3_loaded}</p>
                </div>
                <Zap className="text-yellow-500" size={32} />
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-emerald-500">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-600 text-sm">Context Saved</p>
                  <p className="text-3xl font-bold text-emerald-600">{stats.context_saved}%</p>
                </div>
                <TrendingDown className="text-emerald-500" size={32} />
              </div>
            </div>
          </div>
        )}

        {/* Progressive Disclosure Info */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl shadow-lg p-6 mb-8 text-white">
          <h2 className="text-2xl font-bold mb-4">Progressive Disclosure System</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 bg-blue-400 rounded-full flex items-center justify-center font-bold">1</div>
                <h3 className="font-semibold">Level 1: Metadata</h3>
              </div>
              <p className="text-blue-100 text-sm">~50 tokens per skill - Always in memory</p>
            </div>
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 bg-purple-400 rounded-full flex items-center justify-center font-bold">2</div>
                <h3 className="font-semibold">Level 2: Instructions</h3>
              </div>
              <p className="text-blue-100 text-sm">~500 tokens - Loaded on activation</p>
            </div>
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 bg-pink-400 rounded-full flex items-center justify-center font-bold">3</div>
                <h3 className="font-semibold">Level 3: Resources</h3>
              </div>
              <p className="text-blue-100 text-sm">~2000 tokens - Loaded on use</p>
            </div>
          </div>
        </div>

        {/* Category Filter */}
        <div className="mb-6 flex gap-2 flex-wrap">
          {categories.map(category => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                selectedCategory === category
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              {category.charAt(0).toUpperCase() + category.slice(1)}
            </button>
          ))}
        </div>

        {/* Skills Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredSkills.map((skill) => (
            <div
              key={skill.name}
              className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-bold text-gray-800 mb-1">
                    {skill.name.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                  </h3>
                  <p className="text-sm text-gray-600">{skill.description}</p>
                </div>
                <button
                  onClick={() => toggleSkill(skill.name)}
                  className={`ml-4 p-2 rounded-lg transition-colors ${
                    skill.active
                      ? 'bg-green-100 text-green-600 hover:bg-green-200'
                      : 'bg-gray-100 text-gray-400 hover:bg-gray-200'
                  }`}
                >
                  {skill.active ? <CheckCircle size={20} /> : <XCircle size={20} />}
                </button>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Category:</span>
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-semibold">
                    {skill.category}
                  </span>
                </div>

                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Level:</span>
                  <span className="font-semibold text-gray-800">{skill.level}</span>
                </div>

                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Tokens:</span>
                  <span className="font-semibold text-gray-800">~{skill.estimated_tokens}</span>
                </div>

                <div className="mt-3">
                  <p className="text-xs text-gray-600 mb-1">Triggers:</p>
                  <div className="flex flex-wrap gap-1">
                    {skill.triggers.map((trigger, i) => (
                      <span key={i} className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                        {trigger}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
