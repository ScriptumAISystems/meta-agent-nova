# Sophia Datensätze – Inventarliste

Dieses Dokument dient als zentrales Register für alle Datensätze, die im Rahmen
der Sophia-Finetuning-Pipeline verwendet werden. Ergänze jede Quelle mit den
relevanten Metadaten und dem Compliance-Status.

| Name | Pfad | Eigentümer | Zweck | Freigabe (DSGVO) | Letztes Update |
| --- | --- | --- | --- | --- | --- |
| Train | data/sophia/train.jsonl | tbd | Haupttraining | ausstehend | - |
| Validation | data/sophia/validation.jsonl | tbd | Hyperparam Abstimmung | ausstehend | - |
| Eval | data/sophia/eval.jsonl | tbd | Abschlussmetriken | ausstehend | - |

## Prüf-Checkliste

- [ ] Datensatzschema dokumentiert (`docs/MODEL_OPERATIONS_KICKOFF.md`).
- [ ] Zugriffsbeschränkungen in Data Lake / Object Storage hinterlegt.
- [ ] Redaktionslog in `orchestration_journal/updates/` aktualisiert.
