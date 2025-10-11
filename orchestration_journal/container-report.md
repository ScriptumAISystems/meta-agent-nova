# Nova Container Runtime Check

## Docker Engine
- Status: ✅ ok
- Binary: docker
- Gefunden: Ja
- Version: Docker version 26.0.0

### Hinweise
- Funktionstest `docker run hello-world` erfolgreich dokumentiert.

## Kubernetes CLI
- Status: ✅ ok
- Binary: kubectl
- Gefunden: Ja
- Version: Client Version: v1.30.1
- Kubeconfig: ✅ vorhanden

### Hinweise
- Gefundene Kubeconfig-Dateien: /home/nova/.kube/config
- `kubectl get nodes` meldet `spark-control-plane` im Status Ready.
