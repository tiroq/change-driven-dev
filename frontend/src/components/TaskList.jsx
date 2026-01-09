import React, { useState } from 'react'

const STATUS_COLUMNS = [
  { key: 'pending', label: 'Pending', color: '#6c757d' },
  { key: 'in_progress', label: 'In Progress', color: '#007bff' },
  { key: 'awaiting_approval', label: 'Awaiting Approval', color: '#ffc107' },
  { key: 'approved', label: 'Approved', color: '#28a745' },
  { key: 'completed', label: 'Completed', color: '#17a2b8' },
  { key: 'rejected', label: 'Rejected', color: '#dc3545' }
]

function TaskList({ tasks = [], onTaskUpdate }) {
  const [selectedTask, setSelectedTask] = useState(null)

  const groupTasksByStatus = () => {
    const grouped = {}
    STATUS_COLUMNS.forEach(col => {
      grouped[col.key] = tasks.filter(task => task.status === col.key)
    })
    return grouped
  }

  const tasksByStatus = groupTasksByStatus()

  const getPhaseLabel = (phase) => {
    if (!phase) return 'Not Started'
    return phase.replace('_', ' ').split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
  }

  const getPriorityColor = (priority) => {
    if (priority >= 7) return '#dc3545'
    if (priority >= 4) return '#ffc107'
    return '#6c757d'
  }

  return (
    <div>
      <div style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${STATUS_COLUMNS.length}, 1fr)`,
        gap: '1rem',
        marginBottom: '2rem'
      }}>
        {STATUS_COLUMNS.map(column => (
          <div key={column.key} style={{
            backgroundColor: '#f8f9fa',
            borderRadius: '8px',
            padding: '1rem',
            minHeight: '300px'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              marginBottom: '1rem',
              paddingBottom: '0.5rem',
              borderBottom: `3px solid ${column.color}`
            }}>
              <h3 style={{ 
                margin: 0,
                fontSize: '1rem',
                fontWeight: 'bold',
                flex: 1
              }}>
                {column.label}
              </h3>
              <span style={{
                backgroundColor: column.color,
                color: 'white',
                borderRadius: '12px',
                padding: '0.25rem 0.5rem',
                fontSize: '0.85rem',
                fontWeight: 'bold'
              }}>
                {tasksByStatus[column.key]?.length || 0}
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {tasksByStatus[column.key]?.map(task => (
                <div
                  key={task.id}
                  onClick={() => setSelectedTask(task)}
                  style={{
                    backgroundColor: 'white',
                    padding: '1rem',
                    borderRadius: '6px',
                    border: '1px solid #dee2e6',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    boxShadow: selectedTask?.id === task.id ? '0 2px 8px rgba(0,0,0,0.15)' : 'none'
                  }}
                  onMouseEnter={(e) => {
                    if (selectedTask?.id !== task.id) {
                      e.currentTarget.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)'
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (selectedTask?.id !== task.id) {
                      e.currentTarget.style.boxShadow = 'none'
                    }
                  }}
                >
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                    marginBottom: '0.5rem'
                  }}>
                    <h4 style={{ 
                      margin: 0, 
                      fontSize: '0.95rem',
                      fontWeight: '600',
                      flex: 1
                    }}>
                      {task.title}
                    </h4>
                    {task.priority > 0 && (
                      <span style={{
                        backgroundColor: getPriorityColor(task.priority),
                        color: 'white',
                        borderRadius: '4px',
                        padding: '0.125rem 0.375rem',
                        fontSize: '0.75rem',
                        fontWeight: 'bold',
                        marginLeft: '0.5rem'
                      }}>
                        P{task.priority}
                      </span>
                    )}
                  </div>
                  
                  {task.description && (
                    <p style={{
                      margin: '0.5rem 0',
                      fontSize: '0.85rem',
                      color: '#6c757d',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical'
                    }}>
                      {task.description}
                    </p>
                  )}
                  
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginTop: '0.75rem',
                    fontSize: '0.75rem',
                    color: '#6c757d'
                  }}>
                    <span>{getPhaseLabel(task.current_phase)}</span>
                    <span>v{task.version}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {selectedTask && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}
        onClick={() => setSelectedTask(null)}
        >
          <div 
            style={{
              backgroundColor: 'white',
              borderRadius: '8px',
              padding: '2rem',
              maxWidth: '600px',
              width: '90%',
              maxHeight: '80vh',
              overflow: 'auto'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
              <h2 style={{ margin: 0, flex: 1 }}>{selectedTask.title}</h2>
              <button
                onClick={() => setSelectedTask(null)}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '1.5rem',
                  cursor: 'pointer',
                  padding: '0.25rem',
                  color: '#6c757d'
                }}
              >
                ×
              </button>
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <strong>Status:</strong> {selectedTask.status.replace('_', ' ').toUpperCase()}
            </div>
            <div style={{ marginBottom: '1rem' }}>
              <strong>Phase:</strong> {getPhaseLabel(selectedTask.current_phase)}
            </div>
            <div style={{ marginBottom: '1rem' }}>
              <strong>Version:</strong> {selectedTask.version}
            </div>
            <div style={{ marginBottom: '1rem' }}>
              <strong>Priority:</strong> {selectedTask.priority}
            </div>
            <div style={{ marginBottom: '1rem' }}>
              <strong>Attempts:</strong> {selectedTask.attempts}
            </div>
            
            {selectedTask.description && (
              <div style={{ marginTop: '1.5rem' }}>
                <strong>Description:</strong>
                <p style={{ marginTop: '0.5rem', color: '#495057' }}>{selectedTask.description}</p>
              </div>
            )}

            <div style={{ 
              marginTop: '2rem', 
              paddingTop: '1rem', 
              borderTop: '1px solid #dee2e6',
              display: 'flex',
              gap: '0.5rem',
              flexWrap: 'wrap'
            }}>
              <button
                onClick={() => {
                  // TODO: Implement approve action
                  console.log('Approve task', selectedTask.id)
                }}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: '#28a745',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Approve
              </button>
              <button
                onClick={() => {
                  // TODO: Implement advance action
                  console.log('Advance task', selectedTask.id)
                }}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: '#007bff',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Advance Phase
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default TaskList
