import React from 'react'

function TasksPage() {
  return (
    <div className="page">
      <h2>Tasks</h2>
      <p>View and manage development tasks</p>
      
      <div className="placeholder">
        <h3>Tasks List Placeholder</h3>
        <p>This is where task management will be implemented.</p>
        <p>Features:</p>
        <ul style={{ textAlign: 'left', maxWidth: '400px', margin: '1rem auto' }}>
          <li>View all tasks across projects</li>
          <li>Create new tasks</li>
          <li>Track task status and current phase</li>
          <li>View task version history</li>
          <li>Manage change requests</li>
        </ul>
      </div>
    </div>
  )
}

export default TasksPage
