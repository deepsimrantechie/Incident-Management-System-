export default function StatusBadge({ status }) {
  const colors = {
    OPEN:          { background: '#450a0a', color: '#fca5a5', border: '1px solid #dc2626' },
    INVESTIGATING: { background: '#422006', color: '#fcd34d', border: '1px solid #ca8a04' },
    RESOLVED:      { background: '#0c1a3a', color: '#93c5fd', border: '1px solid #2563eb' },
    CLOSED:        { background: '#052e16', color: '#86efac', border: '1px solid #16a34a' },
  }
  const style = colors[status] || { background: '#1e293b', color: '#94a3b8', border: '1px solid #475569' }
  return (
    <span style={{
      ...style,
      padding: '2px 8px',
      borderRadius: '4px',
      fontSize: '12px',
      fontWeight: '600'
    }}>
      {status}
    </span>
  )
}
