# Foundation-Phase: Security- & Datenschutz-Checks

Dieser Leitfaden beschreibt Schritt 4 der Foundation-Phase für Nova. Ziel ist es, die zentralen Schutzmaßnahmen (Firewall, Anti-Virus, OPA-Policies) nachvollziehbar zu prüfen, Abweichungen zu dokumentieren und handlungsleitende Maßnahmen festzuhalten. Die Anleitung baut auf den bereits fertiggestellten Container- und VPN-Schritten auf.

## 1. Zielzustand & Erfolgskriterien
- [ ] Firewall-Regeln sind aktiv und protokolliert.
- [ ] Anti-Virus-Signaturen sind aktuell und der Dienst läuft.
- [ ] OPA-/Policy-Checks sind eingebunden und erzwingen die freigegebenen Regeln.
- [ ] `python -m nova audit` liefert einen Audit-Report ohne offene Findings.
- [ ] Ergebnisse sind im Orchestrierungstagebuch abgelegt und `Agenten_Aufgaben_Uebersicht.csv` spiegelt den Status wider.

## 2. Vorbereitung & Inventur
1. **Systemzustand erfassen**
   - Sammle die letzten Firewall-Logs (`/var/log/ufw.log` o. ä.).
   - Prüfe Anti-Virus-Status (`sudo systemctl status clamav-freshclam` oder entsprechendes Produkt).
   - Liste die aktiven OPA-Policies (`/etc/opa/policies/`).
2. **Environment-Variablen definieren** (optional)
   - `export NOVA_FIREWALL_ENABLED=enabled`
   - `export NOVA_ANTIVIRUS_ENABLED=enabled`
   - `export NOVA_OPA_POLICIES_ENFORCED=enabled`
   - Alternativ beim CLI-Aufruf über `--firewall enabled` etc. setzen.
3. **Checklisten öffnen**
   - Definition-of-Done für Nova: `docs/DEFINITION_OF_DONE.md` (Kapitel Security).
   - Incident-Response-Plan (falls vorhanden) für Kontext prüfen.

## 3. Audit-Workflow mit CLI
1. **Baseline-Lauf**
   ```bash
   python -m nova audit --firewall enabled --antivirus enabled --policies enabled
   ```
   - Verifiziere, dass alle Controls mit `[ok]` gemeldet werden.
2. **Markdown-Report sichern**
   ```bash
   python -m nova audit --firewall enabled --antivirus enabled --policies enabled \
     > orchestration_journal/security/audit_$(date +%Y%m%d).log
   ```
   - Alternativ `tee` verwenden, um den Report live zu verfolgen.
3. **Abweichungen dokumentieren**
   - Bei `[attention]` oder `[unknown]` Einträgen Ursache recherchieren (z. B. Dienst neu starten, Policy-Pfad prüfen).
   - Ergänze Korrekturmaßnahmen im Orchestrierungstagebuch (`orchestration_journal/security/findings.md`).
4. **Gegenkontrollen**
   - Firewall: `sudo ufw status verbose` oder `iptables -L`.
   - Anti-Virus: Signatur-Update (`freshclam`, `sudo systemctl restart clamav-daemon`).
   - OPA: Policy-Test (`opa eval --data policies --input request.json 'data.access.allow'`).

## 4. Reporting & Fortschrittsabgleich
- Exportiere den finalen Markdown-Report (`orchestration_journal/security/audit_report.md`).
- Aktualisiere `Agenten_Aufgaben_Uebersicht.csv` (Zeile „Security & Datenschutz-Checks durchführen“ → `Abgeschlossen`).
- Trigger einen Alert-Dry-Run, um Security-Events zu testen:
  ```bash
  python -m nova alerts --dry-run --export orchestration_journal/alerts.md
  ```
- Passe `progress_report.md` oder Sprint-Board entsprechend an.

## 5. Eskalation & Follow-up
- Bei wiederholten Findings Ticket im Incident-Board erstellen (z. B. GitHub Issue `security/<topic>`).
- Ergebnisse mit Security Manager teilen; Freigabe-Entscheid dokumentieren.
- Lessons Learned in `orchestration_journal/security/retrospective.md` eintragen.

Mit Abschluss dieser Checkliste ist Schritt 4 der Foundation-Phase belastbar beschrieben. Die darauffolgende Aufgabe fokussiert auf Backup- & Recovery-Systeme (siehe `docs/FOUNDATION_BACKUP_RECOVERY.md`).
