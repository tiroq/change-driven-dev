import React from 'react'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import PlannerPage from './pages/PlannerPage'
import ArchitectPage from './pages/ArchitectPage'
import ReviewApprovalPage from './pages/ReviewApprovalPage'
import CoderPage from './pages/CoderPage'
import ProjectsPage from './pages/ProjectsPage'
import TasksPage from './pages/TasksPage'
import './App.css'

function App() {
  return (
    <Router>
      <div className="app">
        <header className="app-header">
          <h1>Change-Driven Development</h1>
          <p>UI-first, stack-agnostic engineering control system</p>
        </header>
        
        <nav className="app-nav">
          <Link to="/">Projects</Link>
          <Link to="/tasks">Tasks</Link>
          <Link to="/planner">Planner</Link>
          <Link to="/architect">Architect</Link>
          <Link to="/review">Review/Approval</Link>
          <Link to="/coder">Coder</Link>
        </nav>

        <main className="app-main">
          <Routes>
            <Route path="/" element={<ProjectsPage />} />
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
