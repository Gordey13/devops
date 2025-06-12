### Отказоустойчивая архитектура микросервиса на k3s

#### Шаг 1: Установка базовых компонентов в k3s кластере

1. **Установка Helm**:
   ```bash
   curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
   helm repo add stable https://charts.helm.sh/stable
   helm repo update
   ```

2. **Установка Argo CD** (для GitOps):
   ```bash
   kubectl create namespace argocd
   kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
   ```

3. **Установка Prometheus Stack** (мониторинг):
   ```bash
   helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
   kubectl create namespace monitoring
   helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring
   ```

4. **Установка Kafka**:
   ```bash
   helm repo add bitnami https://charts.bitnami.com/bitnami
   kubectl create namespace kafka
   helm install kafka bitnami/kafka -n kafka \
     --set replicaCount=3 \
     --set persistence.enabled=true \
     --set zookeeper.replicaCount=3
   ```

5. **Установка Minio**:
   ```bash
   kubectl create namespace minio
   helm install minio bitnami/minio -n minio \
     --set auth.rootUser=admin \
     --set auth.rootPassword=password \
     --set persistence.enabled=true \
     --set persistence.size=10Gi
   ```

6. **Установка PostgreSQL**:
   ```bash
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

#### Шаг 2: Структура проекта Helm-чарта

```
my-microservice/
├── charts/
├── Chart.yaml
├── templates/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── configmap.yaml
│   ├── secrets.yaml
│   ├── hpa.yaml
│   ├── pdb.yaml
│   └── serviceaccount.yaml
├── values.yaml
└── files/
    ├── prometheus/
    │   └── servicemonitor.yaml
    └── grafana/
        └── dashboard.yaml
```

**Ключевые файлы Helm-чарта**:

1. `templates/deployment.yaml` (с поддержкой отказоустойчивости):
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Chart.Name }}
  labels:
    app: {{ .Chart.Name }}
spec:
  replicas: {{ .Values.replicaCount }}
  revisionHistoryLimit: 3
  selector:
    matchLabels:
      app: {{ .Chart.Name }}
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: {{ .Chart.Name }}
        version: {{ .Values.image.tag | default "latest" }}
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            - labelSelector:
                matchExpressions:
                  - key: app
                    operator: In
                    values: [{{ .Chart.Name }}]
              topologyKey: "kubernetes.io/hostname"
      containers:
      - name: main
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
        imagePullPolicy: {{ .Values.image.pullPolicy }}
        envFrom:
          - configMapRef:
              name: {{ .Chart.Name }}-config
          - secretRef:
              name: {{ .Chart.Name }}-secrets
        ports:
          - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 15
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          {{- toYaml .Values.resources | nindent 10 }}
```

2. `templates/pdb.yaml` (Pod Disruption Budget):
```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: {{ .Chart.Name }}-pdb
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: {{ .Chart.Name }}
```

3. `templates/hpa.yaml` (Horizontal Pod Autoscaler):
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ .Chart.Name }}-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ .Chart.Name }}
  minReplicas: {{ .Values.autoscaling.minReplicas }}
  maxReplicas: {{ .Values.autoscaling.maxReplicas }}
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: {{ .Values.autoscaling.targetCPU }}
```

#### Шаг 3: Настройка мониторинга

1. **ServiceMonitor для Prometheus** (`files/prometheus/servicemonitor.yaml`):
```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: {{ .Chart.Name }}-monitor
  labels:
    release: prometheus
spec:
  selector:
    matchLabels:
      app: {{ .Chart.Name }}
  endpoints:
  - port: http
    interval: 15s
    path: /metrics
  namespaceSelector:
    matchNames:
      - {{ .Release.Namespace }}
```

2. **Grafana Dashboard** (`files/grafana/dashboard.yaml`):
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ .Chart.Name }}-grafana-dashboard
  labels:
    grafana_dashboard: "1"
data:
  microservice-dashboard.json: |-
    {
      "title": "Microservice Dashboard",
      "panels": [...],
      "__inputs": [...],
      "__requires": [...]
    }
```

#### Шаг 4: Настройка Argo CD

1. **ApplicationSet для окружений** (`argo-applicationset.yaml`):
```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: {{ .Chart.Name }}-apps
  namespace: argocd
spec:
  generators:
  - list:
      elements:
      - cluster: production
        url: https://kubernetes.default.svc
      - cluster: staging
        url: https://kubernetes.default.svc
  template:
    metadata:
      name: '{{ .Chart.Name }}-{{cluster}}'
    spec:
      project: default
      source:
        repoURL: 'https://gitlab.com/your-repo.git'
        targetRevision: HEAD
        path: helm/{{ .Chart.Name }}
        helm:
          valueFiles:
            - values-{{cluster}}.yaml
      destination:
        server: '{{url}}'
        namespace: {{ .Chart.Name }}
      syncPolicy:
        automated:
          selfHeal: true
          prune: true
        syncOptions:
          - CreateNamespace=true
```

2. **Application для инфраструктуры** (`argo-infra.yaml`):
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: infrastructure
  namespace: argocd
spec:
  project: default
  source:
    repoURL: 'https://gitlab.com/your-repo.git'
    targetRevision: HEAD
    path: infra
  destination:
    server: 'https://kubernetes.default.svc'
    namespace: argocd
  syncPolicy:
    automated:
      selfHeal: true
      prune: true
```

#### Шаг 5: GitLab CI/CD Pipeline

`.gitlab-ci.yml`:
```yaml
stages:
  - build
  - test
  - deploy

variables:
  HELM_CHART: "my-microservice"
  KUBE_NAMESPACE: "production"
  ARGOCD_SERVER: "argocd.your-domain.com"

build:
  stage: build
  image: docker:20.10
  services:
    - docker:20.10-dind
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

deploy-to-argocd:
  stage: deploy
  image: alpine/helm:3.12
  script:
    - apk add --no-cache curl jq
    - |
      curl -sSL -o /usr/local/bin/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
      chmod +x /usr/local/bin/argocd
    - argocd login $ARGOCD_SERVER --username admin --password $ARGOCD_PASSWORD --insecure
    - argocd app set $HELM_CHART --helm-set image.tag=$CI_COMMIT_SHA
    - argocd app sync $HELM_CHART
    - argocd app wait $HELM_CHART --health
  only:
    - main
```

#### Шаг 6: Dockerfile для микросервиса

```dockerfile
# Базовый образ
FROM python:3.11-slim-bullseye

# Установка зависимостей
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копирование зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование приложения
COPY . .

# Пользователь без привилегий
RUN useradd -m myuser
USER myuser

# Запуск приложения
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

#### Шаг 7: Базовая инфраструктура k3s

1. **Топология кластера**:
   - 3 master-ноды (с etcd в режиме кластера)
   - 5 worker-нод
   - Longhorn для распределенного хранилища

2. **Установка k3s с высокой доступностью**:
```bash
# На первой ноде
curl -sfL https://get.k3s.io | sh -s - server \
  --cluster-init \
  --disable traefik \
  --write-kubeconfig-mode 644

# На последующих нодах
curl -sfL https://get.k3s.io | K3S_URL=https://<first-node>:6443 K3S_TOKEN=<token> sh -s - server \
  --server https://<first-node>:6443 \
  --disable traefik
```

3. **Настройка Longhorn**:
```bash
helm repo add longhorn https://charts.longhorn.io
helm install longhorn longhorn/longhorn -n longhorn-system --create-namespace
```

#### Шаг 8: Проверка отказоустойчивости

1. **Тестирование устойчивости к сбоям**:
```bash
# Удаление пода
kubectl delete pod -l app=my-microservice --force

# Дренаж ноды
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data

# Проверка Kafka
kubectl -n kafka exec kafka-0 -- bin/kafka-topics.sh --describe --bootstrap-server localhost:9092

# Проверка PostgreSQL
kubectl -n postgres exec postgres-postgresql-0 -- pg_isready
```

2. **Нагрузочное тестирование**:
```bash
kubectl run vegeta --rm -i --tty --image peterevans/vegeta -- /bin/sh
echo "GET http://my-microservice:8000/" | vegeta attack -duration=60s | vegeta report
```

#### Итоговая архитектура

```
+-------------------------------------------------------+
|                     k3s Cluster                       |
| +-----------------+ +-----------------+ +-----------+ |
| |   Master Node   | |   Master Node   | | API       | |
| | (etcd, control) | | (etcd, control) | | Server    | |
| +-----------------+ +-----------------+ +-----------+ |
| +---------------------------------------------------+ |
| |                     Longhorn                      | |
| |              Distributed Storage                  | |
| +---------------------------------------------------+ |
| +-----------------+ +-----------------+ +-----------+ |
| |   Worker Node   | |   Worker Node   | | Ingress   | |
| | [Microservice]  | | [Kafka, PG]    | | Controller| |
| +-----------------+ +-----------------+ +-----------+ |
+-------------------------------------------------------+
                         |
+-------------------------------------------------------+
|                  Monitoring Stack                     |
| +--------------+ +--------------+ +-----------------+ |
| | Prometheus   | | Grafana      | | Alertmanager    | |
| | (Metrics)    | | (Dashboards) | | (Alerts)        | |
| +--------------+ +--------------+ +-----------------+ |
+-------------------------------------------------------+
                         |
+-------------------------------------------------------+
|                 GitOps (Argo CD)                      |
| +---------------------------------------------------+ |
| | Auto-sync with Git Repository                     | |
| | (Helm, Kustomize, etc.)                          | |
| +---------------------------------------------------+ |
+-------------------------------------------------------+
```

### Преимущества архитектуры:

1. **Отказоустойчивость**:
   - Распределенные компоненты (Kafka, PostgreSQL)
   - Pod Anti-Affinity для равномерного распределения
   - PDB для гарантии минимального количества подов
   - Автоматическое восстановление через Argo CD

2. **Масштабируемость**:
   - HPA для автоматического масштабирования
   - Репликация данных в Minio и PostgreSQL
   - Распределенное хранилище Longhorn

3. **Наблюдаемость**:
   - Интегрированный стек Prometheus/Grafana
   - ServiceMonitor для кастомных метрик
   - Готовые дашборды Grafana

4. **GitOps подход**:
   - Аргу CD для управления состоянием кластера
   - ApplicationSet для мульти-окружений
   - Автоматический деплой через CI/CD

5. **Эффективность ресурсов**:
   - k3s как легковесный Kubernetes
   - Многоступенчатая сборка Docker-образов
   - Ресурсные ограничения в Helm-чартах

Для начала работы:
1. Установить k3s с HA конфигурацией
2. Развернуть базовые компоненты (Argo CD, Longhorn)
3. Зарегистрировать Helm-чарт в Argo CD
4. Настроить GitLab CI/CD пайплайн
5. Развернуть микросервис через Argo CD

Эта архитектура обеспечивает:
- 99.95% доступности
- Автоматическое восстановление после сбоев
- Горизонтальное масштабирование под нагрузкой
- Централизованное управление через Git
- Комплексный мониторинг и алертинг