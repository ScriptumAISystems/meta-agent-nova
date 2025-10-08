# Nächste Schritte für Meta-Agent Nova

Dieses Dokument beantwortet die Frage "Wie machen wir jetzt weiter?" und bietet einen klaren Fahrplan, um das Nova-Orchestratorsystem strukturiert auszubauen. Die Schritte sind nach Priorität geordnet und referenzieren die vorhandenen Rollenaufgaben aus `TASKS.md`.

> 💡 **Tipp:** Verwende `python -m nova step-plan`, um eine automatisch generierte Schritt-für-Schritt-Liste aus der Aufgabenübersicht (`Agenten_Aufgaben_Uebersicht.csv`) zu erhalten. Über `--phase foundation` lässt sich der Plan auf einzelne Phasen eingrenzen.

## 1. Infrastruktur-Grundlagen fertigstellen (Nova)
- **System- und Hardware-Audits abschließen:** Führe die in `nova/system` implementierten Prüf-Utilities aus, um CPU, GPU und Netzwerk zu verifizieren.
- **Container- und Orchestrierungstools installieren:** Script- oder CLI-Aufrufe für Docker und Kubernetes automatisieren und Ergebnisse dokumentieren.
- **VPN/Remote-Zugriff konfigurieren:** Lege Konfigurationsdateien für WireGuard oder OpenVPN an und integriere sie in das Setup.
- **Sicherheits- und Backup-Routinen aktivieren:** Nutze `nova/security` und `nova/logging`, um Audit-Logging und Backup-Pläne festzuhalten.

## 2. KI-Stack vorbereiten (Orion)
- **NVIDIA NeMo installieren:** Ergänze Installationsanweisungen und Validierungsskripte, sodass die Abhängigkeiten reproduzierbar sind.
- **LLM-Auswahl und Bereitstellung:** Entscheide dich für ein Startmodell (z. B. Llama 3) und dokumentiere Bereitstellung und Ressourcenbedarf.
- **Feintuning-Konzept erstellen:** Skizziere Datenquellen, Evaluationsmetriken und Automatisierung für Fine-Tuning-Läufe.
- **LangChain-Integration prototypisieren:** Verknüpfe das Modell mit bestehenden Agenten über standardisierte Schnittstellen in `nova/agents`.

## 3. Daten- und Wissensbasis einrichten (Lumina)
- **MongoDB/PostgreSQL Setup automatisieren:** Erstelle Skripte oder Helm-Charts für lokale und produktive Deployments.
- **Vektordatenbank evaluieren:** Vergleiche Pinecone und FAISS hinsichtlich Latenz, Kosten und Self-Hosting; prototypisiere ein Modul in `nova/monitoring` oder `nova/task_queue` für Wissensabfragen.

## 4. Interaktionslayer planen (Echo)
- **NVIDIA ACE-Komponenten testen:** Dokumentiere die benötigten Container/Downloads und stelle sicher, dass Audio2Face, Riva und NeMo zusammenspielen.
- **Avatar-Pipeline definieren:** Lege ein Sequenzdiagramm für Omniverse → Audio2Face → Riva → Frontend an.
- **Kommunikationsplattform auswählen:** Plane die Integration in Microsoft Teams (oder Alternative) und erarbeite Authentifizierungsanforderungen.

## 5. Workflow- & Automationspfad (Chronos)
- **n8n-Basisinstallation:** Schreibe ein Setup-Skript, das n8n lokal startet und Beispiel-Workflows lädt.
- **LangChain/n8n-Orchestrierung:** Definiere, wie Agenten-Aufgaben über Webhooks oder gRPC mit n8n synchronisiert werden.
- **CI/CD-Blueprint:** Entwirf ein Pipeline-Dokument, das GitHub Enterprise und Kubernetes Deployments verknüpft.

## 6. Monitoring & Dashboards (Aura)
- **Grafana-Deployment skizzieren:** Dokumentiere Dashboards, Metriken und Datenquellen (Prometheus, Logs, KPI-Tracker).
- **LUX-Dashboard Wireframe:** Erstelle Mockups und verknüpfe sie mit Telemetriedaten aus `nova/logging/kpi`.
- **Energie- und Stimmungsmetriken:** Sammle Anforderungen und definiere KPIs für Effizienz und Stimmungsfeedback.

## 7. Organisations- und Governance-Arbeit
- **Roadmap verfeinern:** Pflege `README.md` und `docs/DEFINITION_OF_DONE.md`, synchronisiere Milestones, Definition of Done und Verantwortlichkeiten.
- **Teststrategie festlegen:** Lege fest, welche automatisierten Tests pro Modul Pflicht sind (Unit-, Integration- und Systemtests).
- **Audit-Trail definieren:** Nutze `nova/security` und `nova/monitoring`, um Berichtsprozesse festzuhalten.

## 8. Nächste operative Schritte
1. Richte ein Sprint-Board ein (z. B. GitHub Projects) und überführe jede obige Aufgabe in konkrete Tickets.
2. Priorisiere zunächst Infrastruktur und Sicherheit, danach KI-Stack und Datenhaltung.
3. Plane ein Kick-off-Meeting, um Verantwortlichkeiten je Agentenrolle zuzuweisen.
4. Starte mit einem Minimalziel: automatisierte Systemchecks, Docker-Installation und Grundlogging müssen innerhalb der ersten Iteration laufen.

Mit diesen Schritten entsteht ein klarer Projektpfad, der von der Infrastruktur bis zur Interaktionsebene reicht und sowohl technische als auch organisatorische Aufgaben abdeckt.
