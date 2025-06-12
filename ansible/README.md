# K3s Ansible Playbook

This Ansible playbook automates the deployment of a highly available K3s cluster with multiple master nodes.

## Prerequisites

- Ansible 2.9 or later
- Ubuntu 20.04 or later on target nodes
- SSH access to target nodes
- SSH key pair for authentication

## Project Structure

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

## Configuration

1. Update the inventory file (`inventory/hosts.ini`) with your master node IP addresses and SSH credentials.
2. Modify the group variables in `group_vars/k3s_masters.yml` according to your needs:
   - Update `k3s_version` if needed
   - Set a secure `k3s_token`
   - Configure your MySQL datastore endpoint
   - Adjust network CIDRs if needed
   - Update TLS SANs with your domain names and IPs

## Usage

1. Check the playbook syntax:
```bash
ansible-playbook playbook.yml --syntax-check
```

2. Perform a dry run:
```bash
ansible-playbook playbook.yml --check
```

3. Deploy the cluster:
```bash
ansible-playbook playbook.yml -i inventory/hosts.ini
```

4. Deploy to a specific node:
```bash
ansible-playbook playbook.yml -i inventory/hosts.ini -l master1
```

## Features

- High availability setup with external datastore
- Wireguard networking for enhanced security
- Systemd integration
- Automatic service recovery
- TLS certificate management
- Docker optimization
- AppArmor support

## Post-Installation

After deployment, you can:

1. Install an Ingress Controller (e.g., Nginx)
2. Add worker nodes using the provided token
3. Deploy Longhorn for persistent storage

## Security Notes

- The playbook uses a static token for node joining
- TLS certificates are configured with proper SANs
- AppArmor is enabled for container security
- Kubeconfig permissions are restricted
- Master nodes are tainted for workload isolation 