# NVIDIA NeMo Installationsleitfaden

## Zusammenfassung
Installations-Playbook für NVIDIA NeMo inklusive Abhängigkeitsmanagement, Validierungsschritten und Übergabe an den Betrieb.

## Ziele & Erfolgskriterien
- GPU- und CPU-kompatible Installationspfade für NeMo bereitstellen (Container & venv).
- Sicherstellen, dass Lizenz- und Compliance-Anforderungen dokumentiert und freigegeben sind.
- Smoke-Tests automatisieren, damit Orion & Chronos die Umgebung reproduzierbar verifizieren können.

## Datenaufbereitung & Governance
- Hardware-Voraussetzungen erfassen (GPU Generation, CUDA-Version, Treiberstand).
- Kompatibilitätsmatrix für PyTorch, CUDA, cuDNN und TensorRT pflegen.
- Offline-Mirror (Wheel-Cache oder Container Registry) für air-gapped Deployments vorbereiten.

## Infrastruktur & Tooling
- Container-Image (`nvcr.io/nvidia/nemo:latest`) referenzieren und Pull-Prüfung dokumentieren.
- Alternativ: Python Virtualenv mit `pip install nemo_toolkit[all]` + `onnxruntime-gpu` beschreiben.
- Monitoring Hooks (DCGM Exporter, nvidia-smi Logs) in Betriebskonzept aufnehmen.

## Trainingspipeline
- Smoke-Test Notebook (NLP + ASR) unter `notebooks/nemo_smoke_test.ipynb` anlegen.
- CLI-Skript `python -m nova models --plan finetune` als Folgeaufgabe verlinken.
- Resource-Quotas definieren (GPU Memory, Disk) und in `deploy/automation/bridge/.env` spiegeln.

## Evaluierung & Qualitätssicherung
- `pytest -k nemo` Workflow in CI integrieren (Mock Tests ohne GPU).
- Validierungslog `orchestration_journal/models/nemo_validation.md` führen.
- Kompatibilitätstests für Mehrsprachigkeit & Mixed Precision dokumentieren.

## Risiken & Gegenmaßnahmen
- Fallback auf CPU-Build dokumentieren (`nemo_toolkit[asr]` + `onnxruntime`).
- Security-Bulletins von NVIDIA beobachten und Hotfix-Pfade festhalten.
- Lizenzbedingungen (NVIDIA AI Enterprise) prüfen und in Governance-Archiv ablegen.

## Übergabe & Automatisierung
- Installationsprotokoll im `orchestration_journal/models/nemo_installation.md` aktualisieren.
- Operations Runbook (`docs/MODEL_OPERATIONS_KICKOFF.md`) mit finalen Parametern ergänzen.
- Ticket in Service-Now/Jira für Go-Live-Abnahme anstoßen.
