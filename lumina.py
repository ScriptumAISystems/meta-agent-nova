"""Utilities for Lumina, the storage and data services specialist."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List


@dataclass(slots=True)
class InstallationStep:
    """Single step within an installation plan."""

    name: str
    command: str
    description: str

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name, "command": self.command, "description": self.description}


@dataclass(slots=True)
class DeploymentPlan:
    """Structured representation of a deployment procedure."""

    service: str
    steps: List[InstallationStep] = field(default_factory=list)
    configuration: Dict[str, str] = field(default_factory=dict)
    verification: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "service": self.service,
            "steps": [step.to_dict() for step in self.steps],
            "configuration": dict(self.configuration),
            "verification": list(self.verification),
        }


def _build_installation_steps(steps: Iterable[tuple[str, str, str]]) -> List[InstallationStep]:
    return [InstallationStep(name=name, command=command, description=description) for name, command, description in steps]


def install_mongodb() -> DeploymentPlan:
    """Return a deployment plan for MongoDB."""

    steps = _build_installation_steps(
        [
            ("update-packages", "sudo apt-get update", "Refresh package metadata to ensure latest releases."),
            (
                "install-mongodb",
                "sudo apt-get install -y mongodb-org",
                "Install the MongoDB community edition binaries.",
            ),
            (
                "enable-service",
                "sudo systemctl enable --now mongod",
                "Start the MongoDB service and enable auto-start on boot.",
            ),
        ]
    )
    config = {
        "bind_ip": "0.0.0.0",
        "replica_set": "sophia-rs",
        "storage_engine": "wiredTiger",
    }
    verification = [
        "mongo --eval 'db.runCommand({ connectionStatus: 1 })'",
        "rs.status()",
    ]
    return DeploymentPlan(service="mongodb", steps=steps, configuration=config, verification=verification)


def install_postgresql() -> DeploymentPlan:
    """Return a deployment plan for PostgreSQL."""

    steps = _build_installation_steps(
        [
            ("update-packages", "sudo apt-get update", "Refresh package metadata to ensure latest releases."),
            (
                "install-postgresql",
                "sudo apt-get install -y postgresql postgresql-contrib",
                "Install PostgreSQL server including common extensions.",
            ),
            (
                "enable-service",
                "sudo systemctl enable --now postgresql",
                "Start PostgreSQL and enable auto-start on boot.",
            ),
            (
                "create-role",
                "sudo -u postgres createuser --superuser sophia",
                "Provision a superuser account for orchestration tasks.",
            ),
        ]
    )
    config = {
        "listen_addresses": "*",
        "max_connections": "200",
        "shared_buffers": "1GB",
    }
    verification = [
        "psql --command 'SELECT version();'",
        "sudo -u postgres psql -c '\\l'",
    ]
    return DeploymentPlan(service="postgresql", steps=steps, configuration=config, verification=verification)


def setup_vector_db(db_type: str) -> DeploymentPlan:
    """Create a deployment plan for the requested vector database type."""

    if not db_type:
        raise ValueError("db_type must be provided")

    key = db_type.strip().lower()
    if key == "pinecone":
        steps = _build_installation_steps(
            [
                (
                    "install-sdk",
                    "pip install --upgrade pinecone-client",
                    "Install the Pinecone Python SDK for index management.",
                ),
                (
                    "configure-project",
                    "pinecone configure --api-key $PINECONE_API_KEY --environment us-west1-gcp",
                    "Link the project credentials and default environment.",
                ),
                (
                    "create-index",
                    "python -m pinecone.scripts.create_index --name sophia-embeddings --dimension 4096",
                    "Provision an index tailored for Sophia embeddings.",
                ),
            ]
        )
        config = {
            "metric": "cosine",
            "pods": "1",
            "replicas": "1",
        }
        verification = [
            "pinecone describe-index --name sophia-embeddings",
            "pinecone list-indexes",
        ]
        return DeploymentPlan(service="pinecone", steps=steps, configuration=config, verification=verification)
    if key == "faiss":
        steps = _build_installation_steps(
            [
                (
                    "install-deps",
                    "sudo apt-get install -y libopenblas-dev libomp-dev",
                    "Install BLAS and OpenMP dependencies required by FAISS.",
                ),
                (
                    "install-faiss",
                    "pip install faiss-cpu",
                    "Install the FAISS CPU package via pip.",
                ),
                (
                    "prepare-index",
                    "python -m faiss.contrib.tutorials.build_index --dimension 4096 --output sophia.index",
                    "Generate a baseline index file for testing queries.",
                ),
            ]
        )
        config = {
            "index_type": "IVF4096,Flat",
            "training_samples": "50000",
        }
        verification = [
            "python -m faiss.contrib.tutorials.query_index --index sophia.index --queries sample.npy",
        ]
        return DeploymentPlan(service="faiss", steps=steps, configuration=config, verification=verification)

    raise ValueError(f"Unsupported vector database type: {db_type}")


__all__ = [
    "DeploymentPlan",
    "InstallationStep",
    "install_mongodb",
    "install_postgresql",
    "setup_vector_db",
]
