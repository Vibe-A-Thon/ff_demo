import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API_BASE = `${BACKEND_URL}/api`;

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('ff_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth APIs
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  getMe: () => api.get('/auth/me'),
};

// Battle APIs
export const battleAPI = {
  getAll: () => api.get('/battles'),
  get: (id) => api.get(`/battles/${id}`),
  create: (data) => api.post('/battles', data),
  start: (id) => api.post(`/battles/${id}/start`),
  stop: (id) => api.post(`/battles/${id}/stop`),
  delete: (id) => api.delete(`/battles/${id}`),
};

// Rule APIs
export const ruleAPI = {
  getAll: () => api.get('/rules'),
  get: (id) => api.get(`/rules/${id}`),
  create: (data) => api.post('/rules', data),
  propose: (data) => api.post('/rules/propose', data),
  update: (id, data) => api.put(`/rules/${id}`, data),
  delete: (id) => api.delete(`/rules/${id}`),
  test: (id) => api.post(`/rules/${id}/test`),
  approve: (id, data) => api.post(`/rules/${id}/approve`, data),
  stage: (id, data) => api.post(`/rules/${id}/stage`, data),
  deploy: (id, data) => api.post(`/rules/${id}/deploy`, data),
};

// RSB Package APIs
export const rsbAPI = {
  getAll: () => api.get('/rsb-packages'),
  get: (id) => api.get(`/rsb-packages/${id}`),
  create: (data) => api.post('/rsb-packages', data),
  test: (id) => api.post(`/rsb-packages/${id}/test`),
  merge: (id) => api.post(`/rsb-packages/${id}/merge`),
  delete: (id) => api.delete(`/rsb-packages/${id}`),
};

// Evidence Pack APIs
export const evidenceAPI = {
  getAll: () => api.get('/evidence-packs'),
  get: (id) => api.get(`/evidence-packs/${id}`),
  generate: (battleId) => api.post(`/evidence-packs/generate/${battleId}`),
  export: (id, params) => api.get(`/evidence-packs/${id}/export`, { params }),
  requestExportApproval: (id, data) =>
    api.post(`/evidence-packs/${id}/request-export-approval`, data),
};

// Knowledge Graph APIs
export const knowledgeAPI = {
  getNodes: () => api.get('/knowledge-nodes'),
  createNode: (data) => api.post('/knowledge-nodes', data),
  connectNodes: (sourceId, targetId) => api.put(`/knowledge-nodes/${sourceId}/connect/${targetId}`),
  deleteNode: (id) => api.delete(`/knowledge-nodes/${id}`),
};

// Approval APIs
export const approvalAPI = {
  getAll: () => api.get('/approvals'),
  create: (data) => api.post('/approvals', data),
  approve: (id, approverId) => api.post(`/approvals/${id}/approve?approver_id=${approverId}`),
  reject: (id, approverId) => api.post(`/approvals/${id}/reject?approver_id=${approverId}`),
};

// Teams & Agents APIs
export const teamAPI = {
  getAll: () => api.get('/teams'),
  get: (id) => api.get(`/teams/${id}`),
  seed: () => api.post('/teams/seed'),
};

export const agentAPI = {
  getAll: (params) => api.get('/agents', { params }),
  get: (id) => api.get(`/agents/${id}`),
  register: (data) => api.post('/agents/register', data),
  seed: () => api.post('/agents/seed'),
  listTasks: (params) => api.get('/agents/tasks', { params }),
  createTask: (data) => api.post('/agents/tasks', data),
  completeTask: (taskId, data) => api.post(`/agents/tasks/${taskId}/complete`, data),
  listRequests: (params) => api.get('/agents/requests', { params }),
  createRequest: (data) => api.post('/agents/requests', data),
  respondRequest: (requestId, data) => api.post(`/agents/requests/${requestId}/respond`, data),
};

// Metrics APIs
export const metricsAPI = {
  getDashboard: () => api.get('/metrics/dashboard'),
};

// RAG APIs
export const ragAPI = {
  listCollections: () => api.get('/rag/collections'),
  listDocuments: (params) => api.get('/rag/documents', { params }),
  createDocument: (data) => api.post('/rag/documents', data),
  seed: (params) => api.post('/rag/seed', null, { params }),
  retrieve: (data) => api.post('/rag/retrieve', data),
  query: (data) => api.post('/rag/query', data),
};

// AI APIs
export const aiAPI = {
  think: (data) => api.post('/ai/think', data),
};

// Seed data
export const seedData = () => api.post('/seed-data');

// WebSocket helper
export const createBattleWebSocket = (battleId) => {
  const wsUrl = BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://');
  return new WebSocket(`${wsUrl}/ws/battle/${battleId}`);
};

export default api;
