import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { agentApi } from '../api/client'

export default function InterviewPrep() {
  const [role, setRole] = useState('Software Engineer')
  const [numQ, setNumQ] = useState(5)
  const [session, setSession] = useState<any>(null)
  const [currentQ, setCurrentQ] = useState(0)
  const [answer, setAnswer] = useState('')
  const [evaluation, setEvaluation] = useState<any>(null)

  const startInterview = useMutation({
    mutationFn: () => agentApi.startInterview({ role, num_questions: numQ }).then(r => r.data),
    onSuccess: (data) => { setSession(data); setCurrentQ(0); setEvaluation(null) },
  })

  const submitAnswer = useMutation({
    mutationFn: () => agentApi.evaluateAnswer({
      session_id: session.session_id,
      question_index: currentQ,
      answer,
    }).then(r => r.data),
    onSuccess: (data) => setEvaluation(data),
  })

  const questions = session?.result?.questions || []
  const currentQuestion = questions[currentQ]

  return (
    <div className="min-h-screen bg-gray-50 px-6 py-8">
      <div className="max-w-3xl mx-auto space-y-6">
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h1 className="text-xl font-bold text-gray-900 mb-1">🎤 Interview Preparation</h1>
          <p className="text-gray-500 text-sm mb-5">Practice role-specific interview questions with AI evaluation.</p>

          <div className="flex gap-4 mb-4">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">Target Role</label>
              <input type="text" value={role} onChange={(e) => setRole(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g. Software Engineer" />
            </div>
            <div className="w-32">
              <label className="block text-sm font-medium text-gray-700 mb-1">Questions</label>
              <select value={numQ} onChange={(e) => setNumQ(Number(e.target.value))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm">
                {[3, 5, 7, 10].map(n => <option key={n} value={n}>{n}</option>)}
              </select>
            </div>
          </div>

          <button onClick={() => startInterview.mutate()} disabled={startInterview.isPending}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2.5 rounded-lg transition disabled:opacity-50">
            {startInterview.isPending ? '🤖 Generating questions...' : '🎯 Start Mock Interview'}
          </button>
        </div>

        {session && questions.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-gray-800">
                Question {currentQ + 1} of {questions.length}
              </h2>
              <div className="flex gap-2">
                <span className={`text-xs px-2 py-1 rounded-full font-medium
                  ${currentQuestion?.difficulty === 'Easy' ? 'bg-green-100 text-green-700' :
                    currentQuestion?.difficulty === 'Medium' ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'}`}>
                  {currentQuestion?.difficulty}
                </span>
                <span className="text-xs px-2 py-1 rounded-full bg-blue-100 text-blue-700 font-medium">
                  {currentQuestion?.type}
                </span>
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4 border border-gray-100">
              <p className="text-gray-800 font-medium">{currentQuestion?.question}</p>
              <p className="text-xs text-gray-400 mt-2">Topic: {currentQuestion?.topic}</p>
            </div>

            <textarea
              value={answer} onChange={(e) => setAnswer(e.target.value)}
              rows={5}
              className="w-full border border-gray-300 rounded-lg px-4 py-3 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Type your answer here..."
            />

            <div className="flex gap-3">
              <button onClick={() => submitAnswer.mutate()} disabled={!answer || submitAnswer.isPending}
                className="flex-1 bg-green-600 hover:bg-green-700 text-white font-semibold py-2.5 rounded-lg transition disabled:opacity-50">
                {submitAnswer.isPending ? '🤖 Evaluating...' : '✅ Submit Answer'}
              </button>
              {currentQ < questions.length - 1 && (
                <button onClick={() => { setCurrentQ(c => c + 1); setAnswer(''); setEvaluation(null) }}
                  className="px-5 bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold py-2.5 rounded-lg transition">
                  Next →
                </button>
              )}
            </div>

            {evaluation && (
              <div className="mt-4 space-y-3">
                <div className={`p-4 rounded-xl border ${evaluation.result?.score >= 7 ? 'bg-green-50 border-green-200' : evaluation.result?.score >= 5 ? 'bg-yellow-50 border-yellow-200' : 'bg-red-50 border-red-200'}`}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold text-lg">{evaluation.result?.grade}</span>
                    <span className={`text-2xl font-bold ${evaluation.result?.score >= 7 ? 'text-green-600' : evaluation.result?.score >= 5 ? 'text-yellow-600' : 'text-red-600'}`}>
                      {evaluation.result?.score}/10
                    </span>
                  </div>
                  <p className="text-sm text-gray-700">{evaluation.result?.detailed_feedback}</p>
                </div>

                {evaluation.result?.model_answer && (
                  <div className="bg-blue-50 border border-blue-100 rounded-xl p-4">
                    <p className="text-xs font-semibold text-blue-700 mb-1">💡 Model Answer</p>
                    <p className="text-sm text-gray-700">{evaluation.result.model_answer}</p>
                  </div>
                )}

                {evaluation.hitl_required && (
                  <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 text-xs rounded-lg px-3 py-2">
                    ⚠️ Low confidence evaluation — flagged for counsellor review.
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
