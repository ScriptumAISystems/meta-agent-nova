# Foundation-Phase: VPN- & Fernzugriff aktivieren

Dieser Leitfaden beschreibt Schritt 3 der Foundation-Phase und ergänzt die Container-Installation um einen abgesicherten Fernzugriff. Nova nutzt die hier definierten Abläufe, um WireGuard oder OpenVPN deterministisch auszurollen, zu validieren und anschließend für Monitoring und Auditing vorzubereiten.

## 1. Zielsetzung & Erfolgsfaktoren

- [ ] Mindestens eine VPN-Variante (WireGuard oder OpenVPN) ist vollständig eingerichtet.
- [ ] Tunnelverbindungen sind getestet und für die relevanten Teammitglieder dokumentiert.
- [ ] Sicherheitskontrollen (mTLS, Schlüsselverwaltung, Firewall-Regeln) sind aktiviert.
- [ ] `python -m nova network --vpn <typ>` liefert einen aktuellen Rollout-Plan und optional einen Markdown-Export für das Orchestrierungstagebuch.
- [ ] `Agenten_Aufgaben_Uebersicht.csv` ist aktualisiert, sobald Validierung & Härtung erfolgreich abgeschlossen sind.

## 2. Entscheidungsbaum

1. **WireGuard bevorzugen**, wenn eine schlanke, performante Lösung mit minimalem Overhead gesucht wird.
2. **OpenVPN wählen**, wenn bereits eine TLS-PKI existiert oder eine Integration in bestehende OpenVPN-Infrastruktur nötig ist.
3. In beiden Fällen sollte die finale Wahl im Orchestrierungstagebuch (`orchestration_journal/vpn/decision.md`) dokumentiert werden.

> ℹ️ Beide Varianten werden vom CLI unterstützt: `python -m nova network --vpn wireguard` bzw. `python -m nova network --vpn openvpn`. Mit `--export <pfad>` kann der Plan als Markdown gespeichert werden.

## 3. WireGuard-Rollout (Empfohlene Default-Variante)

1. Pakete installieren:
   ```bash
   sudo apt-get update
   sudo apt-get install -y wireguard wireguard-tools
   ```
2. Schlüssel generieren:
   ```bash
   sudo mkdir -p /etc/wireguard
   (umask 077 && wg genkey | sudo tee /etc/wireguard/privatekey | wg pubkey | sudo tee /etc/wireguard/publickey)
   ```
3. Interface konfigurieren (`/etc/wireguard/wg0.conf`):
   ```ini
   [Interface]
   Address = 10.20.0.1/24
   ListenPort = 51820
   PrivateKey = <SERVER_PRIVATE_KEY>

   [Peer]
   PublicKey = <CLIENT_PUBLIC_KEY>
   AllowedIPs = 10.20.0.2/32
   PersistentKeepalive = 25
   ```
4. IP-Forwarding aktivieren:
   ```bash
   echo "net.ipv4.ip_forward=1" | sudo tee /etc/sysctl.d/99-wireguard.conf
   echo "net.ipv6.conf.all.forwarding=1" | sudo tee -a /etc/sysctl.d/99-wireguard.conf
   sudo sysctl --system
   ```
5. Dienst starten und aktivieren:
   ```bash
   sudo systemctl enable --now wg-quick@wg0
   ```
6. Validierung:
   ```bash
   sudo wg show
   ip addr show wg0
   ping -c 3 10.20.0.2
   ```
7. Härtung:
   - Private Keys mit `chmod 600` absichern.
   - Firewall-Regeln (z. B. `ufw`) so setzen, dass nur autorisierte Peers zugreifen können.
   - Offboarding-Prozess definieren (Peers in `/etc/wireguard/wg0.conf` entfernen, Schlüssel widerrufen).

## 4. OpenVPN-Rollout (Alternative)

1. Pakete installieren:
   ```bash
   sudo apt-get update
   sudo apt-get install -y openvpn easy-rsa
   ```
2. PKI vorbereiten und Zertifikate generieren:
   ```bash
   make-cadir ~/openvpn-ca
   cd ~/openvpn-ca
   ./easyrsa init-pki
   ./easyrsa build-ca
   ./easyrsa build-server-full server nopass
   ./easyrsa build-client-full client1 nopass
   openvpn --genkey --secret ta.key
   ```
3. Server-Konfiguration (`/etc/openvpn/server.conf`):
   ```ini
   port 1194
   proto udp
   dev tun
   ca /etc/openvpn/pki/ca.crt
   cert /etc/openvpn/pki/issued/server.crt
   key /etc/openvpn/pki/private/server.key
   dh none
   tls-auth /etc/openvpn/ta.key 0
   cipher AES-256-GCM
   auth SHA256
   topology subnet
   server 10.30.0.0 255.255.255.0
   push "redirect-gateway def1 bypass-dhcp"
   push "dhcp-option DNS 1.1.1.1"
   keepalive 10 120
   user nobody
   group nogroup
   persist-key
   persist-tun
   verb 3
   ```
4. Dienst starten:
   ```bash
   sudo systemctl enable --now openvpn-server@server
   ```
5. Client-Profil erzeugen (`client1.ovpn`):
   ```bash
   ./easyrsa build-client-full client1
   ./easyrsa gen-crl
   # Profil zusammenstellen und sicher übergeben
   ```
6. Validierung:
   - Status prüfen: `sudo systemctl status openvpn-server@server`.
   - Test-Client verbinden (`openvpn --config client1.ovpn`).
   - DNS- und Routing-Einträge kontrollieren.
7. Härtung:
   - `tls-version-min 1.3` sowie `tls-cipher`-Suite definieren.
   - CRL-Updates automatisieren (`crl-verify` in der Server-Konfiguration aktivieren).
   - Logs nach zentralem Monitoring streamen.

## 5. Reporting & Übergabe

1. **Dokumentation** – Exportiere den Plan via `python -m nova network --vpn <typ> --export orchestration_journal/vpn/<typ>_plan.md` und füge Testergebnisse hinzu.
2. **Status-Update** – Passe `Agenten_Aufgaben_Uebersicht.csv` an (`VPN & Fernzugriff ...` auf „Abgeschlossen“).
3. **Security-Review** – Ergebnisse mit dem Security-Officer teilen und Freigabe protokollieren.
4. **Monitoring-Hooks** – VPN-Verfügbarkeit als Check in die Alert-Workflows integrieren (`python -m nova alerts --dry-run`).

Mit Abschluss dieses Dokuments ist Schritt 3 der Foundation-Phase detailliert beschrieben. Die nächsten Aufgaben umfassen Sicherheitsprüfungen (`python -m nova audit`) und das Einrichten von Backup-/Recovery-Prozessen (`python -m nova backup --plan default`).
