# Fraud Forge — Portable Evolved Agents Implementation Plan (Bank A ➜ Bank B)
**Goal:** Implement a reliable portability mechanism to export evolved agents from Bank A and import into Bank B using AMC/RSB/BRC plus a Portable Evolution Pack (PEP) with manifest, contracts, validation, and controlled activation.  
**Generated:** 2026-02-01 23:32:58

---

## Phase 1 — Freeze Data Contracts & Formats
1. Create/confirm JSON schemas:
   - `schemas/amc_schema.json`
   - `schemas/rsb_schema.json`
   - `schemas/brc_schema.json`
2. Enforce required metadata headers in every capsule (schema_version, created_at, team_id, agent_ids, hashes, dependencies).
3. Define prohibited-content policy (regex + heuristics).

**Exit criteria:** `ff validate-capsule` validates sample AMC/RSB/BRC successfully and fails on corrupt/missing fields.

---

## Phase 2 — Transfer Manifest
1. Define `transfer_manifest_schema.json`.
2. Implement `manifest_service`:
   - read runtime versions/build hash
   - compute file hashes for included capsules
   - capture prompt/tool registry hashes
   - include model refs/pins + embedding config
3. Implement `validate_manifest()` to block incompatible imports.

**Exit criteria:** Bank B rejects packs with mismatched versions before import.

---

## Phase 3 — Tool & Prompt Contract Pack
1. Implement `tool_registry.yaml` and loader.
2. Implement `prompt_manifest.yaml` (IDs + hashes) and loader.
3. Implement contract compatibility validator:
   - missing tools
   - mismatched arg schema
   - prompt hash mismatch

**Exit criteria:** Import fails fast if agent memory expects Tool X but runtime has Tool X_v2.

---

## Phase 4 — AMC Distillation Pipeline (portable team memory)
1. Build `distillation_service`:
   - extract AMC to temp
   - distill memory/logs into bank-neutral lessons and patterns
   - remove/generalize residual identifiers
   - produce `distillation_map.json` (input hash → output hash)
2. Run prohibited-content scan post-distillation.
3. Generate optional sanitization report (future enterprise).

**Exit criteria:** Distilled AMC passes policy scan and remains useful (pattern IDs, tactics, telemetry categories preserved).

---

## Phase 5 — PEP Packaging Engine
1. Implement `packaging_service`:
   - selection inputs: teams, rsb items, brc runs, include model bundle, include eval suite
   - build folder structure:
     - /capsules, /contracts, /governance, /validation
   - generate `TRANSFER_MANIFEST.json`
2. Compute hashes (`PACK_HASHES.json` optional).
3. (Future) sign the pack; (hackathon) show pack hash.

**Exit criteria:** `.pep.zip` is created deterministically, validates locally, and contains all required contracts/manifest.

---

## Phase 6 — Import + Preview + Merge (Bank B)
1. Implement `/import/pep/validate`:
   - extract pack
   - validate manifest
   - validate schemas
   - validate tool/prompt contracts
   - run prohibited-content scan
2. Implement `/import/pep/preview`:
   - list teams/agents
   - show diffs and conflicts
3. Implement `/import/pep/commit` + merge strategies:
   - AMC: replace / merge / merge+calibration layer
   - RSB: proposed / sandbox-only / approved
   - BRC: store for evidence + replay

**Exit criteria:** Import finishes without touching production activation; preview is clear and accurate.

---

## Phase 7 — Activation Gates (Sandbox First)
1. Enforce sandbox mode for imported agent versions.
2. Create activation workflow:
   - admin approval required
   - optional synthetic eval required
3. Keep rollback mechanism for imported changes.

**Exit criteria:** No imported pack can auto-enable production defenses without explicit approval.

---

## Phase 8 — Synthetic Eval Harness (prove “evolved”)
1. Define synthetic cases dataset (bank-neutral) in `cases.jsonl`.
2. Define expected metrics in `expected_metrics.yaml`.
3. Implement runner + report generator:
   - `eval_report.json`
   - `eval_report.md`

**Exit criteria:** Bank B can run eval in one click and produce a judge-friendly report.

---

## Phase 9 — UI Delivery
### 9.1 Admin UI — Portable Evolution Pack Page
- select scope
- include model bundle toggle (packs into AMC or /model_bundle)
- include eval suite toggle
- generate/download pack
- show versions and hash

### 9.2 Brain Surgery UI — Import Page
- upload pack
- validate → preview → commit
- sandbox activate
- run eval + show report

**Exit criteria:** End-to-end export/import is demo-ready and understandable to judges.

---

## Phase 10 — Post-Hackathon Hardening (roadmap)
- pack signing + verification
- stronger PII detection (NER)
- model privacy gate (distillation/approval)
- export approvals + RBAC enforcement

---

## Minimal Hackathon Scope (recommended)
- PEP builder + manifest + validator
- tool/prompt contracts
- import validate/preview/commit
- sandbox activation
- synthetic eval report

This combination gives a strong “enterprise portability” demo while keeping scope realistic.
