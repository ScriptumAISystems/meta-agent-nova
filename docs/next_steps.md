# Nächste Schritte für Meta-Agent Nova

Dieses Dokument beantwortet die Frage "Wie machen wir jetzt weiter?" und bietet einen klaren Fahrplan, um das Nova-Orchestratorsystem strukturiert auszubauen. Die Schritte sind nach Priorität geordnet und referenzieren die vorhandenen Rollenaufgaben aus `TASKS.md`.

> 💡 **Tipp:** Verwende `python -m nova step-plan`, um eine automatisch generierte Schritt-für-Schritt-Liste aus der Aufgabenübersicht (`Agenten_Aufgaben_Uebersicht.csv`) zu erhalten. Über `--phase foundation` lässt sich der Plan auf einzelne Phasen eingrenzen. Für eine fokussierte Übersicht der wichtigsten To-dos je Spezialist lohnt sich `python -m nova next-steps --phase foundation`. Nutze zusätzlich `python -m nova progress`, um aktuelle Fortschrittswerte und die nächsten Schritte je Agent im Blick zu behalten.

## 1. Infrastruktur-Grundlagen fertigstellen (Nova)
- [x] System- und Hardware-Audits abschließen – Die `nova/system` Prüf-Utilities sind dokumentiert und laut Abschlussbericht erfolgreich ausgeführt.
- [x] Container- und Orchestrierungstools installieren – Die Umsetzung gemäß `docs/FOUNDATION_CONTAINER_SETUP.md` ist abgeschlossen und in den Foundation-Protokollen vermerkt.
- [x] VPN/Remote-Zugriff konfigurieren – WireGuard/OpenVPN-Konfigurationen sind erstellt und Bestandteil der Foundation-Übergabedokumente.
- [x] Sicherheits- und Backup-Routinen aktivieren – Security- und Backup-Leitfäden (`docs/FOUNDATION_SECURITY_AUDIT.md`, `docs/FOUNDATION_BACKUP_RECOVERY.md`) wurden durchgearbeitet und im Orchestrierungsjournal nachgewiesen.

## 2. KI-Stack vorbereiten (Orion)
- [x] NVIDIA NeMo installieren – Installations- und Validierungsskripte sind in `orchestration_journal/models/` dokumentiert und wurden gemäß Fortschrittsbericht abgeschlossen.
- [x] LLM-Auswahl und Bereitstellung abschließen – Die Modellwahl samt Bereitstellungsszenario ist finalisiert und in den Model-Operations-Dokumenten beschrieben.
- [x] Feintuning-Konzept erstellen – Datenquellen, Evaluationsmetriken und Automatisierungspläne liegen im Finetuning-Runbook vor.
- [x] LangChain-Integration prototypisieren – Die Bridge-Implementierungen sind vorhanden und mit den Agenten-Schnittstellen verknüpft.

## 3. Daten- und Wissensbasis einrichten (Lumina)
- [x] MongoDB/PostgreSQL Setup automatisieren – Deployment-Skripte und Automatisierungsnotizen sind abgeschlossen und abgelegt.
- [x] Vektordatenbank evaluieren – Die Evaluierung inklusive Prototyp in `nova/task_queue/vector_ingest.py` ist umgesetzt und dokumentiert.

## 4. Interaktionslayer planen (Echo)
- [x] NVIDIA ACE-Komponenten testen – Testprotokolle und Containeranforderungen sind fertiggestellt und im Experience-Journal festgehalten.
- [x] Avatar-Pipeline definieren – Sequenzdiagramm und Pipelinebeschreibung liegen vor und sind vollständig.
- [x] Kommunikationsplattform auswählen – Die Plattformentscheidung inklusive Auth-Strategie ist dokumentiert.

## 5. Workflow- & Automationspfad (Chronos)
- [x] n8n-Basisinstallation durchführen – Setup-Skripte und Beispiel-Workflows sind erstellt und Bestandteil des Automation-Stacks.
- [x] LangChain/n8n-Orchestrierung gestalten – Die Synchronisationslogik ist beschrieben und im Bridge-Service implementiert.
- [x] CI/CD-Blueprint entwerfen – Der Blueprint ist dokumentiert und mit den Infrastrukturplänen abgestimmt.

## 6. Monitoring & Dashboards (Aura)
- [x] Grafana-Deployment skizzieren – Deployment-Notizen und Dashboardpläne sind fertiggestellt.
- [x] LUX-Dashboard Wireframe erstellen – Mockups liegen vor und sind mit den KPI-Datenquellen abgestimmt.
- [x] Energie- und Stimmungsmetriken definieren – KPI-Definitionen sind dokumentiert und freigegeben.

## 7. Organisations- und Governance-Arbeit
- [x] Roadmap verfeinern – README und Definition-of-Done-Dokumente sind aktualisiert und spiegeln die finalen Zuständigkeiten wider.
- [x] Teststrategie festlegen – Verbindliche Testanforderungen pro Modul sind formuliert und umgesetzt.
- [x] Audit-Trail definieren – Audit- und Monitoringprozesse sind beschrieben und aktiv.

## 8. Nächste operative Schritte
- [x] Sprint-Board einrichten (z. B. GitHub Projects) und Aufgaben als Tickets anlegen – Das Board ist aktiv und mit allen Aufgaben bestückt.
- [x] Infrastruktur und Sicherheit priorisieren, anschließend KI-Stack und Datenhaltung anpacken – Die priorisierte Umsetzung ist laut Fortschrittsbericht abgeschlossen.
- [x] Kick-off-Meeting organisieren, um Verantwortlichkeiten je Agentenrolle zuzuweisen – Kick-off und Übergabe sind dokumentiert.
- [x] Minimalziel starten: automatisierte Systemchecks, Docker-Installation und Grundlogging innerhalb der ersten Iteration sicherstellen – Die Minimalziele wurden in der Foundation-Phase erreicht.

Mit diesen Schritten entsteht ein klarer Projektpfad, der von der Infrastruktur bis zur Interaktionsebene reicht und sowohl technische als auch organisatorische Aufgaben abdeckt.
