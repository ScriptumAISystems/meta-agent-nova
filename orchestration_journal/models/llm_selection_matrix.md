# LLM Auswahlmatrix (Sophia)

Die folgende Matrix bewertet drei priorisierte Kandidaten basierend auf den
Kriterien aus dem Langfristplan (`docs/MODEL_OPERATIONS_KICKOFF.md`). Die
Bewertungen nutzen eine Skala von 1 (schwach) bis 5 (stark). Kommentare
beschreiben Besonderheiten oder erforderliche Maßnahmen.

| Kriterium | Llama 3 8B Instruct | Mixtral 8x7B | Phi-3 Medium |
| --- | --- | --- | --- |
| Lizenz & Nutzungsrechte | 4 – Gemeinnützige Nutzung erlaubt, kommerzielle Nutzung geprüft | 3 – Komplexe Lizenz (Mistral Terms), Review erforderlich | 5 – Microsoft Non-Commercial, Enterprise Addendum notwendig |
| Kontextfenster | 5 – 16k Token, ausreichend für Support-Skripte | 4 – 32k Token, aber höherer Speicherbedarf | 3 – 8k Token, ggf. Erweiterung via Sliding Window |
| Infrastrukturkosten | 4 – Passt in DGX A100 (1x GPU) mit 40 GB | 3 – Benötigt Tensor Parallel >1 GPU | 5 – CPU-fähig, niedrige Betriebskosten |
| Sprachqualität (Deutsch/Englisch) | 4 – Sehr gute Mehrsprachigkeit | 4 – Stark für Englisch, deutsche Trainingsdaten prüfen | 3 – Fokus auf Englisch, Feintuning nötig |
| Sicherheitsfeatures | 3 – Basis-Safety, zusätzliche Guardrails notwendig | 3 – Zusätzliche Moderation einplanen | 4 – Integrierte Safety-Schichten verfügbar |
| Integration in Tooling | 5 – Vollständig kompatibel mit Hugging Face & vLLM | 4 – TensorRT-LLM Support vorhanden | 4 – Azure ML & ONNX Laufzeit verfügbar |
| Community & Support | 4 – Aktive Community, Meta Doku | 4 – Mistral Support (Enterprise) | 3 – Microsoft Research, begrenztere Community |

## Empfehlung

- **Kurzfristig**: Llama 3 8B Instruct als Standardmodell einsetzen. Passt in
  bestehende Toolchains und ist für das initiale Finetuning vorbereitet.
- **Mittelfristig**: Mixtral evaluieren, sobald DGX Spark mehrere GPUs freigibt.
- **Fallback**: Phi-3 Medium als kosteneffiziente Variante in Cloud- oder
  CPU-Szenarien.

## Nächste Schritte

1. Lizenzfreigaben einholen und Entscheidung im Governance-Board dokumentieren.
2. Deployment-Manifeste für Llama 3 finalisieren (`deploy/models/llama3/`).
3. Monitoring-Kennzahlen in `docs/dashboards/lux_dashboard.md` ergänzen.
