import React, { useState } from 'react'
import MapPage from './MapPage.jsx'
import './App.css'

export default function App() {
  const [started, setStarted] = useState(false)

  if (!started) {
    return (
      <div style={{ 
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white'
      }}>
        <div style={{ textAlign: 'center', maxWidth: 600, padding: 40 }}>
          <h1 style={{ fontSize: 48, marginBottom: 20 }}>Real-World Drone Delivery</h1>
          <p style={{ fontSize: 18, marginBottom: 30, lineHeight: 1.6 }}>
            This simulation uses real OpenStreetMap data, real building footprints,
            and real building heights where available. No estimates, no defaults.
          </p>
          <p style={{ fontSize: 14, marginBottom: 30, opacity: 0.9 }}>
            Base: Hanamkonda Head Post Office, Telangana, India
          </p>
          <button
            onClick={() => setStarted(true)}
            style={{ 
              padding: '16px 32px', 
              fontSize: 18,
              background: 'white',
              color: '#667eea',
              border: 'none',
              borderRadius: 8,
              cursor: 'pointer',
              fontWeight: 'bold',
              boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
            }}
          >
            Enter Simulation
          </button>
        </div>
      </div>
    )
  }

  return <MapPage onExit={() => setStarted(false)} />
}
