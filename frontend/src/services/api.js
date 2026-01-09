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
        const errorBody = await response.text()
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorBody}`)
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

  async getTaskVersions(taskId) {
    return this.request(`/tasks/${taskId}/versions`)
  }

  async splitTask(taskId, projectId, task1Title, task1Description, task2Title, task2Description) {
    return this.request(`/tasks/${taskId}/split?project_id=${projectId}`, {
      method: 'POST',
      body: JSON.stringify({
        task1_title: task1Title,
        task1_description: task1Description,
        task2_title: task2Title,
        task2_description: task2Description,
      }),
    })
  }

  async mergeTasks(projectId, taskIds, mergedTitle, mergedDescription) {
    return this.request(`/tasks/merge?project_id=${projectId}`, {
      method: 'POST',
      body: JSON.stringify({
        task_ids: taskIds,
        merged_title: mergedTitle,
        merged_description: mergedDescription,
      }),
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

  // Artifacts
  async getArtifacts(projectId = null, artifactType = null) {
    const params = new URLSearchParams()
    if (projectId) params.append('project_id', projectId)
    if (artifactType) params.append('artifact_type', artifactType)
    const query = params.toString() ? `?${params.toString()}` : ''
    return this.request(`/artifacts/${query}`)
  }

  async getArtifact(id) {
    return this.request(`/artifacts/${id}`)
  }

  async getArtifactContent(id) {
    return this.request(`/artifacts/${id}/content`)
  }

  async downloadArtifact(id) {
    window.open(`${API_BASE_URL}/artifacts/${id}/download`, '_blank')
  }

  // Phase execution
  async runPlanner(projectId, specContent, engineName = null) {
    return this.request('/phase/plan', {
      method: 'POST',
      body: JSON.stringify({
        project_id: projectId,
        spec_content: specContent,
        engine_name: engineName
      }),
    })
  }

  // WebSocket connection
  connectWebSocket(projectId = null, onMessage) {
    const wsUrl = projectId 
      ? `ws://localhost:8000/ws/projects/${projectId}`
      : `ws://localhost:8000/ws`
    
    const ws = new WebSocket(wsUrl)
    
    ws.onopen = () => {
      console.log(`WebSocket connected${projectId ? ` for project ${projectId}` : ' (global)'}`)
      // Send ping every 30 seconds to keep connection alive
      const pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send('ping')
        } else {
          clearInterval(pingInterval)
        }
      }, 30000)
      ws.pingInterval = pingInterval
    }
    
    ws.onmessage = (event) => {
      if (event.data === 'pong') return
      try {
        const data = JSON.parse(event.data)
        onMessage(data)
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
    
    ws.onclose = () => {
      console.log('WebSocket disconnected')
      if (ws.pingInterval) {
        clearInterval(ws.pingInterval)
      }
    }
    
    return ws
  }
}

export default new ApiService()
