# NVIDIA NeMo Validierungsprotokoll

Dieses Protokoll fasst die geplanten Smoke-Tests zusammen, die nach der
Installation von NVIDIA NeMo ausgeführt werden. Die Tests können lokal ohne
GPU durchgeführt werden, indem Mock-Läufe und CPU-Fallbacks verwendet werden.

## Testübersicht

1. **Umgebungskontrolle**
   - `nvidia-smi` Ausgabe sichern und Treiberversion dokumentieren.
   - Python-Umgebung prüfen (`python -m pip list | grep nemo`).
2. **NLP Pipelines (CPU-Fallback)**
   - Beispielskript `python scripts/nemo_smoke_test.py --task nlp` ausführen.
   - Erwartung: Tokenizer-Initialisierung < 5s, Text-zu-Text-Demo liefert Antwort.
3. **ASR Pipeline (Mock Audio)**
   - Dummy-Audio (`tests/fixtures/audio/hello.wav`) verwenden.
   - `python scripts/nemo_smoke_test.py --task asr --device cpu`.
   - Erwartung: Transkription enthält Schlüsselwort "hello".
4. **Konfiguration & Logging**
   - Prüfen, ob `NEMO_LOG_DIR` gesetzt ist und Logs rotiert werden.
   - Exportierte Configs nach `orchestration_journal/models/nemo_configs/` verschieben.

## Fehlermanagement

- Bei GPU-Zugriffen ohne verfügbare Hardware automatisch auf CPU ausweichen.
- Störungen im Container-Pull (`nvcr.io`) via Offline-Mirror (`registry.local/nemo`)
  kompensieren.
- Kritische Fehler (> Severity High) im Incident-Board melden und Ticket
  erstellen (`INC-SOPHIA-NE`).

## Status

- [ ] Container Pull getestet
- [ ] CPU-Fallback validiert
- [ ] Logging & Alerts eingerichtet
- [ ] Dokumentation freigegeben
