"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

const AGENT_TYPES = ['root', 'specialist', 'coordinator', 'worker'];
const AI_MODELS = [
  'claude-3-5-sonnet-20241022',
  'claude-3-opus-20240229',
  'gpt-4-turbo-preview',
  'gpt-4',
  'gemini-pro'
];

const COMMON_SKILLS = [
  'content_creation', 'seo_optimization', 'data_analysis',
  'code_review', 'testing', 'documentation', 'api_development',
  'ui_design', 'database_optimization', 'security_audit',
  'performance_tuning', 'deployment', 'monitoring'
];

export default function NewAgentPage() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [agentType, setAgentType] = useState('specialist');
  const [description, setDescription] = useState('');
  const [skills, setSkills] = useState<string[]>([]);
  const [customSkill, setCustomSkill] = useState('');
  const [model, setModel] = useState('claude-3-5-sonnet-20241022');
  const [temperature, setTemperature] = useState(0.7);
  const [systemPrompt, setSystemPrompt] = useState('');
  const [saving, setSaving] = useState(false);

  const handleAddSkill = (skill: string) => {
    if (skill && !skills.includes(skill)) {
      setSkills([...skills, skill]);
    }
  };

  const handleRemoveSkill = (skill: string) => {
    setSkills(skills.filter(s => s !== skill));
  };

  const handleAddCustomSkill = () => {
    if (customSkill && !skills.includes(customSkill)) {
      setSkills([...skills, customSkill]);
      setCustomSkill('');
    }
  };

  const handleSave = async () => {
    if (!name || skills.length === 0) {
      alert('Please provide a name and at least one skill');
      return;
    }

    setSaving(true);
    try {
      const res = await fetch('/api/fractal/agents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          agent_type: agentType,
          description,
          skills,
          model,
          temperature,
          system_prompt: systemPrompt
        })
      });

      if (res.ok) {
        router.push('/fractal-agents');
      } else {
        alert('Failed to create agent');
      }
    } catch (err) {
      console.error(err);
      alert('Error creating agent');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <Link href="/fractal-agents" className="text-blue-600 hover:underline mb-4 inline-block">
            ← Back to agents
          </Link>
          <h1 className="text-3xl font-bold">Create New Agent</h1>
          <p className="text-gray-600 mt-1">Add a new AI agent to your FractalAgents network</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6 space-y-6">
          {/* Basic Info */}
          <div>
            <h2 className="text-lg font-semibold mb-4">Basic Information</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Agent Name *</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., ContentCreator, DataAnalyzer, CodeReviewer"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Agent Type *</label>
                <select
                  value={agentType}
                  onChange={(e) => setAgentType(e.target.value)}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  {AGENT_TYPES.map(type => (
                    <option key={type} value={type}>{type.charAt(0).toUpperCase() + type.slice(1)}</option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  Root: Main orchestrator | Specialist: Domain expert | Coordinator: Task manager | Worker: Executor
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Description</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  rows={3}
                  placeholder="Describe what this agent does..."
                />
              </div>
            </div>
          </div>

          {/* Skills */}
          <div className="pt-6 border-t">
            <h2 className="text-lg font-semibold mb-4">Skills *</h2>
            
            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-3">Select from common skills:</p>
              <div className="flex flex-wrap gap-2">
                {COMMON_SKILLS.map(skill => (
                  <button
                    key={skill}
                    onClick={() => handleAddSkill(skill)}
                    disabled={skills.includes(skill)}
                    className={`px-3 py-1 text-sm rounded-full transition-colors ${
                      skills.includes(skill)
                        ? 'bg-blue-100 text-blue-800 cursor-not-allowed'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {skill}
                  </button>
                ))}
              </div>
            </div>

            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">Or add custom skill:</p>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={customSkill}
                  onChange={(e) => setCustomSkill(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleAddCustomSkill()}
                  className="flex-1 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter custom skill..."
                />
                <button
                  onClick={handleAddCustomSkill}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Add
                </button>
              </div>
            </div>

            {skills.length > 0 && (
              <div>
                <p className="text-sm text-gray-600 mb-2">Selected skills ({skills.length}):</p>
                <div className="flex flex-wrap gap-2">
                  {skills.map(skill => (
                    <div
                      key={skill}
                      className="inline-flex items-center gap-2 px-3 py-1 bg-blue-100 text-blue-800 rounded-full"
                    >
                      <span className="text-sm">{skill}</span>
                      <button
                        onClick={() => handleRemoveSkill(skill)}
                        className="text-blue-600 hover:text-blue-800"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* AI Configuration */}
          <div className="pt-6 border-t">
            <h2 className="text-lg font-semibold mb-4">AI Configuration</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">AI Model</label>
                <select
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  {AI_MODELS.map(m => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Temperature: {temperature}
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={temperature}
                  onChange={(e) => setTemperature(parseFloat(e.target.value))}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>Focused (0.0)</span>
                  <span>Balanced (0.5)</span>
                  <span>Creative (1.0)</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">System Prompt (Optional)</label>
                <textarea
                  value={systemPrompt}
                  onChange={(e) => setSystemPrompt(e.target.value)}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                  rows={6}
                  placeholder="You are a specialized AI agent that..."
                />
                <p className="text-xs text-gray-500 mt-1">
                  Custom instructions for this agent. Leave empty to use default.
                </p>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-between pt-6 border-t">
            <p className="text-sm text-gray-600">
              * Required fields
            </p>
            <div className="flex gap-3">
              <Link
                href="/fractal-agents"
                className="px-6 py-2 border rounded-lg hover:bg-gray-50"
              >
                Cancel
              </Link>
              <button
                onClick={handleSave}
                disabled={saving || !name || skills.length === 0}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving ? 'Creating...' : 'Create Agent'}
              </button>
            </div>
          </div>
        </div>

        {/* Preview */}
        {name && skills.length > 0 && (
          <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h3 className="font-semibold text-blue-900 mb-3">Preview</h3>
            <div className="space-y-2 text-sm">
              <p><span className="font-medium">Name:</span> {name}</p>
              <p><span className="font-medium">Type:</span> {agentType}</p>
              <p><span className="font-medium">Skills:</span> {skills.join(', ')}</p>
              <p><span className="font-medium">Model:</span> {model}</p>
              <p><span className="font-medium">Temperature:</span> {temperature}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
