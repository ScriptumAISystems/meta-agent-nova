# Wireguard Remote Access Plan

## Zusammenfassung
Richtet einen WireGuard-Tunnel für sicheren Fernzugriff auf die DGX/Spark-Umgebung ein. Alle Konfigurationsdateien werden versioniert und über die Nova-Dokumentation referenziert.

## Voraussetzungen
- Ubuntu 22.04 LTS oder kompatible Distribution mit Root-/Sudo-Zugriff.
- Outbound-Zugriff auf `https://ppa.launchpadcontent.net/wireguard`.
- Firewall-Regeln für UDP-Port 51820 (anpassbar) vorbereitet.

## Installationsschritte
- `sudo apt-get update && sudo apt-get install -y wireguard wireguard-tools`.
- Server-Keys erzeugen: `wg genkey | tee /etc/wireguard/privatekey | wg pubkey > /etc/wireguard/publickey`.
- Interface-Datei `/etc/wireguard/wg0.conf` gemäß Template aus `docs/FOUNDATION_VPN_SETUP.md` anlegen.
- Netzwerk-Forwarding aktivieren (`/etc/sysctl.d/99-wireguard.conf`) und `sudo sysctl --system` ausführen.
- Dienst starten: `sudo systemctl enable --now wg-quick@wg0`.

## Validierung
- Tunnelstatus prüfen: `sudo wg show` und `ip addr show wg0`.
- Konnektivität testen: `ping` auf eine interne Adresse und `python -m nova containers` über den Tunnel ausführen.
- Optional Smoke-Test mit Beispiel-Client (`wg-quick up`) und Prüfung der Protokolle in `/var/log/syslog`.

## Härtung & Betrieb
- Private Keys mit `chmod 600` absichern und Zugriffe auditieren.
- `ufw`/`nftables` auf Tunnel-Subnetz beschränken, Logging aktivieren.
- Peers mit Keepalive und IP-Adressbeschränkungen versehen, Offboarding-Prozess dokumentieren.

## Integration in Nova
- Konfigurationspfad im Orchestrierungstagebuch (`orchestration_journal/vpn/`) dokumentieren.
- Status in `Agenten_Aufgaben_Uebersicht.csv` auf 'Abgeschlossen' setzen, sobald Validierung erfolgreich.
- Monitoring-Hooks für Tunnelverfügbarkeit in `python -m nova alerts --dry-run` aufnehmen.
