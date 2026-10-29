.PHONY: help plan apply destroy setup lint check secrets-check lint-all sops-encrypted-check md-lint md-links hooks

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

ha-config-pull: ## Pull UI-edited Home Assistant YAML (automations/scripts/scenes) from vm-apps into Git (adds the trailing newline HA omits)
	@for f in automations scripts scenes; do \
		ssh -o BatchMode=yes -i ~/.ssh/id_ed25519_homelab ubuntu@192.168.11.20 "sudo cat /opt/homeassistant/config/$$f.yaml" | awk 1 > docker/compose/homeassistant/config/$$f.yaml.tmp \
			&& mv docker/compose/homeassistant/config/$$f.yaml.tmp docker/compose/homeassistant/config/$$f.yaml \
			|| { rm -f docker/compose/homeassistant/config/$$f.yaml.tmp; exit 1; }; \
	done; git status --short docker/compose/homeassistant/config

n8n-workflows-pull: ## Export n8n workflows from vm-apps into Git (workflows only; credentials are not exported)
	@tmp=$$(mktemp -d) && mkdir $$tmp/workflows \
		&& ssh -o BatchMode=yes -i ~/.ssh/id_ed25519_homelab ubuntu@192.168.11.20 "sudo docker exec n8n sh -c 'rm -rf /home/node/.n8n/export && n8n export:workflow --backup --output=/home/node/.n8n/export/' >&2 && sudo tar -C /opt/n8n/data/export -cf - ." > $$tmp/export.tar \
		&& tar -xf $$tmp/export.tar -C $$tmp/workflows \
		&& rm -rf docker/compose/n8n/workflows && mv $$tmp/workflows docker/compose/n8n/workflows \
		&& rm -rf $$tmp && git status --short docker/compose/n8n/workflows \
		|| { rm -rf $$tmp; exit 1; }

setup-proxmox: ## Run Ansible for Proxmox host only
	cd ansible && ansible-playbook playbooks/proxmox.yml

lint: ## Lint Ansible playbooks
	cd ansible && ansible-lint playbooks/

lint-all: lint sops-encrypted-check ## Run every check that CI runs (.github/workflows/lint.yml)
	cd terraform/proxmox && terraform fmt -check -recursive
	cd terraform/proxmox && terraform init -backend=false > /dev/null && terraform validate
	yamllint -s .
	$(MAKE) md-lint md-links
	gitleaks detect --no-banner --log-opts=HEAD

md-lint: ## Lint Markdown style (markdownlint-cli2, needs npx)
	npx --yes markdownlint-cli2@0.24.0

md-links: ## Check internal Markdown links and anchors
	python3 tools/check-md-links.py

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
