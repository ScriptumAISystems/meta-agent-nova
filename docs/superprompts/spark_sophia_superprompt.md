# Spark Sophia – Codex Superprompt

## 🎯 Goal
Develop the central AGI platform **Spark Sophia** into an autonomous, multimodal, and auditable AI partner featuring memory, reasoning, governance, and avatar capabilities. Prioritize stability, semantic memory, governance engine, and multimodality.

## 📦 Current Status
- ✅ Restructured workflows (CI/CD, QA gates, branching) are in place.
- 🧩 Superpower catalog documents ~40 abilities (≈30 % functional, ≈50 % scaffolding).
- 📘 Requirements spec v1.1 defines autonomous target architecture (Level 4), phases, roles, and AI domains (Observability, Memory, Inference, Governance, Vision Events).

## 🛠️ Tasks for Codex
1. **Governance Engine v2**
   - Implement audit logs, rule types, and approval workflow.
2. **Semantic Memory Layer**
   - Integrate `pgvector` with Redis TTL.
   - Expose `/memory/search` API and accompanying tests.
3. **Proactive Engine**
   - Deliver rule and event trigger system (“if context → action”).
4. **Vision Events Pipeline**
   - Provide a video-processing stub covering ASR → LLM → TTS → avatar handoff.
5. **QA / CI Gates**
   - Achieve pytest coverage ≥ 85 %.
   - Refresh GitHub Actions to include GPU-enabled tests.

## ✅ Definition of Done
- Stable MVP with full memory pipeline (pgvector + Redis).
- Policy/audit system activated and observable.
- CI/CD workflows passing end to end.
- Foundational voice and avatar integrations in place.
