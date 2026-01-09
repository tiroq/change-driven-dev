import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import api from '../services/api'

function ArchitectPage() {
  const { projectId } = useParams()
  const [tasks, setTasks] = useState([])
  const [selectedTask, setSelectedTask] = useState(null)
  const [contextContent, setContextContent] = useState('')
  const [architecture, setArchitecture] = useState(null)
  const [adrs, setAdrs] = useState([])
  const [selectedAdr, setSelectedAdr] = useState(null)
  const [adrContent, setAdrContent] = useState('')
  const [loading, setLoading] = useState(false)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadTasks()
  }, [projectId])

  useEffect(() => {
    if (selectedTask) {
      loadArchitecture(selectedTask.id)
    }
  }, [selectedTask])

  const loadTasks = async () => {
    try {
      setLoading(true)
      const tasksData = await api.getTasks(parseInt(projectId))
      setTasks(tasksData)
    } catch (err) {
      setError(`Failed to load tasks: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const loadArchitecture = async (taskId) => {
    try {
      // Load architecture artifact for this task
      const artifacts = await api.getArtifacts(parseInt(projectId), 'architecture')
      const taskArtifacts = artifacts.filter(a => a.task_id === taskId)
      
      if (taskArtifacts.length > 0) {
        // Get the most recent architecture
        const latestArch = taskArtifacts[taskArtifacts.length - 1]
        const archContent = await api.getArtifactContent(latestArch.id)
        setArchitecture(JSON.parse(archContent))
      } else {
        setArchitecture(null)
      }
      
      // Load ADR artifacts
      const adrArtifacts = await api.getArtifacts(parseInt(projectId), 'adr')
      const taskAdrs = adrArtifacts.filter(a => a.task_id === taskId)
      setAdrs(taskAdrs)
      
    } catch (err) {
      console.error('Failed to load architecture:', err)
      setArchitecture(null)
      setAdrs([])
    }
  }

  const handleRunArchitect = async () => {
    if (!selectedTask || !contextContent.trim()) {
      setError('Please select a task and provide architecture context')
      return
    }

    try {
      setRunning(true)
      setError(null)
      
      const result = await api.runArchitect(
        parseInt(projectId),
        selectedTask.id,
        contextContent,
        null // Use default engine
      )
      
      if (result.success) {
        // Reload architecture
        await loadArchitecture(selectedTask.id)
        setError(null)
      } else {
        setError(result.error || 'Architect phase failed')
      }
    } catch (err) {
      setError(`Failed to run architect: ${err.message}`)
    } finally {
      setRunning(false)
    }
  }

  const handleViewAdr = async (adr) => {
    try {
      setSelectedAdr(adr)
      const content = await api.getArtifactContent(adr.id)
      setAdrContent(content)
    } catch (err) {
      setError(`Failed to load ADR: ${err.message}`)
    }
  }

  if (loading) return <div className="p-4">Loading...</div>

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">Architect Phase</h1>
      
      <div className="grid grid-cols-3 gap-6">
        {/* Task Selection */}
        <div className="bg-white shadow rounded-lg p-4">
          <h2 className="text-xl font-semibold mb-4">Tasks</h2>
          <div className="space-y-2">
            {tasks.map(task => (
              <div
                key={task.id}
                onClick={() => setSelectedTask(task)}
                className={`p-3 border rounded cursor-pointer hover:bg-gray-50 ${
                  selectedTask?.id === task.id ? 'border-blue-500 bg-blue-50' : ''
                }`}
              >
                <div className="font-medium">{task.title}</div>
                <div className="text-xs text-gray-500">
                  {task.status} | {task.current_phase || 'No phase'}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Architecture Context & Run */}
        <div className="col-span-2 space-y-6">
          {selectedTask ? (
            <>
              {/* Context Editor */}
              <div className="bg-white shadow rounded-lg p-4">
                <h2 className="text-xl font-semibold mb-4">Architecture Context</h2>
                <p className="text-sm text-gray-600 mb-3">
                  Describe the architectural requirements, constraints, and context for: <strong>{selectedTask.title}</strong>
                </p>
                <textarea
                  value={contextContent}
                  onChange={(e) => setContextContent(e.target.value)}
                  placeholder="Enter architectural context, requirements, constraints, existing systems to integrate with, performance requirements, etc."
                  className="w-full h-32 px-3 py-2 border rounded font-mono text-sm"
                />
                <div className="flex justify-end gap-3 mt-3">
                  <button
                    onClick={handleRunArchitect}
                    disabled={running || !contextContent.trim()}
                    className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
                  >
                    {running ? 'Running Architect...' : 'Run Architect'}
                  </button>
                </div>
                {error && (
                  <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
                    {error}
                  </div>
                )}
              </div>

              {/* Architecture Options */}
              {architecture && (
                <div className="bg-white shadow rounded-lg p-4">
                  <h2 className="text-xl font-semibold mb-4">Architecture Options</h2>
                  {architecture.options && architecture.options.length > 0 ? (
                    <div className="space-y-4">
                      {architecture.options.map((option, idx) => (
                        <div key={idx} className="border rounded p-4">
                          <h3 className="font-semibold text-lg mb-2">
                            Option {idx + 1}: {option.name || `Option ${idx + 1}`}
                          </h3>
                          <p className="text-gray-700 mb-3">{option.description}</p>
                          
                          {option.pros && option.pros.length > 0 && (
                            <div className="mb-2">
                              <h4 className="font-medium text-green-700 text-sm mb-1">Pros:</h4>
                              <ul className="list-disc list-inside text-sm text-gray-600">
                                {option.pros.map((pro, i) => (
                                  <li key={i}>{pro}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                          
                          {option.cons && option.cons.length > 0 && (
                            <div className="mb-2">
                              <h4 className="font-medium text-red-700 text-sm mb-1">Cons:</h4>
                              <ul className="list-disc list-inside text-sm text-gray-600">
                                {option.cons.map((con, i) => (
                                  <li key={i}>{con}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                          
                          {option.trade_offs && (
                            <div className="mt-2 text-sm text-gray-600">
                              <strong>Trade-offs:</strong> {option.trade_offs}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-gray-500 italic">
                      No architecture options found. Try running the architect phase.
                    </div>
                  )}
                  
                  {architecture.raw_response && !architecture.options?.length && (
                    <div className="mt-4">
                      <h4 className="font-medium mb-2">Raw Response:</h4>
                      <pre className="bg-gray-50 p-3 rounded text-xs overflow-auto max-h-96">
                        {architecture.raw_response}
                      </pre>
                    </div>
                  )}
                </div>
              )}

              {/* ADR Documents */}
              {adrs.length > 0 && (
                <div className="bg-white shadow rounded-lg p-4">
                  <h2 className="text-xl font-semibold mb-4">Architecture Decision Records</h2>
                  <div className="grid grid-cols-2 gap-3">
                    {adrs.map(adr => (
                      <div
                        key={adr.id}
                        onClick={() => handleViewAdr(adr)}
                        className={`p-3 border rounded cursor-pointer hover:bg-gray-50 ${
                          selectedAdr?.id === adr.id ? 'border-blue-500 bg-blue-50' : ''
                        }`}
                      >
                        <div className="font-medium text-sm">{adr.name}</div>
                        <div className="text-xs text-gray-500">
                          {new Date(adr.created_at).toLocaleString()}
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  {selectedAdr && adrContent && (
                    <div className="mt-4 border-t pt-4">
                      <h3 className="font-semibold mb-2">{selectedAdr.name}</h3>
                      <div className="prose prose-sm max-w-none">
                        <pre className="bg-gray-50 p-4 rounded text-xs overflow-auto whitespace-pre-wrap">
                          {adrContent}
                        </pre>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </>
          ) : (
            <div className="bg-white shadow rounded-lg p-12 text-center text-gray-500 italic">
              Select a task to run the architect phase
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default ArchitectPage
