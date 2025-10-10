# Foundation-Phase: Docker- & Kubernetes-Installation

Diese Anleitung beschreibt den konkreten Ablauf, um die zweite Aufgabe der Foundation-Phase abzuschließen: die Installation eines Docker-Runtimes und eines Kubernetes-Clusters auf der Zielumgebung (z. B. DGX/Spark Sophia). Alle Schritte sind so dokumentiert, dass sie reproduzierbar sind und sich in das bestehende Monitoring- und Reporting-Setup des Nova-Repos einfügen.

## 1. Zielsetzung und Ausgangslage
- [ ] Docker Engine ist installiert und via `docker --version` verifizierbar.
- [ ] Kubernetes CLI (`kubectl`) ist installiert und kann gegen einen Cluster sprechen.
- [ ] Eine lauffähige Control-Plane existiert (lokal via Kind oder systemweit via kubeadm/k3s).
- [ ] `python -m nova containers` liefert für Docker und Kubernetes den Status ✅.

Voraussetzungen:
- Ubuntu 22.04 LTS oder vergleichbare Linux-Distribution mit Root-/Sudo-Zugriff.
- Internetzugang für Paketinstallationen.
- Vorbereitete Nutzergruppe `docker` (optional, siehe Schritt 2).

## 2. Docker Engine installieren
1. Paketquellen aktualisieren und Dependencies installieren:
   ```bash
   sudo apt-get update
   sudo apt-get install -y ca-certificates curl gnupg lsb-release
   ```
2. Docker GPG-Key einbinden und Repository hinterlegen:
   ```bash
   sudo install -m 0755 -d /etc/apt/keyrings
   curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
   echo \
     "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
     $(lsb_release -cs) stable" | \
     sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
   sudo apt-get update
   ```
3. Engine und CLI installieren:
   ```bash
   sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
   ```
4. (Optional) Benutzer zur Docker-Gruppe hinzufügen und Dienst testen:
   ```bash
   sudo usermod -aG docker $USER
   sudo systemctl enable docker --now
   docker --version
   docker info
   ```
5. Dokumentation aktualisieren:
   - Ergebnis (`docker --version`) im Infrastrukturprotokoll notieren.
   - Log `python -m nova containers` anhängen, sobald Kubernetes installiert ist.

## 3. Kubernetes-Cluster bereitstellen
Je nach Anforderung bieten sich zwei Varianten an. Beide werden hier dokumentiert.

### Variante A: Schnellstart mit Kind (Entwicklung & Tests)
1. Kind installieren:
   ```bash
   curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.23.0/kind-linux-amd64
   chmod +x ./kind
   sudo mv ./kind /usr/local/bin/kind
   kind --version
   ```
2. Cluster starten:
   ```bash
   kind create cluster --name nova-foundation
   ```
3. kubeconfig übernehmen (Kind nutzt standardmäßig `~/.kube/config`).
4. Funktion prüfen:
   ```bash
   kubectl cluster-info --context kind-nova-foundation
   kubectl get nodes
   ```
5. Für Tests wieder entfernen:
   ```bash
   kind delete cluster --name nova-foundation
   ```

### Variante B: Systemweites Cluster via kubeadm (Produktionsnahe Umgebung)
1. Kubernetes-Pakete installieren:
   ```bash
   sudo apt-get update
   sudo apt-get install -y apt-transport-https ca-certificates curl
   sudo curl -fsSLo /usr/share/keyrings/kubernetes-archive-keyring.gpg https://pkgs.k8s.io/core:/stable:/v1.31/deb/Release.key
   echo "deb [signed-by=/usr/share/keyrings/kubernetes-archive-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.31/deb/ /" | \
     sudo tee /etc/apt/sources.list.d/kubernetes.list
   sudo apt-get update
   sudo apt-get install -y kubelet kubeadm kubectl
   sudo apt-mark hold kubelet kubeadm kubectl
   ```
2. Container Runtime (containerd) konfigurieren:
   ```bash
   sudo mkdir -p /etc/containerd
   containerd config default | sudo tee /etc/containerd/config.toml
   sudo systemctl restart containerd
   ```
3. Control-Plane initialisieren:
   ```bash
   sudo kubeadm init --pod-network-cidr=10.244.0.0/16
   ```
4. kubeconfig für aktuellen User einrichten:
   ```bash
   mkdir -p $HOME/.kube
   sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
   sudo chown $(id -u):$(id -g) $HOME/.kube/config
   ```
5. Netzwerk-Plugin deployen (Beispiel: Flannel):
   ```bash
   kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml
   ```
6. Worker-Knoten joinen (Token aus `kubeadm init` verwenden) und Status prüfen:
   ```bash
   kubectl get nodes -o wide
   kubectl get pods -A
   ```

## 4. Validierung & Reporting
Nach der Installation beide Prüfungen durchführen und dokumentieren:

1. `python -m nova containers`
   - Erwartetes Ergebnis: Beide Checks melden ✅ „ok“.
   - Markdown-Ausgabe in das Infrastrukturprotokoll (z. B. `orchestration_journal/`) kopieren.
2. `kubectl get nodes`
   - Ausgabe in den Projekt-Statusbericht übernehmen.
3. `docker run hello-world`
   - Verifizieren, dass Container erfolgreich starten.
4. Fortschritt im CSV aktualisieren:
   - In `Agenten_Aufgaben_Uebersicht.csv` den Status für „Docker und Kubernetes-Cluster installieren“ auf „Abgeschlossen“ setzen, sobald alle Prüfungen grün sind.

## 5. Troubleshooting & Eskalation
- Docker Dienst startet nicht: `journalctl -u docker -xe` prüfen und ggf. Kernelmodule wie `overlay2` aktivieren.
- Kubernetes-Komponenten hängen im Status `NotReady`: Netzwerk-Plugin prüfen (`kubectl get pods -n kube-flannel`).
- Berechtigungsprobleme bei `kubectl`: Besitzrechte der `~/.kube/config` sicherstellen.
- Dokumentiere alle Abweichungen im Orchestrierungstagebuch und informiere Nova, falls weitere Unterstützung benötigt wird.

---

Mit Abschluss dieser Anleitung ist Schritt 2 der Foundation-Phase klar beschrieben und ausführbar. Die nächsten Aufgaben (VPN, Security, Backup) bauen auf der nun verfügbaren Container-Infrastruktur auf.
