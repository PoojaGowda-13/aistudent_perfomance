import axios from 'axios'

const API_BASE = '/api'

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Auto-logout on 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// ─── Auth ──────────────────────────────────────────────────────────────────
export const authApi = {
  register: (data: any) => api.post('/auth/register', data),
  login: (data: any) => api.post('/auth/login', data),
}

// ─── Students ─────────────────────────────────────────────────────────────
export const studentApi = {
  getProfile: () => api.get('/students/me/profile'),
  updateProfile: (data: any) => api.put('/students/me/profile', data),
  getSkills: () => api.get('/students/me/skills'),
  addSkill: (data: any) => api.post('/students/me/skills', data),
  getCareerGoals: () => api.get('/students/me/career-goals'),
  addCareerGoal: (data: any) => api.post('/students/me/career-goals', data),
}

// ─── Academic ─────────────────────────────────────────────────────────────
export const academicApi = {
  getRecords: () => api.get('/academic/records'),
  addRecord: (data: any) => api.post('/academic/records', data),
  addBulkRecords: (data: any[]) => api.post('/academic/records/bulk', data),
  getAnalytics: () => api.get('/academic/analytics'),
}

// ─── Agents ───────────────────────────────────────────────────────────────
export const agentApi = {
  runFullPipeline: () => api.post('/agents/full-pipeline'),
  analyzePerformance: () => api.post('/agents/analyze-performance'),
  detectSkillGaps: () => api.post('/agents/detect-skill-gaps'),
  getCareerRecommendations: () => api.post('/agents/career-recommendations'),
  generateLearningPath: () => api.post('/agents/learning-path'),
  startInterview: (data: { role: string; num_questions: number }) => api.post('/agents/interview/start', data),
  evaluateAnswer: (data: { session_id: string; question_index: number; answer: string }) =>
    api.post('/agents/interview/evaluate', data),
}

// ─── Resume ───────────────────────────────────────────────────────────────
export const resumeApi = {
  upload: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/resume/upload', form, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
  analyze: (resumeId: string) => api.post(`/resume/analyze/${resumeId}`),
  getHistory: () => api.get('/resume/history'),
}

// ─── Admin ────────────────────────────────────────────────────────────────
export const adminApi = {
  getDashboard: () => api.get('/admin/dashboard'),
  getTokenUsage: () => api.get('/admin/token-usage'),
  getHitlQueue: () => api.get('/admin/hitl-queue'),
  approveHitl: (sessionId: string) => api.post(`/admin/hitl-queue/${sessionId}/approve`),
  getUsers: () => api.get('/admin/users'),
}
