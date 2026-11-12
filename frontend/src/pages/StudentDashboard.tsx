import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { academicApi, agentApi } from '../api/client'
import { useAuthStore } from '../store/authStore'
import { useNavigate } from 'react-router-dom'
import {
  RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer,
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, BarChart, Bar,
} from 'recharts'

function StatCard({ title, value, subtitle, color }: any) {
  return (
    <div className={`bg-white border border-gray-200 rounded-xl p-5 border-l-4 ${color}`}>
      <p className="text-sm text-gray-500">{title}</p>
      <p className="text-2xl font-bold text-gray-900 mt-1">{value ?? '—'}</p>
      {subtitle && <p className="text-xs text-gray-400 mt-1">{subtitle}</p>}
    </div>
  )
}

function AgentButton({ label, emoji, onClick, loading, color }: any) {
  return (
    <button
      onClick={onClick} disabled={loading}
      className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold text-white transition disabled:opacity-60 ${color}`}
    >
      <span>{emoji}</span> {loading ? 'Running...' : label}
    </button>
  )
}

export default function StudentDashboard() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const [agentResult, setAgentResult] = useState<any>(null)
  const [activeAgent, setActiveAgent] = useState('')

  const { data: analytics, isLoading: analyticsLoading } = useQuery({
    queryKey: ['analytics'],
    queryFn: () => academicApi.getAnalytics().then(r => r.data),
  })

  const runAgent = useMutation({
    mutationFn: (fn: () => Promise<any>) => fn().then(r => r.data),
    onSuccess: (data) => setAgentResult(data),
  })

  const handleAgent = (name: string, fn: () => Promise<any>) => {
    setActiveAgent(name)
    runAgent.mutate(fn)
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const subjectRadarData = analytics?.subject_performance?.slice(0, 8).map((s: any) => ({
    subject: s.subject.substring(0, 12),
    percentage: s.percentage,
  })) || []

  const semesterData = analytics?.semester_averages || []

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🎓</span>
          <div>
            <h1 className="font-bold text-gray-900">Student AI Platform</h1>
            <p className="text-xs text-gray-500">Welcome, {user?.name}</p>
          </div>
        </div>
        <nav className="flex items-center gap-4 text-sm">
          <a href="/dashboard" className="text-blue-600 font-medium">Dashboard</a>
          <a href="/skills" className="text-gray-600 hover:text-blue-600">Skills</a>
          <a href="/career" className="text-gray-600 hover:text-blue-600">Career</a>
          <a href="/resume" className="text-gray-600 hover:text-blue-600">Resume</a>
          <a href="/interview" className="text-gray-600 hover:text-blue-600">Interview</a>
          <button onClick={handleLogout} className="text-red-500 hover:text-red-700 font-medium">Logout</button>
        </nav>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8 space-y-8">
        {/* Stats Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard title="CGPA" value={analytics?.cgpa ?? 'N/A'} subtitle="Current cumulative" color="border-blue-500" />
          <StatCard title="Subjects" value={analytics?.total_subjects ?? 0} subtitle="Total records" color="border-green-500" />
          <StatCard title="Weak Subjects" value={analytics?.weak_subjects?.length ?? 0} subtitle="Below 50%" color="border-red-500" />
          <StatCard title="Semesters" value={analytics?.semester_averages?.length ?? 0} subtitle="Completed" color="border-purple-500" />
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="font-semibold text-gray-800 mb-4">📈 Semester Performance Trend</h2>
            {semesterData.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={semesterData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="semester" label={{ value: 'Semester', position: 'insideBottom', offset: -5 }} />
                  <YAxis domain={[0, 100]} />
                  <Tooltip />
                  <Line type="monotone" dataKey="average" stroke="#3b82f6" strokeWidth={2} dot={{ r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-center text-gray-400 py-12 text-sm">
                No academic records yet. Add your marks to see the chart.
              </div>
            )}
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="font-semibold text-gray-800 mb-4">🕸️ Subject Performance Radar</h2>
            {subjectRadarData.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <RadarChart data={subjectRadarData}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11 }} />
                  <Radar name="Score" dataKey="percentage" stroke="#7c5cd8" fill="#7c5cd8" fillOpacity={0.3} />
                  <Tooltip />
                </RadarChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-center text-gray-400 py-12 text-sm">
                Add marks to visualize subject performance.
              </div>
            )}
          </div>
        </div>

        {/* AI Agents Panel */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="font-semibold text-gray-800 mb-4">🤖 AI Analysis Agents</h2>
          <div className="flex flex-wrap gap-3 mb-6">
            <AgentButton label="Full Pipeline" emoji="⚡" color="bg-blue-600 hover:bg-blue-700"
              loading={runAgent.isPending && activeAgent === 'pipeline'}
              onClick={() => handleAgent('pipeline', agentApi.runFullPipeline)} />
            <AgentButton label="Academic Analysis" emoji="📊" color="bg-indigo-600 hover:bg-indigo-700"
              loading={runAgent.isPending && activeAgent === 'academic'}
              onClick={() => handleAgent('academic', agentApi.analyzePerformance)} />
            <AgentButton label="Skill Gap" emoji="🔍" color="bg-purple-600 hover:bg-purple-700"
              loading={runAgent.isPending && activeAgent === 'skill'}
              onClick={() => handleAgent('skill', agentApi.detectSkillGaps)} />
            <AgentButton label="Career Match" emoji="💼" color="bg-green-600 hover:bg-green-700"
              loading={runAgent.isPending && activeAgent === 'career'}
              onClick={() => handleAgent('career', agentApi.getCareerRecommendations)} />
            <AgentButton label="Learning Path" emoji="🗺️" color="bg-orange-600 hover:bg-orange-700"
              loading={runAgent.isPending && activeAgent === 'learning'}
              onClick={() => handleAgent('learning', agentApi.generateLearningPath)} />
          </div>

          {runAgent.isPending && (
            <div className="flex items-center gap-3 text-blue-600 text-sm animate-pulse">
              <span>🤖</span> AI agent is running analysis...
            </div>
          )}

          {agentResult && (
            <div className="mt-4 bg-gray-50 rounded-lg border border-gray-200 p-4 overflow-auto max-h-80">
              <p className="text-xs text-gray-400 mb-2 font-mono">Agent Result — {activeAgent}</p>
              <pre className="text-xs text-gray-700 whitespace-pre-wrap">
                {JSON.stringify(agentResult, null, 2)}
              </pre>
            </div>
          )}

          {runAgent.isError && (
            <div className="mt-4 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3">
              {(runAgent.error as any)?.response?.data?.detail || 'Agent failed. Check your profile and marks data.'}
            </div>
          )}
        </div>

        {/* Weak Subjects Alert */}
        {analytics?.weak_subjects?.length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4">
            <h3 className="font-semibold text-red-800 text-sm mb-2">⚠️ Subjects Needing Attention</h3>
            <div className="flex flex-wrap gap-2">
              {analytics.weak_subjects.map((s: string) => (
                <span key={s} className="bg-red-100 text-red-700 text-xs font-medium px-3 py-1 rounded-full">
                  {s}
                </span>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
