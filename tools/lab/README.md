# lab — homelab 監視 CLI

VM とサービスの状態を確認する CLI ツール。

## 使い方

```bash
# ビルド
go build -o lab .

# 状態確認（lab.yaml を自動検索）
./lab status

# 設定ファイルを指定
./lab status -c /path/to/lab.yaml
```

`go mod tidy` は依存パッケージをダウンロードし、`go.sum` にチェックサムを記録する。`go.sum` は再現可能なビルドのために Git にコミットする。

## 出力例

```
NAME                 SERVICE              STATUS
----                 -------              ------
vm-infra             coredns              UP
vm-infra             caddy                UP
vm-infra             tailscale            UP
vm-monitoring        grafana              UP
vm-monitoring        prometheus           UP
vm-monitoring        node_exporter        UP
```

## 設定 (lab.yaml)

`lab.yaml` で VM とサービス、チェック方法を定義する。

| チェック | 説明 |
|---------|------|
| `tcp`   | TCP ポートへの接続 |
| `udp`   | UDP ポートへの接続 |
| `http`  | HTTP GET で 2xx/3xx を期待 |

設定ファイルの検索順序:

1. `-c` オプションで指定したパス
2. 環境変数 `LAB_CONFIG`
3. カレントディレクトリの `lab.yaml`、`lab/lab.yaml`、`tools/lab/lab.yaml`
4. バイナリと同じディレクトリの `lab.yaml`
5. `~/.config/homelab/lab.yaml`
