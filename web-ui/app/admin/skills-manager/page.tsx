'use client'

import { useState, useEffect } from 'react'
import { Zap, Plus, TrendingDown, Edit, Trash2, Save } from 'lucide-react'

interface Skill {
  name: string
  description: string
  category: string
  level: number
  triggers: string[]
  active: boolean
  usage_count: number
  estimated_tokens: {
    level1: number
    level2: number
    level3: number
  }
}

export default function SkillsManagerAdminPage() {
  const [skills, setSkills] = useState<Skill[]>([])
  const [loading, setLoading] = useState(true)
  const [editingSkill, setEditingSkill] = useState<string | null>(null)

  useEffect(() => {
    loadSkills()
  }, [])

  const loadSkills = async () => {
    try {
      // Mock data
      const mockSkills: Skill[] = [
        {
          name: 'backend-development',
          description: 'Backend development and API design',
          category: 'development',
          level: 1,
          triggers: ['backend', 'api', 'server'],
          active: true,
          usage_count: 145,
          estimated_tokens: { level1: 50, level2: 500, level3: 2000 }
        },
        {
          name: 'frontend-development',
          description: 'Frontend development and UI design',
          category: 'development',
          level: 1,
          triggers: ['frontend', 'ui', 'react'],
          active: true,
          usage_count: 98,
          estimated_tokens: { level1: 50, level2: 500, level3: 2000 }
        },
        {
          name: 'database-design',
          description: 'Database schema design and optimization',
          category: 'data',
          level: 1,
          triggers: ['database', 'sql', 'schema'],
          active: false,
          usage_count: 67,
          estimated_tokens: { level1: 50, level2: 500, level3: 2000 }
        }
      ]

      setSkills(mockSkills)
      setLoading(false)
    } catch (error) {
      console.error('Failed to load skills:', error)
      setLoading(false)
    }
  }

  const deleteSkill = async (skillName: string) => {
    if (!confirm(`Delete skill "${skillName}"?`)) return
    setSkills(skills.filter(s => s.name !== skillName))
  }

  const totalContextSaved = 90 // Mock value

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-8 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading skills...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 flex items-center gap-3">
              <Zap className="text-blue-600" size={40} />
              Skills Manager
            </h1>
            <p className="text-gray-600 mt-2">
              Progressive Disclosure System - 90% context savings
            </p>
          </div>
          <button className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-semibold hover:shadow-lg transition-all flex items-center gap-2">
            <Plus size={20} />
            Add Skill
          </button>
        </div>

        {/* Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-blue-500">
            <p className="text-gray-600 text-sm">Total Skills</p>
            <p className="text-3xl font-bold text-gray-900">{skills.length}</p>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-green-500">
            <p className="text-gray-600 text-sm">Active Skills</p>
            <p className="text-3xl font-bold text-gray-900">
              {skills.filter(s => s.active).length}
            </p>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-purple-500">
            <p className="text-gray-600 text-sm">Total Usage</p>
            <p className="text-3xl font-bold text-gray-900">
              {skills.reduce((sum, s) => sum + s.usage_count, 0)}
            </p>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-emerald-500">
            <div className="flex items-center gap-2 mb-1">
              <TrendingDown className="text-emerald-600" size={20} />
              <p className="text-gray-600 text-sm">Context Saved</p>
            </div>
            <p className="text-3xl font-bold text-emerald-600">{totalContextSaved}%</p>
          </div>
        </div>

        {/* Skills Table */}
        <div className="bg-white rounded-xl shadow-md overflow-hidden">
          <div className="p-6 bg-gradient-to-r from-blue-600 to-purple-600 text-white">
            <h2 className="text-2xl font-bold">All Skills</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase">Skill</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase">Category</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase">Triggers</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase">Usage</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase">Tokens</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase">Status</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {skills.map((skill) => (
                  <tr key={skill.name} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div>
                        <p className="font-semibold text-gray-900">{skill.name}</p>
                        <p className="text-sm text-gray-600">{skill.description}</p>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-semibold">
                        {skill.category}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-wrap gap-1">
                        {skill.triggers.slice(0, 2).map((trigger, i) => (
                          <span key={i} className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                            {trigger}
                          </span>
                        ))}
                        {skill.triggers.length > 2 && (
                          <span className="px-2 py-1 bg-gray-200 text-gray-600 rounded text-xs">
                            +{skill.triggers.length - 2}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="font-semibold text-gray-900">{skill.usage_count}</span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-xs text-gray-600">
                        <div>L1: {skill.estimated_tokens.level1}</div>
                        <div>L2: {skill.estimated_tokens.level2}</div>
                        <div>L3: {skill.estimated_tokens.level3}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                        skill.active 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {skill.active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex gap-2">
                        <button className="p-2 hover:bg-blue-100 rounded-lg transition-colors">
                          <Edit size={16} className="text-blue-600" />
                        </button>
                        <button 
                          onClick={() => deleteSkill(skill.name)}
                          className="p-2 hover:bg-red-100 rounded-lg transition-colors"
                        >
                          <Trash2 size={16} className="text-red-600" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
