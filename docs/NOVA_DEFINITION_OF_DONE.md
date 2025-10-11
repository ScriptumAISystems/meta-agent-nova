# Nova Definition of Done (DoD)

Die folgenden Kriterien definieren den binären Abnahmerahmen für Nova. Alle Punkte müssen erfüllt sein, damit Nova als "done" gewertet werden kann. Schwellenwerte basieren auf dem aktuellen Zielbild für Spark DGX/Sophia.

## 1. Stabilität & Self-Monitoring
- [ ] **Health-Checks:** Core-Services liefern über `/healthz` mindestens 99,5 % `200 OK` während eines ungeplanten 72h-Dauerlaufs ohne manuellen Eingriff.
- [ ] **Watchdog:** Crash oder Deadlock wird in ≤ 60 s erkannt und der betroffene Prozess automatisch neu gestartet. Ereignisse sind im Log nachvollziehbar.
- [ ] **Drift-Alerts:** Konfigurationsabweichungen werden binnen ≤ 5 Minuten erkannt und via Slack/Matrix gemeldet.

## 2. Auto-Rollback (sicherer Betrieb)
- [ ] **Canary-Deploy:** Neuer Build läuft zunächst als Canary mit ≥ 5 % Traffic. Folgende Metriken werden kontinuierlich erfasst: Fehlerrate, p95-Latenz, CPU-/GPU-Last.
- [ ] **Rollback-Trigger:** Überschreitet die Fehlerrate 1 % *oder* steigt die p95-Latenz > 2× Basiswert über 10 Minuten, initiiert das System automatisch einen Rollback auf die letzte stabile Version (durch Pipeline-Protokoll belegbar).
- [ ] **Wiederanlauf:** Nach Rollback stabilisiert sich die p95-Latenz innerhalb von Basiswert ± 10 % in ≤ 15 Minuten.

## 3. Bidirektionale Sophia-Kommunikation
- [ ] **Request→Response:** Sophia kann Nova-Tasks via REST/gRPC einreichen. Nova antwortet mit Status-Events (`ACK`, `STARTED`, `PARTIAL`, `DONE`, `ERROR`).
- [ ] **Event-Stream:** Live-Updates stehen per SSE/WebSocket bereit; Paketverlust < 0,1 % über 60 Minuten Dauerbetrieb.
- [ ] **Auth:** mTLS oder OIDC-Token werden erfolgreich validiert. Ungültige Tokens werden abgelehnt und im Audit-Log protokolliert.

## 4. Orchestrierung der Sub-Agenten
- [ ] **Task-Graph:** Nova plant und führt mindestens drei Sub-Agenten nacheinander bzw. parallel aus, inklusive Fehler-Retry mit exponentiellem Backoff.
- [ ] **Idempotenz:** Wiederholte Ausführung führt zu identischem Endzustand (nachgewiesen via Checksums oder State-Hash).
- [ ] **Ressourcen-Budget:** GPU-/CPU-Quoten werden eingehalten; Überschreitungen resultieren in einem Graceful Throttle anstatt eines abrupten Abbruchs.

## 5. Observability & SRE-Basis
- [ ] **Logs/Metrics/Traces:** Alle Signale sind zentral (z. B. Loki/Prometheus/Tempo) einsehbar; Tracing-Span-Rate ≥ 95 %.
- [ ] **SLOs:** Definiert und aktiv überwacht: Verfügbarkeit 99,0 %, p95-Task-Latenz < 30 s, Fehlerrate < 1 %.
- [ ] **Runbooks:** Einseitige Runbooks für "Deploy", "Rollback" und "Hotfix" liegen im Repository vor.

## 6. Sicherheit & Compliance (minimal)
- [ ] **Secrets:** Keine Secrets im Code oder in Logs; alle Zugriffe erfolgen über einen Secret-Store (z. B. Vault oder KMS).
- [ ] **Least-Privilege:** Service-Accounts besitzen minimale Rechte. Ein Policy-Report belegt die Prüfung.
- [ ] **Audit:** Änderungen an Policies oder Konfigurationen sind versioniert und nachvollziehbar.

## 7. Developer Experience & Release-Qualität
- [ ] **One-Command-Setup:** `make up` (oder ein äquivalentes Skript) richtet ein lokales bzw. Staging-System reproduzierbar ein.
- [ ] **CI-Gate:** Kritische Pfade weisen ≥ 80 % Testabdeckung auf. Smoke-Tests sind grün, Security-Scans enthalten keine "High/Critical"-Befunde.
- [ ] **Dokumentation:** README (Start), `ARCH.md` (Übersicht) und API-Spezifikation (OpenAPI/gRPC) sind aktuell und miteinander verlinkt.

## Abnahmetest (30-Minuten-Demo, schwarz/weiß)
1. Canary-Deploy auslösen → Canary bleibt stabil, anschließend wird eine künstliche Degradation provoziert → automatischer Rollback greift.
2. Sophia sendet einen Task → Nova orchestriert drei Agenten, streamt Status-Updates und schließt mit `DONE` + Artefakt-/Resultat-Hash ab.
3. Watchdog-Test: Prozess killen → Neustart ≤ 60 s, SLOs bleiben im Rahmen.
4. Security-Check: Abgelaufenes Token → Request wird abgelehnt, Log/Audit ist sichtbar.
5. One-Command-Setup auf frischer Staging-VM erfolgreich durchlaufen.

> **Bestehensregel:** Jeder Punkt erfüllt = PASS. Ein Punkt fehlt = FAIL.

