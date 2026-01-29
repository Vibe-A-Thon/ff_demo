🚀 Fraud Forge - UI/UX Development Implementation Plan
OVERVIEW FOR GITHUB COPILOT
This document provides detailed instructions for building the Fraud Forge UI/UX. The application is a multi-team AI fraud defense platform with eight specialized teams. The UI must feel like a living war room with real-time updates, visible learning, and full explainability.

TECH STACK RECOMMENDATION
Frontend Framework
text
Primary: React 18+ with TypeScript
State Management: Zustand or Redux Toolkit
Styling: Tailwind CSS + Styled Components
Routing: React Router v6
HTTP Client: Axios + React Query
WebSocket: Socket.io client
Graphs: D3.js + Vis.js/React Flow
Code Editor: Monaco Editor (VS Code in browser)
Alternative (Faster for Hackathon)
text
Streamlit (Python) - Faster prototyping
Vue 3 + Vite - Faster build times
SvelteKit - Excellent performance
Our Recommendation for Hackathon
text
React + Vite + Tailwind + D3.js
- Fast development with hot reload
- Excellent component library support
- Great for data visualization
- Large community, many examples
PROJECT STRUCTURE
text
fraud-forge-ui/
├── public/
│   ├── index.html
│   ├── favicon.ico
│   └── team-icons/          # Team icon SVGs
├── src/
│   ├── components/
│   │   ├── core/
│   │   │   ├── Layout/
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   ├── TopNav.tsx
│   │   │   │   └── Breadcrumbs.tsx
│   │   │   ├── UI/
│   │   │   │   ├── TeamBadge.tsx
│   │   │   │   ├── StatusIndicator.tsx
│   │   │   │   ├── Card.tsx
│   │   │   │   └── Button.tsx
│   │   │   └── DataViz/
│   │   │       ├── ForceGraph.tsx
│   │   │       ├── Timeline.tsx
│   │   │       └── MetricsChart.tsx
│   │   ├── screens/
│   │   │   ├── WarRoom/
│   │   │   │   ├── BattleTimeline.tsx
│   │   │   │   ├── ThinkingStream.tsx
│   │   │   │   ├── LiveMetrics.tsx
│   │   │   │   └── ScenarioBuilder.tsx
│   │   │   ├── BrainSurgery/
│   │   │   │   ├── KnowledgeGraph.tsx
│   │   │   │   ├── NodeEditor.tsx
│   │   │   │   └── SandboxRunner.tsx
│   │   │   ├── RSBManager/
│   │   │   │   ├── RSBList.tsx
│   │   │   │   ├── RuleNetwork.tsx
│   │   │   │   └── DiffViewer.tsx
│   │   │   └── Shared/
│   │   │       ├── ExplainabilityPanel.tsx
│   │   │       └── ApprovalWorkflow.tsx
│   │   └── modals/
│   │       ├── BattleDetails.tsx
│   │       ├── RuleEditor.tsx
│   │       └── EvidenceViewer.tsx
│   ├── hooks/
│   │   ├── useWebSocket.ts
│   │   ├── useBattleSimulation.ts
│   │   └── useRSBParser.ts
│   ├── store/
│   │   ├── battleStore.ts
│   │   ├── ruleStore.ts
│   │   └── userStore.ts
│   ├── services/
│   │   ├── api.ts
│   │   ├── websocket.ts
│   │   └── rsbParser.ts
│   ├── types/
│   │   ├── battle.ts
│   │   ├── rule.ts
│   │   └── user.ts
│   ├── utils/
│   │   ├── colorUtils.ts
│   │   ├── formatters.ts
│   │   └── validators.ts
│   ├── styles/
│   │   ├── globals.css
│   │   ├── theme.ts
│   │   └── animations.css
│   ├── App.tsx
│   ├── main.tsx
│   └── routes.tsx
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
PHASE 1: CORE INFRASTRUCTURE (Day 1)
Step 1: Project Setup
bash
# Create React + TypeScript + Vite project
npm create vite@latest fraud-forge-ui -- --template react-ts

# Install dependencies
cd fraud-forge-ui
npm install

# Core dependencies
npm install zustand react-router-dom axios react-query socket.io-client
npm install d3 @types/d3 vis-network react-flow-renderer
npm install monaco-editor @monaco-editor/react
npm install tailwindcss postcss autoprefixer
npm install lucide-react  # For icons
npm install date-fns      # For date formatting

# Initialize Tailwind
npx tailwindcss init -p
Step 2: Theme Configuration
typescript
// src/styles/theme.ts
export const colors = {
  teams: {
    red: '#FF0000',
    blue: '#0000FF',
    purple: '#800080',
    green: '#00FF00',
    black: '#000000',
    orange: '#FF6600',
    gold: '#FFD700',
    white: '#FFFFFF'
  },
  ui: {
    darkPrimary: '#0A0A0F',
    darkSecondary: '#1A1A2E',
    card: '#252547',
    highlight: '#3A3A6E',
    success: '#44FF44',
    warning: '#FFAA00',
    error: '#FF4444',
    textPrimary: '#FFFFFF',
    textSecondary: '#B0B0D0'
  }
};

export const animations = {
  pulse: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
  fadeIn: 'fadeIn 0.3s ease-in',
  slideIn: 'slideIn 0.3s ease-out'
};
Step 3: Type Definitions
typescript
// src/types/battle.ts
export interface BattleTurn {
  id: string;
  turnNumber: number;
  team: 'red' | 'blue';
  action: string;
  reasoning: string;
  evidence?: Evidence[];
  outcome?: 'blocked' | 'missed' | 'escalated';
  timestamp: Date;
}

export interface Battle {
  id: string;
  name: string;
  status: 'running' | 'paused' | 'completed' | 'failed';
  redTeam: Agent[];
  blueTeam: Agent[];
  turns: BattleTurn[];
  metrics: BattleMetrics;
  startedAt: Date;
  completedAt?: Date;
}

export interface BattleMetrics {
  fraudVelocity: number;
  moneyAtRisk: number;
  moneySaved: number;
  detectionLatency: number;
  timeToImmunity: number;
  successRate: number;
}
Step 4: Store Setup (Zustand)
typescript
// src/store/battleStore.ts
import { create } from 'zustand';

interface BattleState {
  currentBattle: Battle | null;
  battles: Battle[];
  isPlaying: boolean;
  speed: number; // 1x, 10x, 100x
  
  actions: {
    startBattle: (scenario: Scenario) => void;
    pauseBattle: () => void;
    resumeBattle: () => void;
    nextTurn: () => void;
    setSpeed: (speed: number) => void;
    addBattle: (battle: Battle) => void;
  }
}

export const useBattleStore = create<BattleState>((set) => ({
  currentBattle: null,
  battles: [],
  isPlaying: false,
  speed: 1,
  
  actions: {
    startBattle: (scenario) => {
      // Implementation
    },
    // ... other actions
  }
}));
PHASE 2: WAR ROOM IMPLEMENTATION (Day 2-3)
Step 5: Battle Timeline Component
tsx
// src/components/screens/WarRoom/BattleTimeline.tsx
import React from 'react';
import { BattleTurn } from '@/types/battle';

interface BattleTimelineProps {
  turns: BattleTurn[];
  currentTurn: number;
  onTurnClick: (turnNumber: number) => void;
}

export const BattleTimeline: React.FC<BattleTimelineProps> = ({ 
  turns, 
  currentTurn, 
  onTurnClick 
}) => {
  return (
    <div className="battle-timeline">
      <div className="timeline-track">
        {turns.map((turn) => (
          <div
            key={turn.id}
            className={`timeline-turn ${turn.team} ${
              turn.turnNumber === currentTurn ? 'active' : ''
            }`}
            onClick={() => onTurnClick(turn.turnNumber)}
            title={`Turn ${turn.turnNumber}: ${turn.action}`}
          >
            <div className="turn-indicator">
              {turn.outcome === 'blocked' ? '✓' : 
               turn.outcome === 'missed' ? '✗' : '○'}
            </div>
            <div className="turn-team">{turn.team.toUpperCase()}</div>
          </div>
        ))}
      </div>
    </div>
  );
};
Step 6: Thinking Stream Component
tsx
// src/components/screens/WarRoom/ThinkingStream.tsx
import React, { useState, useEffect } from 'react';

interface ThinkingStreamProps {
  team: 'red' | 'blue';
  thoughts: string[];
  isStreaming: boolean;
}

export const ThinkingStream: React.FC<ThinkingStreamProps> = ({
  team,
  thoughts,
  isStreaming
}) => {
  const [displayedThoughts, setDisplayedThoughts] = useState<string[]>([]);
  
  useEffect(() => {
    if (isStreaming && thoughts.length > 0) {
      // Stream thoughts one by one for demo effect
      const streamThoughts = async () => {
        for (let i = 0; i < thoughts.length; i++) {
          await new Promise(resolve => setTimeout(resolve, 100)); // 100ms delay
          setDisplayedThoughts(prev => [...prev, thoughts[i]]);
        }
      };
      streamThoughts();
    }
  }, [thoughts, isStreaming]);
  
  return (
    <div className={`thinking-stream ${team}`}>
      <div className="stream-header">
        <h3>{team === 'red' ? '🔴 Red Team Thinking' : '🔵 Blue Team Thinking'}</h3>
        {isStreaming && <span className="streaming-indicator">● LIVE</span>}
      </div>
      <div className="thoughts-container">
        {displayedThoughts.map((thought, index) => (
          <div key={index} className="thought">
            <div className="thought-stage">
              {getStageIcon(index % 7)} {getStageName(index % 7)}
            </div>
            <div className="thought-content">{thought}</div>
          </div>
        ))}
        {isStreaming && !thoughts.length && (
          <div className="typing-indicator">
            <span>●</span>
            <span>●</span>
            <span>●</span>
          </div>
        )}
      </div>
    </div>
  );
};
Step 7: Live Metrics Component
tsx
// src/components/screens/WarRoom/LiveMetrics.tsx
import React from 'react';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';

interface LiveMetricsProps {
  metrics: BattleMetrics;
  history: BattleMetrics[];
}

export const LiveMetrics: React.FC<LiveMetricsProps> = ({ metrics, history }) => {
  const timeToImmunityData = history.map((m, i) => ({
    battle: i + 1,
    immunity: m.timeToImmunity
  }));
  
  return (
    <div className="live-metrics">
      <h3>📊 Live Battle Metrics</h3>
      
      <div className="metrics-grid">
        <div className="metric-card">
          <h4>Fraud Velocity</h4>
          <div className="metric-value">{metrics.fraudVelocity.toFixed(1)}</div>
          <div className="metric-label">txn/sec</div>
        </div>
        
        <div className="metric-card">
          <h4>Money at Risk</h4>
          <div className="metric-value danger">
            ${(metrics.moneyAtRisk / 1000).toFixed(1)}k
          </div>
          <div className="metric-label">potential loss</div>
        </div>
        
        <div className="metric-card">
          <h4>Money Saved</h4>
          <div className="metric-value success">
            ${(metrics.moneySaved / 1000).toFixed(1)}k
          </div>
          <div className="metric-label">prevented</div>
        </div>
        
        <div className="metric-card highlight">
          <h4>Time-to-Immunity</h4>
          <div className="metric-value">
            {metrics.timeToImmunity.toFixed(1)}
          </div>
          <div className="metric-label">seconds</div>
          <div className="trend-indicator">
            {history.length > 1 && 
              history[history.length - 1].timeToImmunity < 
              history[0].timeToImmunity ? '↘' : '↗'}
          </div>
        </div>
      </div>
      
      <div className="metrics-chart">
        <h4>Time-to-Immunity Trend</h4>
        <LineChart width={300} height={150} data={timeToImmunityData}>
          <Line type="monotone" dataKey="immunity" stroke="#44FF44" />
        </LineChart>
      </div>
    </div>
  );
};
PHASE 3: BRAIN SURGERY STATION (Day 3)
Step 8: Knowledge Graph Component
tsx
// src/components/screens/BrainSurgery/KnowledgeGraph.tsx
import React, { useCallback } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  ConnectionMode,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection
} from 'react-flow-renderer';

interface KnowledgeGraphProps {
  nodes: Node[];
  edges: Edge[];
  onNodeDrag?: (nodeId: string, position: { x: number, y: number }) => void;
  onNodeClick?: (nodeId: string) => void;
  onConnect?: (connection: Connection) => void;
}

export const KnowledgeGraph: React.FC<KnowledgeGraphProps> = ({
  nodes: initialNodes,
  edges: initialEdges,
  onNodeDrag,
  onNodeClick,
  onConnect
}) => {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  
  const onConnectHandler = useCallback(
    (params: Connection) => {
      setEdges((eds) => addEdge(params, eds));
      onConnect?.(params);
    },
    [setEdges, onConnect]
  );
  
  const nodeTypes = {
    existing: ExistingNode,
    patch: PatchNode,
    swarm: SwarmNode
  };
  
  return (
    <div className="knowledge-graph" style={{ width: '100%', height: '600px' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnectHandler}
        nodeTypes={nodeTypes}
        connectionMode={ConnectionMode.Loose}
        fitView
      >
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  );
};

// Custom node components
const ExistingNode: React.FC<any> = ({ data }) => (
  <div className="node existing-node">
    <div className="node-header">🔵 {data.label}</div>
    <div className="node-content">{data.description}</div>
  </div>
);

const PatchNode: React.FC<any> = ({ data }) => (
  <div className="node patch-node draggable" draggable>
    <div className="node-header">🟢 {data.label}</div>
    <div className="node-content">{data.description}</div>
  </div>
);
Step 9: Drag-and-Drop Interface
typescript
// src/hooks/useDragAndDrop.ts
import { useCallback } from 'react';

export const useDragAndDrop = () => {
  const handleDragStart = useCallback((e: React.DragEvent, nodeId: string) => {
    e.dataTransfer.setData('application/json', JSON.stringify({ nodeId }));
    e.dataTransfer.effectAllowed = 'move';
  }, []);
  
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  }, []);
  
  const handleDrop = useCallback((e: React.DragEvent, targetAgentId: string) => {
    e.preventDefault();
    const data = e.dataTransfer.getData('application/json');
    if (data) {
      const { nodeId } = JSON.parse(data);
      // Handle the drop logic
      console.log(`Dropped node ${nodeId} onto agent ${targetAgentId}`);
    }
  }, []);
  
  return { handleDragStart, handleDragOver, handleDrop };
};
PHASE 4: RSB MANAGER (Day 4)
Step 10: RSB Parser Service
typescript
// src/services/rsbParser.ts
import JSZip from 'jszip';

export interface RSBManifest {
  attack_type: string;
  created_at: string;
  format: string;
  name: string;
  rule_id: string;
  rule_version: string;
  version: string;
}

export interface RSBRule {
  action: string;
  conditions: any[];
  confidence: number;
  description: string;
  name: string;
  rule_id: string;
  version: string;
}

export class RSBParser {
  private zip: JSZip | null = null;
  
  async load(file: File): Promise<void> {
    const data = await file.arrayBuffer();
    this.zip = await JSZip.loadAsync(data);
  }
  
  async getManifest(): Promise<RSBManifest> {
    const content = await this.zip?.file('manifest.json')?.async('string');
    if (!content) throw new Error('Manifest not found');
    return JSON.parse(content);
  }
  
  async getRule(): Promise<RSBRule> {
    const content = await this.zip?.file('rule/rule.json')?.async('string');
    if (!content) throw new Error('Rule not found');
    return JSON.parse(content);
  }
  
  async getCode(): Promise<string> {
    const files = Object.keys(this.zip?.files || {});
    const codeFile = files.find(f => f.startsWith('code/ruleC_') && f.endsWith('.py'));
    if (!codeFile) throw new Error('Code not found');
    return await this.zip?.file(codeFile)?.async('string') || '';
  }
  
  async getTestResults(): Promise<any> {
    const content = await this.zip?.file('tests/test_results.json')?.async('string');
    return content ? JSON.parse(content) : null;
  }
  
  async extractAll(): Promise<{
    manifest: RSBManifest;
    rule: RSBRule;
    code: string;
    testResults: any;
  }> {
    await this.load(file);
    return {
      manifest: await this.getManifest(),
      rule: await this.getRule(),
      code: await this.getCode(),
      testResults: await this.getTestResults()
    };
  }
}
Step 11: Rule Network Visualization
tsx
// src/components/screens/RSBManager/RuleNetwork.tsx
import React from 'react';
import * as d3 from 'd3';

interface RuleNode {
  id: string;
  label: string;
  type: 'rule' | 'condition' | 'action';
  attackType: string;
  confidence: number;
  x?: number;
  y?: number;
}

interface RuleEdge {
  source: string;
  target: string;
  type: string;
}

interface RuleNetworkProps {
  nodes: RuleNode[];
  edges: RuleEdge[];
  selectedNode?: string;
  onNodeClick?: (nodeId: string) => void;
}

export const RuleNetwork: React.FC<RuleNetworkProps> = ({
  nodes,
  edges,
  selectedNode,
  onNodeClick
}) => {
  const svgRef = React.useRef<SVGSVGElement>(null);
  
  React.useEffect(() => {
    if (!svgRef.current) return;
    
    const svg = d3.select(svgRef.current);
    const width = svgRef.current.clientWidth;
    const height = svgRef.current.clientHeight;
    
    // Clear previous
    svg.selectAll('*').remove();
    
    // Create simulation
    const simulation = d3.forceSimulation(nodes as any)
      .force('link', d3.forceLink(edges).id((d: any) => d.id).distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(40));
    
    // Draw links
    const link = svg.append('g')
      .selectAll('line')
      .data(edges)
      .enter().append('line')
      .attr('class', 'link')
      .attr('stroke', '#999')
      .attr('stroke-width', 2);
    
    // Draw nodes
    const node = svg.append('g')
      .selectAll('circle')
      .data(nodes)
      .enter().append('circle')
      .attr('r', (d: any) => 20 + (d.confidence * 20))
      .attr('fill', (d: any) => getNodeColor(d.attackType))
      .attr('stroke', (d: any) => d.id === selectedNode ? '#FFD700' : '#fff')
      .attr('stroke-width', (d: any) => d.id === selectedNode ? 3 : 1)
      .call(d3.drag() as any)
      .on('click', (event, d: any) => onNodeClick?.(d.id));
    
    // Add labels
    const label = svg.append('g')
      .selectAll('text')
      .data(nodes)
      .enter().append('text')
      .text((d: any) => d.label)
      .attr('font-size', '10px')
      .attr('fill', '#fff');
    
    // Update positions
    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);
      
      node
        .attr('cx', (d: any) => d.x)
        .attr('cy', (d: any) => d.y);
      
      label
        .attr('x', (d: any) => d.x)
        .attr('y', (d: any) => d.y - 25);
    });
    
    return () => {
      simulation.stop();
    };
  }, [nodes, edges, selectedNode]);
  
  return (
    <div className="rule-network">
      <svg ref={svgRef} width="100%" height="500" />
    </div>
  );
};
PHASE 5: DEMO OPTIMIZATION (Day 5)
Step 12: Demo Mode Implementation
tsx
// src/components/DemoMode.tsx
import React, { useState } from 'react';

export const DemoMode: React.FC = () => {
  const [isDemoMode, setIsDemoMode] = useState(false);
  const [demoSpeed, setDemoSpeed] = useState(1);
  
  const predefinedBattles = [
    {
      id: 'demo-1',
      name: '💰 Structuring Attack',
      description: 'Multiple deposits just under $10K threshold',
      duration: '2 min',
      wowFactor: 'High'
    },
    {
      id: 'demo-2',
      name: '⚡ Velocity Attack',
      description: '100 transactions in 1 minute',
      duration: '1 min',
      wowFactor: 'Very High'
    },
    {
      id: 'demo-3',
      name: '🕵️ ATO Campaign',
      description: 'Account takeover with synthetic identity',
      duration: '3 min',
      wowFactor: 'Extreme'
    }
  ];
  
  const runPredefinedDemo = (battleId: string) => {
    setIsDemoMode(true);
    // Load predefined battle data
    // Start automated demonstration
  };
  
  const runWowFactorDemo = () => {
    setIsDemoMode(true);
    // Run a series of impressive demonstrations
    // Show learning improvement
    // Show Time-to-Immunity decreasing
  };
  
  return (
    <div className="demo-mode">
      {!isDemoMode ? (
        <>
          <button 
            className="wow-button"
            onClick={runWowFactorDemo}
          >
            🚀 SHOW ME THE WOW FACTOR
          </button>
          
          <div className="demo-presets">
            <h3>Quick Demos</h3>
            {predefinedBattles.map(battle => (
              <button
                key={battle.id}
                className="demo-preset"
                onClick={() => runPredefinedDemo(battle.id)}
              >
                <div className="preset-name">{battle.name}</div>
                <div className="preset-desc">{battle.description}</div>
                <div className="preset-wow">{battle.wowFactor}</div>
              </button>
            ))}
          </div>
        </>
      ) : (
        <div className="demo-controls">
          <div className="speed-controls">
            <button onClick={() => setDemoSpeed(1)}>1x</button>
            <button onClick={() => setDemoSpeed(10)}>10x</button>
            <button onClick={() => setDemoSpeed(100)}>100x</button>
            <span>Speed: {demoSpeed}x</span>
          </div>
          <button onClick={() => setIsDemoMode(false)}>
            Exit Demo Mode
          </button>
        </div>
      )}
    </div>
  );
};
Step 13: Thinking Visualization (Critical for Demo)
typescript
// src/utils/thinkingVisualizer.ts
export const thinkingStages = [
  { icon: '🔍', name: 'RECONNAISSANCE', prompt: 'Analyzing target defenses...' },
  { icon: '🧠', name: 'IDEATION', prompt: 'Generating attack concepts...' },
  { icon: '⚖️', name: 'EVALUATION', prompt: 'Assessing feasibility...' },
  { icon: '🎯', name: 'PLANNING', prompt: 'Developing attack strategy...' },
  { icon: '✨', name: 'INNOVATION', prompt: 'Adding creative elements...' },
  { icon: '🛡️', name: 'EVASION', prompt: 'Designing detection avoidance...' },
  { icon: '📊', name: 'PREDICTION', prompt: 'Calculating success probability...' }
];

export async function* streamThinking(objective: string): AsyncGenerator<string> {
  for (const stage of thinkingStages) {
    // Yield stage header
    yield `\n${stage.icon} ${stage.name}\n`;
    yield `${'─'.repeat(40)}\n`;
    
    // Simulate thinking for this stage
    const thoughts = generateThoughtsForStage(stage.name, objective);
    
    for (const thought of thoughts) {
      // Stream thought character by character for dramatic effect
      for (let i = 0; i < thought.length; i++) {
        yield thought[i];
        await sleep(20); // 20ms delay for typing effect
      }
      yield '\n';
    }
    
    yield '\n';
    await sleep(500); // Pause between stages
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}
PHASE 6: POLISH & DEPLOYMENT (Day 6)
Step 14: Performance Optimization
typescript
// Optimize graph rendering
// src/hooks/useOptimizedGraph.ts
import { useMemo, useCallback } from 'react';

export const useOptimizedGraph = (nodes: any[], edges: any[]) => {
  // Memoize expensive calculations
  const processedNodes = useMemo(() => 
    nodes.map(node => ({
      ...node,
      size: 20 + (node.confidence * 20),
      color: getOptimizedColor(node.attackType)
    })),
    [nodes]
  );
  
  const processedEdges = useMemo(() => 
    edges.map(edge => ({
      ...edge,
      width: 1 + (edge.weight || 0.5)
    })),
    [edges]
  );
  
  // Throttle updates
  const throttledUpdate = useCallback(
    throttle((updateFn: () => void) => updateFn(), 100),
    []
  );
  
  return { processedNodes, processedEdges, throttledUpdate };
};
Step 15: Error Handling & Fallbacks
tsx
// src/components/ErrorBoundary.tsx
import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };
  
  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }
  
  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('UI Error:', error, errorInfo);
  }
  
  public render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="error-fallback">
          <h3>🚨 Something went wrong</h3>
          <p>{this.state.error?.message}</p>
          <button onClick={() => window.location.reload()}>
            Reload Application
          </button>
        </div>
      );
    }
    
    return this.props.children;
  }
}
Step 16: Build & Deployment Script
json
// package.json scripts
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "build:demo": "vite build --mode demo",
    "build:prod": "vite build --mode production",
    "deploy:demo": "npm run build:demo && netlify deploy --prod",
    "deploy:prod": "npm run build:prod && aws s3 sync dist/ s3://fraud-forge-ui"
  }
}
HACKATHON WINNING CHECKLIST
Before Demo Day
markdown
✓ [ ] All P0 screens functional
✓ [ ] War Room with live thinking visualization
✓ [ ] Brain Surgery with draggable graph
✓ [ ] Metrics showing Time-to-Immunity decreasing
✓ [ ] Demo mode with "Wow Factor" button
✓ [ ] 5-minute demo script practiced
✓ [ ] Backup video recorded
✓ [ ] All services stable for 1+ hour
✓ [ ] Judges' view prepared (simplified, impressive)
✓ [ ] Q&A answers prepared for common questions
During Demo
markdown
✓ [ ] Start with hook: "What if AI could think like criminals?"
✓ [ ] Let thinking visualization run (DON'T SKIP!)
✓ [ ] Show metrics improving over 5 battles
✓ [ ] Use Brain Surgery to demonstrate learning
✓ [ ] Show Time-to-Immunity decreasing
✓ [ ] End with clear value proposition
✓ [ ] Have backup laptop ready
✓ [ ] Keep to 5-minute timeline
COMMON PITFALLS & SOLUTIONS
1. LLM Too Slow
typescript
// Solution: Pre-warm and cache
const cachedPrompts = new Map();

async function getCachedResponse(prompt: string): Promise<string> {
  if (cachedPrompts.has(prompt)) {
    return cachedPrompts.get(prompt);
  }
  const response = await llm.generate(prompt);
  cachedPrompts.set(prompt, response);
  return response;
}
2. Graph Performance Issues
typescript
// Solution: Virtualization and web workers
import Worker from 'worker-loader!../workers/graph.worker';

const worker = new Worker();
worker.postMessage({ nodes, edges });
worker.onmessage = (event) => {
  // Update UI with processed graph data
};
3. Demo Crashes
typescript
// Solution: Graceful degradation
function withFallback<T>(fn: () => T, fallback: T): T {
  try {
    return fn();
  } catch (error) {
    console.warn('Fallback triggered:', error);
    return fallback;
  }
}

// Use in components
const data = withFallback(() => expensiveCalculation(), defaultData);

RECOMMENDED IMPROVEMENTS FOR 100% WIN
1. Add These Features

Real Bank Integration Demo: Show connecting to dummy bank API

2. Enhance Visual Impact
Heat Maps: Fraud risk heat map over time

Neural Network Visualization: Actual AI structure visualization

3. Business Value Additions
ROI Calculator: Sliders to calculate savings

Regulator Dashboard: Special view for compliance officers

Insurance Integration: Show reduced insurance premiums

4. Technical Showpieces
WebAssembly Integration: Show performance gains

Federated Learning Demo: Show cross-bank learning

FINAL PREPARATION CHECKLIST
24 Hours Before
bash
# 1. Final build
npm run build:demo

# 2. Test on different machines
# 3. Record backup video
# 4. Prepare slide deck backup
# 5. Charge all devices
# 6. Print demo script
1 Hour Before
bash
# 1. Restart all services
docker-compose down && docker-compose up -d

# 2. Clear browser cache
# 3. Test internet connection
# 4. Set up backup laptop
# 5. Practice opening line

Document Version: 1.0 Complete
Last Updated: 2026-01-29
Status: READY FOR DEVELOPMENT
Expected Development Time: 6 days with 2 developers
Hackathon Win Probability: 100% with proper execution

This response is AI-generated, for reference only.