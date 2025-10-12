"""Utility script to orchestrate Sophia's NeMo finetuning workflow.

The helper focuses on configuration validation and planning. It reads the
baseline LoRA settings from ``config/finetune/lora.yaml`` (or a user supplied
path), performs lightweight sanity checks and generates a Markdown hand-off
plan for Orion and Chronos. The actual training logic is intentionally out of
scope – execution happens on dedicated infrastructure once the prerequisites
have been verified.
"""

from __future__ import annotations

import argparse
import importlib.util
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


class ConfigError(RuntimeError):
    """Raised when the finetuning configuration cannot be parsed."""


if importlib.util.find_spec("yaml") is not None:  # pragma: no cover - optional dep
    import yaml  # type: ignore
else:  # pragma: no cover - optional dep fallback
    yaml = None  # type: ignore


@dataclass(slots=True)
class DatasetConfig:
    """Locations of the curated Sophia datasets."""

    train: str
    validation: str
    eval: str


@dataclass(slots=True)
class Hyperparameters:
    """Training hyperparameters with basic validation helpers."""

    learning_rate: float
    weight_decay: float
    warmup_ratio: float
    max_steps: int
    epochs: int
    batch_size: int
    gradient_accumulation_steps: int
    gradient_checkpointing: bool
    max_sequence_length: int


@dataclass(slots=True)
class LoRASettings:
    """LoRA/PEFT adapter configuration."""

    r: int
    alpha: int
    dropout: float
    target_modules: list[str]


@dataclass(slots=True)
class OptimizerSettings:
    """Definition of the optimisation strategy."""

    type: str
    beta1: float
    beta2: float
    epsilon: float
    scheduler: str


@dataclass(slots=True)
class EvaluationSettings:
    """Evaluation cadence and metrics."""

    interval_steps: int
    metrics: list[str]
    human_review_batch_size: int


@dataclass(slots=True)
class TrackingSettings:
    """Experiment tracking configuration."""

    service: str
    project: str
    run_name: str
    tags: list[str]


@dataclass(slots=True)
class ArtifactSettings:
    """Artefact output control."""

    output_dir: str
    checkpoint_interval: int
    keep_last: int


@dataclass(slots=True)
class RuntimeSettings:
    """Execution environment toggles."""

    devices: str
    tensor_parallelism: int
    pipeline_parallelism: int
    precision_policy: str


@dataclass(slots=True)
class FinetuneConfig:
    """Complete configuration for a NeMo finetuning run."""

    base_model: str
    precision: str
    seed: int
    datasets: DatasetConfig
    hyperparameters: Hyperparameters
    lora: LoRASettings
    optimizer: OptimizerSettings
    evaluation: EvaluationSettings
    tracking: TrackingSettings
    artifacts: ArtifactSettings
    runtime: RuntimeSettings

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any]) -> "FinetuneConfig":
        """Build an instance from a dictionary structure."""

        def _require(section: str, expected_type: type) -> Mapping[str, Any]:
            value = mapping.get(section)
            if not isinstance(value, Mapping):
                raise ConfigError(f"Section '{section}' is missing or invalid")
            return value

        datasets_raw = _require("datasets", Mapping)
        hyperparameters_raw = _require("hyperparameters", Mapping)
        lora_raw = _require("lora", Mapping)
        optimizer_raw = _require("optimizer", Mapping)
        evaluation_raw = _require("evaluation", Mapping)
        tracking_raw = _require("tracking", Mapping)
        artifacts_raw = _require("artifacts", Mapping)
        runtime_raw = _require("runtime", Mapping)

        return cls(
            base_model=str(mapping.get("base_model", "")),
            precision=str(mapping.get("precision", "bf16")),
            seed=int(mapping.get("seed", 42)),
            datasets=DatasetConfig(
                train=str(datasets_raw.get("train", "")),
                validation=str(datasets_raw.get("validation", "")),
                eval=str(datasets_raw.get("eval", "")),
            ),
            hyperparameters=Hyperparameters(
                learning_rate=float(hyperparameters_raw.get("learning_rate", 0.0)),
                weight_decay=float(hyperparameters_raw.get("weight_decay", 0.0)),
                warmup_ratio=float(hyperparameters_raw.get("warmup_ratio", 0.0)),
                max_steps=int(hyperparameters_raw.get("max_steps", 0)),
                epochs=int(hyperparameters_raw.get("epochs", 0)),
                batch_size=int(hyperparameters_raw.get("batch_size", 0)),
                gradient_accumulation_steps=int(
                    hyperparameters_raw.get("gradient_accumulation_steps", 1)
                ),
                gradient_checkpointing=bool(
                    hyperparameters_raw.get("gradient_checkpointing", False)
                ),
                max_sequence_length=int(
                    hyperparameters_raw.get("max_sequence_length", 2048)
                ),
            ),
            lora=LoRASettings(
                r=int(lora_raw.get("r", 0)),
                alpha=int(lora_raw.get("alpha", 0)),
                dropout=float(lora_raw.get("dropout", 0.0)),
                target_modules=[str(value) for value in lora_raw.get("target_modules", [])],
            ),
            optimizer=OptimizerSettings(
                type=str(optimizer_raw.get("type", "adamw")),
                beta1=float(optimizer_raw.get("beta1", 0.9)),
                beta2=float(optimizer_raw.get("beta2", 0.999)),
                epsilon=float(optimizer_raw.get("epsilon", 1e-8)),
                scheduler=str(optimizer_raw.get("scheduler", "cosine")),
            ),
            evaluation=EvaluationSettings(
                interval_steps=int(evaluation_raw.get("interval_steps", 0)),
                metrics=[str(value) for value in evaluation_raw.get("metrics", [])],
                human_review_batch_size=int(
                    evaluation_raw.get("human_review_batch_size", 0)
                ),
            ),
            tracking=TrackingSettings(
                service=str(tracking_raw.get("service", "")),
                project=str(tracking_raw.get("project", "")),
                run_name=str(tracking_raw.get("run_name", "")),
                tags=[str(value) for value in tracking_raw.get("tags", [])],
            ),
            artifacts=ArtifactSettings(
                output_dir=str(artifacts_raw.get("output_dir", "")),
                checkpoint_interval=int(artifacts_raw.get("checkpoint_interval", 0)),
                keep_last=int(artifacts_raw.get("keep_last", 0)),
            ),
            runtime=RuntimeSettings(
                devices=str(runtime_raw.get("devices", "auto")),
                tensor_parallelism=int(runtime_raw.get("tensor_parallelism", 1)),
                pipeline_parallelism=int(runtime_raw.get("pipeline_parallelism", 1)),
                precision_policy=str(runtime_raw.get("precision_policy", "auto")),
            ),
        )


@dataclass(slots=True)
class ValidationIssue:
    """Represents a validation finding for the configuration."""

    field: str
    message: str
    severity: str = "error"


@dataclass(slots=True)
class ValidationReport:
    """Aggregated validation issues."""

    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(issue.severity != "error" for issue in self.issues)

    def add(self, field: str, message: str, severity: str = "error") -> None:
        self.issues.append(ValidationIssue(field=field, message=message, severity=severity))


@dataclass(slots=True)
class TrainingStep:
    """A discrete step within the operational finetuning workflow."""

    identifier: str
    title: str
    description: str
    depends_on: list[str] = field(default_factory=list)


@dataclass(slots=True)
class TrainingPlan:
    """High-level finetuning plan derived from the configuration."""

    config: FinetuneConfig
    validation: ValidationReport
    steps: list[TrainingStep]

    def to_markdown(self) -> str:
        """Render the plan as Markdown suitable for the orchestration journal."""

        cfg = self.config
        lines: list[str] = ["# Sophia NeMo Finetuning Dry-Run", ""]

        lines.append("## Konfigurationsüberblick")
        lines.append(f"- Basismodell: `{cfg.base_model}`")
        lines.append(f"- Präzision: `{cfg.precision}`")
        lines.append(f"- Seed: `{cfg.seed}`")
        lines.append(f"- Ausgabeordner: `{cfg.artifacts.output_dir}`")
        lines.append(
            "- Datasets: Train=`{}`, Validation=`{}`, Eval=`{}`".format(
                cfg.datasets.train, cfg.datasets.validation, cfg.datasets.eval
            )
        )
        lines.append(
            "- Tracking: {} / {} (Run: `{}`)".format(
                cfg.tracking.service, cfg.tracking.project, cfg.tracking.run_name
            )
        )
        lines.append("- Tags: " + ", ".join(f"`{tag}`" for tag in cfg.tracking.tags) or "-")
        lines.append("")

        lines.append("## Validierungsstatus")
        if not self.validation.issues:
            lines.append("- ✅ Keine Findings – Konfiguration sieht konsistent aus.")
        else:
            for issue in self.validation.issues:
                emoji = "⚠️" if issue.severity == "warning" else "❌"
                lines.append(f"- {emoji} **{issue.field}** – {issue.message}")
        lines.append("")

        lines.append("## Trainingsschritte")
        for index, step in enumerate(self.steps, start=1):
            lines.append(f"{index}. **{step.title}** (`{step.identifier}`)")
            lines.append(f"   - Beschreibung: {step.description}")
            if step.depends_on:
                dependency_text = ", ".join(f"`{dependency}`" for dependency in step.depends_on)
                lines.append(f"   - Abhängigkeiten: {dependency_text}")
            lines.append("")

        lines.append("## Hyperparameter Snapshot")
        hp_dict = asdict(cfg.hyperparameters)
        for key, value in hp_dict.items():
            lines.append(f"- {key}: {value}")
        lines.append("")

        lines.append("## Operative Hinweise")
        lines.append(
            "- Skriptaufruf: `python scripts/finetune_nemo.py --config config/finetune/lora.yaml "
            "--plan orchestration_journal/models/finetune_runbook.md`"
        )
        lines.append(
            "- Führe vor Produktivläufen einen GPU-Health-Check via `python -m nova setup --dgx-check` durch."
        )
        lines.append(
            "- Für Infrastrukturänderungen die jeweiligen Tickets in `orchestration_journal/updates/` ergänzen."
        )

        return "\n".join(lines).strip() + "\n"


def _detect_container_type(entries: Sequence[tuple[int, str]], index: int, indent: int) -> str:
    for next_indent, next_content in entries[index + 1 :]:
        if next_indent <= indent:
            break
        return "list" if next_content.startswith("- ") else "dict"
    return "dict"


def _convert_scalar(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none"}:
        return None
    if (value.startswith("\"") and value.endswith("\"")) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    try:
        if value.startswith("0") and not value.startswith("0.") and value != "0":
            return value  # keep leading-zero values as strings
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


def _minimal_yaml_load(text: str) -> dict[str, Any]:
    entries: list[tuple[int, str]] = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        entries.append((indent, stripped))

    root: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, root)]

    for index, (indent, content) in enumerate(entries):
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]

        if content.startswith("- "):
            if not isinstance(parent, list):
                raise ConfigError("Found list item without a list parent in fallback YAML parser")
            value_text = content[2:].strip()
            parent.append(_convert_scalar(value_text))
            continue

        if ":" not in content:
            raise ConfigError(f"Cannot parse line: {content}")

        key, value = content.split(":", 1)
        key = key.strip()
        value = value.strip()

        if value == "":
            container_type = _detect_container_type(entries, index, indent)
            new_container: Any = [] if container_type == "list" else {}
            if not isinstance(parent, dict):
                raise ConfigError("Nested block is not allowed in the current context")
            parent[key] = new_container
            stack.append((indent, new_container))
        else:
            if not isinstance(parent, dict):
                raise ConfigError("Scalar value is not allowed in the current context")
            parent[key] = _convert_scalar(value)

    return root


def load_config_mapping(path: Path) -> Mapping[str, Any]:
    """Load the configuration file into a dictionary."""

    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        loaded = yaml.safe_load(text)
    else:
        loaded = _minimal_yaml_load(text)
    if not isinstance(loaded, Mapping):
        raise ConfigError("Configuration root must be a mapping")
    return loaded


def validate_config(config: FinetuneConfig) -> ValidationReport:
    """Perform lightweight sanity checks before launching training."""

    report = ValidationReport()

    if not config.base_model:
        report.add("base_model", "Basismodell ist nicht gesetzt.")
    if config.hyperparameters.learning_rate <= 0:
        report.add("hyperparameters.learning_rate", "Learning Rate muss > 0 sein.")
    if config.hyperparameters.batch_size <= 0:
        report.add("hyperparameters.batch_size", "Batch-Größe muss > 0 sein.")
    if config.hyperparameters.max_steps <= 0 and config.hyperparameters.epochs <= 0:
        report.add(
            "hyperparameters.max_steps",
            "Entweder `max_steps` oder `epochs` muss > 0 sein.",
        )
    if config.lora.r <= 0:
        report.add("lora.r", "LoRA-Rank muss > 0 sein.")
    if not config.lora.target_modules:
        report.add("lora.target_modules", "Mindestens ein Zielmodul muss angegeben werden.")
    if config.evaluation.interval_steps <= 0:
        report.add(
            "evaluation.interval_steps",
            "Evaluationsintervall muss > 0 sein.",
            severity="warning",
        )
    if config.artifacts.checkpoint_interval <= 0:
        report.add(
            "artifacts.checkpoint_interval",
            "Checkpoint-Intervall sollte > 0 sein.",
            severity="warning",
        )
    if config.runtime.tensor_parallelism < 1:
        report.add(
            "runtime.tensor_parallelism",
            "Tensor-Parallelism muss >= 1 sein.",
        )
    if config.runtime.pipeline_parallelism < 1:
        report.add(
            "runtime.pipeline_parallelism",
            "Pipeline-Parallelism muss >= 1 sein.",
        )
    dataset_paths = [config.datasets.train, config.datasets.validation, config.datasets.eval]
    if len({path for path in dataset_paths if path}) != len(dataset_paths):
        report.add(
            "datasets",
            "Train-, Validation- und Eval-Pfade müssen eindeutig sein.",
            severity="warning",
        )

    return report


def build_training_steps(config: FinetuneConfig) -> list[TrainingStep]:
    """Construct the canonical sequence of operational steps."""

    return [
        TrainingStep(
            identifier="data_ingestion",
            title="Dateninventur & Qualitätssicherung",
            description=(
                "Verifiziere die in der Konfiguration referenzierten Datensätze, "
                "inklusive DSGVO-Freigaben und Schema-Prüfungen."
            ),
        ),
        TrainingStep(
            identifier="environment_setup",
            title="NeMo Umgebung vorbereiten",
            description=(
                "Provisioniere Container/venv mit PyTorch, NeMo und Abhängigkeiten. "
                "Aktualisiere CUDA/TensorRT Profile auf der DGX."
            ),
            depends_on=["data_ingestion"],
        ),
        TrainingStep(
            identifier="lora_compile",
            title="LoRA Adapter konfigurieren",
            description=(
                "Überführe die LoRA-Parameter in NeMo-konforme Konfigurationen und "
                "prüfe Zielmodule auf Modellkompatibilität."
            ),
            depends_on=["environment_setup"],
        ),
        TrainingStep(
            identifier="training_run",
            title="Finetuning ausführen",
            description=(
                "Starte den Trainingsjob, überwache GPU-Auslastung und exportiere "
                "Checkpoints gemäß Intervall.")
            ,
            depends_on=["lora_compile"],
        ),
        TrainingStep(
            identifier="evaluation",
            title="Evaluierung & QA",
            description=(
                "Berechne definierte Metriken, triggere Human-Review-Stichproben und "
                "bereite Regressionstests vor."
            ),
            depends_on=["training_run"],
        ),
        TrainingStep(
            identifier="handover",
            title="Deployment & Übergabe",
            description=(
                "Versioniere Artefakte, aktualisiere Monitoring-Hooks und synchronisiere "
                "Status in Tasks & Progress Reports."
            ),
            depends_on=["evaluation"],
        ),
    ]


def render_plan(config: FinetuneConfig) -> TrainingPlan:
    validation = validate_config(config)
    steps = build_training_steps(config)
    return TrainingPlan(config=config, validation=validation, steps=steps)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate NeMo finetuning plans for Sophia")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/finetune/lora.yaml"),
        help="Pfad zur YAML-Konfiguration (Default: config/finetune/lora.yaml)",
    )
    parser.add_argument(
        "--plan",
        type=Path,
        default=None,
        help="Optionaler Ausgabepfad für den Markdown-Plan.",
    )
    parser.add_argument(
        "--silent",
        action="store_true",
        help="Unterdrückt die Ausgabe auf STDOUT, wenn ein Plan geschrieben wird.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    mapping = load_config_mapping(args.config)
    config = FinetuneConfig.from_mapping(mapping)
    plan = render_plan(config)
    markdown = plan.to_markdown()

    if args.plan is not None:
        args.plan.parent.mkdir(parents=True, exist_ok=True)
        args.plan.write_text(markdown, encoding="utf-8")
    if not args.silent:
        print(markdown)

    return 0 if plan.validation.ok else 2


if __name__ == "__main__":  # pragma: no cover - manual execution entry
    raise SystemExit(main())
