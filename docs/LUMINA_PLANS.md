# Lumina Deployment Plans

The ``lumina`` module provides reusable deployment plans that map directly to
Lumina's responsibilities in the Spark Sophia ecosystem. Each function returns
an instance of :class:`lumina.DeploymentPlan` which can be serialised via
``to_dict()`` and consumed by automation tooling.

## MongoDB

- Updates package metadata prior to installation.
- Installs the community edition binaries.
- Enables and starts the ``mongod`` service.
- Defines recommended configuration values (bind IP, replica set, storage
  engine).
- Supplies verification commands for post-install validation.

## PostgreSQL

- Installs PostgreSQL server and common extensions.
- Enables auto-start of the service and provisions a ``sophia`` superuser.
- Proposes performance-related configuration defaults.
- Provides SQL commands for connectivity and database listing checks.

## Vector Databases

Two backends are currently supported:

- **Pinecone** – installs the SDK, configures the project, and provisions a
  ``sophia-embeddings`` index using cosine similarity.
- **FAISS** – installs the necessary system dependencies and Python package,
  then prepares a baseline index for experimentation.

Both plans expose verification commands to confirm that the index is reachable
and operating as expected. Attempts to request an unsupported backend raise a
``ValueError`` to signal misconfiguration early.
