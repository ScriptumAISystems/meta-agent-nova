"""Networking and remote access planning utilities for Nova."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List


_SUPPORTED_VPN_TYPES = {"wireguard", "openvpn"}


@dataclass(slots=True)
class VPNPlan:
    """Structured view of the VPN rollout playbook."""

    vpn_type: str
    summary: str
    prerequisites: List[str] = field(default_factory=list)
    setup_steps: List[str] = field(default_factory=list)
    validation_steps: List[str] = field(default_factory=list)
    hardening_steps: List[str] = field(default_factory=list)
    integration_notes: List[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        lines: list[str] = [f"# {self.vpn_type.title()} Remote Access Plan", ""]
        lines.append("## Zusammenfassung")
        lines.append(self.summary)
        lines.append("")

        def render_section(title: str, items: Iterable[str]) -> None:
            entries = list(items)
            if not entries:
                return
            lines.append(f"## {title}")
            for entry in entries:
                lines.append(f"- {entry}")
            lines.append("")

        render_section("Voraussetzungen", self.prerequisites)
        render_section("Installationsschritte", self.setup_steps)
        render_section("Validierung", self.validation_steps)
        render_section("Härtung & Betrieb", self.hardening_steps)
        render_section("Integration in Nova", self.integration_notes)

        return "\n".join(lines).strip()


def _wireguard_plan() -> VPNPlan:
    summary = (
        "Richtet einen WireGuard-Tunnel für sicheren Fernzugriff auf die DGX/Spark-"
        "Umgebung ein. Alle Konfigurationsdateien werden versioniert und über die "
        "Nova-Dokumentation referenziert."
    )

    prerequisites = [
        "Ubuntu 22.04 LTS oder kompatible Distribution mit Root-/Sudo-Zugriff.",
        "Outbound-Zugriff auf `https://ppa.launchpadcontent.net/wireguard`.",
        "Firewall-Regeln für UDP-Port 51820 (anpassbar) vorbereitet.",
    ]

    setup_steps = [
        "`sudo apt-get update && sudo apt-get install -y wireguard wireguard-tools`.",
        "Server-Keys erzeugen: `wg genkey | tee /etc/wireguard/privatekey | wg pubkey > /etc/wireguard/publickey`.",
        "Interface-Datei `/etc/wireguard/wg0.conf` gemäß Template aus `docs/FOUNDATION_VPN_SETUP.md` anlegen.",
        "Netzwerk-Forwarding aktivieren (`/etc/sysctl.d/99-wireguard.conf`) und `sudo sysctl --system` ausführen.",
        "Dienst starten: `sudo systemctl enable --now wg-quick@wg0`.",
    ]

    validation_steps = [
        "Tunnelstatus prüfen: `sudo wg show` und `ip addr show wg0`.",
        "Konnektivität testen: `ping` auf eine interne Adresse und `python -m nova containers` über den Tunnel ausführen.",
        "Optional Smoke-Test mit Beispiel-Client (`wg-quick up`) und Prüfung der Protokolle in `/var/log/syslog`.",
    ]

    hardening_steps = [
        "Private Keys mit `chmod 600` absichern und Zugriffe auditieren.",
        "`ufw`/`nftables` auf Tunnel-Subnetz beschränken, Logging aktivieren.",
        "Peers mit Keepalive und IP-Adressbeschränkungen versehen, Offboarding-Prozess dokumentieren.",
    ]

    integration_notes = [
        "Konfigurationspfad im Orchestrierungstagebuch (`orchestration_journal/vpn/`) dokumentieren.",
        "Status in `Agenten_Aufgaben_Uebersicht.csv` auf 'Abgeschlossen' setzen, sobald Validierung erfolgreich.",
        "Monitoring-Hooks für Tunnelverfügbarkeit in `python -m nova alerts --dry-run` aufnehmen.",
    ]

    return VPNPlan(
        vpn_type="WireGuard",
        summary=summary,
        prerequisites=prerequisites,
        setup_steps=setup_steps,
        validation_steps=validation_steps,
        hardening_steps=hardening_steps,
        integration_notes=integration_notes,
    )


def _openvpn_plan() -> VPNPlan:
    summary = (
        "Bereitet einen OpenVPN-Server inklusive TLS-PKI vor und stellt Client-Profile"
        " für den Remote-Zugriff bereit."
    )

    prerequisites = [
        "Installierte Pakete: `openvpn`, `easy-rsa`.",
        "Erreichbarkeit der Management-Ports (Standard TCP/UDP 1194).",
        "Plan für Zertifikatsverwaltung (z. B. interne CA oder HashiCorp Vault).",
    ]

    setup_steps = [
        "Easy-RSA-PKI initialisieren (`make-cadir /etc/openvpn/pki`).",
        "CA-, Server- und Client-Zertifikate erstellen (`easyrsa build-ca`, `build-server-full`, `build-client-full`).",
        "Server-Konfiguration unter `/etc/openvpn/server.conf` anhand des Templates in `docs/FOUNDATION_VPN_SETUP.md` anlegen.",
        "TLS-Auth/Prä-Shared-Key generieren (`openvpn --genkey secret /etc/openvpn/ta.key`).",
        "Dienst aktivieren: `sudo systemctl enable --now openvpn-server@server`.",
    ]

    validation_steps = [
        "`sudo systemctl status openvpn-server@server` prüfen.",
        "Client-Profil exportieren (`.ovpn`) und Testverbindung aufbauen.",
        "Routen und DNS per `ip route`, `resolvectl` verifizieren; Funktionsprüfung mit Projektendpunkten.",
    ]

    hardening_steps = [
        "mTLS erzwingen, Cipher-Suite (`AES-256-GCM`) und TLS-Version (`tls-version-min 1.3`) festlegen.",
        "CRL-Handling automatisieren (`crl-verify`), abgelaufene Zertifikate regelmäßig entfernen.",
        "Audit-Logs (`/var/log/openvpn.log`) nach zentralem SIEM weiterleiten.",
    ]

    integration_notes = [
        "Client-Profile verschlüsselt im Secrets-Tresor der Organisation ablegen.",
        "Agenten-Zugang pro Rolle dokumentieren und mit `docs/DEFINITION_OF_DONE.md` abgleichen.",
        "Überwachung der Tunnel mittels `python -m nova alerts --dry-run` vorbereiten (z. B. Ping-Checks).",
    ]

    return VPNPlan(
        vpn_type="OpenVPN",
        summary=summary,
        prerequisites=prerequisites,
        setup_steps=setup_steps,
        validation_steps=validation_steps,
        hardening_steps=hardening_steps,
        integration_notes=integration_notes,
    )


def build_vpn_plan(vpn_type: str) -> VPNPlan:
    """Return the rollout plan for the requested VPN implementation."""

    if not vpn_type:
        raise ValueError("vpn_type must be provided")

    normalised = vpn_type.strip().lower()
    if normalised not in _SUPPORTED_VPN_TYPES:
        supported = ", ".join(sorted(_SUPPORTED_VPN_TYPES))
        raise ValueError(f"Unsupported VPN type: {vpn_type}. Supported values: {supported}")

    if normalised == "wireguard":
        return _wireguard_plan()
    return _openvpn_plan()


def export_vpn_plan(plan: VPNPlan, path: Path) -> Path:
    """Persist ``plan`` as Markdown to ``path`` and return the final location."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(plan.to_markdown() + "\n", encoding="utf-8")
    return path


__all__ = ["VPNPlan", "build_vpn_plan", "export_vpn_plan"]
