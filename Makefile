.PHONY: help plan apply destroy setup lint check

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# --- Terraform ---
plan: ## Terraform plan (proxmox)
	cd terraform/proxmox && terraform plan

apply: ## Terraform apply (proxmox)
	cd terraform/proxmox && terraform apply

destroy: ## Terraform destroy (proxmox)
	cd terraform/proxmox && terraform destroy

tf-init: ## Terraform init (proxmox)
	cd terraform/proxmox && terraform init

tf-fmt: ## Terraform format check
	cd terraform/proxmox && terraform fmt -recursive

# --- Ansible ---
setup: ## Run full Ansible setup (site.yml)
	cd ansible && ansible-playbook playbooks/site.yml

setup-infra: ## Run Ansible for infra VM only
	cd ansible && ansible-playbook playbooks/infra.yml

setup-monitoring: ## Run Ansible for monitoring VM only
	cd ansible && ansible-playbook playbooks/monitoring.yml

setup-apps: ## Run Ansible for apps VM only
	cd ansible && ansible-playbook playbooks/apps.yml

setup-proxmox: ## Run Ansible for Proxmox host only
	cd ansible && ansible-playbook playbooks/proxmox.yml

lint: ## Lint Ansible playbooks
	cd ansible && ansible-lint playbooks/

check: ## Ansible dry-run (check mode)
	cd ansible && ansible-playbook playbooks/site.yml --check --diff

ping: ## Ping all hosts
	cd ansible && ansible all -m ping

# --- Docker ---
monitoring-up: ## Start monitoring stack
	cd docker/compose/monitoring && docker compose up -d

monitoring-down: ## Stop monitoring stack
	cd docker/compose/monitoring && docker compose down

proxy-up: ## Start reverse proxy
	cd docker/compose/reverse-proxy && docker compose up -d

proxy-down: ## Stop reverse proxy
	cd docker/compose/reverse-proxy && docker compose down

# --- Secrets ---
encrypt: ## Encrypt secrets with SOPS
	@echo "Usage: sops -e secrets.yml > secrets.enc.yml"

vault-encrypt: ## Encrypt Ansible vault file
	cd ansible && ansible-vault encrypt inventory/group_vars/all.yml
