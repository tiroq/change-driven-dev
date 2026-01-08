import React from 'react'

function PlannerPage() {
  return (
    <div className="page">
      <h2>Planner Phase</h2>
      <p>Initial task planning and requirement gathering</p>
      
      <div className="placeholder">
        <h3>Planner Phase Placeholder</h3>
        <p>This is where the Planner phase UI will be implemented.</p>
        <p>Purpose:</p>
        <ul style={{ textAlign: 'left', maxWidth: '500px', margin: '1rem auto' }}>
          <li>Define task requirements and objectives</li>
          <li>Break down high-level tasks into actionable items</li>
          <li>Create initial task plans</li>
          <li>Engine-agnostic: works with any AI planner (Copilot, Codex, etc.)</li>
          <li>Generate planning change requests for review</li>
        </ul>
      </div>
    </div>
  )
}

export default PlannerPage
