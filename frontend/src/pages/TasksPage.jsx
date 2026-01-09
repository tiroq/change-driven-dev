import React, { useState, useEffect, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import TaskList from '../components/TaskList'
import api from '../services/api'

function TasksPage() {
  const [searchParams] = useSearchParams()
  const projectId = searchParams.get('project_id')
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [wsConnected, setWsConnected] = useState(false)
  const [notification, setNotification] = useState(null)
  const wsRef = useRef(null)
  const [formData, setFormData] = useState({
    project_id: projectId || 1,
    title: '',
    description: '',
    priority: 0
  })

  useEffect(() => {
    loadTasks()
  }, [projectId])

  // WebSocket connection for real-time updates
  useEffect(() => {
    const connectWebSocket = () => {
      try {
        const ws = api.connectWebSocket(projectId)
        
        ws.onopen = () => {
          console.log('WebSocket connected')
          setWsConnected(true)
        }
        
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            console.log('WebSocket event received:', data)
            
            // Handle different event types
            if (data.event_type === 'task_created' || 
                data.event_type === 'task_updated' || 
                data.event_type === 'task_status_changed') {
              
              // Refresh tasks
              loadTasks()
              
              // Show notification
              const eventLabels = {
                task_created: 'Task Created',
                task_updated: 'Task Updated',
                task_status_changed: 'Task Status Changed'
              }
              setNotification({
                message: eventLabels[data.event_type] || 'Task Event',
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
  }, [projectId])

  const loadTasks = async () => {
    try {
      setLoading(true)
      const data = await api.getTasks(projectId)
      setTasks(data)
      setError(null)
    } catch (err) {
      setError('Failed to load tasks: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateTask = async (e) => {
    e.preventDefault()
    try {
      await api.createTask(formData)
      setShowCreateForm(false)
      setFormData({ project_id: projectId || 1, title: '', description: '', priority: 0 })
      loadTasks()
    } catch (err) {
      setError('Failed to create task: ' + err.message)
    }
  }

  if (loading) {
    return (
      <div className="page">
        <h2>Tasks</h2>
        <p>Loading tasks...</p>
      </div>
    )
  }

  return (
    <div className="page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h2>Tasks</h2>
          {projectId && <p style={{ color: '#666', margin: 0 }}>Project ID: {projectId}</p>}
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
          {showCreateForm ? 'Cancel' : '+ New Task'}
        </button>
      </div>

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
          <h3>Create New Task</h3>
          <form onSubmit={handleCreateTask}>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                Task Title *
              </label>
              <input
                type="text"
                required
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
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
                rows={4}
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
                Priority (0-10)
              </label>
              <input
                type="number"
                min="0"
                max="10"
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) })}
                style={{
                  width: '100px',
                  padding: '0.5rem',
                  border: '1px solid #ddd',
                  borderRadius: '4px'
                }}
              />
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
              Create Task
            </button>
          </form>
        </div>
      )}

      <TaskList tasks={tasks} onTaskUpdate={loadTasks} />
    </div>
  )
}

export default TasksPage
