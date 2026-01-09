import React, { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import api from '../services/api'

function PlannerPage() {
  const [searchParams] = useSearchParams()
  const projectId = searchParams.get('project_id')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [running, setRunning] = useState(false)
  const [planData, setPlanData] = useState(null)
  const [specContent, setSpecContent] = useState('')
  const [showSpecEditor, setShowSpecEditor] = useState(false)
  const [runResult, setRunResult] = useState(null)

  useEffect(() => {
    loadPlan()
  }, [projectId])

  const loadPlan = async () => {
    if (!projectId) return
    
    try {
      setLoading(true)
      // Get latest plan artifact for this project
      const artifacts = await api.getArtifacts(projectId, 'plan')
      if (artifacts && artifacts.length > 0) {
        // Get the most recent plan
        const latestPlan = artifacts[0]
        const planContent = await api.getArtifactContent(latestPlan.id)
        setPlanData(JSON.parse(planContent.content))
      }
    } catch (err) {
      console.error('Failed to load plan:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleRunPlanner = async () => {
    if (!projectId || !specContent.trim()) {
      setError('Please enter project specification')
      return
    }

    try {
      setRunning(true)
      setError(null)
      
      const result = await api.runPlanner(projectId, specContent)
      setRunResult(result)
      
      if (result.success) {
        // Reload plan
        await loadPlan()
      } else {
        setError(result.error || 'Planner failed')
      }
    } catch (err) {
      setError('Failed to run planner: ' + err.message)
    } finally {
      setRunning(false)
    }
  }

  if (loading) {
    return (
      <div className="page">
        <h2>Planner</h2>
        <p>Loading plan...</p>
      </div>
    )
  }

  return (
    <div className="page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h2>Planner</h2>
          {projectId && <p style={{ color: '#666', margin: 0 }}>Project ID: {projectId}</p>}
        </div>
        <button
          onClick={() => setShowSpecEditor(!showSpecEditor)}
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          {showSpecEditor ? 'Hide Spec Editor' : 'Edit Spec & Re-run'}
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

      {showSpecEditor && (
        <div style={{
          padding: '1.5rem',
          backgroundColor: '#f8f9fa',
          borderRadius: '8px',
          marginBottom: '2rem'
        }}>
          <h3>Project Specification</h3>
          <p style={{ color: '#666', fontSize: '0.9rem' }}>
            Enter or paste your project specification. The planner will analyze it and create a task breakdown.
          </p>
          <textarea
            value={specContent}
            onChange={(e) => setSpecContent(e.target.value)}
            rows={12}
            placeholder="Enter project specification here..."
            style={{
              width: '100%',
              padding: '0.75rem',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontFamily: 'monospace',
              fontSize: '0.9rem',
              marginBottom: '1rem'
            }}
          />
          <button
            onClick={handleRunPlanner}
            disabled={running || !specContent.trim()}
            style={{
              padding: '0.75rem 1.5rem',
              backgroundColor: running ? '#6c757d' : '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: running ? 'not-allowed' : 'pointer',
              fontWeight: 'bold'
            }}
          >
            {running ? 'Running Planner...' : '▶ Run Planner'}
          </button>
        </div>
      )}

      {runResult && runResult.success && (
        <div style={{
          padding: '1rem',
          backgroundColor: '#d4edda',
          color: '#155724',
          borderRadius: '4px',
          marginBottom: '1rem'
        }}>
          <strong>✓ Planner completed successfully!</strong>
          <div style={{ marginTop: '0.5rem', fontSize: '0.9rem' }}>
            Created {runResult.tasks_created} tasks (Run ID: {runResult.run_id})
          </div>
        </div>
      )}

      {planData ? (
        <div>
          <h3>Plan Overview</h3>
          <div style={{
            padding: '1.5rem',
            backgroundColor: 'white',
            borderRadius: '8px',
            border: '1px solid #dee2e6',
            marginBottom: '2rem'
          }}>
            {planData.metadata && (
              <div style={{ marginBottom: '1.5rem', paddingBottom: '1rem', borderBottom: '1px solid #dee2e6' }}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
                  {planData.metadata.generated_at && (
                    <div>
                      <strong>Generated:</strong>
                      <div style={{ color: '#666', fontSize: '0.9rem' }}>
                        {new Date(planData.metadata.generated_at).toLocaleString()}
                      </div>
                    </div>
                  )}
                  <div>
                    <strong>Total Tasks:</strong>
                    <div style={{ color: '#666', fontSize: '0.9rem' }}>
                      {planData.tasks?.length || 0}
                    </div>
                  </div>
                </div>
                {planData.metadata.note && (
                  <div style={{ marginTop: '1rem', padding: '0.75rem', backgroundColor: '#fff3cd', borderRadius: '4px' }}>
                    <strong>Note:</strong> {planData.metadata.note}
                  </div>
                )}
              </div>
            )}

            <h4>Tasks</h4>
            {planData.tasks && planData.tasks.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {planData.tasks.map((task, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: '1rem',
                      backgroundColor: '#f8f9fa',
                      borderRadius: '6px',
                      border: '1px solid #dee2e6'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '0.5rem' }}>
                      <h5 style={{ margin: 0 }}>{task.title || `Task ${idx + 1}`}</h5>
                      {task.priority && (
                        <span style={{
                          backgroundColor: task.priority >= 7 ? '#dc3545' : task.priority >= 4 ? '#ffc107' : '#6c757d',
                          color: 'white',
                          padding: '0.25rem 0.5rem',
                          borderRadius: '4px',
                          fontSize: '0.8rem',
                          fontWeight: 'bold'
                        }}>
                          P{task.priority}
                        </span>
                      )}
                    </div>
                    {task.description && (
                      <p style={{ margin: '0.5rem 0', color: '#495057', fontSize: '0.9rem' }}>
                        {task.description}
                      </p>
                    )}
                    {task.acceptance_criteria && task.acceptance_criteria.length > 0 && (
                      <div style={{ marginTop: '0.75rem' }}>
                        <strong style={{ fontSize: '0.85rem' }}>Acceptance Criteria:</strong>
                        <ul style={{ margin: '0.25rem 0 0 0', paddingLeft: '1.5rem', fontSize: '0.85rem' }}>
                          {task.acceptance_criteria.map((criterion, cidx) => (
                            <li key={cidx}>{criterion}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: '#666', fontStyle: 'italic' }}>No tasks in plan</p>
            )}

            {planData.raw_response && (
              <details style={{ marginTop: '1.5rem' }}>
                <summary style={{ cursor: 'pointer', fontWeight: 'bold', marginBottom: '0.5rem' }}>
                  Raw Response
                </summary>
                <pre style={{
                  padding: '1rem',
                  backgroundColor: '#f8f9fa',
                  borderRadius: '4px',
                  overflow: 'auto',
                  fontSize: '0.85rem',
                  whiteSpace: 'pre-wrap'
                }}>
                  {planData.raw_response}
                </pre>
              </details>
            )}
          </div>
        </div>
      ) : (
        <div style={{
          padding: '3rem',
          textAlign: 'center',
          backgroundColor: '#f8f9fa',
          borderRadius: '8px',
          border: '2px dashed #dee2e6'
        }}>
          <h3 style={{ color: '#6c757d' }}>No Plan Yet</h3>
          <p style={{ color: '#6c757d', marginBottom: '1.5rem' }}>
            Click "Edit Spec & Re-run" to create a plan for this project
          </p>
        </div>
      )}
    </div>
  )
}

export default PlannerPage
