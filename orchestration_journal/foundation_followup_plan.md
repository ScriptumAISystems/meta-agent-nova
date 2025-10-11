# Foundation Follow-up Aktionsplan (Stand 11.10.2025)

Dieser Plan beantwortet "Wie machen wir weiter?" für die anstehenden Schritte der Foundation-Phase. Er konsolidiert die wichtigsten Aktionen aus den Nova-CLI-Reports und den Detailanleitungen im `docs/`-Ordner.

## 1. Container-Basis fertigstellen (Foundation Schritt 2)

- [x] **Docker Engine & CLI installieren**
  - Abschluss: Docker 26.0.0 inkl. `docker run hello-world` am 12.10.2025 protokolliert.
- [x] **Kubernetes-Tooling aktivieren**
  - kubeadm-Cluster initialisiert, `kubectl get nodes` zeigt `spark-control-plane` im Status Ready.
- [x] **Nova-Validierung laufen lassen**
  - `python -m nova containers --export orchestration_journal/container-report.md` bestätigt beide Runtimes mit ✅.
- [x] **Status dokumentieren**
  - CSV aktualisiert, Update im Orchestrierungstagebuch unter `updates/2025-10-12.md` hinterlegt.

## 2. Nachfolgende Foundation-Schritte vorbereiten

- [x] **VPN & Fernzugriff planen**
  - Abschluss: WireGuard-Plan am 12.10.2025 exportiert (`orchestration_journal/vpn/wireguard_plan.md`).
  - Kommender Fokus: Security-Audit vorbereiten und Backup-Plan exportieren.
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

- [ ] Nach jedem abgeschlossenen Schritt einen kurzen Statusblock im Orchestrierungstagebuch ergänzen (z. B. `orchestration_journal/updates/2025-10-12.md`, `updates/2025-10-12_0722.md`).
- [ ] `python -m nova progress --limit 1` erneut ausführen und Screenshot/Markdown sichern (nächster Turnus nach VPN-Setup).
- [x] Wöchentliche Zusammenfassung in `progress_report.md` aktualisieren.

> 💡 Tipp: Alle neuen Markdown-Exports bitte versionieren, um den Audit-Trail konsistent zu halten.
