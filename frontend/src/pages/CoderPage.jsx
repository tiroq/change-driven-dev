import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import api from '../services/api'

function CoderPage() {
  const { projectId } = useParams()
  const [tasks, setTasks] = useState([])
  const [selectedTask, setSelectedTask] = useState(null)
  const [gateResults, setGateResults] = useState(null)
  const [gitStatus, setGitStatus] = useState(null)
  const [running, setRunning] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [lastResult, setLastResult] = useState(null)

  useEffect(() => {
    loadTasks()
    loadGitStatus()
  }, [projectId])

  useEffect(() => {
    if (selectedTask) {
      loadTaskGates(selectedTask.id)
    }
  }, [selectedTask])

  const loadTasks = async () => {
    try {
      setLoading(true)
      const tasksData = await api.getTasks(parseInt(projectId))
      // Filter to show only approved tasks
      const approvedTasks = tasksData.filter(t => t.status === 'approved')
      setTasks(approvedTasks)
    } catch (err) {
      setError(`Failed to load tasks: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const loadGitStatus = async () => {
    try {
      const status = await api.getGitStatus(parseInt(projectId))
      setGitStatus(status)
    } catch (err) {
      console.error('Failed to load git status:', err)
      setGitStatus(null)
    }
  }

  const loadTaskGates = async (taskId) => {
    try {
      const gates = await api.getTaskGates(taskId)
      // Gates are just for display, will be executed by coder phase
    } catch (err) {
      console.error('Failed to load gates:', err)
    }
  }

  const handleRunCoder = async () => {
    if (!selectedTask) {
      setError('Please select a task')
      return
    }

    try {
      setRunning(true)
      setError(null)
      setLastResult(null)
      setGateResults(null)
      
      const result = await api.runCoder(
        parseInt(projectId),
        selectedTask.id,
        null // Use default engine
      )
      
      setLastResult(result)
      setGateResults(result.gate_results || null)
      
      // Reload tasks and git status
      await loadTasks()
      await loadGitStatus()
      
      if (result.gates_passed) {
        setError(null)
      } else {
        setError('Implementation completed but gates failed. See results below.')
      }
    } catch (err) {
      setError(`Failed to run coder: ${err.message}`)
      setLastResult(null)
    } finally {
      setRunning(false)
    }
  }

  if (loading) return <div className="p-4">Loading...</div>

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">Coder Phase</h1>
      
      <div className="grid grid-cols-3 gap-6">
        {/* Task Queue */}
        <div className="bg-white shadow rounded-lg p-4">
          <h2 className="text-xl font-semibold mb-4">Approved Tasks</h2>
          {tasks.length === 0 ? (
            <p className="text-gray-500 italic">No approved tasks</p>
          ) : (
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
                    Attempts: {task.attempts} | Priority: {task.priority}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Execution Controls & Status */}
        <div className="col-span-2 space-y-6">
          {selectedTask ? (
            <>
              {/* Task Info & Run Button */}
              <div className="bg-white shadow rounded-lg p-4">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h2 className="text-xl font-semibold">{selectedTask.title}</h2>
                    <p className="text-gray-600 mt-1">{selectedTask.description}</p>
                    <div className="mt-2 text-sm">
                      <span className="text-gray-500">Status:</span>{' '}
                      <span className="font-medium">{selectedTask.status}</span>
                      {' | '}
                      <span className="text-gray-500">Attempts:</span>{' '}
                      <span className="font-medium">{selectedTask.attempts}</span>
                    </div>
                  </div>
                  <button
                    onClick={handleRunCoder}
                    disabled={running}
                    className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed font-semibold"
                  >
                    {running ? 'Running...' : 'Execute Task'}
                  </button>
                </div>
                
                {error && (
                  <div className={`p-3 border rounded ${
                    error.includes('gates failed') 
                      ? 'bg-yellow-50 border-yellow-200 text-yellow-800'
                      : 'bg-red-50 border-red-200 text-red-700'
                  }`}>
                    {error}
                  </div>
                )}
              </div>

              {/* Gate Results */}
              {gateResults && (
                <div className="bg-white shadow rounded-lg p-4">
                  <h3 className="text-lg font-semibold mb-3">Gate Execution Results</h3>
                  
                  {/* Summary */}
                  <div className={`p-3 rounded mb-4 ${
                    gateResults.all_passed 
                      ? 'bg-green-50 border border-green-200'
                      : 'bg-red-50 border border-red-200'
                  }`}>
                    <div className="flex justify-between items-center">
                      <span className="font-semibold">
                        {gateResults.all_passed ? '✓ All Gates Passed' : '✗ Gates Failed'}
                      </span>
                      <span className="text-sm">
                        {gateResults.summary.passed} / {gateResults.summary.total} passed
                      </span>
                    </div>
                  </div>

                  {/* Individual Gate Results */}
                  <div className="space-y-2">
                    {gateResults.results && gateResults.results.map((result, idx) => (
                      <div
                        key={idx}
                        className={`p-3 border rounded ${
                          result.passed 
                            ? 'border-green-200 bg-green-50'
                            : 'border-red-200 bg-red-50'
                        }`}
                      >
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <div className="font-medium">
                              {result.passed ? '✓' : '✗'} {result.gate_name}
                            </div>
                            <div className="text-xs text-gray-600 mt-1">
                              Exit code: {result.exit_code} | 
                              Time: {result.execution_time.toFixed(2)}s
                            </div>
                            {result.error && (
                              <div className="text-xs text-red-600 mt-1">
                                Error: {result.error}
                              </div>
                            )}
                            {result.stdout && (
                              <details className="mt-2">
                                <summary className="text-xs cursor-pointer text-gray-600">
                                  Show output
                                </summary>
                                <pre className="text-xs bg-gray-900 text-gray-100 p-2 rounded mt-1 overflow-auto max-h-32">
                                  {result.stdout}
                                </pre>
                              </details>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Success State */}
              {lastResult && lastResult.gates_passed && (
                <div className="bg-white shadow rounded-lg p-4">
                  <div className="bg-green-50 border border-green-200 rounded p-4">
                    <h3 className="text-lg font-semibold text-green-800 mb-2">
                      ✓ Task Completed Successfully
                    </h3>
                    <div className="text-sm text-green-700 space-y-1">
                      <p>• Implementation completed and all gates passed</p>
                      {lastResult.commit_sha && (
                        <p>• Changes committed: {lastResult.commit_sha.substring(0, 8)}</p>
                      )}
                      <p>• Task status: {lastResult.task_status}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Git Status */}
              {gitStatus && gitStatus.is_repo && (
                <div className="bg-white shadow rounded-lg p-4">
                  <h3 className="text-lg font-semibold mb-3">Git Status</h3>
                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="text-gray-600">Branch:</span>{' '}
                      <span className="font-mono">{gitStatus.branch}</span>
                    </div>
                    {gitStatus.has_changes ? (
                      <>
                        <div className="text-yellow-600">
                          ⚠ Uncommitted changes detected
                        </div>
                        {gitStatus.staged_files.length > 0 && (
                          <div>
                            <span className="text-gray-600">Staged:</span>{' '}
                            {gitStatus.staged_files.length} files
                          </div>
                        )}
                        {gitStatus.unstaged_files.length > 0 && (
                          <div>
                            <span className="text-gray-600">Unstaged:</span>{' '}
                            {gitStatus.unstaged_files.length} files
                          </div>
                        )}
                      </>
                    ) : (
                      <div className="text-green-600">✓ No uncommitted changes</div>
                    )}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="bg-white shadow rounded-lg p-12 text-center text-gray-500 italic">
              Select an approved task to execute
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default CoderPage
