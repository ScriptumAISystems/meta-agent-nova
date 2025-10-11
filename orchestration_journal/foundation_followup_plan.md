# Foundation Follow-up Aktionsplan (Stand 11.10.2025)

Dieser Plan beantwortet "Wie machen wir weiter?" für die anstehenden Schritte der Foundation-Phase. Er konsolidiert die wichtigsten Aktionen aus den Nova-CLI-Reports und den Detailanleitungen im `docs/`-Ordner.

## 1. Container-Basis fertigstellen (Foundation Schritt 2)

- [ ] **Docker Engine & CLI installieren**
  - Anleitung: `docs/FOUNDATION_CONTAINER_SETUP.md`, Abschnitt "Docker Engine installieren".
  - Nacharbeit: `docker --version` und `docker info` ausführen, Ergebnisse protokollieren.
- [ ] **Kubernetes-Tooling aktivieren**
  - Wähle entweder Kind (Tests) oder kubeadm/k3s (Produktivpfad) gemäß Dokumentation in `docs/FOUNDATION_CONTAINER_SETUP.md`.
  - Prüfe `kubectl cluster-info` und `kubectl get nodes`.
- [ ] **Nova-Validierung laufen lassen**
  - `python -m nova containers --export orchestration_journal/container-report.md --fix-export orchestration_journal/container-fix.md`.
  - Erwartung: Beide Checks zeigen ✅. Andernfalls Fix-Plan aktualisieren und erneut durchführen.
- [ ] **Status dokumentieren**
  - `Agenten_Aufgaben_Uebersicht.csv`: Aufgabe "Docker und Kubernetes-Cluster installieren" auf „Abgeschlossen" setzen.
  - Kurzes Log im Orchestrierungstagebuch ergänzen (siehe Abschnitt 4).

## 2. Nachfolgende Foundation-Schritte vorbereiten

- [ ] **VPN & Fernzugriff planen**
  - Anleitung: `docs/FOUNDATION_VPN_SETUP.md`.
  - Optionaler Export für das Tagebuch: `python -m nova network --vpn wireguard --export orchestration_journal/vpn/wireguard_plan.md`.
- [ ] **Security & Datenschutz-Checks terminieren**
  - Leitfaden: `docs/FOUNDATION_SECURITY_AUDIT.md`.
  - Vorbereitend `python -m nova audit --export orchestration_journal/security/initial_audit.md` (Skript erstellen, falls noch nicht vorhanden).
- [ ] **Backup- & Recovery-Plan finalisieren**
  - Anleitung: `docs/FOUNDATION_BACKUP_RECOVERY.md`.
  - CLI: `python -m nova backup --plan default --export orchestration_journal/backups/default_plan.md`.

## 3. Koordination mit anderen Agenten (Ausblick)

- [ ] **Orion**: Aufgaben laut `docs/next_steps.md` (Abschnitt „KI-Stack vorbereiten“) und `docs/OPERATIVE_ARBEITSPAKETE.md` (Kapitel „Orion – KI & Modellbetrieb“) reviewen, damit Installations- und Finetuning-Workflows vorbereitet sind, sobald Container & Netzwerk bereitstehen.
- [ ] **Lumina**: Infrastruktur-Abhängigkeit prüfen; Orientierung bietet `docs/next_steps.md` (Abschnitt „Daten- und Wissensbasis einrichten“) sowie `docs/OPERATIVE_ARBEITSPAKETE.md` (Kapitel „Lumina – Daten & Storage“).
- [ ] **Echo**: Asset-Pipeline-Blueprints aus `docs/next_steps.md` (Abschnitt „Interaktionslayer planen“) und `docs/OPERATIVE_ARBEITSPAKETE.md` (Kapitel „Echo – Avatar & Experience“) konsolidieren.
- [ ] **Chronos**: n8n- und LangChain-Deployments anhand von `docs/next_steps.md` (Abschnitt „Workflow- & Automationspfad“) sowie den Definition-of-Done-Kriterien in `docs/DEFINITION_OF_DONE.md` vorbereiten.
- [ ] **Aura**: Monitoring-Stack und LUX-Dashboard Planung gemäß `docs/next_steps.md` (Abschnitt „Monitoring & Dashboards“) und `docs/DEFINITION_OF_DONE.md` (Kapitel „Aura – Monitoring & Dashboards“) priorisieren.

## 4. Reporting & Kommunikation

- [ ] Nach jedem abgeschlossenen Schritt einen kurzen Statusblock im Orchestrierungstagebuch ergänzen (z. B. `orchestration_journal/updates/2025-10-11.md`).
- [ ] `python -m nova progress --limit 1` erneut ausführen und Screenshot/Markdown sichern.
- [ ] Wöchentliche Zusammenfassung in `progress_report.md` aktualisieren.

> 💡 Tipp: Alle neuen Markdown-Exports bitte versionieren, um den Audit-Trail konsistent zu halten.
