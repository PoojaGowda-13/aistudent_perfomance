import { useQuery } from '@tanstack/react-query'
import { adminApi } from '../api/client'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export default function AdminDashboard() {
  const { data: dashboard } = useQuery({
    queryKey: ['admin-dashboard'],
    queryFn: () => adminApi.getDashboard().then(r => r.data),
  })

  const { data: tokenUsage } = useQuery({
    queryKey: ['token-usage'],
    queryFn: () => adminApi.getTokenUsage().then(r => r.data),
  })

  const { data: hitlQueue } = useQuery({
    queryKey: ['hitl-queue'],
    queryFn: () => adminApi.getHitlQueue().then(r => r.data),
  })

  const overview = dashboard?.overview || {}
  const agentBreakdown = dashboard?.agent_breakdown || []
  const usageData = tokenUsage?.usage_by_provider || []

  return (
    <div className="min-h-screen bg-gray-50 px-6 py-8">
      <div className="max-w-6xl mx-auto space-y-8">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">🛡️ Admin Dashboard</h1>
          <span className="text-sm text-gray-500">Student AI Platform</span>
        </div>

        {/* Overview Stats */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {[
            { label: 'Total Users', value: overview.total_users, color: 'border-blue-500' },
            { label: 'Students', value: overview.total_students, color: 'border-green-500' },
            { label: 'Agent Calls', value: overview.total_agent_calls, color: 'border-purple-500' },
            { label: 'Total Cost', value: `$${(overview.total_cost_usd || 0).toFixed(4)}`, color: 'border-yellow-500' },
            { label: 'HITL Pending', value: overview.hitl_pending_reviews, color: 'border-red-500' },
            { label: 'Resumes', value: overview.total_resumes_uploaded, color: 'border-indigo-500' },
          ].map((stat) => (
            <div key={stat.label} className={`bg-white border border-gray-200 rounded-xl p-4 border-l-4 ${stat.color}`}>
              <p className="text-xs text-gray-500">{stat.label}</p>
              <p className="text-xl font-bold text-gray-900 mt-1">{stat.value ?? '—'}</p>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Agent Breakdown Chart */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="font-semibold text-gray-800 mb-4">🤖 Agent Calls Breakdown</h2>
            {agentBreakdown.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={agentBreakdown}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="agent" tick={{ fontSize: 10 }} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : <p className="text-gray-400 text-sm py-10 text-center">No agent call data yet.</p>}
          </div>

          {/* Token Usage */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="font-semibold text-gray-800 mb-4">💰 LLM Cost by Provider</h2>
            {usageData.length > 0 ? (
              <div className="space-y-3">
                {usageData.map((u: any) => (
                  <div key={`${u.provider}-${u.model}`} className="flex items-center justify-between text-sm">
                    <div>
                      <span className="font-medium text-gray-800">{u.provider}</span>
                      <span className="text-gray-400 ml-2 text-xs">{u.model}</span>
                    </div>
                    <div className="text-right">
                      <span className="font-bold text-gray-900">${u.total_cost_usd.toFixed(4)}</span>
                      <span className="text-gray-400 ml-2 text-xs">{u.calls} calls</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : <p className="text-gray-400 text-sm py-10 text-center">No token usage data yet.</p>}
          </div>
        </div>

        {/* HITL Queue */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="font-semibold text-gray-800 mb-4">👁️ Human-in-the-Loop Review Queue</h2>
          {hitlQueue?.length > 0 ? (
            <div className="overflow-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100 text-left text-gray-500 text-xs">
                    <th className="pb-2 pr-4">Agent</th>
                    <th className="pb-2 pr-4">Summary</th>
                    <th className="pb-2 pr-4">Created</th>
                    <th className="pb-2">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {hitlQueue.map((item: any) => (
                    <tr key={item.id} className="border-b border-gray-50 hover:bg-gray-50">
                      <td className="py-2 pr-4">
                        <span className="bg-purple-100 text-purple-700 text-xs font-medium px-2 py-0.5 rounded-full">{item.agent_type}</span>
                      </td>
                      <td className="py-2 pr-4 text-gray-700 text-xs max-w-xs truncate">{item.input_summary}</td>
                      <td className="py-2 pr-4 text-gray-400 text-xs">{new Date(item.created_at).toLocaleDateString()}</td>
                      <td className="py-2">
                        <button onClick={() => adminApi.approveHitl(item.id)}
                          className="text-xs bg-green-100 text-green-700 hover:bg-green-200 px-3 py-1 rounded-full font-medium transition">
                          Approve
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-gray-400 text-sm py-6 text-center">No items pending review. 🎉</p>
          )}
        </div>
      </div>
    </div>
  )
}
