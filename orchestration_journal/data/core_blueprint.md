# Sophia Data Core Blueprint

## Zusammenfassung
Bündelt die vorbereitenden Arbeiten für Datenbanken und Vektor-Store, damit Lumina die Plattform vor dem DGX-Spark-Go-Live stabilisieren kann.

## Relationale Datenbanken

### MongoDB Cluster (Ops Ready)

Bereitet die MongoDB-Umgebung für Sophia vor und stellt sicher, dass Replica-Set und Netzwerk-Vorgaben dokumentiert sind.

**Deployment-Schritte**
1. `sudo apt-get update` – Refresh package metadata to ensure latest releases.
2. `sudo apt-get install -y mongodb-org` – Install the MongoDB community edition binaries.
3. `sudo systemctl enable --now mongod` – Start the MongoDB service and enable auto-start on boot.

**Konfigurationsempfehlungen**
- `bind_ip` → 0.0.0.0
- `replica_set` → sophia-rs
- `storage_engine` → wiredTiger

**Validierung**
- `mongo --eval 'db.runCommand({ connectionStatus: 1 })'`
- `rs.status()`

**Hardening & Betriebstipps**
- Enable TLS/SSL and enforce SCRAM-SHA auth before produktivem Go-Live.
- Konfiguriere Backup-Targets (`python -m nova backup --plan data`) nach dem ersten Health-Check.

**Follow-up / Ownership**
- Operations-Team informiert, wenn Replica-Set initialisiert wurde (`rs.initiate()`).
- Firewall-Regeln für Ports 27017/27018 mit Security abstimmen.

### PostgreSQL Service (SOP)

Installiert PostgreSQL inkl. Basis-Konfiguration und stellt Prüfschritte für Zugänge bereit.

**Deployment-Schritte**
1. `sudo apt-get update` – Refresh package metadata to ensure latest releases.
2. `sudo apt-get install -y postgresql postgresql-contrib` – Install PostgreSQL server including common extensions.
3. `sudo systemctl enable --now postgresql` – Start PostgreSQL and enable auto-start on boot.
4. `sudo -u postgres createuser --superuser sophia` – Provision a superuser account for orchestration tasks.

**Konfigurationsempfehlungen**
- `listen_addresses` → *
- `max_connections` → 200
- `shared_buffers` → 1GB

**Validierung**
- `psql --command 'SELECT version();'`
- `sudo -u postgres psql -c '\l'`

**Hardening & Betriebstipps**
- Aktiviere `pg_hba.conf`-Restriktionen (nur VPN/VPC) und erzwinge Passwortrotation.
- Plane PITR-Backups über `pg_basebackup` oder WAL-G shipping ein.

**Follow-up / Ownership**
- `sophia`-Role in Secrets-Management aufnehmen und mit DevOps teilen.
- Schema-Migrationspfad (Alembic/Flyway) mit Chronos abstimmen.

## Vector Knowledge Base

### Pinecone (Managed Option)

Managed Vektorservice für schnelle Produktions-Reife. Enthält Credential-Setup und Index-Provisionierung.

**Deployment-Schritte**
1. `pip install --upgrade pinecone-client` – Install the Pinecone Python SDK for index management.
2. `pinecone configure --api-key $PINECONE_API_KEY --environment us-west1-gcp` – Link the project credentials and default environment.
3. `python -m pinecone.scripts.create_index --name sophia-embeddings --dimension 4096` – Provision an index tailored for Sophia embeddings.

**Konfigurationsempfehlungen**
- `metric` → cosine
- `pods` → 1
- `replicas` → 1

**Validierung**
- `pinecone describe-index --name sophia-embeddings`
- `pinecone list-indexes`

**Hardening & Betriebstipps**
- API-Keys im Secrets-Store (1Password/Vault) hinterlegen und Rotation halbjährlich planen.
- Traffic-Monitoring via Pinecone Usage Dashboard aktivieren und Kosten-Limits definieren.

**Follow-up / Ownership**
- Data-Ingestion-Pipeline (Chronos) auf Index `sophia-embeddings` zeigen lassen.
- Service-Kontrakt (SLA/Limits) mit Procurement und Legal dokumentieren.

### FAISS (Self-Hosted Option)

On-Premise Alternative inklusive Build-Schritte und Testaufrufen für CPU-basierte Experimente.

**Deployment-Schritte**
1. `sudo apt-get install -y libopenblas-dev libomp-dev` – Install BLAS and OpenMP dependencies required by FAISS.
2. `pip install faiss-cpu` – Install the FAISS CPU package via pip.
3. `python -m faiss.contrib.tutorials.build_index --dimension 4096 --output sophia.index` – Generate a baseline index file for testing queries.

**Konfigurationsempfehlungen**
- `index_type` → IVF4096,Flat
- `training_samples` → 50000

**Validierung**
- `python -m faiss.contrib.tutorials.query_index --index sophia.index --queries sample.npy`

**Hardening & Betriebstipps**
- Index-Dateien verschlüsselt speichern (LUKS/eCryptfs) und Backup-Strategie definieren.
- GPU-Beschleunigung evaluieren, sobald DGX Spark verfügbar ist (CUDA Faiss-Paket).

**Follow-up / Ownership**
- CI-Pipeline erweitern, um Index-Build Smoke-Tests auszuführen.
- Zugriffspfade (POSIX ACLs) für Data-Science-Team dokumentieren.

## Betrieb & Automatisierung

- Registriere Health-Checks (MongoDB/PostgreSQL) in `python -m nova monitor` für Availability-Alerts.
- Synchronisiere Backup-Zeitpläne mit Nova (`python -m nova backup --plan data --export ...`).
- Verknüpfe Vector-Store-Latenzen mit dem LUX-Dashboard (Aura) für Experience-KPIs.

## Übergabe & Dokumentation

- Exportiere dieses Blueprint nach `orchestration_journal/data/core_blueprint.md` und teile es mit Lumina/Chronos.
- Aktualisiere `Agenten_Aufgaben_Uebersicht.csv` sobald MongoDB/PostgreSQL Provisionierung abgeschlossen ist.
- Dokumentiere Zugangsdaten & Netzwerkpfade im `orchestration_journal/data/`-Verzeichnis.
