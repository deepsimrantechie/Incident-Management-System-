export default function PriorityBadge({ priority }) {
  const colors = {
    P0: { background: '#dc2626', color: 'white' },
    P1: { background: '#ea580c', color: 'white' },
    P2: { background: '#ca8a04', color: 'white' },
    P3: { background: '#2563eb', color: 'white' },
  }
  const style = colors[priority] || { background: '#64748b', color: 'white' }
  return (
    <span style={{
      ...style,
      padding: '2px 8px',
      borderRadius: '4px',
      fontSize: '12px',
      fontWeight: 'bold'
    }}>
      {priority}
    </span>
  )
}
