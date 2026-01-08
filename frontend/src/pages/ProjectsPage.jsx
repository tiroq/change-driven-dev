import React from 'react'

function ProjectsPage() {
  return (
    <div className="page">
      <h2>Projects</h2>
      <p>Manage your development projects</p>
      
      <div className="placeholder">
        <h3>Projects List Placeholder</h3>
        <p>This is where project management will be implemented.</p>
        <p>Features:</p>
        <ul style={{ textAlign: 'left', maxWidth: '400px', margin: '1rem auto' }}>
          <li>View all projects</li>
          <li>Create new projects</li>
          <li>Each project has its own SQLite database</li>
          <li>View project details and tasks</li>
        </ul>
      </div>
    </div>
  )
}

export default ProjectsPage
