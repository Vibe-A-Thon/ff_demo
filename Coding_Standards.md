# Fraud Forge Application - Coding Standards & Best Practices

## Executive Summary

This document outlines the coding standards, best practices, and conventions for developing the Fraud Forge Application. These standards are compiled from the engineering practices of world-class organizations including:

**Purpose:** Ensure code quality, maintainability, scalability, and team collaboration.

**Scope:** All TypeScript, React, and Electron code in the Fraud Forge Application.

---

## Table of Contents

1. [General Principles](#1-general-principles)
2. [TypeScript Standards](#2-typescript-standards)
3. [React Standards](#3-react-standards)
4. [Electron-Specific Standards](#4-electron-specific-standards)
5. [File & Folder Organization](#5-file--folder-organization)
6. [Naming Conventions](#6-naming-conventions)
7. [Code Formatting](#7-code-formatting)
8. [Comments & Documentation](#8-comments--documentation)
9. [Error Handling](#9-error-handling)
10. [Testing Standards](#10-testing-standards)
11. [Performance Best Practices](#11-performance-best-practices)
12. [Security Standards](#12-security-standards)
13. [Git Workflow & Commit Standards](#13-git-workflow--commit-standards)
14. [Code Review Guidelines](#14-code-review-guidelines)
15. [Accessibility Standards](#15-accessibility-standards)
16. [Tooling & Automation](#16-tooling--automation)

---

## 1. General Principles

### 1.1 Core Values

**SOLID Principles:**
- ✅ **Single Responsibility** - Each function/class does ONE thing
- ✅ **Open/Closed** - Open for extension, closed for modification
- ✅ **Liskov Substitution** - Subtypes must be substitutable for base types
- ✅ **Interface Segregation** - Many specific interfaces > one general interface
- ✅ **Dependency Inversion** - Depend on abstractions, not concretions

**DRY (Don't Repeat Yourself):**
- Extract repeated logic into reusable functions/components
- Use custom hooks for repeated React logic
- Create utility functions for common operations

**KISS (Keep It Simple, Stupid):**
- Prefer simple solutions over clever ones
- Avoid premature optimization
- Write code for humans first, machines second

**YAGNI (You Aren't Gonna Need It):**
- Don't add functionality until it's needed
- Avoid over-engineering
- Implement features only when required

### 1.2 Code Quality Metrics

**Target Metrics:**
- **Code Coverage:** >80% for critical paths
- **Cyclomatic Complexity:** <10 per function
- **File Length:** <300 lines (prefer smaller modules)
- **Function Length:** <50 lines (prefer <20)
- **Function Parameters:** <5 parameters (use object for >3)
- **Type Coverage:** 100% (strict TypeScript)

### 1.3 Boy Scout Rule

> "Always leave the code better than you found it."

- Fix nearby issues while working on a feature
- Refactor legacy code incrementally
- Update outdated dependencies when safe

---

## 2. TypeScript Standards

### 2.1 Strict Mode

**Always use TypeScript strict mode:**

```json
// tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "strictBindCallApply": true,
    "strictPropertyInitialization": true,
    "noImplicitThis": true,
    "alwaysStrict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  }
}
```

### 2.2 Type Definitions

**✅ DO:**

```typescript
// Explicit return types for public APIs
export function parseRSB(filePath: string): Promise<RSB> {
  // Implementation
}

// Use interfaces for object shapes
interface RSB {
  manifest: Manifest;
  rule: Rule;
  code: string;
  tests: TestSuite;
}

// Use type aliases for unions/intersections
type Status = 'available' | 'staged' | 'deployed' | 'archived';
type DeploymentType = 'full' | 'merge' | 'rollback';

// Use const assertions for literal types
const ATTACK_TYPES = ['account_takeover', 'card_testing', 'velocity'] as const;
type AttackType = typeof ATTACK_TYPES[number];

// Use generics for reusable types
interface ApiResponse<T> {
  data: T;
  error?: string;
  timestamp: string;
}
```

**❌ DON'T:**

```typescript
// Avoid 'any'
function processData(data: any) { } // ❌ BAD

// Avoid implicit any
function process(data) { } // ❌ BAD

// Avoid type assertions unless absolutely necessary
const rsb = data as RSB; // ❌ Avoid if possible

// Don't use Object, Function, String, Number, Boolean
function validate(obj: Object) { } // ❌ Use 'object' or specific interface
```

### 2.3 Nullability

**✅ DO:**

```typescript
// Use optional chaining
const ruleId = rsb?.manifest?.rule_id;

// Use nullish coalescing
const confidence = rule.confidence ?? 0.0;

// Handle null/undefined explicitly
function getRSB(id: string): RSB | null {
  return database.find(id) ?? null;
}

// Use optional properties
interface User {
  id: string;
  name: string;
  email?: string; // Optional
}
```

**❌ DON'T:**

```typescript
// Don't use null and undefined interchangeably
function getData(): null | undefined { } // ❌ Pick one

// Don't check for null/undefined with ==
if (value == null) { } // ❌ Use === null or === undefined
```

### 2.4 Enums vs Union Types

**Prefer union types over enums:**

```typescript
// ✅ GOOD - Union type
type Action = 'review' | 'block' | 'flag' | 'alert' | 'score';

// ❌ AVOID - Enum (generates runtime code)
enum Action {
  Review = 'review',
  Block = 'block',
  Flag = 'flag',
}

// Exception: Use const enum if you need enum benefits
const enum LogLevel {
  Debug,
  Info,
  Warn,
  Error
}
```

### 2.5 Type Guards

**Use type guards for runtime type checking:**

```typescript
// Type predicate
function isRSB(obj: unknown): obj is RSB {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    'manifest' in obj &&
    'rule' in obj
  );
}

// Usage
if (isRSB(data)) {
  // data is now typed as RSB
  console.log(data.manifest.rule_id);
}

// Discriminated unions
type Result<T> =
  | { success: true; data: T }
  | { success: false; error: string };

function handleResult<T>(result: Result<T>) {
  if (result.success) {
    console.log(result.data); // TypeScript knows this is safe
  } else {
    console.error(result.error);
  }
}
```

---

## 3. React Standards

### 3.1 Component Structure

**Functional Components with TypeScript:**

```typescript
import React, { useState, useEffect, useCallback } from 'react';

// Props interface
interface RSBCardProps {
  rsb: RSB;
  onDeploy?: (rsb: RSB) => void;
  className?: string;
}

// Component
export const RSBCard: React.FC<RSBCardProps> = ({ 
  rsb, 
  onDeploy,
  className 
}) => {
  // Hooks first
  const [isExpanded, setIsExpanded] = useState(false);
  
  // Event handlers
  const handleDeploy = useCallback(() => {
    onDeploy?.(rsb);
  }, [rsb, onDeploy]);
  
  // Effects
  useEffect(() => {
    // Side effects
  }, []);
  
  // Early returns
  if (!rsb) {
    return null;
  }
  
  // Render
  return (
    <div className={className}>
      {/* JSX */}
    </div>
  );
};

// Display name for debugging
RSBCard.displayName = 'RSBCard';
```

**Component Order:**

1. Imports
2. Type definitions (interfaces, types)
3. Component definition
4. Hooks (useState, useEffect, custom hooks)
5. Event handlers (useCallback recommended)
6. Helper functions (if any)
7. Early returns (loading, error states)
8. Main render logic
9. Export

### 3.2 Hooks Best Practices

**✅ DO:**

```typescript
// Custom hooks for reusable logic
function useRSB(rsbId: string) {
  const [rsb, setRSB] = useState<RSB | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  
  useEffect(() => {
    let cancelled = false;
    
    async function fetchRSB() {
      try {
        const data = await rsbService.getRSB(rsbId);
        if (!cancelled) {
          setRSB(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err as Error);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }
    
    fetchRSB();
    
    return () => {
      cancelled = true;
    };
  }, [rsbId]);
  
  return { rsb, loading, error };
}

// Memoize expensive computations
const expensiveValue = useMemo(() => {
  return computeExpensiveValue(input);
}, [input]);

// Memoize callbacks passed to child components
const handleClick = useCallback(() => {
  doSomething(id);
}, [id]);

// Cleanup in useEffect
useEffect(() => {
  const subscription = subscribeToNotifications();
  
  return () => {
    subscription.unsubscribe();
  };
}, []);
```

**❌ DON'T:**

```typescript
// Don't call hooks conditionally
if (condition) {
  useEffect(() => { }); // ❌ BAD
}

// Don't call hooks in loops
for (let i = 0; i < 10; i++) {
  useState(0); // ❌ BAD
}

// Don't call hooks in callbacks
const handleClick = () => {
  useState(0); // ❌ BAD
};

// Don't forget dependencies
useEffect(() => {
  fetchData(userId); // ❌ Missing userId in deps
}, []); // Should be [userId]
```

### 3.3 Props Best Practices

**✅ DO:**

```typescript
// Destructure props
const MyComponent: React.FC<Props> = ({ name, age, onSave }) => {
  // ...
};

// Use default props
interface Props {
  name: string;
  theme?: 'light' | 'dark';
}

const MyComponent: React.FC<Props> = ({ 
  name, 
  theme = 'light' // Default value
}) => {
  // ...
};

// Use children prop correctly
interface Props {
  children: React.ReactNode;
}

// Spread remaining props
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary';
}

const Button: React.FC<ButtonProps> = ({ variant = 'primary', children, ...rest }) => {
  return (
    <button className={`btn btn-${variant}`} {...rest}>
      {children}
    </button>
  );
};
```

**❌ DON'T:**

```typescript
// Don't use props as state
const MyComponent: React.FC<Props> = (props) => {
  const [name, setName] = useState(props.name); // ❌ BAD
  // name won't update if props.name changes
};

// Don't mutate props
const MyComponent: React.FC<Props> = ({ data }) => {
  data.push(newItem); // ❌ BAD - mutating props
};
```

### 3.4 State Management

**✅ DO:**

```typescript
// Prefer local state when possible
const [isOpen, setIsOpen] = useState(false);

// Use Zustand for global state
import { create } from 'zustand';

interface RSBStore {
  rsbs: RSB[];
  addRSB: (rsb: RSB) => void;
  removeRSB: (id: string) => void;
}

const useRSBStore = create<RSBStore>((set) => ({
  rsbs: [],
  addRSB: (rsb) => set((state) => ({ 
    rsbs: [...state.rsbs, rsb] 
  })),
  removeRSB: (id) => set((state) => ({ 
    rsbs: state.rsbs.filter(r => r.manifest.rule_id !== id) 
  })),
}));

// Use reducer for complex state logic
const [state, dispatch] = useReducer(reducer, initialState);
```

**❌ DON'T:**

```typescript
// Don't update state directly
state.value = newValue; // ❌ BAD

// Use setState instead
setState({ ...state, value: newValue }); // ✅ GOOD

// Don't use setState with previous state without function
setState({ count: state.count + 1 }); // ❌ BAD
setState((prev) => ({ count: prev.count + 1 })); // ✅ GOOD
```

### 3.5 Conditional Rendering

**✅ DO:**

```typescript
// Use short-circuit evaluation for simple conditions
{isLoading && <Spinner />}

// Use ternary for if-else
{isLoading ? <Spinner /> : <Content />}

// Use early returns for complex conditions
if (error) {
  return <ErrorMessage error={error} />;
}

if (loading) {
  return <Spinner />;
}

return <Content data={data} />;

// Use nullish coalescing for defaults
{title ?? 'Default Title'}
```

**❌ DON'T:**

```typescript
// Don't use && with numbers (0 is falsy)
{count && <Badge count={count} />} // ❌ Won't show when count is 0
{count > 0 && <Badge count={count} />} // ✅ GOOD

// Avoid complex inline conditionals
{isLoading ? (
  isPending ? (
    hasError ? <ErrorSpinner /> : <LoadingSpinner />
  ) : <PartialLoad />
) : <Content />} // ❌ Too complex
```

### 3.6 Lists & Keys

**✅ DO:**

```typescript
// Use stable, unique keys
{rsbs.map((rsb) => (
  <RSBCard key={rsb.manifest.rule_id} rsb={rsb} />
))}

// Use index only for static lists
{STATIC_ITEMS.map((item, index) => (
  <li key={index}>{item}</li>
))}
```

**❌ DON'T:**

```typescript
// Don't use index for dynamic lists
{rsbs.map((rsb, index) => (
  <RSBCard key={index} rsb={rsb} /> // ❌ BAD
))}

// Don't use random keys
{rsbs.map((rsb) => (
  <RSBCard key={Math.random()} rsb={rsb} /> // ❌ BAD
))}
```

---

## 4. Electron-Specific Standards

### 4.1 Process Architecture

**Main Process (Node.js):**

```typescript
// electron/main.ts
import { app, BrowserWindow } from 'electron';
import path from 'path';

let mainWindow: BrowserWindow | null = null;

const createWindow = () => {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,        // ✅ Security
      contextIsolation: true,         // ✅ Security
      enableRemoteModule: false,      // ✅ Security
      preload: path.join(__dirname, 'preload.js'),
    },
  });
  
  mainWindow.loadFile('index.html');
};

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
```

**Preload Script (Bridge):**

```typescript
// electron/preload.ts
import { contextBridge, ipcRenderer } from 'electron';

// Expose protected methods that allow renderer to use ipcRenderer
contextBridge.exposeInMainWorld('electronAPI', {
  // File operations
  readFile: (filePath: string) => ipcRenderer.invoke('read-file', filePath),
  writeFile: (filePath: string, data: string) => 
    ipcRenderer.invoke('write-file', filePath, data),
  
  // Database operations
  queryDB: (query: string, params: any[]) => 
    ipcRenderer.invoke('query-db', query, params),
  
  // FTP operations
  downloadRSB: (config: FTPConfig, remotePath: string, localPath: string) =>
    ipcRenderer.invoke('download-rsb', config, remotePath, localPath),
  
  // Notifications
  onNotification: (callback: (data: any) => void) => {
    ipcRenderer.on('notification', (_, data) => callback(data));
  },
});

// Type declarations
declare global {
  interface Window {
    electronAPI: {
      readFile: (filePath: string) => Promise<string>;
      writeFile: (filePath: string, data: string) => Promise<void>;
      queryDB: (query: string, params: any[]) => Promise<any[]>;
      downloadRSB: (config: FTPConfig, remotePath: string, localPath: string) => Promise<void>;
      onNotification: (callback: (data: any) => void) => void;
    };
  }
}
```

**Renderer Process (React):**

```typescript
// src/services/electron-api.ts
class ElectronAPI {
  async readRSBFile(filePath: string): Promise<string> {
    if (!window.electronAPI) {
      throw new Error('Electron API not available');
    }
    return window.electronAPI.readFile(filePath);
  }
  
  async downloadRSB(config: FTPConfig, remotePath: string, localPath: string): Promise<void> {
    if (!window.electronAPI) {
      throw new Error('Electron API not available');
    }
    return window.electronAPI.downloadRSB(config, remotePath, localPath);
  }
}

export const electronAPI = new ElectronAPI();
```

### 4.2 IPC Communication

**✅ DO:**

```typescript
// Use invoke/handle for request-response
// Main process
ipcMain.handle('read-file', async (event, filePath: string) => {
  try {
    const data = await fs.promises.readFile(filePath, 'utf-8');
    return { success: true, data };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// Renderer process
const result = await window.electronAPI.readFile('/path/to/file');

// Use send/on for one-way messages
// Main process
mainWindow.webContents.send('notification', { 
  type: 'info', 
  message: 'New RSB available' 
});

// Renderer process
window.electronAPI.onNotification((data) => {
  showNotification(data);
});
```

**❌ DON'T:**

```typescript
// Don't use remote module (deprecated and insecure)
const { dialog } = require('electron').remote; // ❌ BAD

// Don't enable nodeIntegration
webPreferences: {
  nodeIntegration: true // ❌ SECURITY RISK
}

// Don't expose entire Node.js APIs
contextBridge.exposeInMainWorld('fs', require('fs')); // ❌ SECURITY RISK
```

### 4.3 Security Best Practices

**Content Security Policy:**

```html
<!-- index.html -->
<meta http-equiv="Content-Security-Policy" 
      content="default-src 'self'; 
               script-src 'self'; 
               style-src 'self' 'unsafe-inline';
               img-src 'self' data:;">
```

**Validate All IPC Inputs:**

```typescript
// Main process
ipcMain.handle('read-file', async (event, filePath: string) => {
  // ✅ Validate input
  if (typeof filePath !== 'string') {
    throw new Error('Invalid file path');
  }
  
  // ✅ Sanitize path
  const safePath = path.normalize(filePath);
  
  // ✅ Check if path is within allowed directory
  const allowedDir = path.join(app.getPath('userData'), 'rsb_files');
  if (!safePath.startsWith(allowedDir)) {
    throw new Error('Access denied');
  }
  
  return fs.promises.readFile(safePath, 'utf-8');
});
```

---

## 5. File & Folder Organization

### 5.1 Directory Structure

```
src/
├── assets/                    # Static assets
│   ├── icons/
│   ├── images/
│   └── fonts/
│
├── components/                # Reusable UI components
│   ├── common/               # Generic components
│   │   ├── Button/
│   │   │   ├── Button.tsx
│   │   │   ├── Button.test.tsx
│   │   │   ├── Button.styles.ts
│   │   │   └── index.ts      # Barrel export
│   │   └── ...
│   │
│   ├── rsb/                  # Domain-specific components
│   │   ├── RSBCard/
│   │   ├── RSBList/
│   │   └── NetworkGraph/
│   │
│   └── layout/               # Layout components
│       ├── Header/
│       ├── Sidebar/
│       └── Footer/
│
├── pages/                    # Page components (routes)
│   ├── Dashboard/
│   │   ├── Dashboard.tsx
│   │   ├── Dashboard.test.tsx
│   │   └── index.ts
│   ├── MergeWorkspace/
│   └── Settings/
│
├── hooks/                    # Custom React hooks
│   ├── useRSB.ts
│   ├── useNotifications.ts
│   ├── useFTP.ts
│   └── index.ts
│
├── services/                 # Business logic & API calls
│   ├── rsb/
│   │   ├── rsb-parser.ts
│   │   ├── rsb-validator.ts
│   │   └── index.ts
│   ├── database/
│   ├── ftp/
│   └── deployment/
│
├── stores/                   # State management (Zustand)
│   ├── rsbStore.ts
│   ├── notificationStore.ts
│   ├── settingsStore.ts
│   └── index.ts
│
├── types/                    # TypeScript type definitions
│   ├── rsb.ts
│   ├── network.ts
│   ├── api.ts
│   └── index.ts
│
├── utils/                    # Utility functions
│   ├── validation.ts
│   ├── formatting.ts
│   ├── checksum.ts
│   └── index.ts
│
├── constants/                # Application constants
│   ├── colors.ts
│   ├── routes.ts
│   ├── config.ts
│   └── index.ts
│
├── styles/                   # Global styles
│   ├── theme.ts
│   ├── global.css
│   └── variables.css
│
├── App.tsx                   # Root component
├── main.tsx                  # Entry point
└── vite-env.d.ts            # Vite types
```

### 5.2 Component File Structure

**One Component Per File:**

```typescript
// ✅ GOOD - Button.tsx
export const Button: React.FC<ButtonProps> = ({ ... }) => {
  return <button>...</button>;
};

// ❌ BAD - Components.tsx
export const Button = () => { };
export const Input = () => { };
export const Select = () => { };
```

**Barrel Exports (index.ts):**

```typescript
// components/common/Button/index.ts
export { Button } from './Button';
export type { ButtonProps } from './Button';

// Usage
import { Button, ButtonProps } from '@/components/common/Button';
```

### 5.3 Import Organization

**Order:**

1. External libraries (React, third-party)
2. Internal absolute imports (aliases)
3. Internal relative imports
4. Types
5. Styles
6. Assets

```typescript
// 1. External libraries
import React, { useState, useEffect } from 'react';
import { Box, Typography } from '@mui/material';
import { format } from 'date-fns';

// 2. Internal absolute imports
import { useRSBStore } from '@/stores/rsbStore';
import { parseRSB } from '@/services/rsb/rsb-parser';
import { Button } from '@/components/common/Button';

// 3. Internal relative imports
import { RSBCard } from './RSBCard';
import { NetworkGraph } from './NetworkGraph';

// 4. Types
import type { RSB, Manifest } from '@/types/rsb';

// 5. Styles
import './Dashboard.css';

// 6. Assets
import logo from '@/assets/logo.png';
```

---

## 6. Naming Conventions

### 6.1 Files & Folders

**Convention:**

| Type | Convention | Example |
|------|-----------|---------|
| Components | PascalCase | `RSBCard.tsx`, `NetworkGraph.tsx` |
| Hooks | camelCase + use prefix | `useRSB.ts`, `useNotifications.ts` |
| Utils | camelCase | `validation.ts`, `formatting.ts` |
| Types | camelCase | `rsb.ts`, `api.ts` |
| Constants | camelCase | `colors.ts`, `config.ts` |
| Tests | Same as source + .test | `Button.test.tsx` |
| Styles | Same as component + .styles | `Button.styles.ts` |

### 6.2 Variables & Functions

**Variables:**

```typescript
// camelCase for variables
const rsbFile = 'file.rsb';
const isLoading = true;
const totalCount = 42;

// UPPER_SNAKE_CASE for constants
const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100MB
const API_BASE_URL = 'https://api.fraudforge.com';
const DEFAULT_TIMEOUT = 30000;

// PascalCase for type/interface names
interface RSBManifest { }
type DeploymentStatus = 'pending' | 'success' | 'failed';

// Prefix boolean variables with is/has/should/can
const isValid = true;
const hasError = false;
const shouldRetry = true;
const canDeploy = false;
```

**Functions:**

```typescript
// camelCase for functions
function parseRSB(filePath: string): RSB { }
function validateManifest(manifest: Manifest): boolean { }

// Verb + Noun pattern
function getRSBById(id: string): RSB | null { }
function setCurrentRSB(rsb: RSB): void { }
function downloadRSBFile(url: string): Promise<void> { }

// Event handlers: handle + Action
const handleClick = () => { };
const handleSubmit = () => { };
const handleChange = () => { };

// Async functions: verb + Async (optional but recommended)
async function fetchRSBAsync(id: string): Promise<RSB> { }
```

### 6.3 Components

**PascalCase:**

```typescript
// Component names
export const RSBCard: React.FC = () => { };
export const NetworkGraph: React.FC = () => { };
export const DeploymentWorkspace: React.FC = () => { };

// Avoid generic names
const Container = () => { }; // ❌ Too generic
const RSBContainer = () => { }; // ✅ Better

// Use descriptive names
const Item = () => { }; // ❌ Too vague
const RSBListItem = () => { }; // ✅ Clear
```

### 6.4 Props Interfaces

**Pattern: ComponentName + Props**

```typescript
interface RSBCardProps {
  rsb: RSB;
  onDeploy?: (rsb: RSB) => void;
  className?: string;
}

interface NetworkGraphProps {
  nodes: RuleNode[];
  edges: RuleEdge[];
  onNodeClick?: (node: RuleNode) => void;
}
```

---

## 7. Code Formatting

### 7.1 Prettier Configuration

**.prettierrc.json:**

```json
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false,
  "arrowParens": "always",
  "bracketSpacing": true,
  "endOfLine": "lf"
}
```

### 7.2 ESLint Configuration

**.eslintrc.json:**

```json
{
  "extends": [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:react/recommended",
    "plugin:react-hooks/recommended",
    "prettier"
  ],
  "parser": "@typescript-eslint/parser",
  "plugins": ["@typescript-eslint", "react", "react-hooks"],
  "rules": {
    "react/react-in-jsx-scope": "off",
    "react/prop-types": "off",
    "@typescript-eslint/explicit-module-boundary-types": "off",
    "@typescript-eslint/no-unused-vars": ["error", { 
      "argsIgnorePattern": "^_" 
    }],
    "no-console": ["warn", { 
      "allow": ["warn", "error"] 
    }],
    "prefer-const": "error",
    "no-var": "error"
  },
  "settings": {
    "react": {
      "version": "detect"
    }
  }
}
```

### 7.3 Line Length & Wrapping

**Maximum line length: 100 characters**

```typescript
// ✅ GOOD - Break into multiple lines
const result = await database.query(
  'SELECT * FROM rsb_files WHERE rule_id = ? AND status = ?',
  [ruleId, status]
);

// ✅ GOOD - Object properties
const config = {
  host: 'ftp.example.com',
  port: 21,
  username: 'user',
  password: 'pass',
};

// ❌ BAD - Too long
const result = await database.query('SELECT * FROM rsb_files WHERE rule_id = ? AND status = ?', [ruleId, status]);
```

---

## 8. Comments & Documentation

### 8.1 JSDoc Comments

**✅ DO:**

```typescript
/**
 * Parses an RSB file and extracts its contents.
 * 
 * @param filePath - Absolute path to the RSB file
 * @returns Parsed RSB object with manifest, rule, code, and tests
 * @throws {Error} If file is not a valid ZIP archive
 * @throws {Error} If manifest.json is missing or invalid
 * 
 * @example
 * ```typescript
 * const rsb = await parseRSB('/path/to/file.rsb');
 * console.log(rsb.manifest.rule_id);
 * ```
 */
export async function parseRSB(filePath: string): Promise<RSB> {
  // Implementation
}

/**
 * React component for displaying RSB information card.
 * 
 * @component
 * @example
 * ```tsx
 * <RSBCard 
 *   rsb={rsbData} 
 *   onDeploy={(rsb) => console.log('Deploying', rsb.manifest.name)}
 * />
 * ```
 */
export const RSBCard: React.FC<RSBCardProps> = ({ rsb, onDeploy }) => {
  // Implementation
};
```

### 8.2 Inline Comments

**✅ GOOD comments:**

```typescript
// Explain WHY, not WHAT
// We need to clone the array to avoid mutating the original
const newRSBs = [...rsbs];

// Explain non-obvious business logic
// Account takeover rules must have confidence >= 0.7 per compliance requirements
if (rsb.rule.confidence < 0.7 && rsb.manifest.attack_type === 'account_takeover') {
  throw new Error('Account takeover rules must have minimum 70% confidence');
}

// TODO: Implement retry logic for failed downloads (JIRA-123)
// FIXME: This causes memory leak in long-running sessions (JIRA-456)
// HACK: Temporary workaround until API v2 is released
```

**❌ BAD comments:**

```typescript
// ❌ Stating the obvious
// Increment counter
counter++;

// ❌ Commented-out code (use version control instead)
// const oldFunction = () => { };
// return oldValue;

// ❌ Misleading or outdated
// This always returns true
function validate() {
  return false; // Contradicts comment
}
```

### 8.3 File Headers

**Add headers to complex files:**

```typescript
/**
 * @fileoverview RSB parser service for extracting and validating RSB files.
 * @module services/rsb/parser
 * 
 * This module handles:
 * - ZIP archive extraction
 * - Manifest validation
 * - Rule definition parsing
 * - Test suite loading
 * 
 * @author Fraud Forge Team
 * @version 1.0.0
 */

// Imports
// ...
```

---

## 9. Error Handling

### 9.1 Error Handling Strategy

**✅ DO:**

```typescript
// Use custom error classes
class RSBValidationError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly details?: unknown
  ) {
    super(message);
    this.name = 'RSBValidationError';
  }
}

// Throw typed errors
function validateManifest(manifest: unknown): Manifest {
  if (!isValidManifest(manifest)) {
    throw new RSBValidationError(
      'Invalid manifest structure',
      'INVALID_MANIFEST',
      { received: manifest }
    );
  }
  return manifest as Manifest;
}

// Handle errors at boundaries
async function loadRSB(filePath: string): Promise<RSB | null> {
  try {
    const rsb = await parseRSB(filePath);
    return rsb;
  } catch (error) {
    if (error instanceof RSBValidationError) {
      logger.error('RSB validation failed', {
        code: error.code,
        details: error.details,
      });
      toast.error('Invalid RSB file');
    } else {
      logger.error('Unexpected error loading RSB', error);
      toast.error('Failed to load RSB file');
    }
    return null;
  }
}

// Use Result type for operations that can fail
type Result<T, E = Error> =
  | { success: true; data: T }
  | { success: false; error: E };

async function downloadRSB(url: string): Promise<Result<RSB>> {
  try {
    const rsb = await fetchRSB(url);
    return { success: true, data: rsb };
  } catch (error) {
    return { 
      success: false, 
      error: error instanceof Error ? error : new Error('Unknown error') 
    };
  }
}
```

**❌ DON'T:**

```typescript
// Don't swallow errors silently
try {
  parseRSB(filePath);
} catch (error) {
  // ❌ Silent failure
}

// Don't use generic error messages
throw new Error('Error'); // ❌ Not helpful

// Don't catch errors without re-throwing or handling
try {
  criticalOperation();
} catch (error) {
  console.log('Error:', error); // ❌ Not enough
}
```

### 9.2 Async Error Handling

**✅ DO:**

```typescript
// Use try-catch with async/await
async function deployRSB(rsb: RSB): Promise<void> {
  try {
    await validateRSB(rsb);
    await backupCurrentRSB();
    await installNewRSB(rsb);
    await restartEngine();
  } catch (error) {
    // Rollback on error
    await rollbackDeployment();
    throw error;
  }
}

// Handle promise rejections
Promise.allSettled([
  downloadRSB('file1.rsb'),
  downloadRSB('file2.rsb'),
  downloadRSB('file3.rsb'),
]).then((results) => {
  results.forEach((result, index) => {
    if (result.status === 'rejected') {
      logger.error(`Download ${index} failed:`, result.reason);
    }
  });
});
```

---

## 10. Testing Standards

### 10.1 Test Organization

**File naming:**
- Unit tests: `ComponentName.test.tsx`
- Integration tests: `ComponentName.integration.test.tsx`
- E2E tests: `feature-name.e2e.test.ts`

**Test structure (AAA pattern):**

```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { RSBCard } from './RSBCard';

describe('RSBCard', () => {
  // Arrange - Setup
  const mockRSB: RSB = {
    manifest: {
      rule_id: 'R-TEST',
      name: 'Test Rule',
      rule_version: '1.0.0',
      attack_type: 'account_takeover',
      created_at: '2025-01-11T00:00:00Z',
      format: 'RSB',
      version: '1.0',
    },
    rule: {
      action: 'review',
      confidence: 0.8,
      description: 'Test description',
      name: 'Test Rule',
      rule_id: 'R-TEST',
      version: '1.0.0',
      conditions: [],
    },
    // ... other fields
  };
  
  it('should render RSB name and version', () => {
    // Arrange
    const onDeploy = vi.fn();
    
    // Act
    render(<RSBCard rsb={mockRSB} onDeploy={onDeploy} />);
    
    // Assert
    expect(screen.getByText('Test Rule')).toBeInTheDocument();
    expect(screen.getByText('1.0.0')).toBeInTheDocument();
  });
  
  it('should call onDeploy when deploy button is clicked', () => {
    // Arrange
    const onDeploy = vi.fn();
    render(<RSBCard rsb={mockRSB} onDeploy={onDeploy} />);
    
    // Act
    const deployButton = screen.getByRole('button', { name: /deploy/i });
    fireEvent.click(deployButton);
    
    // Assert
    expect(onDeploy).toHaveBeenCalledTimes(1);
    expect(onDeploy).toHaveBeenCalledWith(mockRSB);
  });
});
```

### 10.2 Test Coverage Goals

**Minimum coverage:**
- Critical paths: 100%
- Business logic: 90%
- UI components: 80%
- Overall: 80%

**What to test:**

✅ **DO test:**
- User interactions
- Edge cases and error states
- Business logic
- API integrations
- State management

❌ **DON'T test:**
- Third-party library internals
- Implementation details (internal state)
- Styling (unless it affects functionality)

### 10.3 Mocking

```typescript
// Mock services
import { vi } from 'vitest';
import * as rsbService from '@/services/rsb/rsb-parser';

vi.mock('@/services/rsb/rsb-parser', () => ({
  parseRSB: vi.fn(),
}));

// Use mocks in tests
it('should handle parse error', async () => {
  vi.mocked(rsbService.parseRSB).mockRejectedValue(
    new Error('Invalid RSB file')
  );
  
  const result = await loadRSB('/path/to/file.rsb');
  expect(result).toBeNull();
});
```

---

## 11. Performance Best Practices

### 11.1 React Performance

**✅ DO:**

```typescript
// Memoize expensive computations
const sortedRSBs = useMemo(() => {
  return rsbs.sort((a, b) => 
    a.manifest.created_at.localeCompare(b.manifest.created_at)
  );
}, [rsbs]);

// Memoize components that don't need to re-render
const MemoizedRSBCard = React.memo(RSBCard, (prevProps, nextProps) => {
  return prevProps.rsb.manifest.rule_id === nextProps.rsb.manifest.rule_id;
});

// Use virtualization for long lists
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={600}
  itemCount={rsbs.length}
  itemSize={80}
  width="100%"
>
  {({ index, style }) => (
    <div style={style}>
      <RSBCard rsb={rsbs[index]} />
    </div>
  )}
</FixedSizeList>

// Lazy load routes
const Dashboard = lazy(() => import('@/pages/Dashboard'));
const Settings = lazy(() => import('@/pages/Settings'));

// Debounce expensive operations
import { debounce } from 'lodash';

const debouncedSearch = useMemo(
  () => debounce((query: string) => {
    performSearch(query);
  }, 300),
  []
);
```

### 11.2 Bundle Optimization

```typescript
// Dynamic imports for code splitting
const loadGraph = async () => {
  const { NetworkGraph } = await import('@/components/rsb/NetworkGraph');
  return NetworkGraph;
};

// Tree-shakeable imports
import { format } from 'date-fns'; // ✅ Only imports format
import * as dateFns from 'date-fns'; // ❌ Imports everything
```

### 11.3 Database Optimization

```typescript
// Use indexes
db.exec(`
  CREATE INDEX IF NOT EXISTS idx_rule_id ON rsb_files(rule_id);
  CREATE INDEX IF NOT EXISTS idx_status ON rsb_files(status);
`);

// Use prepared statements
const stmt = db.prepare('SELECT * FROM rsb_files WHERE rule_id = ?');
const rsb = stmt.get(ruleId);

// Batch inserts
const insert = db.prepare('INSERT INTO rsb_files VALUES (?, ?, ?)');
const insertMany = db.transaction((rsbs) => {
  for (const rsb of rsbs) {
    insert.run(rsb.id, rsb.name, rsb.version);
  }
});

insertMany(rsbArray);
```

---

## 12. Security Standards

### 12.1 Input Validation

**✅ DO:**

```typescript
// Validate all user inputs
function validateRuleId(ruleId: string): boolean {
  // Must match pattern: R-[A-Z_]+
  const pattern = /^R-[A-Z_]+$/;
  return pattern.test(ruleId);
}

// Sanitize file paths
import path from 'path';

function sanitizePath(userPath: string): string {
  // Normalize path
  const normalized = path.normalize(userPath);
  
  // Ensure it's within allowed directory
  const allowedDir = '/safe/directory';
  const resolved = path.resolve(allowedDir, normalized);
  
  if (!resolved.startsWith(allowedDir)) {
    throw new Error('Invalid path');
  }
  
  return resolved;
}

// Escape HTML to prevent XSS
function escapeHtml(unsafe: string): string {
  return unsafe
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
```

### 12.2 Secrets Management

**✅ DO:**

```typescript
// Use environment variables
const FTP_PASSWORD = process.env.FTP_PASSWORD;

// Encrypt sensitive data before storing
import { safeStorage } from 'electron';

const encryptedPassword = safeStorage.encryptString(password);
localStorage.setItem('ftp_pass', encryptedPassword);

// Decrypt when needed
const decryptedPassword = safeStorage.decryptString(
  localStorage.getItem('ftp_pass')
);
```

**❌ DON'T:**

```typescript
// Don't hardcode secrets
const API_KEY = 'sk-1234567890abcdef'; // ❌ BAD

// Don't log sensitive data
console.log('Password:', password); // ❌ BAD

// Don't store plaintext passwords
localStorage.setItem('password', password); // ❌ BAD
```

### 12.3 Dependency Security

```bash
# Audit dependencies regularly
npm audit

# Fix vulnerabilities
npm audit fix

# Check for outdated packages
npm outdated

# Use exact versions for security-critical deps
"better-sqlite3": "9.2.2"  # Exact version
"react": "^18.2.0"          # Allow patches
```

---

## 13. Git Workflow & Commit Standards

### 13.1 Branch Naming

**Convention:**
```
<type>/<ticket-id>-<short-description>

Examples:
feature/FF-123-rsb-merge-interface
bugfix/FF-456-fix-graph-rendering
hotfix/FF-789-security-patch
refactor/FF-101-cleanup-database-layer
```

**Types:**
- `feature/` - New features
- `bugfix/` - Bug fixes
- `hotfix/` - Urgent production fixes
- `refactor/` - Code refactoring
- `docs/` - Documentation changes
- `test/` - Test additions/changes
- `chore/` - Build/tooling changes

### 13.2 Commit Messages

**Format (Conventional Commits):**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Example:**
```
feat(rsb): add visual merge preview interface

Implement three-panel merge workspace with color-coded nodes
showing existing, new, and modified rules. Includes real-time
preview of merge result with statistics.

- Add MergeWorkspace component
- Implement merge preview logic
- Add color coding for change types
- Add conflict detection

Closes FF-123
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `style` - Formatting (no code change)
- `refactor` - Code refactoring
- `test` - Tests
- `chore` - Build/tooling
- `perf` - Performance improvement

**Rules:**
- Use imperative mood ("add" not "added")
- First line <72 characters
- Separate subject from body with blank line
- Capitalize subject line
- No period at end of subject
- Reference issue/ticket in footer

### 13.3 Pull Request Guidelines

**PR Title:**
```
[FF-123] Add visual merge preview interface
```

**PR Description Template:**
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] New feature
- [ ] Bug fix
- [ ] Breaking change
- [ ] Documentation update

## Related Issues
Closes #123

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Screenshots (if applicable)
[Add screenshots]

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests pass locally
```

---

## 14. Code Review Guidelines

### 14.1 Review Checklist

**Functionality:**
- [ ] Code does what it's supposed to do
- [ ] Edge cases are handled
- [ ] Error handling is appropriate
- [ ] No obvious bugs

**Code Quality:**
- [ ] Code is readable and maintainable
- [ ] Naming is clear and consistent
- [ ] No code duplication (DRY)
- [ ] Functions are focused (SRP)
- [ ] Complexity is reasonable

**TypeScript:**
- [ ] Strong typing (no `any`)
- [ ] Proper null handling
- [ ] Type guards where needed
- [ ] Interfaces/types are well-defined

**React:**
- [ ] Components are properly structured
- [ ] Hooks follow rules
- [ ] Proper memoization
- [ ] No prop drilling (use context/store)

**Testing:**
- [ ] Tests are included
- [ ] Tests are meaningful
- [ ] Coverage is adequate
- [ ] Tests pass

**Security:**
- [ ] No hardcoded secrets
- [ ] Input validation present
- [ ] No SQL injection risks
- [ ] No XSS vulnerabilities

**Performance:**
- [ ] No obvious performance issues
- [ ] Proper use of memoization
- [ ] No memory leaks
- [ ] Database queries optimized

### 14.2 Review Comments

**✅ GOOD comments:**
```
"Consider using useMemo here to avoid recomputing on every render"

"This could cause a memory leak. Add cleanup in useEffect return"

"Great use of type guards! This makes the code much safer"

"Could you add a JSDoc comment explaining the algorithm?"
```

**❌ BAD comments:**
```
"This is wrong" (Not constructive)

"Why did you do it this way?" (Could be perceived as confrontational)

"I would have done it differently" (Not helpful without specifics)
```

---

## 15. Accessibility Standards

### 15.1 WCAG 2.1 Compliance

**Target: AA Level**

**✅ DO:**

```tsx
// Semantic HTML
<button onClick={handleClick}>Deploy</button> // ✅ GOOD
<div onClick={handleClick}>Deploy</div>       // ❌ BAD

// ARIA labels
<button aria-label="Deploy RSB to production">
  <DeployIcon />
</button>

// Keyboard navigation
<div 
  role="button"
  tabIndex={0}
  onClick={handleClick}
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      handleClick();
    }
  }}
>
  Action
</div>

// Alt text for images
<img src={logo} alt="Fraud Forge logo" />

// Form labels
<label htmlFor="rule-id">Rule ID</label>
<input id="rule-id" type="text" />

// Color contrast (minimum 4.5:1 for text)
const theme = createTheme({
  palette: {
    text: {
      primary: '#000000',  // On white: 21:1 ✅
      secondary: '#666666', // On white: 5.7:1 ✅
    },
  },
});

// Focus indicators
button:focus {
  outline: 2px solid #1976D2;
  outline-offset: 2px;
}
```

### 15.2 Screen Reader Support

```tsx
// Announce dynamic content changes
import { announce } from '@react-aria/live-announcer';

const handleDeploy = async () => {
  announce('Deployment started', 'polite');
  await deploy();
  announce('Deployment completed successfully', 'assertive');
};

// Skip links
<a href="#main-content" className="skip-link">
  Skip to main content
</a>
```

---

## 16. Tooling & Automation

### 16.1 Pre-commit Hooks

**Husky + lint-staged:**

```json
// package.json
{
  "husky": {
    "hooks": {
      "pre-commit": "lint-staged",
      "commit-msg": "commitlint -E HUSKY_GIT_PARAMS"
    }
  },
  "lint-staged": {
    "*.{ts,tsx}": [
      "eslint --fix",
      "prettier --write",
      "vitest related --run"
    ],
    "*.{json,md}": [
      "prettier --write"
    ]
  }
}
```

### 16.2 CI/CD Pipeline

**GitHub Actions (.github/workflows/ci.yml):**

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - run: npm ci
      
      - run: npm run lint
      
      - run: npm run test:coverage
      
      - run: npm run build
      
      - uses: codecov/codecov-action@v3
        with:
          files: ./coverage/coverage-final.json
```

### 16.3 VS Code Settings

**.vscode/settings.json:**

```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true,
    "source.organizeImports": true
  },
  "typescript.tsdk": "node_modules/typescript/lib",
  "typescript.enablePromptUseWorkspaceTsdk": true,
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

**.vscode/extensions.json:**

```json
{
  "recommendations": [
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "bradlc.vscode-tailwindcss",
    "styled-components.vscode-styled-components",
    "vitest.explorer"
  ]
}
```

---

## 17. Enforcement & Continuous Improvement

### 17.1 Automated Enforcement

**Tools that enforce standards automatically:**

✅ **TypeScript Compiler** - Type safety
✅ **ESLint** - Code quality
✅ **Prettier** - Code formatting
✅ **Husky** - Pre-commit hooks
✅ **GitHub Actions** - CI/CD checks

### 17.2 Manual Enforcement

**Code Reviews:**
- All code must be reviewed before merging
- Use review checklist
- Provide constructive feedback

**Pair Programming:**
- Complex features: pair programming recommended
- Knowledge sharing
- Real-time code quality

### 17.3 Learning & Improvement

**Weekly Tech Talks:**
- Share new patterns/techniques
- Discuss code quality issues
- Review challenging PRs together

**Quarterly Standards Review:**
- Update standards based on learnings
- Adopt new best practices
- Deprecate outdated patterns

**Documentation:**
- Keep this document updated
- Add examples of good/bad code
- Document architectural decisions (ADRs)

---

## 18. Exceptions & Waivers

### 18.1 When to Break the Rules

**Valid Reasons:**
- Performance-critical code (with comments explaining why)
- Third-party API constraints
- Backward compatibility requirements
- Technical debt (with plan to address)

**Process:**
```typescript
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const legacyData: any = oldAPI.getData();
// TODO: Type this properly when API v2 is available (FF-999)
```

**Document in Code:**
- Explain WHY rule is broken
- Link to ticket for fixing
- Add TODO/FIXME with ownership

---

## 19. Resources

### 19.1 Official Style Guides

- [React TypeScript Cheatsheet](https://react-typescript-cheatsheet.netlify.app/)

### 19.2 Tools Documentation

- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [React Documentation](https://react.dev)
- [Electron Documentation](https://www.electronjs.org/docs/latest)
- [Vitest Documentation](https://vitest.dev/)

### 19.3 Internal Resources

- Architecture Decision Records (ADRs): `/docs/architecture`
- Component Library: `/docs/components`
- API Documentation: `/docs/api`

---

## 20. Summary

### 20.1 Key Takeaways

✅ **Quality First** - Code quality is not negotiable
✅ **Type Safety** - Use TypeScript strictly
✅ **Testing** - 80%+ coverage for critical paths
✅ **Security** - Never compromise on security
✅ **Performance** - Optimize where it matters
✅ **Accessibility** - Build for everyone
✅ **Consistency** - Follow conventions religiously

### 20.2 Quick Checklist

Before submitting code:
- [ ] TypeScript strict mode passes
- [ ] ESLint shows no errors
- [ ] Prettier formatting applied
- [ ] Tests written and passing
- [ ] Code reviewed by peer
- [ ] Documentation updated
- [ ] No console.logs/debugger
- [ ] Commit message follows convention
- [ ] PR description complete

---

**Document Version:** 1.0  
**Last Updated:** 2026-01-11  
**Maintained By:** Fraud Forge Engineering Team  
**Review Cycle:** Quarterly

---

## Appendix A: Code Examples

### A.1 Complete Component Example

```typescript
/**
 * @fileoverview RSB Card component for displaying RSB information
 */

import React, { useState, useCallback, memo } from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Chip,
  Box,
} from '@mui/material';
import { format } from 'date-fns';
import type { RSB } from '@/types/rsb';

/**
 * Props for RSBCard component
 */
interface RSBCardProps {
  /** RSB data to display */
  rsb: RSB;
  /** Callback when deploy button is clicked */
  onDeploy?: (rsb: RSB) => void;
  /** Additional CSS class name */
  className?: string;
}

/**
 * Card component for displaying RSB information with deploy action.
 * 
 * @component
 * @example
 * ```tsx
 * <RSBCard 
 *   rsb={rsbData}
 *   onDeploy={(rsb) => deployRSB(rsb)}
 * />
 * ```
 */
export const RSBCard: React.FC<RSBCardProps> = memo(({
  rsb,
  onDeploy,
  className,
}) => {
  // State
  const [isDeploying, setIsDeploying] = useState(false);

  // Handlers
  const handleDeploy = useCallback(async () => {
    if (!onDeploy) return;

    setIsDeploying(true);
    try {
      await onDeploy(rsb);
    } finally {
      setIsDeploying(false);
    }
  }, [rsb, onDeploy]);

  // Derived values
  const formattedDate = format(
    new Date(rsb.manifest.created_at),
    'PPp'
  );

  const confidencePercent = Math.round(rsb.rule.confidence * 100);

  // Early return for invalid state
  if (!rsb?.manifest) {
    return null;
  }

  // Render
  return (
    <Card className={className}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6" component="h2">
            {rsb.manifest.name}
          </Typography>
          <Chip 
            label={`v${rsb.manifest.rule_version}`}
            size="small"
            color="primary"
          />
        </Box>

        <Typography color="text.secondary" gutterBottom>
          Rule ID: {rsb.manifest.rule_id}
        </Typography>

        <Typography variant="body2">
          Attack Type: {rsb.manifest.attack_type}
        </Typography>

        <Typography variant="body2">
          Confidence: {confidencePercent}%
        </Typography>

        <Typography variant="caption" display="block">
          Created: {formattedDate}
        </Typography>
      </CardContent>

      {onDeploy && (
        <CardActions>
          <Button
            size="small"
            variant="contained"
            onClick={handleDeploy}
            disabled={isDeploying}
          >
            {isDeploying ? 'Deploying...' : 'Deploy'}
          </Button>
        </CardActions>
      )}
    </Card>
  );
});

// Display name for debugging
RSBCard.displayName = 'RSBCard';
```

---

**This coding standards document represents world-class engineering practices. Following these standards will ensure the Fraud Forge  Application is maintainable, scalable, secure, and a joy to work with.** 🚀
