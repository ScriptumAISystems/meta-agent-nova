# NVIDIA Software Stack – DGX Integrationsleitfaden

> Ziel: Den kompletten NVIDIA Software-Stack (Base Stack, Frameworks, System-Integration) in den ersten zwei DGX-Wochen betriebsbereit aufsetzen, um GPU-Ressourcen ohne Verzögerung produktiv zu nutzen.

---

## Überblick & Zeitplan

| Phase | Zeitraum      | Fokus                                                         |
| :---- | :------------ | :------------------------------------------------------------ |
| 1     | DGX-Woche 1 – Tage 1–2 | Basissystem (OS, Treiber, CUDA/cuDNN) validieren und GPU-fähige Containerläufe sicherstellen. |
| 2     | DGX-Woche 1 – Tage 3–5 | NVIDIA Framework Stack (Riva, NeMo, Triton, Omniverse, DCGM Exporter) bereitstellen. |
| 3     | DGX-Woche 2 – Tage 6–10 | Services zu End-to-End-Pipelines für Nova, Sophia und Aurora verbinden. |

---

## Phase 1 – DGX Basis (Tag 1–2)

1. **NVIDIA Base Stack installieren**
   ```bash
   sudo apt install -y nvidia-driver-550 nvidia-container-toolkit nvidia-docker2
   sudo systemctl restart docker
   nvidia-smi
   ```
   - ✅ Erwartung: Alle GPUs erscheinen mit korrekten Spezifikationen in `nvidia-smi`.

2. **CUDA & cuDNN prüfen**
   - DGX OS Images liefern CUDA 12.x und cuDNN 9.x mit. `nvcc --version` und `cat /usr/include/cudnn_version.h | grep CUDNN_MAJOR -A2` verifizieren Versionsstände.

3. **Docker GPU-Runtime testen**
   ```bash
   docker run --rm --gpus all nvidia/cuda:12.4.0-base nvidia-smi
   ```
   - ✅ Erwartung: Ausgabe analog zum lokalen `nvidia-smi`, keine CUDA-Treiberfehler.

---

## Phase 2 – NVIDIA Framework Stack (Tag 3–5)

| Komponente | Zweck | Integrationshinweise |
| :--------- | :---- | :------------------- |
| **NVIDIA Riva** | Speech ASR/TTS für Sophia Avatar | Container aus der NGC Registry ziehen (`nvcr.io/nvidia/riva/riva-speech:latest`). Endpunkte für `asr` und `tts` auf `localhost:50051` bzw. via Ingress bereitstellen. |
| **NVIDIA NeMo** | Training & Fine-Tuning der Nova LLMs | Nutzung via Docker (`nvcr.io/nvidia/nemo:latest`) oder Python Virtual Env (`pip install nemo_toolkit[gpu]`). Prüfroutinen für GPU-Verfügbarkeit einplanen (`python -c "import torch; print(torch.cuda.is_available())"`). |
| **NVIDIA Triton Inference Server** | High-Performance Inference API für Nova/Sophia | Eigenen Service (`docker-compose.triton.yml`) mit Modell-Repository (`models/`). REST/gRPC Ports (8000/8001) freigeben, Health-Checks aktivieren (`/v2/health/ready`). |
| **NVIDIA Omniverse Kit + Audio2Face** | Avatar & 3D-Pipeline für Aurora + Sophia | Installation lokal oder auf Spark Workstation; Remote-Zugriff über LAN. Projektpfade und LiveLink-Verbindungen dokumentieren. |
| **NVIDIA DCGM Exporter** | GPU-Monitoring für Prometheus/Grafana | Container `nvcr.io/nvidia/k8s/dcgm-exporter:latest` auf Port 9400 bereitstellen. Prometheus Scrape-Config (`prometheus.yml`) erweitern. |

> Hinweise:
> - Alle Komponenten sind in der `NGC` Registry verfügbar. Vorab `ngc registry resource download` Skripte vorbereiten.
> - Die Integrationspunkte sind in den Dokumenten `Lastenheft v1.1` und diesem Leitfaden referenziert.

---

## Phase 3 – System-Integration (Tag 6–10)

1. **Triton ↔ Nova**
   - REST/gRPC Client (`nova/services/triton_client.py`) nutzt Batch-Inferenz.
   - Automatisierte Tests für Modell-Latenz und Batch-Durchsatz definieren.

2. **Riva ↔ Sophia**
   - Voice Loop: `ASR → LLM → TTS`.
   - gRPC-Verbindungen absichern (TLS) und Latenzprofil mit kurzen Soundbites testen.

3. **Omniverse ↔ Aurora**
   - Steuerung über Omniverse Kit Scripts (z. B. USD Events).
   - Audio2Face Output mit Sophia TTS synchronisieren.

4. **DCGM Exporter ↔ Prometheus/Grafana**
   - Prometheus-Scrape aktivieren, Dashboards importieren (GPU-Auslastung, Temperatur, Speicher).
   - Alerting-Regeln (`gpu_overtemp`, `gpu_mem_high`) definieren.

---

## Validierung & Übergang in die Optimierungsphase

- ✅ **Smoke Tests**: `nvidia-smi`, `docker run --gpus all`, Riva Quickstart (`riva_start.sh`), Triton Health Checks.
- ✅ **Monitoring**: Grafana Dashboard mit DCGM-Metriken zeigt Live-Daten.
- ✅ **Pipelines**: End-to-End Durchläufe für Nova/Sophia/Aurora abgeschlossen.
- ➡️ **Next Step**: Optimierungsphase (A3 Autonomy + Self-Optimization), Feinjustierung der Modell- und Pipeline-Parameter.

---

## Checkliste

- [ ] DGX Basis-Stack erfolgreich installiert und validiert.
- [ ] Framework-Komponenten (Riva, NeMo, Triton, Omniverse, DCGM) provisioniert.
- [ ] End-to-End-Integrationen produktiv nutzbar.
- [ ] Monitoring/Alerting aktiv.
- [ ] Optimierungsphase vorbereitet.

---

### Referenzen
- DGX OS Dokumentation (NVIDIA).
- NVIDIA NGC Registry.
- Projektinterne Dokumente: `Lastenheft v1.1`, `docs/EXECUTION_PLAN.md`, `docs/NEXT_RELEASE_PLAYBOOK.md`.
