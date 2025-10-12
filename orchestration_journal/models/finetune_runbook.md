# Finetuning Runbook – Sophia v1

Dieser Runbook-Eintrag bündelt die vorbereitenden Aktivitäten für das
Finetuning der Sophia-Grundmodelle mit NVIDIA NeMo. Er basiert auf der
Konfiguration aus `config/finetune/lora.yaml` und der durch das Skript
`scripts/finetune_nemo.py` generierten Planungsübersicht.

## 1. Vorbereitung & Validierung

1. **Konfiguration prüfen** – `python scripts/finetune_nemo.py --silent` ausführen.
   - Rückgabewert `0` signalisiert, dass alle harten Checks bestanden sind.
   - Bei Exit-Code `2` die ausgegebenen Findings in diesem Runbook ergänzen.
2. **Dateninventur** – Einträge für Train/Validation/Eval in
   `orchestration_journal/data/datasets.md` aktualisieren, inklusive Eigentümer
   und Freigabenachweise.
3. **Security Review** – Mit Nova Security abstimmen, ob zusätzliche Data Leak
   Tests notwendig sind (`python -m nova audit --mode data`).

## 2. Infrastruktur & Umgebung

1. **NeMo Container** – Aktuelle Version `nvcr.io/nvidia/nemo:24.06` auf der DGX
   synchronisieren.
2. **CUDA / TensorRT Profil** – Sicherstellen, dass CUDA 12.4 und TensorRT-LLM
   installiert sind (siehe `docs/DGX_PRE_ARRIVAL_PLAN.md`).
3. **Artefakt-Registry** – Bucket `models/finetune/` anlegen und mit Versionierung
   versehen (`sophia-finetune-<datum>`).

## 3. Trainingsdurchführung

1. **LoRA Setup** – Die Werte aus `config/finetune/lora.yaml` in eine NeMo
   Experiment-Konfig (`configs/nemo/sophia_lora.yaml`) spiegeln.
2. **Training starten** – Neptune Job oder Slurm Submit vorbereiten.
   - Command-Template: `python -m nemo.collections.llm.finetune --config-path configs/nemo --config-name sophia_lora`.
   - Monitoring via `python -m nova monitor --job sophia-finetune-dev` aktivieren.
3. **Checkpoints prüfen** – Nach jedem Intervall `artifacts/checkpoints/` auf
   Konsistenz kontrollieren.

## 4. Evaluierung & Abnahme

1. **Automatisierte Metriken** – BLEU, ROUGE-L und Win-Rate-Skripte ausführen; Ergebnisse
   in `orchestration_journal/models/finetune_metrics.md` protokollieren.
2. **Human Review** – Stichprobe von 50 Dialogen vorbereiten, Feedback in
   `orchestration_journal/models/finetune_reviews.md` dokumentieren.
3. **Rollback-Check** – Baseline-Modell bereit halten (`orchestration_journal/models/baseline_inventory.md`).

## 5. Übergabe & Kommunikation

1. **Artefakte versionieren** – Finale Adapter-Gewichte + Configs nach
   `models/finetune/<datum>/` hochladen.
2. **Tasks aktualisieren** – `Agenten_Aufgaben_Uebersicht.csv` für Orion aktualisieren
   (Status → Abgeschlossen).
3. **Stakeholder informieren** – Update in `progress_report.md` sowie Meeting-Notiz in
   `orchestration_journal/updates/` hinterlegen.

## 6. Offene Punkte / Follow-ups

- [ ] Integrationstest mit LangChain-Bridge (siehe `orchestration_journal/automation/langchain_bridge.md`).
- [ ] Alerts anpassen (`python -m nova alerts --dry-run --export orchestration_journal/alerts.md`).
- [ ] Ergebnisse in Monitoring-Dashboard (`docs/dashboards/lux_dashboard.md`) einspeisen.
