# Model-Operations Kick-off

Dieser Leitfaden beschreibt die ersten Umsetzungsschritte nach Abschluss der
Foundation-Phase. Er richtet sich an **Orion** (KI-Software-Spezialist) und
**Chronos** (Workflow & Automatisierungsspezialist) und verweist auf die
bereitgestellten Artefakte im Repository.

## 1. NeMo Finetuning-Playbook aktivieren (Orion)
- Exportiere das Finetuning-Playbook mit `python -m nova models --plan finetune --export orchestration_journal/models/finetune_plan.md`.
- Prüfe die Abschnitte zu Datenaufbereitung, Infrastruktur und Trainingspipeline.
- Ergänze offene Punkte in `orchestration_journal/models/finetune_runbook.md` sobald Implementierungsdetails feststehen.
- Verwende `python scripts/finetune_nemo.py --plan orchestration_journal/models/finetune_runbook.md`, um die aktuelle Konfiguration
  (`config/finetune/lora.yaml`) zu validieren und den Runbook-Plan automatisch zu befüllen.

## 2. n8n Plattform provisionieren (Chronos)
- Verwende `deploy/automation/n8n/docker-compose.yml`, um lokal eine n8n Instanz mit PostgreSQL und Redis zu starten.
- Die Compose-Datei aktiviert Basic Auth und legt persistente Volumes für n8n, Postgres und Redis an.
- Optionale Initialisierungsskripte können in `deploy/automation/n8n/init/` hinterlegt werden.

## 3. Beispiel-Workflow importieren
- Importiere `orchestration_journal/automation/n8n_sample_workflow.json` in die n8n Instanz.
- Der Workflow ruft den Nova CLI Summary-Endpunkt ab und sendet Updates an einen Microsoft Teams Webhook.
- Passe die Umgebungsvariablen `TEAMS_WEBHOOK_URL`, `TEAMS_WEBHOOK_USER` und `TEAMS_WEBHOOK_PASSWORD` in der n8n UI oder `.env` Datei an.

## 4. Integration mit LangChain vorbereiten
- Skizziere eine HTTP- oder gRPC-Schnittstelle, über die LangChain-Agenten Workflows triggern können.
- Ergänze die Schnittstellenbeschreibung im geplanten Dokument `orchestration_journal/automation/langchain_bridge.md`.
- Lege Testfälle für automatisierte Regressionen in `tests/automation/` an (Platzhalter, aktuell nicht vorhanden).

## 5. Nächste Schritte & Reporting
- Aktualisiere `progress_report.md` nach jedem abgeschlossenen Teilabschnitt.
- Nutze `python -m nova progress` und `python -m nova next-steps --phase model-operations`, um den Status zu verfolgen.
- Dokumentiere Abhängigkeiten oder Blocker im Orchestrierungstagebuch (`orchestration_journal/updates/`).
