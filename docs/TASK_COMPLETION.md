# Task Coverage Summary

The blueprint catalogue now covers every task from `TASKS.md` through
dedicated agent specifications. The table below lists the mapping between
the original requirements and the blueprint task identifiers.

| Agent   | TASKS.md requirement                                                | Blueprint task name             |
|---------|---------------------------------------------------------------------|---------------------------------|
| Nova    | DGX/Spark hardware validation                                       | `infrastructure-audit`          |
|         | Container & orchestration tooling                                   | `container-platform`            |
|         | Secure remote access (WireGuard/OpenVPN)                            | `secure-remote-access`          |
|         | Security & privacy audits                                           | `security-audit`                |
|         | Backup & recovery strategy                                          | `backup-recovery`               |
| Orion   | Install NVIDIA NeMo                                                 | `nemo-installation`             |
|         | Select LLM (Llama 3/Mixtral etc.)                                   | `llm-selection`                 |
|         | Finetune LLM for Sophia                                             | `finetuning-protocol`           |
|         | LangChain/Agent framework integration                               | `langchain-integration`         |
| Lumina  | Install & configure MongoDB and PostgreSQL                          | `relational-databases`          |
|         | Build vector database (Pinecone/FAISS)                              | `vector-knowledge-base`         |
| Echo    | Install NVIDIA ACE stack (Riva, Audio2Face, NeMo)                   | `ace-toolkit-setup`             |
|         | Avatar pipeline (Omniverse, Audio2Face, Riva)                       | `avatar-pipeline`               |
|         | Sophia avatar integration into Teams                                | `teams-integration`             |
| Chronos | Install & configure n8n                                             | `bootstrap-n8n`                 |
|         | LangChain/n8n automation pipelines                                  | `agent-pipelines`               |
|         | Data flywheel for self-improving processes                          | `data-flywheel`                 |
|         | CI/CD pipeline with GitHub Enterprise & Kubernetes                  | `continuous-delivery`           |
| Aura    | Install Grafana                                                     | `install-grafana`               |
|         | Develop & integrate the LUX dashboard                               | `lux-dashboard`                 |
|         | Optimise energy/resource efficiency                                 | `efficiency-optimisation`       |
|         | Visualise emotional & sentiment feedback                            | `emotional-feedback-visualisation` |

Running ``python -m nova orchestrate`` executes all tasks in these
blueprints and emits a Markdown report stored at
``$NOVA_HOME/reports/nova-test-report.md`` that documents the successful
completion of the simulated workflows.
