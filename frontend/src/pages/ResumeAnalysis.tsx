import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { resumeApi } from '../api/client'

export default function ResumeAnalysis() {
  const [file, setFile] = useState<File | null>(null)
  const [uploadResult, setUploadResult] = useState<any>(null)
  const [analysis, setAnalysis] = useState<any>(null)

  const upload = useMutation({
    mutationFn: (f: File) => resumeApi.upload(f).then(r => r.data),
    onSuccess: (data) => setUploadResult(data),
  })

  const analyze = useMutation({
    mutationFn: (id: string) => resumeApi.analyze(id).then(r => r.data),
    onSuccess: (data) => setAnalysis(data),
  })

  return (
    <div className="min-h-screen bg-gray-50 px-6 py-8">
      <div className="max-w-3xl mx-auto space-y-6">
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h1 className="text-xl font-bold text-gray-900 mb-1">📄 Resume Analysis</h1>
          <p className="text-gray-500 text-sm mb-5">Upload your PDF resume for AI-powered ATS scoring and improvement suggestions.</p>

          <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-blue-400 transition">
            <input type="file" accept=".pdf" className="hidden" id="resume-upload"
              onChange={(e) => setFile(e.target.files?.[0] || null)} />
            <label htmlFor="resume-upload" className="cursor-pointer">
              <div className="text-4xl mb-3">📎</div>
              <p className="text-sm text-gray-600">
                {file ? <span className="font-medium text-blue-600">{file.name}</span> : 'Click to select your resume PDF'}
              </p>
              <p className="text-xs text-gray-400 mt-1">PDF only, max 5MB</p>
            </label>
          </div>

          <button
            onClick={() => file && upload.mutate(file)} disabled={!file || upload.isPending}
            className="mt-4 w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2.5 rounded-lg transition disabled:opacity-50"
          >
            {upload.isPending ? 'Uploading...' : 'Upload Resume'}
          </button>
        </div>

        {uploadResult && (
          <div className="bg-green-50 border border-green-200 rounded-xl p-4 text-sm">
            <p className="font-semibold text-green-800">✅ Resume uploaded — Version {uploadResult.version}</p>
            <button
              onClick={() => analyze.mutate(uploadResult.resume_id)} disabled={analyze.isPending}
              className="mt-3 bg-purple-600 hover:bg-purple-700 text-white font-semibold px-6 py-2 rounded-lg text-sm transition disabled:opacity-50"
            >
              {analyze.isPending ? '🤖 Analyzing...' : '🤖 Run AI Analysis'}
            </button>
          </div>
        )}

        {analysis && (
          <div className="space-y-4">
            {/* ATS Score Card */}
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h2 className="font-semibold text-gray-800 mb-3">ATS Score</h2>
              <div className="flex items-center gap-4">
                <div className={`text-4xl font-bold ${analysis.ats_score >= 70 ? 'text-green-600' : analysis.ats_score >= 50 ? 'text-yellow-600' : 'text-red-600'}`}>
                  {analysis.ats_score}%
                </div>
                <div>
                  <p className="font-medium text-gray-700">{analysis.overall_rating}</p>
                  <p className="text-sm text-gray-500">{analysis.overall_feedback?.substring(0, 120)}...</p>
                </div>
              </div>
              {analysis.hitl_required && (
                <div className="mt-3 bg-yellow-50 border border-yellow-200 text-yellow-800 text-xs rounded-lg px-3 py-2">
                  ⚠️ This analysis has been flagged for counsellor review due to low score.
                </div>
              )}
            </div>

            {/* Improvements */}
            {analysis.critical_issues?.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h2 className="font-semibold text-gray-800 mb-3">🔧 Critical Issues</h2>
                <ul className="space-y-2">
                  {analysis.critical_issues.map((issue: string, i: number) => (
                    <li key={i} className="flex gap-2 text-sm text-gray-700">
                      <span className="text-red-500 mt-0.5">•</span> {issue}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Missing Keywords */}
            {analysis.missing_keywords?.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h2 className="font-semibold text-gray-800 mb-3">🔑 Missing Keywords</h2>
                <div className="flex flex-wrap gap-2">
                  {analysis.missing_keywords.map((kw: string, i: number) => (
                    <span key={i} className="bg-red-50 text-red-700 text-xs font-medium px-3 py-1 rounded-full">{kw}</span>
                  ))}
                </div>
              </div>
            )}

            {/* Rewritten Summary */}
            {analysis.rewritten_summary && (
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h2 className="font-semibold text-gray-800 mb-2">✍️ Suggested Summary Rewrite</h2>
                <p className="text-sm text-gray-700 bg-blue-50 rounded-lg p-3 italic">{analysis.rewritten_summary}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
