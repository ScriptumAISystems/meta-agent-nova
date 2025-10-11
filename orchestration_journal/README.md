# Orchestrierungstagebuch

Dieses Verzeichnis bündelt die Markdown-Protokolle, die während der Nova-CLI-Läufe erzeugt
werden. Jeder Export dokumentiert den Status eines Foundation-Schritts oder liefert
einen direkt umsetzbaren Maßnahmenplan.

## Container-Basis (Foundation Schritt 2)
- `container-report.md`: Ergebnis von `python -m nova containers --fix --export orchestration_journal/container-report.md --fix-export orchestration_journal/container-fix.md`. Der Lauf vom 11.10.2025 (UTC) bestätigt, dass weder `docker` noch `kubectl` auf der aktuellen Umgebung installiert sind.
- `container-fix.md`: Automatisch generierter Fix-Plan mit den Installationsschritten aus `docs/FOUNDATION_CONTAINER_SETUP.md`.

## Nutzung & Aktualisierung
1. Re-run des Checks nach jeder Änderung an der Container-Infrastruktur: `python -m nova containers --fix --export orchestration_journal/container-report.md --fix-export orchestration_journal/container-fix.md`.
2. Neue Reports unter Versionskontrolle bringen, damit die Historie der Validierungen nachvollziehbar bleibt.
3. Bei erfolgreichen Installationen den Status in `Agenten_Aufgaben_Uebersicht.csv` anpassen und den Fortschritt via `python -m nova progress` dokumentieren.
