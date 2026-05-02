import { BrowserRouter, Routes, Route } from 'react-router-dom'
import LiveFeed from './components/LiveFeed'
import IncidentDetail from './components/IncidentDetail'

export default function App() {
  return (
    <BrowserRouter>
      <div style={{ minHeight: '100vh', backgroundColor: '#0f172a' }}>

        <nav style={{
          backgroundColor: '#1e293b',
          borderBottom: '1px solid #334155',
          padding: '16px 24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '24px' }}>🚨</span>
            <div>
              <div style={{ color: 'white', fontWeight: 'bold', fontSize: '18px' }}>IMS</div>
              <div style={{ color: '#94a3b8', fontSize: '12px' }}>Incident Management System</div>
            </div>
          </div>
          <div style={{ color: '#94a3b8', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{
              width: '8px', height: '8px',
              backgroundColor: '#22c55e',
              borderRadius: '50%',
              display: 'inline-block'
            }}></span>
            System Operational
          </div>
        </nav>

        <main style={{ maxWidth: '900px', margin: '0 auto', padding: '32px 24px' }}>
          <Routes>
            <Route path="/" element={<LiveFeed />} />
            <Route path="/incident/:id" element={<IncidentDetail />} />
          </Routes>
        </main>

      </div>
    </BrowserRouter>
  )
}
