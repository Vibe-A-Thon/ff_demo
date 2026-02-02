# 🛠️ FRAUD FORGE - Development Instructions & Implementation Plan
## GitHub Copilot-Ready Guide for Building the UI/UX
### Version 2.0 | Complete Development Blueprint

---

# 📋 TABLE OF CONTENTS

1. [Project Setup](#1-project-setup)
2. [Technology Stack](#2-technology-stack)
3. [Project Structure](#3-project-structure)
4. [Core Components](#4-core-components)
5. [State Management](#5-state-management)
6. [API Integration](#6-api-integration)
7. [Screen Implementations](#7-screen-implementations)
8. [Styling & Theming](#8-styling--theming)
9. [Type Definitions](#9-type-definitions)
10. [Deployment](#10-deployment)
11. [Implementation Checklist](#11-implementation-checklist)

---

# 1. PROJECT SETUP

## 1.1 Initialize Project

```bash
# Create new React project with Vite and TypeScript
npm create vite@latest fraud-forge -- --template react-ts
cd fraud-forge
npm install
```

## 1.2 Install Dependencies

```bash
# Core UI & Routing
npm install react-router-dom@6 zustand immer
npm install @tanstack/react-query axios

# UI Components
npm install @radix-ui/react-dialog @radix-ui/react-tabs
npm install @radix-ui/react-tooltip @radix-ui/react-progress
npm install lucide-react

# Styling
npm install tailwindcss postcss autoprefixer
npm install class-variance-authority clsx tailwind-merge

# Forms & Validation
npm install react-hook-form @hookform/resolvers zod

# Visualization
npm install recharts react-force-graph-2d

# Code & Diff
npm install react-diff-viewer-continued prism-react-renderer
npm install @monaco-editor/react

# Real-time & Files
npm install socket.io-client react-dropzone jszip

# Utilities
npm install date-fns uuid lodash-es

# Dev Dependencies
npm install -D @types/react @types/react-dom @types/lodash-es
npm install -D vitest @testing-library/react @testing-library/jest-dom
```

## 1.3 Environment Configuration

Create `.env`:
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_OLLAMA_URL=http://localhost:11434
VITE_MODEL_NAME=mistral
VITE_DEMO_MODE=true
```

---

# 2. TECHNOLOGY STACK

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | React 18 + TypeScript | UI Framework |
| Styling | Tailwind CSS + CVA | Styling System |
| State | Zustand + Immer | Global State |
| Data | TanStack Query | Server State |
| Forms | React Hook Form + Zod | Form Handling |
| Charts | Recharts | Data Visualization |
| Graph | react-force-graph-2d | Knowledge Graph |
| Code | Monaco Editor | Code Editing |
| Real-time | Socket.io | WebSocket |

---

# 3. PROJECT STRUCTURE

```
fraud-forge/
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── index.css
│   │
│   ├── components/
│   │   ├── ui/           # Base components
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Badge.tsx
│   │   │   └── index.ts
│   │   ├── layout/       # Layout components
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   └── MainLayout.tsx
│   │   ├── battle/       # Battle components
│   │   ├── thinking/     # AI Thinking viz
│   │   ├── graph/        # Knowledge graph
│   │   ├── rsb/          # RSB Manager
│   │   ├── rules/        # Rule Editor
│   │   ├── approvals/    # Approvals
│   │   ├── metrics/      # Metrics
│   │   └── xai/          # Explainability
│   │
│   ├── pages/            # Page components
│   ├── hooks/            # Custom hooks
│   ├── services/         # API services
│   ├── store/            # Zustand stores
│   ├── types/            # TypeScript types
│   ├── utils/            # Utilities
│   └── config/           # Configuration
```

---

# 4. CORE COMPONENTS

## 4.1 Utility - cn

```typescript
// src/utils/cn.ts
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

## 4.2 Button Component

```typescript
// src/components/ui/Button.tsx
import { forwardRef } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/utils/cn';

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'bg-accent text-white hover:bg-accent/90',
        outline: 'border border-border-primary bg-transparent hover:bg-bg-tertiary',
        ghost: 'hover:bg-bg-tertiary',
        red: 'bg-red-team/20 text-red-500 border border-red-team/50 hover:bg-red-team/30',
        blue: 'bg-blue-team/20 text-blue-400 border border-blue-team/50 hover:bg-blue-team/30',
        green: 'bg-green-500/20 text-green-400 border border-green-500/50 hover:bg-green-500/30',
        purple: 'bg-purple-500/20 text-purple-400 border border-purple-500/50 hover:bg-purple-500/30',
        gold: 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/50 hover:bg-yellow-500/30',
        orange: 'bg-orange-500/20 text-orange-400 border border-orange-500/50 hover:bg-orange-500/30',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 rounded-md px-3',
        lg: 'h-11 rounded-md px-8',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  isLoading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, isLoading, children, ...props }, ref) => (
    <button
      className={cn(buttonVariants({ variant, size, className }))}
      ref={ref}
      disabled={isLoading || props.disabled}
      {...props}
    >
      {isLoading && (
        <svg className="mr-2 h-4 w-4 animate-spin" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      )}
      {children}
    </button>
  )
);
```

## 4.3 Card Component

```typescript
// src/components/ui/Card.tsx
import { forwardRef } from 'react';
import { cn } from '@/utils/cn';

export const Card = forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('rounded-lg border border-border-primary bg-bg-secondary shadow-sm', className)} {...props} />
  )
);

export const CardHeader = forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('flex flex-col space-y-1.5 p-6', className)} {...props} />
  )
);

export const CardTitle = forwardRef<HTMLHeadingElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h3 ref={ref} className={cn('text-xl font-semibold', className)} {...props} />
  )
);

export const CardContent = forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('p-6 pt-0', className)} {...props} />
  )
);
```

## 4.4 Streaming Text Component

```typescript
// src/components/thinking/StreamingText.tsx
import { useEffect, useState, useRef } from 'react';

interface StreamingTextProps {
  text: string;
  speed?: number;
  onComplete?: () => void;
}

export function StreamingText({ text, speed = 20, onComplete }: StreamingTextProps) {
  const [displayedText, setDisplayedText] = useState('');
  const [cursorVisible, setCursorVisible] = useState(true);
  const indexRef = useRef(0);

  useEffect(() => {
    setDisplayedText('');
    indexRef.current = 0;

    const interval = setInterval(() => {
      if (indexRef.current < text.length) {
        setDisplayedText(prev => prev + text[indexRef.current]);
        indexRef.current++;
      } else {
        clearInterval(interval);
        onComplete?.();
      }
    }, speed);

    return () => clearInterval(interval);
  }, [text, speed, onComplete]);

  useEffect(() => {
    const interval = setInterval(() => setCursorVisible(v => !v), 500);
    return () => clearInterval(interval);
  }, []);

  return (
    <span className="whitespace-pre-wrap font-mono">
      {displayedText}
      <span className={cursorVisible ? 'opacity-100' : 'opacity-0'}>▌</span>
    </span>
  );
}
```

## 4.5 Thinking Visualizer

```typescript
// src/components/thinking/ThinkingVisualizer.tsx
import { cn } from '@/utils/cn';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { StreamingText } from './StreamingText';
import type { ThinkingState } from '@/types/battle';

const STAGES = [
  { id: 'reconnaissance', icon: '🔍', label: 'RECONNAISSANCE' },
  { id: 'ideation', icon: '🧠', label: 'IDEATION' },
  { id: 'evaluation', icon: '⚖️', label: 'EVALUATION' },
  { id: 'planning', icon: '🎯', label: 'PLANNING' },
  { id: 'innovation', icon: '✨', label: 'INNOVATION' },
  { id: 'evasion', icon: '🛡️', label: 'EVASION' },
  { id: 'prediction', icon: '📊', label: 'PREDICTION' },
];

interface Props {
  thinking: ThinkingState;
  team: 'red' | 'blue';
  className?: string;
}

export function ThinkingVisualizer({ thinking, team, className }: Props) {
  const stageIndex = STAGES.findIndex(s => s.id === thinking.currentStage);
  const colors = {
    red: { border: 'border-red-500/50', bg: 'bg-red-500/5', text: 'text-red-500', bar: 'bg-red-500' },
    blue: { border: 'border-blue-500/50', bg: 'bg-blue-500/5', text: 'text-blue-400', bar: 'bg-blue-500' },
  }[team];

  return (
    <Card className={cn(colors.border, colors.bg, className)}>
      <CardHeader className="pb-2">
        <CardTitle className={cn('text-sm flex items-center gap-2', colors.text)}>
          {team === 'red' ? '🔴 RED PHANTOM' : '🔵 BLUE SENTINEL'} THINKING...
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className={cn('text-lg font-bold', colors.text)}>
          {STAGES[stageIndex]?.icon} {STAGES[stageIndex]?.label}
        </div>
        <div className="border-t border-border-primary" />
        <div className="text-sm text-text-secondary min-h-[100px] max-h-[200px] overflow-auto">
          <StreamingText text={thinking.content} speed={20} />
        </div>
        <div className="w-full bg-bg-tertiary rounded-full h-1.5">
          <div
            className={cn('h-1.5 rounded-full transition-all duration-500', colors.bar)}
            style={{ width: `${((stageIndex + 1) / STAGES.length) * 100}%` }}
          />
        </div>
      </CardContent>
    </Card>
  );
}
```

---

# 5. STATE MANAGEMENT

## 5.1 Battle Store

```typescript
// src/store/battleStore.ts
import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import type { Battle, BattleTurn, BattleMetrics } from '@/types/battle';

interface BattleState {
  currentBattle: Battle | null;
  isRunning: boolean;
  currentTurn: number;
  metrics: BattleMetrics | null;
  
  setBattle: (battle: Battle | null) => void;
  addTurn: (turn: BattleTurn) => void;
  setRunning: (running: boolean) => void;
  setMetrics: (metrics: BattleMetrics) => void;
  reset: () => void;
}

export const useBattleStore = create<BattleState>()(
  immer((set) => ({
    currentBattle: null,
    isRunning: false,
    currentTurn: 0,
    metrics: null,

    setBattle: (battle) => set((state) => { state.currentBattle = battle; }),
    addTurn: (turn) => set((state) => {
      if (state.currentBattle) {
        state.currentBattle.turns.push(turn);
        state.currentTurn = turn.turnNumber;
      }
    }),
    setRunning: (running) => set((state) => { state.isRunning = running; }),
    setMetrics: (metrics) => set((state) => { state.metrics = metrics; }),
    reset: () => set((state) => {
      state.currentBattle = null;
      state.isRunning = false;
      state.currentTurn = 0;
      state.metrics = null;
    }),
  }))
);
```

## 5.2 Auth Store

```typescript
// src/store/authStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '@/types/auth';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (user: User, token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      login: (user, token) => set({ user, token, isAuthenticated: true }),
      logout: () => set({ user: null, token: null, isAuthenticated: false }),
    }),
    { name: 'fraud-forge-auth' }
  )
);
```

---

# 6. API INTEGRATION

## 6.1 API Client

```typescript
// src/services/api.ts
import axios from 'axios';
import { useAuthStore } from '@/store/authStore';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

## 6.2 Battle Service

```typescript
// src/services/battleService.ts
import { api } from './api';
import type { Battle, BattleTurn, BattleMetrics } from '@/types/battle';

export const battleService = {
  create: (data: { scenarioId?: string }) => 
    api.post<Battle>('/api/battles', data).then(r => r.data),
  
  get: (id: string) => 
    api.get<Battle>(`/api/battles/${id}`).then(r => r.data),
  
  executeTurn: (id: string) => 
    api.post<BattleTurn>(`/api/battles/${id}/turn`).then(r => r.data),
  
  getMetrics: (id: string) => 
    api.get<BattleMetrics>(`/api/battles/${id}/metrics`).then(r => r.data),
};
```

## 6.3 WebSocket Hook

```typescript
// src/hooks/useWebSocket.ts
import { useEffect, useRef, useState, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';
import { useAuthStore } from '@/store/authStore';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

export function useWebSocket(namespace = '/') {
  const socketRef = useRef<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const token = useAuthStore(s => s.token);

  useEffect(() => {
    const socket = io(`${WS_URL}${namespace}`, {
      auth: { token },
      transports: ['websocket'],
    });

    socket.on('connect', () => setIsConnected(true));
    socket.on('disconnect', () => setIsConnected(false));
    socketRef.current = socket;

    return () => { socket.disconnect(); };
  }, [namespace, token]);

  const emit = useCallback((event: string, data?: unknown) => {
    socketRef.current?.emit(event, data);
  }, []);

  return { socket: socketRef.current, isConnected, emit };
}
```

---

# 7. SCREEN IMPLEMENTATIONS

## 7.1 Battle Arena Page

```typescript
// src/pages/BattleArenaPage.tsx
import { useState } from 'react';
import { useBattleStore } from '@/store/battleStore';
import { battleService } from '@/services/battleService';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { ThinkingVisualizer } from '@/components/thinking/ThinkingVisualizer';
import { Play, Pause, RotateCcw, SkipForward } from 'lucide-react';

export function BattleArenaPage() {
  const { currentBattle, isRunning, currentTurn, setRunning, setBattle, addTurn, reset } = useBattleStore();
  const [redThinking, setRedThinking] = useState<ThinkingState | null>(null);
  const [blueThinking, setBlueThinking] = useState<ThinkingState | null>(null);

  const startBattle = async () => {
    const battle = await battleService.create({});
    setBattle(battle);
    setRunning(true);
  };

  const stepForward = async () => {
    if (!currentBattle) return;
    const turn = await battleService.executeTurn(currentBattle.id);
    addTurn(turn);
  };

  return (
    <div className="flex flex-col h-full gap-4 p-4">
      {/* Header with Controls */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Battle Arena</h1>
          <p className="text-text-secondary">Red Team vs Blue Team</p>
        </div>
        <div className="flex gap-2">
          {!isRunning ? (
            <Button variant="green" onClick={startBattle}>
              <Play className="w-4 h-4 mr-2" /> Start
            </Button>
          ) : (
            <Button variant="orange" onClick={() => setRunning(false)}>
              <Pause className="w-4 h-4 mr-2" /> Pause
            </Button>
          )}
          <Button variant="outline" onClick={stepForward} disabled={isRunning}>
            <SkipForward className="w-4 h-4 mr-2" /> Step
          </Button>
          <Button variant="outline" onClick={reset}>
            <RotateCcw className="w-4 h-4 mr-2" /> Reset
          </Button>
        </div>
      </div>

      {/* Main Battle Grid */}
      <div className="grid grid-cols-12 gap-4 flex-1">
        {/* Red Team */}
        <div className="col-span-3 space-y-4">
          <Card className="border-red-500/30">
            <CardHeader>
              <CardTitle className="text-red-500">🔴 Red Team</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-text-secondary">The Challengers</p>
            </CardContent>
          </Card>
          {redThinking && <ThinkingVisualizer thinking={redThinking} team="red" />}
        </div>

        {/* Timeline */}
        <div className="col-span-6">
          <Card className="h-full">
            <CardHeader>
              <CardTitle className="flex justify-between">
                <span>Battle Timeline</span>
                <span className="text-sm font-normal text-text-secondary">
                  Turn {currentTurn} / {currentBattle?.maxTurns || 20}
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent className="h-[calc(100%-80px)] overflow-auto">
              {currentBattle?.turns.map((turn, i) => (
                <div key={i} className="mb-4 p-3 rounded border border-border-primary">
                  <div className="flex justify-between text-sm">
                    <span className="text-red-500">Red: {turn.redAction.attackType}</span>
                    <span className="text-blue-400">Blue: {turn.blueAction.type}</span>
                  </div>
                  <div className="text-xs text-text-secondary mt-1">
                    {turn.outcome.winner === 'red' ? '🔴 Red wins' : '🔵 Blue wins'}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Blue Team */}
        <div className="col-span-3 space-y-4">
          <Card className="border-blue-500/30">
            <CardHeader>
              <CardTitle className="text-blue-400">🔵 Blue Team</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-text-secondary">The Defenders</p>
            </CardContent>
          </Card>
          {blueThinking && <ThinkingVisualizer thinking={blueThinking} team="blue" />}
        </div>
      </div>
    </div>
  );
}
```

---

# 8. STYLING & THEMING

## 8.1 Tailwind Config

```javascript
// tailwind.config.js
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        'red-team': '#FF0000',
        'blue-team': '#0000FF',
        'green-team': '#00FF00',
        'gold-team': '#FFD700',
        'purple-team': '#800080',
        'orange-team': '#FF6600',
        'bg-primary': '#0a0a0f',
        'bg-secondary': '#12121a',
        'bg-tertiary': '#1a1a24',
        'border-primary': '#2a2a3a',
        'text-primary': '#ffffff',
        'text-secondary': '#a0a0b0',
        'accent': '#6366f1',
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'monospace'],
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
};
```

## 8.2 Global CSS

```css
/* src/index.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply bg-bg-primary text-text-primary;
    font-family: 'Inter', sans-serif;
  }
  
  ::-webkit-scrollbar { width: 8px; }
  ::-webkit-scrollbar-track { @apply bg-bg-tertiary; }
  ::-webkit-scrollbar-thumb { @apply bg-border-primary rounded-full; }
}

@layer components {
  .glow-red { box-shadow: 0 0 20px rgba(255, 0, 0, 0.3); }
  .glow-blue { box-shadow: 0 0 20px rgba(0, 0, 255, 0.3); }
  .glow-green { box-shadow: 0 0 20px rgba(0, 255, 0, 0.3); }
}
```

---

# 9. TYPE DEFINITIONS

```typescript
// src/types/battle.ts
export interface Battle {
  id: string;
  status: 'pending' | 'running' | 'paused' | 'completed';
  turns: BattleTurn[];
  maxTurns: number;
  redTeam: TeamState;
  blueTeam: TeamState;
}

export interface BattleTurn {
  turnNumber: number;
  timestamp: string;
  redAction: { type: string; attackType: string; confidence: number };
  blueAction: { type: string; riskScore: number };
  outcome: { winner: 'red' | 'blue'; moneyAtRisk: number };
}

export interface BattleMetrics {
  successRate: number;
  detectionRate: number;
  patternsLearned: number;
  timeToImmunity: number;
  improvement: number;
}

export interface ThinkingState {
  currentStage: 'reconnaissance' | 'ideation' | 'evaluation' | 'planning' | 'innovation' | 'evasion' | 'prediction';
  content: string;
  progress: number;
}

// src/types/rsb.ts
export interface RSB {
  id: string;
  manifest: { name: string; rule_id: string; rule_version: string; attack_type: string };
  code: string;
  status: 'available' | 'staged' | 'deployed';
}

// src/types/agent.ts
export type Team = 'red' | 'blue' | 'purple' | 'green' | 'black' | 'orange' | 'gold' | 'white';

export interface TeamConfig {
  id: Team;
  name: string;
  marketName: string;
  color: string;
  icon: string;
}
```

---

# 10. DEPLOYMENT

## Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  frontend:
    build: .
    ports: ["3000:80"]
    environment:
      - VITE_API_URL=http://api:8000

  api:
    build: ./backend
    ports: ["8000:8000"]
    depends_on: [db, redis, ollama]

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: fraudforge
      POSTGRES_PASSWORD: password
    volumes: [postgres_data:/var/lib/postgresql/data]

  redis:
    image: redis:7-alpine

  ollama:
    image: ollama/ollama
    ports: ["11434:11434"]
    volumes: [ollama_models:/root/.ollama]

  chromadb:
    image: chromadb/chroma
    ports: ["8001:8000"]

volumes:
  postgres_data:
  ollama_models:
```

---

# 11. IMPLEMENTATION CHECKLIST

## Phase 1: Foundation (Days 1-2)
- [ ] Project setup with Vite + React + TypeScript
- [ ] Tailwind CSS with team colors
- [ ] Base UI components (Button, Card, Badge)
- [ ] Layout components (Sidebar, Header, MainLayout)
- [ ] Router configuration
- [ ] Auth store and API client

## Phase 2: Battle System (Days 3-5)
- [ ] Battle Arena page
- [ ] Thinking Visualizer with streaming text
- [ ] Team panels (Red/Blue)
- [ ] Battle timeline component
- [ ] WebSocket integration
- [ ] Battle store and services

## Phase 3: RSB & Rules (Days 6-7)
- [ ] RSB Manager page
- [ ] Code viewer with syntax highlighting
- [ ] RSB upload and validation
- [ ] Rule Editor with form
- [ ] Test runner

## Phase 4: Governance (Days 8-9)
- [ ] Approvals page
- [ ] Workflow states
- [ ] Audit log viewer
- [ ] RBAC integration

## Phase 5: Polish (Day 10)
- [ ] Metrics dashboard
- [ ] XAI Explainability panel
- [ ] Error handling
- [ ] Loading states
- [ ] Demo mode

---

# 🎯 KEY COPILOT PROMPTS

```
"Create a React component for [X] with TypeScript, Tailwind CSS, following the existing patterns"

"Create a custom hook use[X] that [description] with Zustand integration"

"Create TypeScript interfaces for [X] based on: [requirements]"

"Create a service for [X] with methods for CRUD operations"
```

---

**Version:** 2.0 | **Status:** READY FOR IMPLEMENTATION

# 🚀 START CODING NOW!
