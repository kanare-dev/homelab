# 0006. CI は lint のみ。デプロイは自動化しない

- ステータス: 採用
- 日付: 記録なし

## 背景

Terraform と Ansible で構成を管理している。GitHub Actions でどこまで自動化するかを決める必要があった。リポジトリは公開で、運用者は 1 人。

## 決定

CI は GitHub hosted runner での lint・静的チェックだけにする（ansible-lint、terraform fmt / validate、yamllint、SOPS 暗号化チェック、gitleaks）。`terraform plan` / `apply` と `ansible-playbook` は自動化せず、手元で実行する。

## 理由

| 対象 | 自動化しない理由 |
|---|---|
| `terraform plan` | state と Proxmox API に届く runner が必要。VM 数が少なく、手元で足りる |
| `terraform apply` | 意図しない VM 削除のリスクがある |
| `ansible-playbook` | LAN 内 runner に SSH 鍵を置くことになり、公開リポジトリでは fork PR 経由の実行リスクを抱える |

lint は LAN にも秘密情報にも触れず、公開リポジトリでの平文シークレット混入を CI で止められる。

## 影響と再検討の条件

- デプロイは運用者の手作業に依存する。
- 得られる効果に対してリスクが大きい間は、この方針を維持する。

詳細: [CI/CD](../services/cicd.md)
