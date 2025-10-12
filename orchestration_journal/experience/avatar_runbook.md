# Avatar Pipeline Runbook

Dieses Runbook beschreibt die End-to-End-Pipeline vom Omniverse-Authoring bis
zur Integration in Microsoft Teams. Die Schritte lassen sich ohne produktive
Anbindung in einer Staging-Umgebung vorbereiten.

## Architekturüberblick

1. **Omniverse Stage** – Enthält die Avatar-Geometrie und animierbare
   Blendshapes (`assets/avatar/sophia_stage.usd`).
2. **Audio2Face** – Generiert per Audioinput eine Mimikspur (JSON/Cache).
3. **Riva Services** – ASR transkribiert Benutzerinput, TTS erzeugt Antwort.
4. **LangChain Bridge** – Orchestriert Dialoglogik und ruft LLM/Vector-Store ab.
5. **n8n Workflow** – Persistiert Konversationen, stößt Alerts an.
6. **Teams Adapter** – WebRTC Gateway, authentifiziert via Azure AD App-Registrierung.

## Betriebsablauf

1. `deploy/avatar/riva-compose.yml` starten (`docker compose up -d`).
2. Audio2Face im Headless-Modus starten: `a2f run --scene sophia_stage.usd --port 8011`.
3. Bridge-Service deployen (`deploy/automation/bridge/docker-compose.yml`).
4. Teams Adapter konfigurieren (`deploy/avatar/teams-adapter/`), Webhook-URL
   im n8n Workflow hinterlegen.
5. End-to-End-Test: `python scripts/avatar_e2e.py --channel teams --language de`.

## Monitoring & KPIs

- Riva Latenz < 400ms (Audio Roundtrip).
- Audio2Face Frame-Drop < 2%.
- Teams Adapter Paketverlust < 5%.
- KPIs im LUX Dashboard visualisieren (`docs/dashboards/lux_dashboard.md`).

## Incident Response

| Szenario | Sofortmaßnahme | Eskalation |
| --- | --- | --- |
| Audioausfall | Audio2Face Logs prüfen, ggf. Cache neu laden | Echo → Chronos |
| ASR erkennt nichts | Riva Pipeline neustarten, Mikrofon-Level prüfen | Echo → Orion |
| Teams Disconnect | Token erneuern, Netzwerkpfad prüfen | Echo → Nova |

## Change Management

- Änderungen an Omniverse Assets via Pull Request (`assets/avatar/`).
- Konfigurationsänderungen dokumentieren (`orchestration_journal/experience/change_log.md`).
- QA-Checkliste vor Live-Schaltung durchgehen.

## Offene Aufgaben

- [ ] Teams Recording-Funktion aktivieren und DSGVO-Check durchführen.
- [ ] Automatisierte Tests (`pytest -k avatar`) implementieren.
- [ ] Monitoring-Integration mit Grafana Panel finalisieren.
