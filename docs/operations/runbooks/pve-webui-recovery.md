# PVE の管理画面が開かないとき

ブラウザのコンソールに `Uncaught SyntaxError: Invalid or unexpected token` が出て、画面が描画されない場合。
`pvemanagerlib.js` の `defaultText` や `c is not a constructor` は派生のエラーで、原因は `proxmoxlib.js` の構文エラー。

1. SSH で入り、壊れ方を確認する（VM とサービスは無影響。CLI は使える）。
   ```bash
   grep -c 'void\\(' /usr/share/javascript/proxmox-widget-toolkit/proxmoxlib.js   # 1 以上なら壊れている（0 なら正常）
   ```
2. 正規のファイルに戻す。**バージョンを固定する**（指定しないと最新版が入る）。
   ```bash
   apt-get install --reinstall proxmox-widget-toolkit=$(dpkg-query -W -f='${Version}' proxmox-widget-toolkit)
   ```
   更新後は `pve-nag-buster` のフックがサブスクリプション警告を消し、`pveproxy` を再起動する。
3. ブラウザで強制再読み込み（`Cmd+Shift+R`）。

`proxmox` ロールのパッチは、判定式を `false` に置換するだけで冪等。PVE の更新後に警告が再び出ても、`pve-nag-buster` が当て直す。
`ansible-playbook playbooks/proxmox.yml` を再実行しても壊れない（2 回目以降は `changed=0`）。

詳細は `docs/operations/incidents/2026-10-22-pve-webui-broken-by-ansible-patch.md` を参照。
