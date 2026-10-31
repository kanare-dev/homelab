# GPU 搭載ゲーミング PC 兼ホームサーバー

[ロードマップ](../roadmap.md)の大型計画。未着手。構成を決めて購入に進むときは、設計書（`docs/architecture/`）と構成図の更新、ADR の追加を同じ変更で行う。

## 目的

- PC ゲームへの入門
- ローカル LLM・機械学習の実行環境構築
- GPU 計算リソースのホームラボへの統合
- MacBook Pro からのリモート操作環境構築
- 将来的なハードウェア・サーバー用途の拡張

## 基本方針

- 予算: 20〜25 万円
- BTO の Windows デスクトップ PC を購入
- 普段はヘッドレスで運用し、MacBook Pro からリモート接続
- 必要に応じてディスプレイ・キーボードを直接接続可能にする
- GPU 性能だけでなく、拡張性・静音性・冷却性能を重視
- 常時稼働サービスは既存 ThinkCentre に配置し、GPU 搭載 PC は必要時のみ起動

## ハードウェア構成（候補）

| パーツ | 推奨構成 |
| --- | --- |
| CPU | Ryzen 5 7600 / Ryzen 7 7700（AM5） |
| GPU | NVIDIA RTX 5060 Ti 16GB 以上 |
| RAM | DDR5 32GB（将来 64GB 以上へ拡張） |
| SSD | NVMe 1TB 以上 |
| マザーボード | B650 / B850（拡張性重視） |
| 電源 | 750W 80 PLUS Gold 以上 |
| ケース | ATX ミドルタワー（静音・冷却・拡張性重視） |
| ネットワーク | 有線 LAN（可能なら 2.5GbE） |

購入前の確認事項:

- RAM スロット数・最大搭載容量
- M.2 スロット数・空きスロット
- PCIe スロット構成
- 将来の大型 GPU への交換可否
- 電源容量・補助電源コネクタ
- Wake-on-LAN 対応（UEFI・NIC）
- BTO メーカーの保証条件とパーツ交換制限

## OS・ソフトウェア構成

- ホスト OS: Windows 11
- Linux 環境: WSL2（Ubuntu）
- ゲーム: Steam
- リモートゲーミング: Sunshine（ホスト）+ Moonlight（Mac）
- 開発・管理: SSH / VS Code Remote
- コンテナ: Docker
- ローカル LLM: Ollama / Open WebUI
- 機械学習: CUDA / PyTorch
- GPU 監視: NVIDIA SMI / Prometheus / Grafana

## ネットワーク・運用構成

- MacBook Pro: メイン操作端末
- GPU 搭載 PC: ゲーム・LLM 推論・機械学習
- ThinkCentre: DNS・監視・Docker 等の常時稼働サービス
- Omada: LAN・VLAN・ネットワーク管理

運用方針:

- GPU 搭載 PC は有線 LAN 接続
- MacBook から Moonlight でゲームをプレイ
- SSH で WSL2 の Linux 開発環境へ接続
- Wake-on-LAN でリモート起動
- 未使用時はシャットダウンして消費電力を削減
- ヘッドレス運用に必要な仮想ディスプレイを設定
- 障害時は物理ディスプレイ・キーボードを接続して復旧
- Open WebUI 等の常時稼働フロントエンドは ThinkCentre に配置し、GPU 搭載 PC 上の Ollama API へ接続

## 導入ロードマップ

### Phase 1: 機種選定・購入

- [ ] BTO メーカー・機種の比較
- [ ] GPU VRAM 16GB 以上を確保
- [ ] RAM 32GB 以上を確保
- [ ] マザーボード・電源・ケースの拡張性を確認
- [ ] Wake-on-LAN 対応を確認
- [ ] 予算 20〜25 万円以内で購入

### Phase 2: Windows・リモートゲーミング環境

- [ ] Windows 初期設定・GPU ドライバー導入
- [ ] Steam 導入
- [ ] Sunshine 導入
- [ ] MacBook Pro に Moonlight 導入
- [ ] LAN 内でゲームストリーミングを検証
- [ ] 遅延・画質・フレームレートを測定
- [ ] 仮想ディスプレイ設定
- [ ] ヘッドレス運用を検証

### Phase 3: リモート管理・電源制御

- [ ] 有線 LAN 接続・IP アドレス固定化（DHCP 予約）
- [ ] Wake-on-LAN 設定
- [ ] MacBook からのリモート起動を検証
- [ ] Windows のリモート管理環境を構築
- [ ] WSL2 への SSH 接続を構築
- [ ] 再起動・障害時の復旧手順を整備

### Phase 4: GPU 計算環境

- [ ] WSL2 Ubuntu 導入
- [ ] CUDA 対応環境構築
- [ ] Docker 環境構築
- [ ] PyTorch で GPU 動作確認
- [ ] Ollama 導入
- [ ] ローカル LLM の推論性能を測定
- [ ] ThinkCentre 上の Open WebUI と連携
- [ ] MacBook から LLM API を利用

### Phase 5: ホームラボ統合

- [ ] Omada ネットワークへ統合
- [ ] VLAN・ファイアウォールルール設計
- [ ] GPU 使用率・VRAM・温度・消費電力の監視
- [ ] Prometheus / Grafana への統合
- [ ] GPU 搭載 PC の稼働状態を可視化
- [ ] GPU 計算ジョブのリモート実行を整備

### Phase 6: 将来的な拡張

- [ ] RAM 64GB 以上への増設
- [ ] NVMe SSD 追加
- [ ] 大容量 VRAM GPU への交換検討
- [ ] Linux ネイティブ環境への移行検討
- [ ] Proxmox / GPU パススルーの検証
- [ ] Kubernetes からの GPU ワークロード実行
- [ ] ローカル LLM 推論サーバーの高度化
- [ ] 複数端末からの GPU リソース利用

## 設計上の注意点

- ゲームの互換性を優先し、初期構成は Windows 11 を採用
- Proxmox は初期導入せず、将来の検証対象とする
- GPU の VM 間共有には技術的制約がある
- GPU 搭載 PC の停止中は LLM API を利用できない
- Windows Update による再起動・サービス停止を考慮する
- WSL2 のサービス自動起動・復旧方法は別途設計する
- Wake-on-LAN は機種・設定によって動作条件が異なる
- 24 時間稼働による電気代・発熱・騒音に注意する

## 最終的な目標

MacBook Pro をメイン端末として、必要なときに GPU 搭載 PC をリモート起動し、ゲーム・LLM 推論・機械学習を実行できる環境を構築する。

既存 ThinkCentre を常時稼働サーバーとして活用しながら、GPU 搭載 PC をオンデマンドの高性能計算ノードとして統合する。

将来的には、GPU リソースをホームラボ内の複数サービスや Kubernetes ワークロードから利用できる構成へ発展させる。
