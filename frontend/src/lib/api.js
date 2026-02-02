import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API_BASE = `${BACKEND_URL}/api`;

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("ff_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth APIs
export const authAPI = {
  register: (data) => api.post("/auth/register", data),
  login: (data) => api.post("/auth/login", data),
  getMe: () => api.get("/auth/me"),
};

// Battle APIs
export const battleAPI = {
  getAll: () => api.get("/battles"),
  get: (id) => api.get(`/battles/${id}`),
  create: (data) => api.post("/battles", data),
  start: (id) => api.post(`/battles/${id}/start`),
  stop: (id) => api.post(`/battles/${id}/stop`),
  importBrc: (formData) =>
    api.post("/battles/import-brc", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  delete: (id) => api.delete(`/battles/${id}`),
};

// BRC Capsule APIs - Complete Battle Run Capsule operations
export const brcAPI = {
  // Core operations
  validate: (formData) =>
    api.post("/brc/validate", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  preview: (formData) =>
    api.post("/brc/preview", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  import: (formData) =>
    api.post("/brc/import", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  export: (battleId, options = {}) =>
    api.post(
      "/brc/export",
      new URLSearchParams({
        battle_id: battleId,
        include_telemetry: options.includeTelemetry ?? true,
        include_graphs: options.includeGraphs ?? true,
      }),
      { responseType: "blob" }
    ),

  // Catalog management
  getCatalog: (params = {}) => api.get("/brc/catalog", { params }),
  getPackage: (packageId) => api.get(`/brc/catalog/${packageId}`),
  deletePackage: (packageId) => api.delete(`/brc/catalog/${packageId}`),

  // Replay operations
  startReplay: (formData) =>
    api.post("/brc/replay/start", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  listReplaySessions: (params = {}) =>
    api.get("/brc/replay/sessions", { params }),
  getReplaySession: (sessionId) =>
    api.get(`/brc/replay/sessions/${sessionId}`),
  reevaluate: (sessionId) =>
    api.post(`/brc/replay/sessions/${sessionId}/reevaluate`),
  rerunDefense: (sessionId, improvementFactor = 0.1) =>
    api.post(
      `/brc/replay/sessions/${sessionId}/rerun-defense`,
      new URLSearchParams({ improvement_factor: improvementFactor })
    ),

  // Comparison
  compare: (beforeFile, afterFile) => {
    const formData = new FormData();
    formData.append("before_file", beforeFile);
    formData.append("after_file", afterFile);
    return api.post("/brc/compare", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  // Postmortem generation
  generatePostmortem: (formData) =>
    api.post("/brc/postmortem", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  getBattlePostmortem: (battleId) => api.get(`/brc/${battleId}/postmortem`),
};


// Run (War Loop) APIs
export const runAPI = {
  getAll: () => api.get("/runs"),
  start: (data) => api.post("/runs/start", data),
  get: (id) => api.get(`/runs/${id}`),
  step: (id) => api.post(`/runs/${id}/step`),
  replay: (id, data) => api.post(`/runs/${id}/replay`, data),
  exportBrc: (id) =>
    api.get(`/runs/${id}/export-brc`, { responseType: "blob" }),
};

// Workflow APIs
export const workflowAPI = {
  get: (runId) => api.get(`/workflow/${runId}`),
  getStatus: (runId) => api.get(`/workflow/${runId}/status`),
  getApprovals: (runId) => api.get(`/workflow/${runId}/approvals`),
  advance: (runId, data) => api.post(`/workflow/${runId}/advance`, data),
  decide: (runId, data) => api.post(`/workflow/${runId}/decision`, data),
  autoRun: (runId, data) => api.post(`/workflow/${runId}/auto-run`, data),
  freeze: (runId, data) => api.post(`/workflow/${runId}/freeze`, data),
  rollback: (runId, data) => api.post(`/workflow/${runId}/rollback`, data),
  reset: (runId, data) => api.post(`/workflow/${runId}/reset`, data),
};

// Graph APIs
export const graphAPI = {
  getRunGraph: (runId) => api.get(`/runs/${runId}/graph`),
  getRunLineage: (runId) => api.get(`/runs/${runId}/lineage-graph`),
  getEvidenceLineage: (packId) =>
    api.get(`/evidence-packs/${packId}/lineage-graph`),
};

// Rule APIs
export const ruleAPI = {
  getAll: () => api.get("/rules"),
  get: (id) => api.get(`/rules/${id}`),
  create: (data) => api.post("/rules", data),
  propose: (data) => api.post("/rules/propose", data),
  update: (id, data) => api.put(`/rules/${id}`, data),
  delete: (id) => api.delete(`/rules/${id}`),
  test: (id) => api.post(`/rules/${id}/test`),
  approve: (id, data) => api.post(`/rules/${id}/approve`, data),
  stage: (id, data) => api.post(`/rules/${id}/stage`, data),
  deploy: (id, data) => api.post(`/rules/${id}/deploy`, data),
};

// RSB Package APIs
export const rsbAPI = {
  getAll: () => api.get("/rsb-packages"),
  get: (id) => api.get(`/rsb-packages/${id}`),
  create: (data) => api.post("/rsb-packages", data),
  upload: (formData) =>
    api.post("/rsb-packages/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  validate: (id) => api.post(`/rsb-packages/${id}/validate`),
  test: (id) => api.post(`/rsb-packages/${id}/test`),
  getDiffs: (id) => api.get(`/rsb-packages/${id}/diffs`),
  applyPatch: (id, data) => api.post(`/rsb-packages/${id}/apply-patch`, data),
  merge: (id) => api.post(`/rsb-packages/${id}/merge`),
  resolveConflicts: (id, data) =>
    api.post(`/rsb-packages/${id}/resolve-conflicts`, data),
  stage: (id) => api.post(`/rsb-packages/${id}/stage`),
  export: (id) =>
    api.get(`/rsb-packages/${id}/export`, { responseType: "blob" }),
  delete: (id) => api.delete(`/rsb-packages/${id}`),
};

// AMC Capsule APIs
export const amcAPI = {
  export: (data) => api.post("/amc/export", data, { responseType: "blob" }),
  validate: (formData) =>
    api.post("/amc/validate", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  preview: (formData) =>
    api.post("/amc/preview", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  import: (formData) =>
    api.post("/amc/import", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  diff: (formData) =>
    api.post("/amc/diff", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  catalog: () => api.get("/amc/catalog"),
  baseline: (teamId) =>
    api.get("/amc/baseline", { params: { team_id: teamId } }),
  activate: (formData) =>
    api.post("/amc/activate", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
};

// Brain Surgery APIs - Hot-swap, Merge, Rollback operations
export const brainSurgeryAPI = {
  // Session management
  startSession: (formData) =>
    api.post("/brain-surgery/sessions", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  listSessions: (params) =>
    api.get("/brain-surgery/sessions", { params }),
  getSession: (sessionId) =>
    api.get(`/brain-surgery/sessions/${sessionId}`),
  
  // Analyze AMC for session
  analyzeAmc: (sessionId, formData) =>
    api.post(`/brain-surgery/sessions/${sessionId}/analyze`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  
  // Conflict resolution
  resolveConflict: (sessionId, formData) =>
    api.post(`/brain-surgery/sessions/${sessionId}/resolve-conflict`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  
  // Sandbox validation
  runSandbox: (sessionId) =>
    api.post(`/brain-surgery/sessions/${sessionId}/sandbox`),
  
  // Hot-swap execution
  executeHotSwap: (sessionId, formData) =>
    api.post(`/brain-surgery/sessions/${sessionId}/hot-swap`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  
  // Rollback
  rollback: (formData) =>
    api.post("/brain-surgery/rollback", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  
  // Team state
  getTeamState: (teamId) =>
    api.get(`/brain-surgery/teams/${teamId}/state`),
  listRollbackSnapshots: (teamId, limit = 10) =>
    api.get(`/brain-surgery/teams/${teamId}/rollback-snapshots`, { params: { limit } }),
  
  // Knowledge graph for merge visualization
  getKnowledgeGraph: (sessionId) =>
    api.get(`/brain-surgery/sessions/${sessionId}/knowledge-graph`),
};

// Lessons API - Lesson Distiller for BRC/Battle learnings
export const lessonsAPI = {
  // Distill battle learnings to AMC format
  distillBattle: (formData) =>
    api.post("/lessons/distill-battle", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  
  // Distill BRC postmortem to AMC format
  distillBrc: (formData) =>
    api.post("/lessons/distill-brc", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  
  // Get distilled lessons for a team
  getTeamLessons: (teamId, sinceDays = 180) =>
    api.get(`/lessons/team/${teamId}`, { params: { since_days: sinceDays } }),
  
  // List distillation records
  listDistillations: (params) =>
    api.get("/lessons/distillations", { params }),
};

// PEP APIs
export const pepAPI = {
  export: (data) => api.post("/pep/export", data, { responseType: "blob" }),
  validate: (formData) =>
    api.post("/pep/validate", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  preview: (formData) =>
    api.post("/pep/preview", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  import: (formData) =>
    api.post("/pep/import", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
};

// Evidence Pack APIs
export const evidenceAPI = {
  getAll: () => api.get("/evidence-packs"),
  get: (id) => api.get(`/evidence-packs/${id}`),
  generate: (battleId) => api.post(`/evidence-packs/generate/${battleId}`),
  generateRun: (runId) => api.post(`/evidence-packs/generate/run/${runId}`),
  export: (id, params) => {
    const responseType =
      params?.format === "pdf" || params?.format === "story_pdf"
        ? "blob"
        : undefined;
    return api.get(`/evidence-packs/${id}/export`, { params, responseType });
  },
  requestExportApproval: (id, data) =>
    api.post(`/evidence-packs/${id}/request-export-approval`, data),
};

// Knowledge Graph APIs
export const knowledgeAPI = {
  getNodes: () => api.get("/knowledge-nodes"),
  createNode: (data) => api.post("/knowledge-nodes", data),
  connectNodes: (sourceId, targetId) =>
    api.put(`/knowledge-nodes/${sourceId}/connect/${targetId}`),
  deleteNode: (id) => api.delete(`/knowledge-nodes/${id}`),
  syncNeo4j: () => api.post("/knowledge-nodes/sync-neo4j"),
  neo4jHealth: () => api.get("/knowledge-nodes/neo4j-health"),
  graphSyncStatus: () => api.get("/knowledge-nodes/graph-sync-status"),
};

// Approval APIs
export const approvalAPI = {
  getAll: () => api.get("/approvals"),
  create: (data) => api.post("/approvals", data),
  approve: (id, approverId) =>
    api.post(`/approvals/${id}/approve?approver_id=${approverId}`),
  reject: (id, approverId) =>
    api.post(`/approvals/${id}/reject?approver_id=${approverId}`),
};

// Teams & Agents APIs
export const teamAPI = {
  getAll: () => api.get("/teams"),
  get: (id) => api.get(`/teams/${id}`),
  seed: () => api.post("/teams/seed"),
};

export const agentAPI = {
  getAll: (params) => api.get("/agents", { params }),
  get: (id) => api.get(`/agents/${id}`),
  getRegistry: (params) => api.get("/agents/registry", { params }),
  register: (data) => api.post("/agents/register", data),
  seed: () => api.post("/agents/seed"),
  listTasks: (params) => api.get("/agents/tasks", { params }),
  createTask: (data) => api.post("/agents/tasks", data),
  completeTask: (taskId, data) =>
    api.post(`/agents/tasks/${taskId}/complete`, data),
  executeTask: (taskId) => api.post(`/agents/tasks/${taskId}/execute`),
  routeTasks: (data) => api.post("/agents/route", data),
  orchestrate: (data) => api.post("/agents/orchestrate", data),
  listRequests: (params) => api.get("/agents/requests", { params }),
  createRequest: (data) => api.post("/agents/requests", data),
  respondRequest: (requestId, data) =>
    api.post(`/agents/requests/${requestId}/respond`, data),
  listArtifacts: (params) => api.get("/agents/artifacts", { params }),
  getArtifact: (id) => api.get(`/agents/artifacts/${id}`),
  getLineage: (id) => api.get(`/agents/artifacts/${id}/lineage`),
};

// Metrics APIs
export const metricsAPI = {
  getDashboard: () => api.get("/metrics/dashboard"),
  getPerf: () => api.get("/metrics/perf"),
};

// RAG APIs
export const ragAPI = {
  listCollections: () => api.get("/rag/collections"),
  listDocuments: (params) => api.get("/rag/documents", { params }),
  createDocument: (data) => api.post("/rag/documents", data),
  seed: (params) => api.post("/rag/seed", null, { params }),
  retrieve: (data) => api.post("/rag/retrieve", data),
  query: (data) => api.post("/rag/query", data),
  evaluate: (data) => api.post("/rag/evaluate", data),
  evaluateGold: () => api.get("/rag/evaluate-gold"),
  evaluationHistory: (params) =>
    api.get("/rag/evaluations/history", { params }),
  evaluationAlerts: (params) => api.get("/rag/evaluations/alerts", { params }),
  cacheTelemetry: (params) => api.get("/rag/cache/telemetry", { params }),
};

// Settings APIs
export const settingsAPI = {
  get: () => api.get("/settings"),
  update: (data) => api.put("/settings", data),
};

// AI APIs
export const aiAPI = {
  think: (data) => api.post("/ai/think", data),
};

// LLM APIs
export const llmAPI = {
  getConfig: () => api.get("/llm/config"),
  updateConfig: (data) => api.put("/llm/config", data),
  getTelemetry: (params) => api.get("/llm/telemetry", { params }),
};

// XAI APIs
export const xaiAPI = {
  commentor: (data) => api.post("/xai/commentary", data),
  explainRun: (runId) => api.get(`/xai/explain/${runId}`),
  explainRunFull: (runId) => api.get(`/xai/explain/${runId}/full`),
  explainPackage: (packageId) => api.get(`/xai/package/${packageId}`),
  // Counterfactuals API - linked to real evidence
  getCounterfactuals: (data) => api.post("/xai/counterfactuals", data),
  // Similar Cases API - linked to real evidence packs
  getSimilarCases: (data) => api.post("/xai/similar-cases", data),
  // Find similar cases to an evidence pack
  getSimilarToPack: (packId, params) =>
    api.get(`/xai/evidence-pack/${packId}/similar`, { params }),
};

// Seed data
export const seedData = () => api.post("/seed-data");

// WebSocket helper
export const createBattleWebSocket = (battleId) => {
  const wsUrl = BACKEND_URL.replace("https://", "wss://").replace(
    "http://",
    "ws://",
  );
  const token = localStorage.getItem("ff_token");
  const tokenParam = token ? `?token=${encodeURIComponent(token)}` : "";
  return new WebSocket(`${wsUrl}/ws/battle/${battleId}${tokenParam}`);
};

export default api;
