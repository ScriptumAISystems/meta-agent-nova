# Datenbank-Betriebshandbuch (Lumina)

Dieses Handbuch beschreibt die wiederholbaren Schritte, um die Kern-Datenbanken
(PostgreSQL und MongoDB) für Sophia auf dem DGX Spark Stack zu betreiben. Die
Compose-Dateien befinden sich unter `deploy/databases/` und sind auf lokale
Entwicklung sowie prä-produktive Tests ausgerichtet.

## 1. Vorbereitung

1. `.env` mit sicheren Zugangsdaten befüllen:
   ```bash
   cp deploy/databases/.env.sample .env
   # POSTGRES_PASSWORD und MONGO_INITDB_ROOT_PASSWORD anpassen
   ```
2. Optional: Initialisierungsskripte in `deploy/databases/postgres/init/` und
   `deploy/databases/mongo/init/` ablegen.
3. Monitoring-Endpunkte in die zentralen Prometheus-Scrape-Configs übernehmen.

## 2. Start der Datenbank-Services

```bash
cd deploy/databases
docker compose up -d
```

- PostgreSQL ist auf Port `5432` erreichbar.
- MongoDB lauscht auf Port `27017`.
- Exporter stellen Metriken auf den Ports `9187` (PostgreSQL) und `9216`
  (MongoDB) bereit.

## 3. Healthchecks & Validierung

```bash
# PostgreSQL
PGPASSWORD="$POSTGRES_PASSWORD" psql -h localhost -U nova_admin -d sophia -c 'SELECT 1;'

# MongoDB
mongosh "mongodb://nova_admin:$MONGO_INITDB_ROOT_PASSWORD@localhost:27017/admin" --eval "db.runCommand({ ping: 1 })"

# Prometheus Targets (lokal)
curl -f http://localhost:9187/metrics
curl -f http://localhost:9216/metrics
```

Die Healthchecks sind zusätzlich in `docker-compose.yml` hinterlegt und
verhindern, dass abhängige Services starten, bevor die Datenbanken bereit sind.

## 4. Backup & Restore Hooks

- PostgreSQL: `pg_dump -Fc --dbname=$POSTGRES_DB --file=/backups/postgres/
  sophia_$(date +%F).dump`
- MongoDB: `mongodump --uri="mongodb://nova_admin:$MONGO_INITDB_ROOT_PASSWORD@
  mongo:27017" --out /backups/mongo/$(date +%F)`
- Restore-Probe monatlich durchführen und Ergebnisse im
  `orchestration_journal/backups/` Ordner dokumentieren.

## 5. Wartung & Automatisierung

- `docs/LUMINA_PLANS.md` referenzieren, um Konfigurationsparameter und
  Erweiterungen abzugleichen.
- GitHub Actions Workflow (folgt) triggert Smoke-Tests mit `docker compose run`
  und stellt sicher, dass neue Commits die Datenbanken erfolgreich starten.
- Für Produktionsbetrieb Kubernetes-Manifeste generieren (Helm Chart geplant).

## Statusmeldung

- [x] Docker-Compose-Stack modelliert (`deploy/databases/docker-compose.yml`).
- [x] Healthchecks & Monitoring-Exporter integriert.
- [ ] Kubernetes-Deployment finalisiert.
- [ ] Automatisierte Backups im CI hinterlegt.
