import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Create axios instance
const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authApi = {
  login: async (username: string, password: string) => {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)
    
    const response = await api.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  getCurrentUser: async () => {
    const response = await api.get('/auth/me')
    return response.data
  },

  createUser: async (userData: { username: string; password: string; role_name: string }) => {
    const response = await api.post('/auth/users', userData)
    return response.data
  },

  deleteUser: async (userId: number) => {
    const response = await api.delete(`/auth/users/${userId}`)
    return response.data
  },
}

// Employee API
export const employeeApi = {
  getEmployees: async (params?: { page?: number; per_page?: number; search?: string }) => {
    const response = await api.get('/employees', { params })
    return response.data
  },

  getEmployee: async (employeeId: string) => {
    const response = await api.get(`/employees/${employeeId}`)
    return response.data
  },

  createEmployee: async (employeeData: any) => {
    const response = await api.post('/employees', employeeData)
    return response.data
  },

  updateEmployee: async (employeeId: string, employeeData: any) => {
    const response = await api.put(`/employees/${employeeId}`, employeeData)
    return response.data
  },

  deleteEmployee: async (employeeId: string) => {
    const response = await api.delete(`/employees/${employeeId}`)
    return response.data
  },

  enrollFaces: async (employeeId: string, files: FileList) => {
    const formData = new FormData()
    Array.from(files).forEach(file => {
      formData.append('files', file)
    })
    
    const response = await api.post(`/employees/${employeeId}/enroll`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  getEmbeddings: async (employeeId: string) => {
    const response = await api.get(`/employees/${employeeId}/embeddings`)
    return response.data
  },

  deleteEmbedding: async (employeeId: string, embeddingId: number) => {
    const response = await api.delete(`/employees/${employeeId}/embeddings/${embeddingId}`)
    return response.data
  },
}

// Attendance API
export const attendanceApi = {
  getAttendanceRecords: async (params?: any) => {
    const response = await api.get('/attendance', { params })
    return response.data
  },

  getPresentEmployees: async () => {
    const response = await api.get('/attendance/present')
    return response.data
  },

  getEmployeeAttendance: async (employeeId: string, params?: any) => {
    const response = await api.get(`/attendance/employee/${employeeId}`, { params })
    return response.data
  },

  getAttendanceSummary: async (employeeId: string, params?: any) => {
    const response = await api.get(`/attendance/summary/${employeeId}`, { params })
    return response.data
  },
}

// Admin API
export const adminApi = {
  getDashboard: async () => {
    const response = await api.get('/admin/dashboard')
    return response.data
  },

  getUsers: async () => {
    const response = await api.get('/admin/users')
    return response.data
  },

  updateUserStatus: async (userId: number, status: string) => {
    const response = await api.put(`/admin/users/${userId}/status`, { status })
    return response.data
  },

  getSystemLogs: async (params?: any) => {
    const response = await api.get('/admin/system-logs', { params })
    return response.data
  },

  getRoles: async () => {
    const response = await api.get('/admin/roles')
    return response.data
  },

  cleanupLogs: async (days: number) => {
    const response = await api.delete(`/admin/system-logs/cleanup?days=${days}`)
    return response.data
  },
}

// Camera API
export const cameraApi = {
  getStatus: async () => {
    const response = await api.get('/camera/status')
    return response.data
  },

  startCamera: async () => {
    const response = await api.post('/camera/start')
    return response.data
  },

  stopCamera: async () => {
    const response = await api.post('/camera/stop')
    return response.data
  },

  getConfig: async () => {
    const response = await api.get('/camera/config')
    return response.data
  },

  updateConfig: async (config: any) => {
    const response = await api.put('/camera/config', config)
    return response.data
  },
}

export default api