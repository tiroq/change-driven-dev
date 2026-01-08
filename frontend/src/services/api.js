/**
 * API service for communicating with the backend.
 * Provides methods for all API endpoints.
 */

const API_BASE_URL = '/api'

class ApiService {
  async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    }

    try {
      const response = await fetch(url, config)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
      console.error('API request failed:', error)
      throw error
    }
  }

  // Projects
  async getProjects() {
    return this.request('/projects/')
  }

  async getProject(id) {
    return this.request(`/projects/${id}`)
  }

  async createProject(data) {
    return this.request('/projects/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // Tasks
  async getTasks(projectId = null) {
    const query = projectId ? `?project_id=${projectId}` : ''
    return this.request(`/tasks/${query}`)
  }

  async getTask(id) {
    return this.request(`/tasks/${id}`)
  }

  async createTask(data) {
    return this.request('/tasks/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async advanceTask(id) {
    return this.request(`/tasks/${id}/advance`, {
      method: 'POST',
    })
  }

  // Change Requests
  async getChangeRequests(taskId = null) {
    const query = taskId ? `?task_id=${taskId}` : ''
    return this.request(`/change-requests/${query}`)
  }

  async getChangeRequest(id) {
    return this.request(`/change-requests/${id}`)
  }

  async createChangeRequest(data) {
    return this.request('/change-requests/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async submitChangeRequest(id) {
    return this.request(`/change-requests/${id}/submit`, {
      method: 'POST',
    })
  }

  async approveChangeRequest(id) {
    return this.request(`/change-requests/${id}/approve`, {
      method: 'POST',
    })
  }

  async rejectChangeRequest(id) {
    return this.request(`/change-requests/${id}/reject`, {
      method: 'POST',
    })
  }
}

export default new ApiService()
