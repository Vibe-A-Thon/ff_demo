export const battleAPI = {
  getAll: jest.fn(() => Promise.resolve({ data: [] })),
  get: jest.fn(() => Promise.resolve({ data: {} })),
  create: jest.fn(() => Promise.resolve({ data: {} })),
  start: jest.fn(() => Promise.resolve({ data: {} })),
  stop: jest.fn(() => Promise.resolve({ data: {} })),
  delete: jest.fn(() => Promise.resolve({ data: {} })),
};

export const ruleAPI = {
  getAll: jest.fn(() => Promise.resolve({ data: [] })),
  get: jest.fn(() => Promise.resolve({ data: {} })),
  create: jest.fn(() => Promise.resolve({ data: {} })),
  update: jest.fn(() => Promise.resolve({ data: {} })),
  delete: jest.fn(() => Promise.resolve({ data: {} })),
  test: jest.fn(() => Promise.resolve({ data: {} })),
};

export const rsbAPI = {
  getAll: jest.fn(() => Promise.resolve({ data: [] })),
  get: jest.fn(() => Promise.resolve({ data: {} })),
  create: jest.fn(() => Promise.resolve({ data: {} })),
  test: jest.fn(() => Promise.resolve({ data: {} })),
  merge: jest.fn(() => Promise.resolve({ data: {} })),
  delete: jest.fn(() => Promise.resolve({ data: {} })),
};

export const evidenceAPI = {
  getAll: jest.fn(() => Promise.resolve({ data: [] })),
  get: jest.fn(() => Promise.resolve({ data: {} })),
  generate: jest.fn(() => Promise.resolve({ data: {} })),
  export: jest.fn(() => Promise.resolve({ data: {} })),
};

export const knowledgeAPI = {
  getNodes: jest.fn(() => Promise.resolve({ data: [] })),
  createNode: jest.fn(() => Promise.resolve({ data: {} })),
  connectNodes: jest.fn(() => Promise.resolve({ data: {} })),
  deleteNode: jest.fn(() => Promise.resolve({ data: {} })),
};

export const approvalAPI = {
  getAll: jest.fn(() => Promise.resolve({ data: [] })),
  create: jest.fn(() => Promise.resolve({ data: {} })),
  approve: jest.fn(() => Promise.resolve({ data: {} })),
  reject: jest.fn(() => Promise.resolve({ data: {} })),
};

export const metricsAPI = {
  getDashboard: jest.fn(() => Promise.resolve({ data: {} })),
};

export const aiAPI = {
  think: jest.fn(() => Promise.resolve({ data: {} })),
};

export const seedData = jest.fn(() => Promise.resolve({ data: {} }));

export const API_BASE = "http://localhost/api";

export default {};
