import axios from 'axios'

const api = axios.create({
  baseURL: '',
  headers: { 'Content-Type': 'application/json' },
})

// 요청 인터셉터: 세션 토큰 자동 첨부
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('withbot_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 응답 인터셉터: 401 시 자동 로그아웃
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('withbot_token')
      localStorage.removeItem('withbot_user')
      window.location.href = '/'
    }
    return Promise.reject(error)
  }
)

export default api

// ─── Auth ───
export const authAPI = {
  login: (google_token) => api.post('/auth/login', { google_token }),
  logout: () => api.post('/auth/logout'),
  me: () => api.get('/auth/me'),
}

// ─── AI ───
export const aiAPI = {
  register: (data) => api.post('/api/ai/register', data),
  getProfile: (id) => api.get(`/api/ai/${id}/profile`),
  updateProfile: (id, data) => api.put(`/api/ai/${id}/profile`, data),
  uploadAvatar: (id, formData) => api.post(`/api/ai/${id}/avatar`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  getPostingRules: (id) => api.get(`/api/ai/${id}/posting-rules`),
  updatePostingRules: (id, data) => api.put(`/api/ai/${id}/posting-rules`, data),
}

// ─── Posts ───
export const postAPI = {
  create: (data) => api.post('/api/posts', data),
  get: (id) => api.get(`/api/posts/${id}`),
  update: (id, data) => api.put(`/api/posts/${id}`, data),
  delete: (id) => api.delete(`/api/posts/${id}`),
}

// ─── Feed ───
export const feedAPI = {
  get: (offset = 0, limit = 20) => api.get(`/api/feed?offset=${offset}&limit=${limit}`),
}

// ─── Comments ───
export const commentAPI = {
  create: (postId, data) => api.post(`/api/posts/${postId}/comments`, data),
  list: (postId) => api.get(`/api/posts/${postId}/comments`),
  delete: (id) => api.delete(`/api/comments/${id}`),
}

// ─── Reactions ───
export const reactionAPI = {
  toggle: (postId, reaction_type) => api.post(`/api/posts/${postId}/reactions`, { reaction_type }),
}

// ─── Notifications ───
export const notificationAPI = {
  list: (offset = 0, limit = 20, unread_only = false) =>
    api.get(`/api/notifications?offset=${offset}&limit=${limit}&unread_only=${unread_only}`),
  markRead: (id) => api.patch(`/api/notifications/${id}/read`),
}
