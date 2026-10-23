.PHONY: help plan apply destroy setup lint check secrets-check lint-all sops-encrypted-check hooks

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

setup-code: ## Run Ansible for code VM only
	cd ansible && ansible-playbook playbooks/code.yml

setup-proxmox: ## Run Ansible for Proxmox host only
	cd ansible && ansible-playbook playbooks/proxmox.yml

lint: ## Lint Ansible playbooks
	cd ansible && ansible-lint playbooks/

lint-all: lint sops-encrypted-check ## Run every check that CI runs (.github/workflows/lint.yml)
	cd terraform/proxmox && terraform fmt -check -recursive
	cd terraform/proxmox && terraform init -backend=false > /dev/null && terraform validate
	yamllint -s .
	gitleaks detect --no-banner --log-opts=HEAD

sops-encrypted-check: ## Verify SOPS files are encrypted without decrypting them
	@status=0; for f in $$(git ls-files '*/*.sops.yml' '*/*.sops.yaml'); do \
		grep -q '^sops:' "$$f" && echo "OK   $$f" || { echo "FAIL $$f (not encrypted)"; status=1; }; \
	done; exit $$status

hooks: ## Enable the repo's git hooks (.githooks/)
	git config core.hooksPath .githooks

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

homepage-up: ## Start homepage dashboard
	cd docker/compose/homepage && docker compose up -d

homepage-down: ## Stop homepage dashboard
	cd docker/compose/homepage && docker compose down

# --- Secrets ---
secrets-check: ## Verify every SOPS file can be decrypted (values are not printed)
	@for f in $$(git ls-files -c -o --exclude-standard '*/*.sops.yml' '*/*.sops.yaml'); do \
		sops -d "$$f" > /dev/null && echo "OK   $$f" || { echo "FAIL $$f"; exit 1; }; \
	done
