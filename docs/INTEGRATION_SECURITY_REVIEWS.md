# Integration & Security Review Schedule

To satisfy the roadmap milestone "Schedule early integration and security reviews for each phase",
this document aligns all agent owners on the review cadence, scope and deliverables.

## 1. Review Cadence Overview

| Phase | Agents Involved | Review Window | Goal |
| --- | --- | --- | --- |
| Foundation (Infrastructure) | Nova, Chronos, Aura | KW 26 | Validate Spark environment readiness, security baselines and observability hooks. |
| Intelligence (Model & Data) | Orion, Lumina | KW 27 | Confirm model deployment prerequisites, data migration safeguards and compliance controls. |
| Interaction (UX & Automation) | Echo, Chronos | KW 28 | Stress-test integration APIs, avatar pipeline readiness and workflow automation alignment. |
| Cut-over & Operations | Nova, Aura, Security Manager | KW 31 | Approve production release, rollback paths and on-call rotations. |

## 2. Responsibilities

- **Review Leads** coordinate agendas, capture minutes and track follow-up actions.
- **Security Manager** performs threat modelling, policy validation and ensures OPA rules are up to date before each review.
- **QA Liaison (Chronos)** bundles automated test evidence, failure logs and KPI snapshots 48 h before a review.
- **Compliance Officer (Aura)** assembles audit artefacts and ensures storage of decisions in the compliance registry.

## 3. Inputs & Artefacts Per Review

| Review | Required Inputs | Artefacts Produced |
| --- | --- | --- |
| Foundation | Spark cluster spec sheet, namespace allocation plan, firewall topology draft. | Signed-off infrastructure checklist, risk register updates. |
| Intelligence | LLM deployment plan, data migration runbook, encryption baselines. | Approved data handling policy, outstanding model validation issues. |
| Interaction | Avatar integration diagram, workflow API tests, user journey storyboard. | Integration sign-off, UI/UX action list, automation backlog entries. |
| Cut-over | Final migration rehearsal report, rollback procedure, support schedule. | Production go/no-go decision, final compliance attestation incl. LUX compliance slice export. |

## 4. Communication & Tracking

- Meeting invites distributed via shared calendar with agenda at least 72 h in advance.
- Decisions and open issues tracked in the orchestration journal with cross-links to `docs/SPARK_MIGRATION_PLAN.md` tasks.
- Escalations route to the Nova steering committee when blockers exceed 3 business days without mitigation.
- Dashboard references: Grafana KPI export under `docs/dashboards/spark_migration_grafana.json`, LUX compliance evidence slice under `docs/dashboards/lux_compliance_slice.json` (mirrors audit trail coverage & policy drift per review window).

## 5. Next Actions

1. ✅ Confirmed review slots with all participants (calendar invitations sent 2024-06-11).
2. ✅ Security Manager mapped checklist templates to OPA policy audit trail (stored in `nova/security`).
3. 🔄 Chronos to automate evidence export from the test harness before KW 26 review.
4. ✅ Aura prepared compliance reporting dashboard slice (LUX) ahead of KW 27 session – see `docs/dashboards/lux_compliance_slice.json` and `nova/__main__.py::run_monitor` export hook.
