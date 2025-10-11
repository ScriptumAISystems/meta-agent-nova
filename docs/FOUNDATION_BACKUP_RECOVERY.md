# Foundation-Phase: Backup- & Recovery-Systeme

Dieser Leitfaden deckt Schritt 5 der Foundation-Phase ab. Er beschreibt, wie ein standardisiertes Sicherungs- und Wiederherstellungsprogramm für Sophias Infrastruktur (DGX/Spark, Kubernetes, Datenbanken, LLM-Artefakte) aufgebaut, getestet und dokumentiert wird.

## 1. Zielbild & Abnahmekriterien
- [ ] Schutzumfang (System, Datenbanken, Modelle) ist inventarisiert.
- [ ] Backup-Jobs sind automatisiert, versioniert und überwacht.
- [ ] Mindestens ein Restore-Drill wurde erfolgreich durchgeführt und protokolliert.
- [ ] `python -m nova backup --plan default` ist dokumentiert und bei Bedarf angepasst.
- [ ] Fortschritt ist in `Agenten_Aufgaben_Uebersicht.csv` markiert und im Orchestrierungstagebuch verlinkt.

## 2. Vorbereitung
1. **Inventarisierung**
   - Komponentenliste: Kubernetes-Manifeste, Docker-Compose, ConfigMaps, Secrets.
   - Datenhaltung: MongoDB, PostgreSQL, VectorDB (FAISS/Pinecone), Artefakt-Registry.
   - Geschäftsanforderungen: RTO/RPO, Compliance (DSGVO, ISO 27001).
2. **Speicherziele definieren**
   - Primär: Objekt-Storage (S3/MinIO) oder dedizierter Backup-Server.
   - Sekundär: Offline/Offsite-Backup für Desasterfälle.
3. **Credentials & Policies vorbereiten**
   - Secrets im Vault hinterlegen, Rotation planen.
   - Zugriff auf Backup-Storage per Firewall/VPN einschränken.

## 3. Plan mit CLI ableiten
1. **Standardplan anzeigen**
   ```bash
   python -m nova backup --plan default
   ```
   - Prüfe die Abschnitte zu Backup-Jobs, Recovery-Übungen und Retention.
2. **Markdown-Export erzeugen**
   ```bash
   python -m nova backup --plan default \
     --export orchestration_journal/backups/backup_plan_default.md
   ```
3. **Plan anpassen**
   - Ergänze projektspezifische Speicherpfade, Tools (Restic, Velero, Borg, etc.).
   - Aktualisiere bei Bedarf den CLI-Plan (`nova/system/backup.py`) oder lege eine projektspezifische Variante an (`custom`).

## 4. Umsetzung & Automatisierung
1. **Backup-Jobs einrichten**
   - Kubernetes: Nutze CronJobs/Velero für Cluster-Ressourcen.
   - Datenbanken: `pg_dump`, `mongodump`, VectorDB-Export skripten und mit Hash-Werten versehen.
   - LLM-Artefakte: Versionierung in Artefakt-Registry (z. B. MLflow, Hugging Face Hub).
2. **Scheduling & Monitoring**
   - Cron/Argo Workflows aufsetzen, Status nach `orchestration_journal/backups/` spiegeln.
   - `python -m nova alerts --dry-run` erweitern, um Backup-Latenzen zu prüfen.
3. **Restore-Tests**
   - Monatlicher Drill auf isolierter Umgebung (`staging` Namespace, Offline-Netz).
   - Wiederherstellung protokollieren (`orchestration_journal/backups/drills/<datum>.md`).

## 5. Reporting & Abschluss
- Backup-Ergebnisse im Sprint-Review vorstellen.
- Tickets für Verbesserungen anlegen (z. B. `backups/<topic>`).
- Definition-of-Done-Checkliste (Nova) abhaken, wenn Restore erfolgreich dokumentiert ist.
- Fortschritt im CSV (Aufgabe „Backup- & Recovery-System aufsetzen“) auf `Abgeschlossen` setzen und CLI-Reports (`python -m nova progress`) aktualisieren.

Mit diesem Dokument ist die Foundation-Phase vollständig dokumentiert: Schritte 1–5 besitzen reproduzierbare Leitfäden. Folgearbeiten konzentrieren sich jetzt auf Model-Operations, Datenservices und Observability.
