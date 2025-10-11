# Playbook: Schritte bis zur nächsten Freigabe

Dieser Playbook-Entwurf beantwortet die Frage "Wie weiter machen bis zur nächsten Freigabe?" und fasst die aktuellen Prioritäten aus `progress_report.md`, den Foundation-Leitfäden sowie den Agenten-Checklisten zusammen. Ziel ist es, alle noch offenen Foundation-Aufgaben von Nova sauber abzuschließen und parallel die übrigen Spezialisten für die Launch-Phase vorzubereiten.

## 1. Operative Prioritäten (Foundation-Phase, Nova)

> Referenz: `docs/FOUNDATION_VPN_SETUP.md`, `docs/FOUNDATION_SECURITY_AUDIT.md`, `docs/FOUNDATION_BACKUP_RECOVERY.md`

- [ ] **VPN/Fernzugriff aktivieren**
  - Entscheidung zwischen WireGuard und OpenVPN dokumentieren (`orchestration_journal/vpn/decision.md`).
  - Rollout-Plan per CLI exportieren: `python -m nova network --vpn wireguard --export orchestration_journal/vpn/wireguard_plan.md`.
  - Verbindungstests und Firewall-Härtung durchführen; Ergebnisse im Orchestrierungstagebuch vermerken.
- [ ] **Security- & Datenschutz-Checks durchführen**
  - Prüfkatalog laut `docs/FOUNDATION_SECURITY_AUDIT.md` abarbeiten.
  - CLI-Run für Audit-Dry-Run: `python -m nova audit --export orchestration_journal/security/audit_report.md`.
  - Abweichungen samt Gegenmaßnahmen dokumentieren.
- [ ] **Backup- & Recovery-Plan finalisieren**
  - Standard-Plan generieren: `python -m nova backup --plan default --export orchestration_journal/backups/default_plan.md`.
  - Wiederherstellungstest simulieren und Lessons Learned erfassen.
- [ ] **Statuspflege & Freigabe-Dokumentation**
  - Nach jedem abgeschlossenen Schritt `Agenten_Aufgaben_Uebersicht.csv` aktualisieren.
  - Fortschritt via `python -m nova progress --limit 1` prüfen und den Snapshot im Journal ablegen.

## 2. Freigabe-Gates vor dem Go/No-Go-Meeting

- [ ] **Technische Validierung** – Logs, Audit-Reports und Backup-Checks liegen im Orchestrierungstagebuch vor.
- [ ] **Security-Signet** – Datenschutz- und Compliance-Verantwortliche haben die Audit-Ergebnisse gegengezeichnet.
- [ ] **Runbook-Abnahme** – VPN-, Security- und Backup-Runbooks sind in der Wissensbasis versioniert.
- [ ] **Rollback-Plan** – Für VPN und Backup existieren getestete Rückfalloptionen (z. B. Revocation-Prozess, Restore-Szenario).

## 3. Parallele Vorbereitung der Spezialisten

- **Orion (LLM/Software)**
  - [ ] Finetuning-Plan für Sophia finalisieren (vgl. `docs/DEFINITION_OF_DONE.md`, Abschnitt Orion).
  - [ ] Datenquellen- und Prompt-Governance abstimmen.
- **Lumina (Daten & Speicher)**
  - [ ] Vector-Datenbank-Setup vorbereiten (`docs/LUMINA_PLANS.md`).
  - [ ] Datenqualitäts-Metriken definieren.
- **Echo (Avatar & Interaktion)**
  - [ ] Avatar-Pipeline skizzieren (Audio2Face, Riva) und Abhängigkeiten erfassen.
  - [ ] Erste Mockups oder Animationsproben sammeln.
- **Chronos (Automation)**
  - [ ] Data-Flywheel-Blueprint aktualisieren (`docs/DEFINITION_OF_DONE.md`, Abschnitt Chronos).
  - [ ] Trigger für automatische Verbesserungszyklen definieren.
- **Aura (Monitoring & Dashboard)**
  - [ ] Metrik- und Alert-Design vorbereiten, insbesondere Stimmung/Emotion.
  - [ ] Dashboard-Prototypen planen (ggf. `python -m nova monitor --export ...`).

> Jeder Spezialist dokumentiert Ergebnisse in den jeweiligen Unterordnern des `orchestration_journal`, damit Nova die finale Freigabe zentral bewerten kann.

## 4. Reporting- und Kommunikationsrhythmus

- [ ] Wöchentlicher Review-Call, in dem Nova den Fortschritt pro Agent*in mit `python -m nova summary --limit 1` vorstellt.
- [ ] Tägliches Async-Update im Journal (Kurznotiz: erledigte Tasks, Blocker, nächste Schritte).
- [ ] Alerts-Dry-Run einmal pro Woche aktualisieren: `python -m nova alerts --dry-run --export orchestration_journal/alerts.md`.

## 5. Definition of Ready für die Freigabeentscheidung

Die nächste Freigabe kann erfolgen, sobald alle Checkboxen in Abschnitt 1 und 2 abgehakt sind **und** die Spezialisten ihre vorbereitenden Deliverables (Abschnitt 3) im Journal hinterlegt haben. Ergänzend gilt:

- [ ] Risiko- und Blocker-Liste ist leer bzw. mitigiert.
- [ ] Freigabemeeting ist terminlich bestätigt; Agenda enthält Demo, KPI-Review und offene Fragen.
- [ ] Release-Notes-Entwurf existiert (wird im Meeting finalisiert).

## 6. Nächste Schritte nach der Freigabe

- [ ] Live-Schaltung des VPN für das Operationsteam.
- [ ] Start der Security-Audit-Überwachung (kontinuierliche Checks in CI/Monitoring).
- [ ] Rollout des Backup-Plans auf produktionsnahe Systeme.
- [ ] Übergang in die Build-Phase für Orion, Lumina, Echo, Chronos und Aura gemäß Step-Plan.

---

Dieses Playbook dient als Referenzrahmen. Passe es bei neuen Erkenntnissen über den CLI-Status (`python -m nova progress`) oder externe Freigabeanforderungen an.
