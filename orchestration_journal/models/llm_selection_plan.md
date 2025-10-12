# Sophia LLM Auswahl- und Bereitstellungsplan

## Zusammenfassung
Entscheidungsmatrix und Bereitstellungsplan für Sophias Basismodell inklusive Governance-Checks.

## Ziele & Erfolgskriterien
- Transparente Bewertung von mindestens drei LLM-Kandidaten (Lizenz, Kontextfenster, Kosten).
- Proof-of-Concept-Bereitstellung (HF Inference Endpoint oder TensorRT-LLM) sicherstellen.
- Integration in Monitoring und Sicherheitsrichtlinien vorbereiten (Audit Logging, Access Control).

## Datenaufbereitung & Governance
- Eval-Datensätze definieren (Dialoge, Compliance, Eskalationen).
- Prompt-Guidelines und Guardrails (Safety Prompts, Moderation) aufnehmen.
- Legal/Procurement-Review für Lizenzbedingungen dokumentieren.

## Infrastruktur & Tooling
- Deployment-Optionen vergleichen: Managed (Azure OpenAI, AWS Bedrock) vs. Self-Hosted (DGX).
- Helm/Compose-Manifest in `deploy/models/<candidate>/` vorbereiten.
- Observability (latency, token-usage) mit Prometheus/Grafana koppeln.

## Trainingspipeline
- Baseline-Benchmarks durchführen (`python -m nova benchmarks --profile llm-core`).
- Red Teaming-Scenarios definieren und in QA-Plan aufnehmen.
- Vorbereitung für Adapter/LoRA-Anbindung dokumentieren (Kompatibilität).

## Evaluierung & Qualitätssicherung
- Bewertungstabelle `orchestration_journal/models/llm_selection_matrix.md` pflegen.
- KPI-Katalog (Latenz, Win-Rate, Kosten) mit Aura abstimmen.
- Stakeholder-Review (Product, Legal, Security) einholen und protokollieren.

## Risiken & Gegenmaßnahmen
- Fallback-Modell definieren (z. B. Mixtral 8x7B) mit reduzierten Ressourcen.
- Exit-Strategie bei Lizenzänderungen oder API-Limits beschreiben.
- Datenschutz-Folgenabschätzung (DSFA) dokumentieren, falls Cloud-Anbieter im Spiel sind.

## Übergabe & Automatisierung
- Decision Log in `docs/MODEL_OPERATIONS_KICKOFF.md` ergänzen.
- `Agenten_Aufgaben_Uebersicht.csv` aktualisieren (Status → Abgeschlossen) nach Freigabe.
- Monitoring & Alerts für gewähltes Modell aktivieren (`python -m nova alerts`).
