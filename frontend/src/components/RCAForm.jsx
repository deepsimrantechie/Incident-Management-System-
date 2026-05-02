import { useState } from 'react'
import { submitRCA } from '../api'

const CATEGORIES = [
  'Hardware Failure',
  'Software Bug',
  'Configuration Error',
  'Network Issue',
  'Capacity Exhaustion',
  'Third Party Failure',
  'Human Error',
  'Security Incident',
  'Unknown',
]

const inputStyle = {
  width: '100%',
  background: '#0f172a',
  border: '1px solid #475569',
  borderRadius: '6px',
  padding: '8px 12px',
  color: 'white',
  fontSize: '14px',
  outline: 'none',
  boxSizing: 'border-box',
}

const labelStyle = {
  display: 'block',
  color: '#94a3b8',
  fontSize: '13px',
  marginBottom: '6px',
}

export default function RCAForm({ workItemId, onSuccess }) {
  const [form, setForm] = useState({
    incident_start: '',
    incident_end: '',
    root_cause_category: '',
    fix_applied: '',
    prevention_steps: '',
  })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  const handleSubmit = async () => {
    if (!form.incident_start || !form.incident_end || !form.root_cause_category || !form.fix_applied || !form.prevention_steps) {
      setError('All fields are required')
      return
    }
    setSubmitting(true)
    setError(null)
    try {
      await submitRCA(workItemId, {
        ...form,
        incident_start: new Date(form.incident_start).toISOString(),
        incident_end: new Date(form.incident_end).toISOString(),
      })
      onSuccess()
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to submit RCA')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div style={{
      background: '#1e293b',
      border: '1px solid #16a34a',
      borderRadius: '8px',
      padding: '24px',
    }}>
      <h3 style={{ color: '#86efac', fontSize: '16px', fontWeight: 'bold', marginTop: 0, marginBottom: '20px' }}>
        Root Cause Analysis Form
      </h3>

      {error && (
        <div style={{
          background: '#450a0a',
          border: '1px solid #dc2626',
          color: '#fca5a5',
          padding: '12px',
          borderRadius: '6px',
          marginBottom: '16px',
          fontSize: '13px'
        }}>
          {error}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
        <div>
          <label style={labelStyle}>Incident Start</label>
          <input type="datetime-local" name="incident_start"
            value={form.incident_start} onChange={handleChange} style={inputStyle} />
        </div>
        <div>
          <label style={labelStyle}>Incident End</label>
          <input type="datetime-local" name="incident_end"
            value={form.incident_end} onChange={handleChange} style={inputStyle} />
        </div>
      </div>

      <div style={{ marginBottom: '16px' }}>
        <label style={labelStyle}>Root Cause Category</label>
        <select name="root_cause_category" value={form.root_cause_category}
          onChange={handleChange} style={inputStyle}>
          <option value="">Select a category...</option>
          {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      <div style={{ marginBottom: '16px' }}>
        <label style={labelStyle}>Fix Applied</label>
        <textarea name="fix_applied" value={form.fix_applied}
          onChange={handleChange} rows={3}
          placeholder="Describe what fix was applied..."
          style={{ ...inputStyle, resize: 'none' }} />
      </div>

      <div style={{ marginBottom: '20px' }}>
        <label style={labelStyle}>Prevention Steps</label>
        <textarea name="prevention_steps" value={form.prevention_steps}
          onChange={handleChange} rows={3}
          placeholder="How will this be prevented in future..."
          style={{ ...inputStyle, resize: 'none' }} />
      </div>

      <button
        onClick={handleSubmit}
        disabled={submitting}
        style={{
          width: '100%',
          background: submitting ? '#166534' : '#16a34a',
          color: 'white',
          padding: '10px',
          borderRadius: '6px',
          border: 'none',
          fontSize: '14px',
          fontWeight: '600',
          cursor: submitting ? 'not-allowed' : 'pointer',
        }}
      >
        {submitting ? 'Submitting...' : 'Submit RCA and Close Incident'}
      </button>
    </div>
  )
}
