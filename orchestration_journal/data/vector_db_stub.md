# Vector-Datenbank Prototyp (Lumina)

Am 12.10.2025 wurde ein erster Prototyp für die Wissensdatenbank von Sophia in
Code gegossen. Das Modul `nova.data.vector_store` stellt eine abstrahierte
Schnittstelle bereit, die sowohl Pinecone- als auch FAISS-Szenarien abbildet.

## Funktionsumfang

- Gemeinsame Konfigurationsstruktur (`VectorStoreConfig`) mit Dimension,
  Metrik und Metadatenschema.
- In-Memory-Implementierung für lokale Tests inklusive Cosine-, Dot- und
  Euclid-Metrik.
- Pinecone- und FAISS-Stubs, die auf der In-Memory-Variante aufbauen und
  deploymentspezifische Metadaten exponieren.
- Query-Ergebnisse liefern Score + Metadaten und lassen sich für Ranking-Checks
  nutzen.

## Validierung

Die Unit-Tests (`tests/test_vector_store.py`) decken folgende Szenarien ab:

1. Upsert/Query-Fluss mit Cosine Similarity.
2. Lösch-Operationen und defensives Verhalten bei fehlenden IDs.
3. Factory-Initialisierung für Pinecone, FAISS und Memory-Betrieb.
4. Alternative Metriken (Dot Product, Euclidean Distance).
5. Plausibilitätsprüfung für Dimensionsfehler.
6. `describe()`-Ausgabe inklusive Metadaten-Schema.

## Nächste Schritte

- Pinecone-/FAISS-SDKs einbinden, sobald API-Keys bzw. GPU-Hardware bereitsteht.
- Persistenzschicht für produktive Deployments (z. B. PostgreSQL + pgvector)
  evaluieren.
- Integration in `lumina`-CLI-Flows vorbereiten, damit Datenbank-Pläne direkt
  mit dem Vector-Store verkettet werden können.
