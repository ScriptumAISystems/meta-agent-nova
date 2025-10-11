# Kurzüberblick: Nächste Schritte

Diese Übersicht fasst die priorisierten Folgeaktivitäten für Meta-Agent Nova zusammen. Detaillierte Beschreibungen stehen in `docs/next_steps.md`.

## Top-Prioritäten (0-2 Wochen)
- [ ] **DGX Spark Vorbereitungsplan umsetzen** – siehe `docs/DGX_PRE_ARRIVAL_PLAN.md` für detaillierte Checklisten.
- [ ] Infrastruktur-Audits ausführen (CPU/GPU/Netzwerk) und Ergebnisse dokumentieren.
- [ ] Automatisiertes Setup für Container-Orchestrierung (Docker, Kubernetes) bereitstellen – Anleitung `docs/FOUNDATION_CONTAINER_SETUP.md` befolgen und Status mit `python -m nova containers` dokumentieren.
- [ ] VPN/Remote-Zugriff abschließen und Security-/Backup-Leitfäden abarbeiten (`docs/FOUNDATION_VPN_SETUP.md`, `docs/FOUNDATION_SECURITY_AUDIT.md`, `docs/FOUNDATION_BACKUP_RECOVERY.md`).

## KI-Stack vorbereiten (Parallel zu oben)
- [ ] NVIDIA NeMo inkl. Abhängigkeiten installieren und Validierungsskripte hinterlegen.
- [ ] Start-LLM auswählen, Bereitstellungsschritte sowie Ressourcenbedarf festhalten.
- [ ] Konzept für Fine-Tuning (Datenquellen, Evaluationsmetriken) erstellen.

## Daten & Wissensbasis (2-4 Wochen)
- [ ] Automatisiertes Setup für MongoDB/PostgreSQL (lokal & produktiv) implementieren.
- [ ] Vektordatenbank evaluieren (Pinecone vs. FAISS) und Prototyp zur Wissensabfrage bauen.

## Interaktions- & Automationspfad (4-6 Wochen)
- [ ] NVIDIA ACE-Komponenten (Audio2Face, Riva, NeMo) testen und Pipeline dokumentieren.
- [ ] Kommunikationsplattform (Teams o.ä.) auswählen inkl. Authentifizierungsstrategie.
- [ ] n8n-Workflows initialisieren und Orchestrierung mit LangChain spezifizieren.

## Governance & Monitoring (fortlaufend)
- [ ] Grafana-Deployment und KPI-Dashboards planen (inkl. Energie-/Stimmungsmetriken).
- [ ] Roadmap, Definition-of-Done und Teststrategie regelmäßig aktualisieren.
- [ ] Sprint-Board anlegen, Kick-off organisieren und Minimalziel (Systemchecks + Docker + Logging) starten.

> 📌 Nutze `python -m nova step-plan`, `python -m nova summary` und `python -m nova progress`, um den aktuellen Status je Agentenrolle zu verfolgen.

## Issue-Triage & Bearbeitungsrhythmus

| Zeitpunkt | Aktivität | Verantwortlich | Ziel |
| --- | --- | --- | --- |
| **Montag 09:00 UTC** | Gemeinsames Issue-Triage-Meeting (max. 30 Minuten). Neue Issues priorisieren, Blocker erfassen, Verantwortliche zuweisen. | Nova & betroffene Spezialisten | Aktualisiertes Backlog mit klaren Zuständigkeiten für die laufende Woche |
| **Dienstag–Donnerstag** | Fokus-Arbeitsblöcke je Team (mindestens 2 Stunden pro Tag). Review-Zeitfenster von 16:00–17:00 UTC für PRs und technische Klärungen reservieren. | Zuständige Agentenrollen | Stetiger Fortschritt an priorisierten Issues, Abschluss offener Reviews |
| **Freitag 14:00 UTC** | Fortschritts-Check-in (15 Minuten). Offene Punkte für die nächste Woche sammeln, Lessons Learned festhalten. | Nova (Moderation) & alle Agentenrollen | Transparente Statusübersicht, Übernahme offener Restarbeiten in nächste Iteration |

### Leitplanken für Issue-Bearbeitung

- **WIP-Limits beachten:** Pro Agentenrolle maximal zwei gleichzeitig aktive Issues; neue Aufgaben erst beginnen, wenn ein Slot frei ist.
- **Dokumentation erzwingen:** Ergebnisse und Entscheidungen unmittelbar im passenden Dokument (`docs/…` oder `orchestration_journal/…`) oder direkt im Issue protokollieren.
- **Automatisierte Checks:** Vor jedem Check-in mindestens `python -m nova progress` ausführen und relevante Reports anhängen, damit der Status nachvollziehbar bleibt.
- **Blocker sofort melden:** Blockierende Issues werden direkt im täglichen Review-Fenster (16:00–17:00 UTC) adressiert oder eskaliert.
