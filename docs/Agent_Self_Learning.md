# Agent Self-Learning & Evolution Architecture

## Overview
As of the latest update, **all** AI Agents, Sub-Agents, and relevant XAI components in Fraud Forge have been upgraded with **Self-Learning Capabilities**. This allows agents to learn from their past executions, retain successful strategies, and evolve their behaviors over time without code changes.

## Core Components

### 1. Learning Engine (`backend/app/core/agent_learning.py`)
This centralized engine manages the lifecycle of agent memories.
- **Record Lesson**: Stores task outcomes, summaries, and embedding vectors in the `agent_memories` collection.
- **Recall Lessons**: Retrieves semantic matches for a current task from the agent's (or team's) collective history.
- **Distillation**: (Planned) Aggregates individual lessons into broader "Rules of Thumb".

### 2. Base Agent Integration (`backend/app/agents.py`)
The `BaseAgent.run_task` method—the runtime kernel for all 56 sub-agents—now includes a learning loop:
1.  **Pre-computation**: Before planning, the agent asks the Learning Engine: *"Have I (or my team) done something like `task_type: {objective}` before?"*
2.  **Context Injection**: Relevant past lessons (strategies that worked, pitfalls to avoid) are injected into the LLM's system prompt.
3.  **Execution & Reflection**: The agent performs the task.
4.  **Memory Encoding**: If successful, the agent records a new lesson: *"In context X, strategy Y resulted in outcome Z."*

### 3. XAI Commentor Integration (`backend/app/routes/xai.py`)
The "Commentor" agent (which generates narrative overlays) also participates in learning:
- It recalls past high-quality commentaries for similar screens/contexts.
- It records its own generations to build a style guide of "what looks good".

## How It Works in Practice

### Scenario: Red Team Attack Evolution
1.  **Attempt 1**: `red.agent.03` tries a simple SQL injection. result: **BLOCKED**.
2.  **Learning**: Agent records: *"Simple SQLi on login blocked by WAF."*
3.  **Attempt 2**: `red.agent.03` is tasked with a similar objective.
4.  **Recall**: It recalls the failure of Attempt 1.
5.  **Evolution**: The LLM prompt now contains *"Avoid simple SQLi; it was blocked previously."* The agent adapts and tries **Obfuscated SQLi**.
6.  **Success**: Attack succeeds. Agent records: *"Obfuscation worked against WAF."*

### Scenario: Blue Team Defense Tuning
1.  **Miss**: `blue.agent.02` misses the obfuscated attack.
2.  **Feedback**: The system (or Purple Team validation) flags the miss.
3.  **Learning**: Agent records a lesson (or Anti-Pattern): *"Standard regex missed obfuscated payload."*
4.  **Next Run**: Agent recalls this miss and adjusts its rule generation strategy to include normalization before regex.

## Data Structure (`agent_memories` Collection)
```json
{
  "agent_id": "red.agent.03",
  "team_id": "red",
  "task_type": "exploit_execution",
  "content": "Using hex encoding bypassed the initial filter.",
  "embedding": [0.12, -0.05, ...],
  "outcome": "success",
  "confidence": 0.95,
  "created_at": "2025-..."
}
```

## Future Roadmap (Self-Evolving)
- **Active Reflection**: A nightly job to "dream" (process daily memories) and update the agent's core `system_prompt` permanently.
- **Cross-Team Sharing**: Allow Blue team to learn from Red team's *successful* attacks immediately (Adversarial Training).
