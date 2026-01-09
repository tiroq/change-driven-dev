import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import api from '../services/api'

function ReviewApprovalPage() {
  const { projectId } = useParams()
  const [tasks, setTasks] = useState([])
  const [selectedTask, setSelectedTask] = useState(null)
  const [versions, setVersions] = useState([])
  const [changeRequests, setChangeRequests] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  // Split dialog state
  const [showSplitDialog, setShowSplitDialog] = useState(false)
  const [splitForm, setSplitForm] = useState({
    task1_title: '',
    task1_description: '',
    task2_title: '',
    task2_description: ''
  })
  
  // Merge dialog state
  const [showMergeDialog, setShowMergeDialog] = useState(false)
  const [selectedTaskIds, setSelectedTaskIds] = useState([])
  const [mergeForm, setMergeForm] = useState({
    merged_title: '',
    merged_description: ''
  })

  useEffect(() => {
    loadTasks()
  }, [projectId])

  useEffect(() => {
    if (selectedTask) {
      loadTaskDetails(selectedTask.id)
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

  const loadTaskDetails = async (taskId) => {
    try {
      // Load version history
      const versionsData = await api.getTaskVersions(taskId)
      setVersions(versionsData)
      
      // Load change requests for this task
      const crsData = await api.getChangeRequests(taskId)
      setChangeRequests(crsData)
    } catch (err) {
      setError(`Failed to load task details: ${err.message}`)
    }
  }

  const handleTaskSelect = (task) => {
    setSelectedTask(task)
    setVersions([])
    setChangeRequests([])
  }

  const handleSplitTask = async () => {
    try {
      await api.splitTask(
        selectedTask.id,
        parseInt(projectId),
        splitForm.task1_title,
        splitForm.task1_description,
        splitForm.task2_title,
        splitForm.task2_description
      )
      setShowSplitDialog(false)
      setSplitForm({
        task1_title: '',
        task1_description: '',
        task2_title: '',
        task2_description: ''
      })
      loadTasks()
      setSelectedTask(null)
    } catch (err) {
      setError(`Failed to split task: ${err.message}`)
    }
  }

  const handleMergeTasks = async () => {
    try {
      await api.mergeTasks(
        parseInt(projectId),
        selectedTaskIds,
        mergeForm.merged_title,
        mergeForm.merged_description
      )
      setShowMergeDialog(false)
      setSelectedTaskIds([])
      setMergeForm({
        merged_title: '',
        merged_description: ''
      })
      loadTasks()
      setSelectedTask(null)
    } catch (err) {
      setError(`Failed to merge tasks: ${err.message}`)
    }
  }

  const handleApproveChangeRequest = async (crId) => {
    try {
      await api.approveChangeRequest(crId)
      loadTaskDetails(selectedTask.id)
    } catch (err) {
      setError(`Failed to approve change request: ${err.message}`)
    }
  }

  const handleRejectChangeRequest = async (crId) => {
    try {
      await api.rejectChangeRequest(crId)
      loadTaskDetails(selectedTask.id)
    } catch (err) {
      setError(`Failed to reject change request: ${err.message}`)
    }
  }

  const toggleTaskSelection = (taskId) => {
    setSelectedTaskIds(prev => 
      prev.includes(taskId) 
        ? prev.filter(id => id !== taskId)
        : [...prev, taskId]
    )
  }

  if (loading) return <div className="p-4">Loading...</div>
  if (error) return <div className="p-4 text-red-600">Error: {error}</div>

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">Review & Approval</h1>
      
      <div className="grid grid-cols-3 gap-6">
        {/* Task List */}
        <div className="bg-white shadow rounded-lg p-4">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Tasks</h2>
            <button
              onClick={() => setShowMergeDialog(true)}
              disabled={selectedTaskIds.length < 2}
              className="px-3 py-1 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-sm"
            >
              Merge ({selectedTaskIds.length})
            </button>
          </div>
          
          <div className="space-y-2">
            {tasks.map(task => (
              <div
                key={task.id}
                className={`p-3 border rounded cursor-pointer hover:bg-gray-50 ${
                  selectedTask?.id === task.id ? 'border-blue-500 bg-blue-50' : ''
                }`}
              >
                <div className="flex items-start gap-2">
                  <input
                    type="checkbox"
                    checked={selectedTaskIds.includes(task.id)}
                    onChange={() => toggleTaskSelection(task.id)}
                    className="mt-1"
                    onClick={(e) => e.stopPropagation()}
                  />
                  <div onClick={() => handleTaskSelect(task)} className="flex-1">
                    <div className="font-medium">{task.title}</div>
                    <div className="text-xs text-gray-500">
                      Status: {task.status} | Version: {task.version}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Version History & Details */}
        <div className="col-span-2 bg-white shadow rounded-lg p-4">
          {selectedTask ? (
            <>
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h2 className="text-xl font-semibold">{selectedTask.title}</h2>
                  <p className="text-gray-600 mt-1">{selectedTask.description}</p>
                </div>
                <button
                  onClick={() => setShowSplitDialog(true)}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Split Task
                </button>
              </div>

              {/* Change Requests */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-3">Change Requests</h3>
                {changeRequests.length === 0 ? (
                  <p className="text-gray-500 italic">No change requests</p>
                ) : (
                  <div className="space-y-2">
                    {changeRequests.map(cr => (
                      <div key={cr.id} className="border rounded p-3">
                        <div className="flex justify-between items-start">
                          <div>
                            <div className="font-medium">{cr.title}</div>
                            <div className="text-sm text-gray-600">{cr.description}</div>
                            <div className="text-xs text-gray-500 mt-1">
                              Status: {cr.status} | Submitted: {cr.submitted_at || 'Not submitted'}
                            </div>
                          </div>
                          {cr.status === 'submitted' && (
                            <div className="flex gap-2">
                              <button
                                onClick={() => handleApproveChangeRequest(cr.id)}
                                className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 text-sm"
                              >
                                Approve
                              </button>
                              <button
                                onClick={() => handleRejectChangeRequest(cr.id)}
                                className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 text-sm"
                              >
                                Reject
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Version History */}
              <div>
                <h3 className="text-lg font-semibold mb-3">Version History</h3>
                {versions.length === 0 ? (
                  <p className="text-gray-500 italic">No version history yet</p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Version</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Title</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {versions.map(version => (
                          <tr key={version.id}>
                            <td className="px-4 py-2 text-sm">v{version.version_num}</td>
                            <td className="px-4 py-2 text-sm">{version.title}</td>
                            <td className="px-4 py-2 text-sm text-gray-600">{version.description || '-'}</td>
                            <td className="px-4 py-2 text-sm text-gray-500">{new Date(version.created_at).toLocaleString()}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="text-gray-500 italic text-center py-12">
              Select a task to view details
            </div>
          )}
        </div>
      </div>

      {/* Split Task Dialog */}
      {showSplitDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full">
            <h2 className="text-2xl font-bold mb-4">Split Task: {selectedTask.title}</h2>
            
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold mb-2">Task 1</h3>
                <input
                  type="text"
                  placeholder="Title"
                  value={splitForm.task1_title}
                  onChange={(e) => setSplitForm({...splitForm, task1_title: e.target.value})}
                  className="w-full px-3 py-2 border rounded mb-2"
                />
                <textarea
                  placeholder="Description"
                  value={splitForm.task1_description}
                  onChange={(e) => setSplitForm({...splitForm, task1_description: e.target.value})}
                  className="w-full px-3 py-2 border rounded"
                  rows={3}
                />
              </div>
              
              <div>
                <h3 className="font-semibold mb-2">Task 2</h3>
                <input
                  type="text"
                  placeholder="Title"
                  value={splitForm.task2_title}
                  onChange={(e) => setSplitForm({...splitForm, task2_title: e.target.value})}
                  className="w-full px-3 py-2 border rounded mb-2"
                />
                <textarea
                  placeholder="Description"
                  value={splitForm.task2_description}
                  onChange={(e) => setSplitForm({...splitForm, task2_description: e.target.value})}
                  className="w-full px-3 py-2 border rounded"
                  rows={3}
                />
              </div>
            </div>
            
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowSplitDialog(false)}
                className="px-4 py-2 border rounded hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSplitTask}
                disabled={!splitForm.task1_title || !splitForm.task2_title}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
              >
                Split Task
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Merge Tasks Dialog */}
      {showMergeDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg p-6 max-w-xl w-full">
            <h2 className="text-2xl font-bold mb-4">Merge {selectedTaskIds.length} Tasks</h2>
            
            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">Selected tasks:</p>
              <ul className="list-disc list-inside text-sm">
                {selectedTaskIds.map(id => {
                  const task = tasks.find(t => t.id === id)
                  return task ? <li key={id}>{task.title}</li> : null
                })}
              </ul>
            </div>
            
            <div className="space-y-4">
              <input
                type="text"
                placeholder="Merged task title"
                value={mergeForm.merged_title}
                onChange={(e) => setMergeForm({...mergeForm, merged_title: e.target.value})}
                className="w-full px-3 py-2 border rounded"
              />
              <textarea
                placeholder="Merged task description"
                value={mergeForm.merged_description}
                onChange={(e) => setMergeForm({...mergeForm, merged_description: e.target.value})}
                className="w-full px-3 py-2 border rounded"
                rows={4}
              />
            </div>
            
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowMergeDialog(false)}
                className="px-4 py-2 border rounded hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleMergeTasks}
                disabled={!mergeForm.merged_title}
                className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
              >
                Merge Tasks
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ReviewApprovalPage
