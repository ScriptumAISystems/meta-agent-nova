# Orchestrierungstagebuch

Dieses Verzeichnis bündelt die Markdown-Protokolle, die während der Nova-CLI-Läufe erzeugt
werden. Jeder Export dokumentiert den Status eines Foundation-Schritts oder liefert
einen direkt umsetzbaren Maßnahmenplan.

## Container-Basis (Foundation Schritt 2)
- `container-report.md`: Ergebnis von `python -m nova containers --fix --export orchestration_journal/container-report.md --fix-export orchestration_journal/container-fix.md`. Der Lauf vom 11.10.2025 (UTC) bestätigt, dass weder `docker` noch `kubectl` auf der aktuellen Umgebung installiert sind.
- `container-fix.md`: Automatisch generierter Fix-Plan mit den Installationsschritten aus `docs/FOUNDATION_CONTAINER_SETUP.md`.

## Foundation Follow-up Plan
- `foundation_followup_plan.md`: Schritt-für-Schritt-Aktionsplan mit allen unmittelbar nächsten Aufgaben (Docker/Kubernetes validieren, VPN planen, Security/Backup vorbereiten) sowie Koordinationshinweisen für die übrigen Agentenrollen.

## Laufende Status-Updates
- `updates/2025-10-11.md`: Zusammenfassung der CLI-Läufe vom 11.10.2025 (Progress-, Summary- und Container-Checks) mit Ableitung der nächsten Aktionen und Hinweisen zu Blockern.

## Nutzung & Aktualisierung
1. Re-run des Checks nach jeder Änderung an der Container-Infrastruktur: `python -m nova containers --fix --export orchestration_journal/container-report.md --fix-export orchestration_journal/container-fix.md`.
2. Den Follow-up Plan nach jeder Runde abhaken und bei Bedarf erweitern (z. B. neue Unterordner `orchestration_journal/vpn/`, `.../security/`, `.../backups/`).
3. Neue Reports unter Versionskontrolle bringen, damit die Historie der Validierungen nachvollziehbar bleibt.
4. Bei erfolgreichen Installationen den Status in `Agenten_Aufgaben_Uebersicht.csv` anpassen und den Fortschritt via `python -m nova progress` dokumentieren.
