# LangChain ↔︎ n8n Bridge Konzept

Dieses Dokument beschreibt den Integrationspfad zwischen der Nova Agentenwelt
(LangChain-basierte Tools) und der Automatisierungsplattform n8n. Ziel ist es,
Finetuning- und Monitoring-Aufgaben direkt aus Agentenläufen heraus triggern zu
können.

## 1. Architekturüberblick

```
LangChain Agent (Orion) ──HTTP POST──▶ Bridge Service ──REST──▶ n8n Webhook
                                       │                           │
                                       └──Event Stream─────────────┘
```

- **Bridge Service**: Leichtgewichtiger FastAPI-Endpunkt, der Requests aus
  LangChain entgegennimmt, Authentifizierung prüft und an n8n weiterleitet.
- **Event Stream**: Optionaler Redis Stream (reuse aus `deploy/automation/n8n`),
  um Statusänderungen zurück in LangChain zu pushen.

## 2. Authentifizierung & Sicherheit

- Eingehende Agenten-Calls signieren (`X-Nova-Signature` HMAC Header).
- n8n Webhook mit Basic Auth absichern (siehe `deploy/automation/n8n/docker-compose.yml`).
- Secrets zentral in `.env` verwalten: `N8N_WEBHOOK_URL`, `N8N_WEBHOOK_USER`,
  `N8N_WEBHOOK_PASSWORD`, `NOVA_BRIDGE_TOKEN`.

## 3. Referenz-API (Bridge Service)

| Methode | Pfad | Beschreibung |
| --- | --- | --- |
| `POST` | `/workflows/summary-refresh` | Trigger für den bestehenden Teams Reporting Workflow. |
| `POST` | `/workflows/finetune-status` | Legt Statusupdates zum Finetuning im Event Stream ab. |
| `GET` | `/health` | Healthcheck für Chronos Monitoring. |

Beispiel-Request für Orion:

```json
{
  "workflow": "finetune-status",
  "payload": {
    "run_id": "sophia-finetune-dev",
    "stage": "evaluation",
    "metrics": {
      "bleu": 36.4,
      "rouge_l": 0.41,
      "win_rate": 0.67
    }
  }
}
```

## 4. Schrittplan

1. **Bridge Skeleton** – Repository `deploy/automation/bridge/` anlegen
   (FastAPI + uvicorn, Dockerfile, Compose Override).
2. **n8n Workflow erweitern** – Webhook `finetune-status` ergänzen, der die Werte
   nach Teams pusht und in PostgreSQL persistiert.
3. **LangChain Tooling** – Neues Tool `FinetuneStatusTool` in `nova/agents`
   registrieren, welches obiges JSON Payload sendet.
4. **Monitoring** – Alert-Regeln (`python -m nova alerts --dry-run`) aktualisieren,
   sodass fehlende Statusupdates nach 30 Minuten ein Warning auslösen.

## 5. Offene Entscheidungen

- [ ] Event Stream via Redis Streams oder Kafka realisieren?
- [ ] Auth-Mechanismus auf OAuth 2.0 erweitern?
- [ ] Webhook Rate Limiting (Cloudflare / Traefik) nötig?
