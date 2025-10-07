"""Blueprint generator module for Nova Blueprints."""

from __future__ import annotations

from typing import Callable, Dict

from .models import AgentBlueprint, AgentTaskSpec, build_blueprint


def _build_monitoring_blueprint() -> AgentBlueprint:
    return build_blueprint(
        agent_type="aura",
        description=(
            "Observability and insights specialist responsible for telemetry, "
            "dashboards and experiential feedback loops."
        ),
        tasks=[
            AgentTaskSpec(
                name="install-grafana",
                goal="Provide visual telemetry via Grafana dashboards.",
                steps=[
                    "Verify Grafana binaries are available or download the package.",
                    "Generate baseline configuration files for dashboards.",
                    "Register default data sources for CPU, GPU and latency metrics.",
                ],
                outputs=[
                    "Grafana configuration file",
                    "Dashboards for system metrics",
                ],
            ),
            AgentTaskSpec(
                name="emotional-feedback-visualisation",
                goal="Expose user sentiment telemetry on the monitoring stack.",
                steps=[
                    "Collect recent sentiment snapshots from the feedback store.",
                    "Transform the snapshots into Grafana compatible panels.",
                    "Publish an insights report summarising notable trends.",
                ],
                outputs=["Weekly emotional state summary"],
            ),
        ],
    )


def _build_workflow_blueprint() -> AgentBlueprint:
    return build_blueprint(
        agent_type="chronos",
        description=(
            "Automation engineer coordinating pipelines, retraining loops and "
            "deployment lifecycles."
        ),
        tasks=[
            AgentTaskSpec(
                name="bootstrap-n8n",
                goal="Provision an n8n instance for workflow orchestration.",
                steps=[
                    "Validate docker environment readiness.",
                    "Compose a container definition for n8n.",
                    "Store generated manifests for future deployment.",
                ],
                outputs=["n8n docker compose manifest"],
            ),
            AgentTaskSpec(
                name="continuous-delivery",
                goal="Prepare CI/CD configuration for agent services.",
                steps=[
                    "Generate GitHub Actions workflow for automated testing.",
                    "Create Kubernetes deployment templates for staging.",
                    "Register deployment artefacts with the release catalogue.",
                ],
                outputs=[
                    "CI workflow definition",
                    "Kubernetes deployment templates",
                ],
            ),
        ],
    )


def _build_avatar_blueprint() -> AgentBlueprint:
    return build_blueprint(
        agent_type="echo",
        description="Avatar and experiential interaction specialist.",
        tasks=[
            AgentTaskSpec(
                name="ace-toolkit-setup",
                goal="Configure NVIDIA ACE dependencies for avatar streaming.",
                steps=[
                    "Enumerate ACE toolkit components and validate versions.",
                    "Generate configuration templates for Riva and Audio2Face.",
                    "Produce a readiness checklist for deployment teams.",
                ],
                outputs=["ACE readiness checklist"],
            ),
            AgentTaskSpec(
                name="teams-integration",
                goal="Create a Teams manifest for embedding the Sophia avatar.",
                steps=[
                    "Draft Teams application manifest metadata.",
                    "Outline required OAuth scopes and permissions.",
                    "Publish integration guidelines for operators.",
                ],
                outputs=["Teams integration guide"],
            ),
        ],
    )


def _build_modelops_blueprint() -> AgentBlueprint:
    return build_blueprint(
        agent_type="orion",
        description="Model operations expert providing LLM lifecycle management.",
        tasks=[
            AgentTaskSpec(
                name="nemo-installation",
                goal="Ensure NeMo tooling is prepared for experimentation.",
                steps=[
                    "Inspect python environment for compatibility.",
                    "Record the command set required for installation.",
                    "Simulate package download to validate connectivity.",
                ],
                outputs=["NeMo installation plan"],
            ),
            AgentTaskSpec(
                name="finetuning-protocol",
                goal="Document the finetuning workflow for Sophia specific data.",
                steps=[
                    "Define dataset requirements and validation rules.",
                    "Describe the training command template.",
                    "List evaluation metrics for acceptance.",
                ],
                outputs=["Finetuning playbook"],
            ),
        ],
    )


def _build_infrastructure_blueprint() -> AgentBlueprint:
    return build_blueprint(
        agent_type="nova",
        description="Chief agent coordinating core infrastructure readiness tasks.",
        tasks=[
            AgentTaskSpec(
                name="infrastructure-audit",
                goal="Validate DGX/Spark Sophia hardware and operating system state.",
                steps=[
                    "Collect CPU, GPU and network adapter inventory details.",
                    "Verify driver versions against approved compatibility matrix.",
                    "Capture operating system tuning applied to the DGX nodes.",
                ],
                outputs=["Infrastructure readiness report"],
            ),
            AgentTaskSpec(
                name="container-platform",
                goal="Prepare container and orchestration tooling for deployment teams.",
                steps=[
                    "Check Docker installation prerequisites and runtime configuration.",
                    "Generate Kubernetes bootstrap manifests for the control plane.",
                    "Document post-install validation commands for operators.",
                ],
                outputs=["Container platform activation guide"],
            ),
            AgentTaskSpec(
                name="secure-remote-access",
                goal="Enable VPN and remote access pathways using WireGuard or OpenVPN.",
                steps=[
                    "Draft WireGuard and OpenVPN configuration templates.",
                    "Outline firewall adjustments required for remote connectivity.",
                    "Distribute credential rotation policy for remote operators.",
                ],
                outputs=["Remote access configuration pack"],
            ),
            AgentTaskSpec(
                name="security-audit",
                goal="Conduct security and privacy audits across the platform.",
                steps=[
                    "Assess firewall posture and document exposed services.",
                    "List anti-virus and OPA policy enforcement checkpoints.",
                    "Compile remediation recommendations for identified gaps.",
                ],
                outputs=["Security and privacy audit findings"],
            ),
            AgentTaskSpec(
                name="backup-recovery",
                goal="Outline data and model backup as well as recovery strategies.",
                steps=[
                    "Identify critical datasets and models requiring protection.",
                    "Define backup schedules and storage retention targets.",
                    "Publish recovery runbook including validation drills.",
                ],
                outputs=["Backup and recovery playbook"],
            ),
        ],
    )


def _build_data_blueprint() -> AgentBlueprint:
    return build_blueprint(
        agent_type="lumina",
        description="Database and storage expert ensuring resilient data services.",
        tasks=[
            AgentTaskSpec(
                name="relational-databases",
                goal="Provision MongoDB and PostgreSQL instances for the platform.",
                steps=[
                    "Prepare configuration defaults for MongoDB and PostgreSQL clusters.",
                    "Outline deployment procedures for development and production tiers.",
                    "Record health check commands for both database engines.",
                ],
                outputs=["Database configuration bundle"],
            ),
            AgentTaskSpec(
                name="vector-knowledge-base",
                goal="Set up the vector store backing Sophia's knowledge base.",
                steps=[
                    "Compare Pinecone and FAISS deployment considerations.",
                    "Design indexing pipeline for embeddings ingestion.",
                    "Document query patterns and latency expectations.",
                ],
                outputs=["Vector store deployment guide"],
            ),
        ],
    )


_BLUEPRINT_BUILDERS: Dict[str, Callable[[], AgentBlueprint]] = {
    "aura": _build_monitoring_blueprint,
    "chronos": _build_workflow_blueprint,
    "echo": _build_avatar_blueprint,
    "lumina": _build_data_blueprint,
    "nova": _build_infrastructure_blueprint,
    "orion": _build_modelops_blueprint,
}


def generate_blueprint(agent_type: str) -> AgentBlueprint:
    """Return a blueprint for the specified agent type."""

    key = agent_type.lower()
    builder = _BLUEPRINT_BUILDERS.get(key)
    if builder is not None:
        return builder()
    return build_blueprint(
        agent_type=key,
        description="Unknown agent type",
        tasks=[],
    )


def list_blueprints() -> list[str]:
    """List available blueprint names."""

    return sorted(_BLUEPRINT_BUILDERS.keys())


def list_available_blueprints() -> list[str]:
    """Alias for backwards compatibility."""

    return list_blueprints()


def create_blueprint(agent_type: str) -> AgentBlueprint:
    """Alias maintained for older imports."""

    return generate_blueprint(agent_type)


__all__ = [
    "AgentBlueprint",
    "AgentTaskSpec",
    "create_blueprint",
    "generate_blueprint",
    "list_available_blueprints",
    "list_blueprints",
]
