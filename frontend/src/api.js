import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' }
})

export const getWorkItems = () => api.get('/workitems')
export const getWorkItem = (id) => api.get('/workitems/' + id)
export const transitionWorkItem = (id) => api.patch('/workitems/' + id + '/transition')
export const submitRCA = (id, data) => api.post('/workitems/' + id + '/rca', data)
export const getRCA = (id) => api.get('/workitems/' + id + '/rca')
export const sendSignal = (data) => api.post('/signals', data)
export const getHealth = () => axios.get('http://localhost:8000/health')
