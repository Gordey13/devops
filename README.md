### Ansible Playbook для настройки k3s Master Node

#### Структура проекта:
```
k3s-ansible/
├── inventory/
│   └── hosts.ini
├── group_vars/
│   └── k3s_masters.yml
├── roles/
│   └── k3s_master/
│       ├── tasks/
│       │   └── main.yml
│       ├── templates/
│       │   ├── config.yaml.j2
│       │   └── k3s.service.j2
│       └── handlers/
│           └── main.yml
└── playbook.yml
```

#### 1. Инвентарь (`inventory/hosts.ini`)
```ini
[k3s_masters]
master1 ansible_host=192.168.1.10
master2 ansible_host=192.168.1.11
master3 ansible_host=192.168.1.12

[k3s_masters:vars]
ansible_user=ubuntu
ansible_ssh_private_key_file=~/.ssh/k3s-cluster.pem
```

#### 2. Групповые переменные (`group_vars/k3s_masters.yml`)
```yaml
---
# Параметры кластера
k3s_version: v1.29.0+k3s1
k3s_token: "my-strong-token-123"
k3s_datastore_endpoint: "mysql://user:password@tcp(db-host:3306)/k3s"

# Сетевые настройки
k3s_cluster_cidr: "10.42.0.0/16"
k3s_service_cidr: "10.43.0.0/16"
k3s_cluster_dns: "10.43.0.10"

# TLS SANs для сертификата API
k3s_tls_sans:
  - "k3s.example.com"
  - "192.168.1.100" # Виртуальный IP

# Опции для systemd
k3s_exec_flags:
  - "--disable=traefik"
  - "--disable=servicelb"
  - "--flannel-backend=wireguard-native"
  - "--node-taint CriticalAddonsOnly=true:NoExecute"
```

#### 3. Роль k3s_master (`roles/k3s_master/tasks/main.yml`)
```yaml
---
- name: Установка зависимостей
  apt:
    name:
      - curl
      - gnupg
      - software-properties-common
      - nfs-common
      - apparmor
      - apparmor-utils
    state: present
    update_cache: yes

- name: Добавление репозитория Docker
  apt_repository:
    repo: "deb [arch=amd64] https://download.docker.com/linux/ubuntu {{ ansible_distribution_release }} stable"
    state: present
    filename: docker-ce

- name: Установка Docker
  apt:
    name: 
      - containerd.io
      - docker-ce
      - docker-ce-cli
    state: present

- name: Настройка Docker
  copy:
    content: |
      {
        "exec-opts": ["native.cgroupdriver=systemd"],
        "log-driver": "json-file",
        "log-opts": {
          "max-size": "100m"
        },
        "storage-driver": "overlay2"
      }
    dest: /etc/docker/daemon.json
  notify: restart docker

- name: Загрузка и установка k3s
  shell: |
    curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION={{ k3s_version }} INSTALL_K3S_EXEC="server \
      --token {{ k3s_token }} \
      --datastore-endpoint '{{ k3s_datastore_endpoint }}' \
      --cluster-cidr {{ k3s_cluster_cidr }} \
      --service-cidr {{ k3s_service_cidr }} \
      --cluster-dns {{ k3s_cluster_dns }} \
      --tls-san {{ item }} \
      {{ k3s_exec_flags | join(' ') }}" sh -
  args:
    creates: /usr/local/bin/k3s
  loop: "{{ k3s_tls_sans }}"

- name: Копирование конфигурационного файла
  template:
    src: config.yaml.j2
    dest: /etc/rancher/k3s/config.yaml
  notify: restart k3s

- name: Создание systemd сервиса
  template:
    src: k3s.service.j2
    dest: /etc/systemd/system/k3s.service
  notify: reload systemd and restart k3s

- name: Копирование kubeconfig для пользователя
  copy:
    src: /etc/rancher/k3s/k3s.yaml
    dest: "{{ ansible_env.HOME }}/.kube/config"
    owner: "{{ ansible_user }}"
    group: "{{ ansible_user }}"
    mode: 0600

- name: Установка kubectl
  snap:
    name: kubectl
    classic: yes
    state: present

- name: Проверка состояния кластера
  command: kubectl get nodes
  register: k3s_status
  changed_when: false
  until: k3s_status.rc == 0
  retries: 10
  delay: 10
```

#### 4. Шаблоны конфигурации

`roles/k3s_master/templates/config.yaml.j2`:
```yaml
token: {{ k3s_token }}
datastore-endpoint: {{ k3s_datastore_endpoint }}
cluster-cidr: {{ k3s_cluster_cidr }}
service-cidr: {{ k3s_service_cidr }}
cluster-dns: {{ k3s_cluster_dns }}
tls-san:
{% for san in k3s_tls_sans %}
  - {{ san }}
{% endfor %}
disable:
  - traefik
  - servicelb
flannel-backend: wireguard-native
node-taint:
  - CriticalAddonsOnly=true:NoExecute
```

`roles/k3s_master/templates/k3s.service.j2`:
```ini
[Unit]
Description=Lightweight Kubernetes
Documentation=https://k3s.io
After=network.target

[Service]
Type=notify
EnvironmentFile=/etc/systemd/system/k3s.service.env
ExecStartPre=-/sbin/modprobe br_netfilter
ExecStartPre=-/sbin/modprobe overlay
ExecStart=/usr/local/bin/k3s server
KillMode=process
Delegate=yes
LimitNOFILE=infinity
LimitNPROC=infinity
LimitCORE=infinity
TasksMax=infinity
Restart=always
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

#### 5. Обработчики (`roles/k3s_master/handlers/main.yml`)
```yaml
---
- name: restart docker
  service:
    name: docker
    state: restarted
    enabled: yes

- name: restart k3s
  service:
    name: k3s
    state: restarted
    enabled: yes

- name: reload systemd and restart k3s
  systemd:
    daemon_reload: yes
    name: k3s
    state: restarted
    enabled: yes
```

#### 6. Основной playbook (`playbook.yml`)
```yaml
---
- name: Настройка k3s Master Node
  hosts: k3s_masters
  become: yes
  gather_facts: yes

  pre_tasks:
    - name: Обновление системы
      apt:
        upgrade: dist
        update_cache: yes

  roles:
    - role: k3s_master

  post_tasks:
    - name: Проверка состояния кластера
      command: kubectl get nodes -o wide
      register: nodes
      changed_when: false

    - name: Вывод информации о нодах
      debug:
        var: nodes.stdout_lines
```

### Запуск Playbook:
```bash
# Проверка синтаксиса
ansible-playbook playbook.yml --syntax-check

# Тестовый запуск (dry-run)
ansible-playbook playbook.yml --check

# Запуск на всех мастер-нодах
ansible-playbook playbook.yml -i inventory/hosts.ini

# Запуск на конкретной ноде
ansible-playbook playbook.yml -i inventory/hosts.ini -l master1
```

### Особенности конфигурации:
1. **Высокая доступность**:
   - Внешний datastore (MySQL) вместо встроенного etcd
   - TLS SANs для виртуального IP
   - Wireguard для сетевой безопасности

2. **Оптимизация производительности**:
   - Настройка Docker для использования systemd cgroup
   - Отключение ненужных компонентов (Traefik, ServiceLB)
   - Установка taints для мастер-нод

3. **Безопасность**:
   - Статический токен для присоединения нод
   - AppArmor для контейнеров
   - Ограниченные разрешения для kubeconfig

4. **Отказоустойчивость**:
   - Автоматический restart при сбоях
   - Проверка состояния после установки
   - Повторные попытки подключения к datastore

### Дополнительные настройки после установки:

1. Настройка Ingress Controller (например, Nginx):
```yaml
k3s_exec_flags:
  - "--disable=traefik"
  - "--disable=servicelb"
  - "--kube-apiserver-arg=enable-admission-plugins=NodeRestriction"
```

2. Добавление worker-нод:
```bash
curl -sfL https://get.k3s.io | K3S_URL=https://k3s.example.com:6443 K3S_TOKEN=my-strong-token-123 sh -
```

3. Настройка Longhorn для хранилища:
```bash
kubectl apply -f https://raw.githubusercontent.com/longhorn/longhorn/v1.5.1/deploy/longhorn.yaml
```

Данный playbook обеспечивает:
- Автоматическую установку HA k3s кластера
- Централизованное управление конфигурацией
- Поддержку внешнего хранилища данных
- Оптимизированные сетевые настройки
- Готовую инфраструктуру для развертывания приложений
- Соответствие security best practices