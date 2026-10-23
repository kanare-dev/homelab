# 障害時切り分け

## VM が応答しない

```text
1. ping で疎通確認
   $ ping 192.168.11.XX

2. Proxmox Web UI で VM のステータス確認
   → https://192.168.11.10:8006

3. Proxmox コンソールで起動状況を確認
   → Web UI > VM > Console
   ※ ログインはできない。VM の `ubuntu` / `root` はパスワードがロックされており、
     SSH も鍵認証のみ（`PasswordAuthentication no`）。表示されるのは起動ログとログインプロンプトまで。
     入る必要があるときは SSH を使う。緊急用のパスワードは設定していない（2026-10-22 に見送り）

4. VM を再起動
   $ ssh root@192.168.11.10 "qm reboot <vmid>"

5. VM を強制停止・起動
   $ ssh root@192.168.11.10 "qm stop <vmid> && qm start <vmid>"
```

## サービスが応答しない

```text
1. Docker コンテナのステータス確認
   $ docker compose ps

2. ログ確認
   $ docker compose logs --tail=50 <service>

3. コンテナ再起動
   $ docker compose restart <service>

4. コンテナ再作成
   $ docker compose up -d --force-recreate <service>
```

## DNS が引けない

```text
1. CoreDNS のステータス確認
   $ ssh ubuntu@192.168.11.11 "systemctl status coredns"

2. CoreDNS のログ確認
   $ ssh ubuntu@192.168.11.11 "journalctl -u coredns --tail=50"

3. 直接クエリして確認
   $ dig @192.168.11.11 grafana.lab.kanare.dev

4. CoreDNS を再起動
   $ ssh ubuntu@192.168.11.11 "sudo systemctl restart coredns"
```

## Prometheus がスクレイプに失敗

```text
1. Prometheus の Targets ページを確認
   → http://192.168.11.13:9090/targets

2. ターゲット VM の node_exporter を確認
   $ curl http://192.168.11.XX:9100/metrics

3. ファイアウォール確認
   $ ssh ubuntu@192.168.11.XX "sudo ufw status"

4. node_exporter を再起動
   $ ssh ubuntu@192.168.11.XX "sudo systemctl restart node_exporter"
```

## Grafana にログインできない

```text
1. Grafana のステータス確認
   $ docker compose -f /opt/monitoring/docker-compose.yml ps grafana

2. パスワードリセット
   $ docker compose -f /opt/monitoring/docker-compose.yml exec grafana \
       grafana cli admin reset-admin-password <new-password>
```
