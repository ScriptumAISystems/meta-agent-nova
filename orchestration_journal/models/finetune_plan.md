# Sophia Finetuning Playbook

## Zusammenfassung
Standardisierte LoRA/PEFT-Finetuning-Pipeline für Sophia inklusive Daten-Governance, Infrastruktur und Übergabe an Betriebsteams.

## Ziele & Erfolgskriterien
- Lieferung eines reproduzierbaren Finetuning-Playbooks für Orion inkl. GPU- und CPU-Fallback.
- Dokumentierter Pfad von Datenaufnahme bis Modellübergabe mit klaren KPIs (BLEU, ROUGE, Win-Rate).
- Verankerung der Aufgaben in Novas Task- und Monitoring-Ökosystem (Alerts, Backups, Journale).

## Datenaufbereitung & Governance
- Domänenspezifische Korpora inventarisieren (Dialoge, SOPs, Wissensartikel) inklusive Eigentümer & Klassifizierung.
- Anonymisierung & DSGVO-Konformität sicherstellen; Freigaben in `orchestration_journal/data/consent_log.md` protokollieren.
- Annotation-Guidelines definieren (Richtlinien, Quality-Gates, Review-Kadenz).
- Datenaufteilung festlegen (Train/Val/Test ≥ 70/15/15) und Seed-Management dokumentieren.

## Infrastruktur & Tooling
- NeMo & Abhängigkeiten in isolierter Umgebung bereitstellen (`nemo`, `pytorch`, `transformers`).
- DGX GPU-Profile vorbereiten (CUDA Toolkit, TensorRT-LLM) und CPU-Fallback via vLLM oder HF-Inference beschreiben.
- Artefakt-Registry und Weights-Speicher (`models/finetune/`) mit Versionsschema einrichten.
- Überwachungshooks für Trainingsjobs in `python -m nova monitor` aufnehmen (Laufzeit, GPU-Auslastung, Fehler).

## Trainingspipeline
- Baseline-Modell auswählen (z. B. Llama 3 8B Instruct) und Hyperparameter-Tabelle bereitstellen.
- LoRA/PEFT-Konfiguration in YAML-Schablone erfassen (`config/finetune/lora.yaml`).
- Trainingsskript skizzieren (`scripts/finetune_nemo.py`) inkl. Resume/Checkpoint-Handling.
- Experiment-Tracking (Weights & Biases oder MLflow) mit Namenskonvention `sophia-finetune-<datum>` definieren.
- Deployment-Pipeline vorbereiten (Helm/Terraform) für aktualisierte Adapter-Gewichte.

## Evaluierung & Qualitätssicherung
- Evaluationsdatensätze kuratieren (Szenario-Dialoge, Edge-Cases) und Referenzantworten festlegen.
- Automatisierte Metriken (BLEU ≥ 35, ROUGE-L ≥ 0.4, Win-Rate ≥ 65 %) konfigurieren.
- Human-in-the-loop Review-Panel etablieren; Feedback in `orchestration_journal/models/finetune_reviews.md` sammeln.
- Regressionstests gegen Basismodell durchführen; Abweichungen dokumentieren und bei Bedarf Rollback initiieren.

## Risiken & Gegenmaßnahmen
- Data-Leakage-Prüfungen (Prompt-Leaks, PII) mit Security-Team abstimmen und Findings triagieren.
- Fallback-Strategie definieren: Basismodell + Safety-Layer aktivieren, wenn KPIs unterschritten werden.
- Kosten- und Laufzeitbudget monitoren; Schwellenwerte in `python -m nova alerts --dry-run` testen.
- Compliance-Review (Lizenz, Exportkontrollen) vor Go-Live dokumentieren.

## Übergabe & Automatisierung
- Trainingslog, Configs und Adapter-Gewichte unter `orchestration_journal/models/` versionieren.
- Runbook für Deployment und Rollback (`orchestration_journal/models/finetune_runbook.md`) erstellen.
- Agenten-Aufgabenliste aktualisieren (Status → Abgeschlossen) und Stakeholder informieren.
- Lessons Learned & nächste Iterationen in `progress_report.md` bzw. Nova CLI (`python -m nova summary`) spiegeln.
