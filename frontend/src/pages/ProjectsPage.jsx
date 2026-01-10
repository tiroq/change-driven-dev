import React, { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

function ProjectsPage({ onProjectSelect }) {
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [wsConnected, setWsConnected] = useState(false)
  const [notification, setNotification] = useState(null)
  const wsRef = useRef(null)
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    root_path: '',
    default_engine: 'copilot_cli'
  })
  const navigate = useNavigate()

  useEffect(() => {
    loadProjects()
  }, [])

  // WebSocket connection for real-time updates
  useEffect(() => {
    const connectWebSocket = () => {
      try {
        const ws = api.connectWebSocket(null) // Global connection
        
        ws.onopen = () => {
          console.log('WebSocket connected (global)')
          setWsConnected(true)
        }
        
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            console.log('WebSocket event received:', data)
            
            // Handle project-related events
            if (data.event_type === 'project_created' || 
                data.event_type === 'project_updated' || 
                data.event_type === 'project_deleted') {
              
              // Refresh projects
              loadProjects()
              
              // Show notification
              const eventLabels = {
                project_created: 'Project Created',
                project_updated: 'Project Updated',
                project_deleted: 'Project Deleted'
              }
              setNotification({
                message: eventLabels[data.event_type] || 'Project Event',
                timestamp: new Date().toLocaleTimeString()
              })
              setTimeout(() => setNotification(null), 3000)
            }
          } catch (err) {
            console.error('Error parsing WebSocket message:', err)
          }
        }
        
        ws.onerror = (err) => {
          console.error('WebSocket error:', err)
          setWsConnected(false)
        }
        
        ws.onclose = () => {
          console.log('WebSocket disconnected')
          setWsConnected(false)
          // Attempt reconnection after 5 seconds
          setTimeout(connectWebSocket, 5000)
        }
        
        wsRef.current = ws
      } catch (err) {
        console.error('Failed to connect WebSocket:', err)
      }
    }
    
    connectWebSocket()
    
    // Cleanup on unmount
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  const loadProjects = async () => {
    try {
      setLoading(true)
      const data = await api.getProjects()
      setProjects(data)
      setError(null)
    } catch (err) {
      setError('Failed to load projects: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateProject = async (e) => {
    e.preventDefault()
    try {
      await api.createProject(formData)
      setShowCreateForm(false)
      setFormData({ name: '', description: '', root_path: '', default_engine: 'copilot_cli' })
      loadProjects()
    } catch (err) {
      setError('Failed to create project: ' + err.message)
    }
  }

  const handleViewProject = (projectId) => {
    // Set the selected project
    if (onProjectSelect) {
      onProjectSelect(projectId)
    }
    navigate(`/tasks?project_id=${projectId}`)
  }

  if (loading) {
    return (
      <div className="page">
        <h2>Projects</h2>
        <p>Loading projects...</p>
      </div>
    )
  }

  return (
    <div className="page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h2>Projects</h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            padding: '0.5rem 1rem',
            backgroundColor: wsConnected ? '#d4edda' : '#f8d7da',
            color: wsConnected ? '#155724' : '#721c24',
            borderRadius: '4px',
            fontSize: '0.875rem'
          }}>
            <span style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: wsConnected ? '#28a745' : '#dc3545',
              marginRight: '0.5rem'
            }}></span>
            {wsConnected ? 'Live' : 'Disconnected'}
          </div>
          <button 
            onClick={() => setShowCreateForm(!showCreateForm)}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            {showCreateForm ? 'Cancel' : '+ New Project'}
          </button>
        </div>
      </div>

      {notification && (
        <div style={{
          position: 'fixed',
          top: '20px',
          right: '20px',
          padding: '1rem 1.5rem',
          backgroundColor: '#28a745',
          color: 'white',
          borderRadius: '4px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
          zIndex: 1000,
          animation: 'slideIn 0.3s ease-out'
        }}>
          <div style={{ fontWeight: 'bold' }}>{notification.message}</div>
          <div style={{ fontSize: '0.85rem', marginTop: '0.25rem', opacity: 0.9 }}>
            {notification.timestamp}
          </div>
        </div>
      )}

      {error && (
        <div style={{ 
          padding: '1rem', 
          backgroundColor: '#fee', 
          color: '#c33',
          borderRadius: '4px',
          marginBottom: '1rem'
        }}>
          {error}
        </div>
      )}

      {showCreateForm && (
        <div style={{
          padding: '1.5rem',
          backgroundColor: '#f8f9fa',
          borderRadius: '8px',
          marginBottom: '2rem'
        }}>
          <h3>Create New Project</h3>
          <form onSubmit={handleCreateProject}>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                Project Name *
              </label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: '1px solid #ddd',
                  borderRadius: '4px'
                }}
              />
            </div>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: '1px solid #ddd',
                  borderRadius: '4px'
                }}
              />
            </div>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                Root Path (optional)
              </label>
              <input
                type="text"
                value={formData.root_path}
                onChange={(e) => setFormData({ ...formData, root_path: e.target.value })}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: '1px solid #ddd',
                  borderRadius: '4px'
                }}
                placeholder="/path/to/project"
              />
            </div>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                Default Engine
              </label>
              <select
                value={formData.default_engine}
                onChange={(e) => setFormData({ ...formData, default_engine: e.target.value })}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: '1px solid #ddd',
                  borderRadius: '4px'
                }}
              >
                <option value="copilot_cli">GitHub Copilot CLI</option>
                <option value="codex">OpenAI Codex</option>
              </select>
            </div>
            <button
              type="submit"
              style={{
                padding: '0.75rem 1.5rem',
                backgroundColor: '#28a745',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontWeight: 'bold'
              }}
            >
              Create Project
            </button>
          </form>
        </div>
      )}

      {projects.length === 0 ? (
        <div style={{
          padding: '3rem',
          textAlign: 'center',
          backgroundColor: '#f8f9fa',
          borderRadius: '8px'
        }}>
          <p style={{ fontSize: '1.2rem', color: '#666' }}>No projects yet</p>
          <p>Create your first project to get started</p>
        </div>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
          gap: '1.5rem'
        }}>
          {projects.map((project) => (
            <div
              key={project.id}
              style={{
                padding: '1.5rem',
                backgroundColor: 'white',
                border: '1px solid #ddd',
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'box-shadow 0.2s',
              }}
              onClick={() => handleViewProject(project.id)}
              onMouseEnter={(e) => e.currentTarget.style.boxShadow = '0 4px 8px rgba(0,0,0,0.1)'}
              onMouseLeave={(e) => e.currentTarget.style.boxShadow = 'none'}
            >
              <h3 style={{ marginTop: 0, marginBottom: '0.5rem' }}>{project.name}</h3>
              <p style={{ color: '#666', fontSize: '0.9rem', marginBottom: '1rem' }}>
                {project.description || 'No description'}
              </p>
              <div style={{ fontSize: '0.85rem', color: '#999' }}>
                <div>Engine: {project.default_engine || 'copilot_cli'}</div>
                {project.current_phase && <div>Phase: {project.current_phase}</div>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default ProjectsPage
