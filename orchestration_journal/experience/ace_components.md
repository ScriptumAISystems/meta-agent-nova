# NVIDIA ACE Komponenten-Checkliste

Diese Checkliste dokumentiert die Schritte, um den ACE-Stack (Riva, Audio2Face,
NeMo) für Sophias Avatar vorzubereiten. Alle Schritte sind als vorbereitende
Maßnahmen ohne DGX-Hardware ausführbar.

## 1. Komponentenübersicht

| Komponente | Version | Bereitstellung | Notizen |
| --- | --- | --- | --- |
| Riva Speech Services | 2.16 | Docker Compose (`deploy/avatar/riva-compose.yml`) | Enthält ASR & TTS Pipelines |
| Audio2Face | 2024.1 | Omniverse Launcher (Headless) | Exportiert Blendshape-Animationen |
| NeMo Conversational AI | 2.0 | Gemeinsame GPU/CPU-Umgebung | Wird für Intent-Pipelines genutzt |

## 2. Installationsschritte

1. `docker login nvcr.io` mit Service Account durchführen.
2. Container-Images via `deploy/avatar/pull_images.sh` vorausladen.
3. Audio2Face Dataset (`assets/avatar/base_head.usd`) herunterladen und in
   `orchestration_journal/experience/assets/` ablegen.
4. Konfigurationsdateien (`config/avatar/*.yaml`) erstellen und Parameter
   (Stimmfarbe, Sample-Rate) abstimmen.

## 3. Validierung

- Riva: `python scripts/riva_smoke_test.py --pipeline asr-tts`.
- Audio2Face: Export-CLI `a2f render --usd assets/avatar/base_head.usd --audio tests/fixtures/audio/hello.wav`.
- NeMo: Intent-Slot-Demo `python scripts/nemo_smoke_test.py --task nlu`.

## 4. Offene Punkte

- [ ] GPU Performance-Messung nach DGX-Verfügbarkeit.
- [ ] Lizenz-Review für Omniverse Assets abschließen.
- [ ] Integrationstest mit Avatar-Pipeline dokumentieren.

## Referenzen

- `docs/MODEL_OPERATIONS_KICKOFF.md`
- `docs/OPERATIVE_ARBEITSPAKETE.md` (Paket E1)
