import React, { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import PlannerPage from './pages/PlannerPage'
import ArchitectPage from './pages/ArchitectPage'
import ReviewApprovalPage from './pages/ReviewApprovalPage'
import CoderPage from './pages/CoderPage'
import ProjectsPage from './pages/ProjectsPage'
import TasksPage from './pages/TasksPage'
import './App.css'

function App() {
  const [selectedProject, setSelectedProject] = useState(() => {
    // Load from localStorage on mount
    const saved = localStorage.getItem('selectedProjectId')
    return saved ? parseInt(saved) : null
  })

  // Save to localStorage whenever it changes
  useEffect(() => {
    if (selectedProject) {
      localStorage.setItem('selectedProjectId', selectedProject.toString())
    } else {
      localStorage.removeItem('selectedProjectId')
    }
  }, [selectedProject])

  return (
    <Router>
      <div className="app">
        <header className="app-header">
          <h1>Change-Driven Development</h1>
          <p>UI-first, stack-agnostic engineering control system</p>
        </header>
        
        <nav className="app-nav">
          <Link to="/">Projects</Link>
          <Link to={selectedProject ? `/tasks?project_id=${selectedProject}` : "/tasks"}>Tasks</Link>
          <Link to={selectedProject ? `/planner?project_id=${selectedProject}` : "/planner"}>Planner</Link>
          <Link to={selectedProject ? `/architect?project_id=${selectedProject}` : "/architect"}>Architect</Link>
          <Link to={selectedProject ? `/review?project_id=${selectedProject}` : "/review"}>Review/Approval</Link>
          <Link to={selectedProject ? `/coder?project_id=${selectedProject}` : "/coder"}>Coder</Link>
        </nav>

        {selectedProject && (
          <div style={{
            padding: '0.5rem 1rem',
            backgroundColor: '#e7f3ff',
            borderBottom: '1px solid #0066cc',
            fontSize: '0.9rem',
            color: '#0066cc'
          }}>
            📁 Current Project ID: {selectedProject}
            <button 
              onClick={() => setSelectedProject(null)}
              style={{
                marginLeft: '1rem',
                padding: '0.25rem 0.5rem',
                fontSize: '0.8rem',
                cursor: 'pointer'
              }}
            >
              Clear Selection
            </button>
          </div>
        )}

        <main className="app-main">
          <Routes>
            <Route path="/" element={<ProjectsPage onProjectSelect={setSelectedProject} />} />
            <Route path="/tasks" element={<TasksPage />} />
            <Route path="/planner" element={<PlannerPage />} />
            <Route path="/architect" element={<ArchitectPage />} />
            <Route path="/review" element={<ReviewApprovalPage />} />
            <Route path="/coder" element={<CoderPage />} />
          </Routes>
        </main>
        
        <footer className="app-footer">
          <p>v0.1.0 - Engine-agnostic AI development platform</p>
        </footer>
      </div>
    </Router>
  )
}

export default App
