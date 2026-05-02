import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getWorkItem, transitionWorkItem } from '../api'
import PriorityBadge from './PriorityBadge'
import StatusBadge from './StatusBadge'
import RCAForm from './RCAForm'

export default function IncidentDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [transitioning, setTransitioning] = useState(false)
  const [showRCA, setShowRCA] = useState(false)

  const fetchData = async () => {
    try {
      const res = await getWorkItem(id)
      setData(res.data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData() }, [id])

  const handleTransition = async () => {
    setTransitioning(true)
    try {
      await transitionWorkItem(id)
      await fetchData()
    } catch (e) {
      alert(e.response?.data?.detail || 'Transition failed')
    } finally {
      setTransitioning(false)
    }
  }

  if (loading) return (
    <div style={{ textAlign: 'center', padding: '64px', color: '#94a3b8' }}>
      Loading incident...
    </div>
  )

  if (!data) return (
    <div style={{ color: '#fca5a5' }}>Incident not found</div>
  )

  const { work_item, signals } = data
  const canTransition = work_item.status !== 'CLOSED' && work_item.status !== 'RESOLVED'
  const canRCA = work_item.status === 'RESOLVED'

  const nextLabel = {
    OPEN: 'Move to INVESTIGATING',
    INVESTIGATING: 'Move to RESOLVED',
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
        <button
          onClick={() => navigate('/')}
          style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '14px' }}
        >
          ← Back
        </button>
        <span style={{ color: 'white', fontWeight: 'bold', fontSize: '18px', fontFamily: 'monospace' }}>
          {work_item.component_id}
        </span>
        <PriorityBadge priority={work_item.priority} />
        <StatusBadge status={work_item.status} />
      </div>

      <div style={{
        background: '#1e293b',
        border: '1px solid #334155',
        borderRadius: '8px',
        padding: '24px',
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: '16px'
      }}>
        <div>
          <div style={{ color: '#94a3b8', fontSize: '12px', marginBottom: '4px' }}>Signal Count</div>
          <div style={{ color: 'white', fontWeight: 'bold', fontSize: '28px' }}>{work_item.signal_count}</div>
        </div>
        <div>
          <div style={{ color: '#94a3b8', fontSize: '12px', marginBottom: '4px' }}>Priority</div>
          <div style={{ marginTop: '4px' }}><PriorityBadge priority={work_item.priority} /></div>
        </div>
        <div>
          <div style={{ color: '#94a3b8', fontSize: '12px', marginBottom: '4px' }}>Started At</div>
          <div style={{ color: 'white', fontSize: '13px' }}>
            {new Date(work_item.start_time).toLocaleString()}
          </div>
        </div>
        <div>
          <div style={{ color: '#94a3b8', fontSize: '12px', marginBottom: '4px' }}>MTTR</div>
          <div style={{ color: 'white', fontWeight: 'bold' }}>
            {work_item.mttr_seconds ? Math.round(work_item.mttr_seconds / 60) + ' min' : '—'}
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '12px' }}>
        {canTransition && (
          <button
            onClick={handleTransition}
            disabled={transitioning}
            style={{
              background: '#2563eb',
              color: 'white',
              padding: '10px 20px',
              borderRadius: '6px',
              border: 'none',
              fontSize: '14px',
              fontWeight: '600',
              cursor: transitioning ? 'not-allowed' : 'pointer',
              opacity: transitioning ? 0.6 : 1,
            }}
          >
            {transitioning ? 'Processing...' : nextLabel[work_item.status]}
          </button>
        )}
        {canRCA && (
          <button
            onClick={() => setShowRCA(!showRCA)}
            style={{
              background: '#16a34a',
              color: 'white',
              padding: '10px 20px',
              borderRadius: '6px',
              border: 'none',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer',
            }}
          >
            {showRCA ? 'Hide RCA Form' : 'Submit RCA and Close'}
          </button>
        )}
        {work_item.status === 'CLOSED' && (
          <div style={{ color: '#86efac', padding: '10px', fontSize: '14px' }}>
            ✅ Incident closed successfully
          </div>
        )}
      </div>

      {showRCA && (
        <RCAForm workItemId={id} onSuccess={() => { setShowRCA(false); fetchData() }} />
      )}

      <div>
        <h3 style={{ color: 'white', fontSize: '16px', fontWeight: '600', marginBottom: '12px' }}>
          Raw Signals ({signals.length})
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '400px', overflowY: 'auto' }}>
          {signals.length === 0 ? (
            <p style={{ color: '#64748b', fontSize: '14px' }}>
              No signals linked yet — consumer may still be processing
            </p>
          ) : (
            signals.map((sig, i) => (
              <div key={i} style={{
                background: '#0f172a',
                border: '1px solid #334155',
                borderRadius: '6px',
                padding: '12px',
                fontFamily: 'monospace',
                fontSize: '12px',
                color: '#cbd5e1'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ color: '#f87171' }}>{sig.error_code}</span>
                  <span style={{ color: '#64748b' }}>{sig.timestamp}</span>
                </div>
                <div>{sig.message}</div>
              </div>
            ))
          )}
        </div>
      </div>

    </div>
  )
}
