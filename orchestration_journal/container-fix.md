# Nova Container Fix-Plan

## Docker Engine
*Problemanalyse:*
- Binary wurde nicht im PATH gefunden.
- Hinweis: Binary 'docker' wurde nicht im PATH gefunden.

*Empfohlene Maßnahmen:*
- Paketquellen aktualisieren: `sudo apt-get update`.
- Basisabhängigkeiten installieren: `sudo apt-get install -y ca-certificates curl gnupg lsb-release`.
- Docker-Repository laut `docs/FOUNDATION_CONTAINER_SETUP.md` Abschnitt 2 hinzufügen und Schlüssel ablegen.
- Engine installieren: `sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin`.
- Dienst aktivieren und testen: `sudo systemctl enable docker --now` sowie `docker --version` und `docker run hello-world` ausführen.

## Kubernetes CLI
*Problemanalyse:*
- Binary wurde nicht im PATH gefunden.
- Hinweis: Binary 'kubectl' wurde nicht im PATH gefunden.

*Empfohlene Maßnahmen:*
- Kubernetes-Repository einrichten (siehe `docs/FOUNDATION_CONTAINER_SETUP.md`, Abschnitt 3B).
- CLI und Control-Plane-Pakete installieren: `sudo apt-get install -y kubelet kubeadm kubectl` und Pakete mittels `sudo apt-mark hold ...` fixieren.
- Cluster initialisieren oder Kind-Cluster starten (Abschnitt 3A/3B) und mit `kubectl get nodes` validieren.
- Kubeconfig bereitstellen: `mkdir -p $HOME/.kube` und z. B. `/etc/kubernetes/admin.conf` nach `~/.kube/config` kopieren.
