# Fault-Tolerant Microservice on k3s

This project implements a fault-tolerant microservice architecture using k3s, Argo CD, and various supporting components.

## Prerequisites

- k3s cluster with high availability setup
- Helm 3.x
- Argo CD
- GitLab CI/CD
- Docker

## Architecture Components

1. **Base Infrastructure**:
   - k3s with HA setup
   - Longhorn for distributed storage
   - Prometheus Stack for monitoring
   - Argo CD for GitOps

2. **Data Services**:
   - Kafka for message streaming
   - PostgreSQL for data persistence
   - Minio for object storage

3. **Microservice Features**:
   - Fault tolerance with pod anti-affinity
   - Horizontal Pod Autoscaling
   - Pod Disruption Budget
   - Health checks and probes
   - Prometheus monitoring

## Setup Instructions

1. **Install Base Components**:
   ```bash
   # Install Helm
   curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
   
   # Install Argo CD
   kubectl create namespace argocd
   kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
   
   # Install Prometheus Stack
   helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
   kubectl create namespace monitoring
   helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring
   ```

2. **Install Data Services**:
   ```bash
   # Install Kafka
   helm repo add bitnami https://charts.bitnami.com/bitnami
   kubectl create namespace kafka
   helm install kafka bitnami/kafka -n kafka \
     --set replicaCount=3 \
     --set persistence.enabled=true \
     --set zookeeper.replicaCount=3
   
   # Install PostgreSQL
   kubectl create namespace postgres
   helm install postgres bitnami/postgresql -n postgres \
     --set auth.postgresPassword=password \
     --set auth.username=user \
     --set auth.password=password \
     --set auth.database=mydb \
     --set persistence.enabled=true \
     --set persistence.size=10Gi \
     --set replication.enabled=true \
     --set replication.slaveReplicas=2
   ```

3. **Deploy Microservice**:
   ```bash
   # Register Helm chart in Argo CD
   kubectl apply -f argo-applicationset.yaml
   
   # Deploy through GitLab CI/CD
   git push origin main
   ```

## Monitoring and Maintenance

1. **Access Prometheus**:
   ```bash
   kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090
   ```

2. **Access Grafana**:
   ```bash
   kubectl port-forward -n monitoring svc/grafana 3000:3000
   ```

3. **Check Argo CD Status**:
   ```bash
   kubectl port-forward -n argocd svc/argocd-server 8080:443
   ```

## Fault Tolerance Testing

1. **Test Pod Recovery**:
   ```bash
   kubectl delete pod -l app=my-microservice --force
   ```

2. **Test Node Drain**:
   ```bash
   kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data
   ```

3. **Load Testing**:
   ```bash
   kubectl run vegeta --rm -i --tty --image peterevans/vegeta -- /bin/sh
   echo "GET http://my-microservice:8000/" | vegeta attack -duration=60s | vegeta report
   ```

## Security Considerations

- All sensitive data is stored in Kubernetes secrets
- Pod security context is configured
- Network policies are in place
- Regular security updates are automated
- Access control through RBAC

## Troubleshooting

1. **Check Pod Status**:
   ```bash
   kubectl get pods -n <namespace>
   kubectl describe pod <pod-name>
   ```

2. **Check Logs**:
   ```bash
   kubectl logs -f <pod-name>
   ```

3. **Check Events**:
   ```bash
   kubectl get events --sort-by='.lastTimestamp'
   ```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 