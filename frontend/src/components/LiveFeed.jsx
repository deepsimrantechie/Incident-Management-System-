import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getWorkItems } from '../api'
import PriorityBadge from './PriorityBadge'
import StatusBadge from './StatusBadge'

export default function LiveFeed() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  const fetchItems = async () => {
    try {
      const res = await getWorkItems()
      setItems(res.data)
      setError(null)
    } catch (e) {
      setError('Failed to connect to backend. Make sure backend is running on port 8000.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchItems()
    const interval = setInterval(fetchItems, 5000)
    return () => clearInterval(interval)
  }, [])

  if (loading) return (
    <div style={{ textAlign: 'center', padding: '64px', color: '#94a3b8' }}>
      Loading incidents...
    </div>
  )

  if (error) return (
    <div style={{
      background: '#450a0a',
      border: '1px solid #dc2626',
      color: '#fca5a5',
      padding: '16px',
      borderRadius: '8px'
    }}>
      {error}
    </div>
  )

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h2 style={{ color: 'white', fontSize: '20px', fontWeight: 'bold', margin: 0 }}>
          Live Incidents
        </h2>
        <span style={{ color: '#94a3b8', fontSize: '13px' }}>
          Auto-refreshes every 5s
        </span>
      </div>

      {items.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '64px', color: '#64748b' }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>✅</div>
          <div>No active incidents. System is healthy.</div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {items.map(item => (
            <div
              key={item.id}
              onClick={() => navigate('/incident/' + item.id)}
              style={{
                background: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '8px',
                padding: '16px',
                cursor: 'pointer',
              }}
              onMouseEnter={e => e.currentTarget.style.borderColor = '#3b82f6'}
              onMouseLeave={e => e.currentTarget.style.borderColor = '#334155'}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <PriorityBadge priority={item.priority} />
                  <span style={{ color: 'white', fontWeight: '600', fontFamily: 'monospace' }}>
                    {item.component_id}
                  </span>
                  <StatusBadge status={item.status} />
                </div>
                <div style={{ textAlign: 'right', color: '#94a3b8', fontSize: '13px' }}>
                  <div>{item.signal_count} signals</div>
                  <div>{new Date(item.created_at).toLocaleTimeString()}</div>
                </div>
              </div>
              {item.mttr_seconds && (
                <div style={{ marginTop: '8px', fontSize: '12px', color: '#86efac' }}>
                  MTTR: {Math.round(item.mttr_seconds / 60)} minutes
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
