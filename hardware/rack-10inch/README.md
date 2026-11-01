# 10 インチラックマウント（3D プリント）

ThinkCentre M70q Tiny、ER605、SG2210P を 10 インチラックに収めるための、3D プリント用マウントを管理する。プリント用のデータ（STL など）は [models/](models/README.md) に置き、配布元のサイトへのリンクはこの文書にまとめる。

> [!NOTE]
> 状況は 2026-11-01 時点。リンク先の内容（対応機種・寸法・ライセンス）は、検索結果の要約で確認したもので、**ページ本体は確認できていない**。プリントする前に、配布ページで対応機種・ネジの種類・ライセンスを確認し、この表を更新する。

## 対象機器

| 機器 | 役割 | 状況 | 備考 |
| --- | --- | --- | --- |
| Lenovo ThinkCentre M70q Tiny | Proxmox ホスト（`192.168.11.10`） | 稼働中 | 配布元の対応表に載っていても、実機の穴位置と合わない場合がある。M70q は「判断が写真とデータシート頼み」と注記するモデルがあり、実機で確認する |
| TP-Link ER605 V2 | ルーター | 未購入 | [Omada・VLAN 化](../../docs/operations/roadmap/04-network-omada-vlan.md)の段階 1 で導入 |
| TP-Link SG2210P | PoE+ マネージドスイッチ（8 ポート + SFP 2 スロット） | 未購入 | SG2008P から変更（[VLAN 設計](../../docs/architecture/08-vlan-design.md#導入の段階)）。版数の確認が必要 |

## 配布元のリンク

「確認状況」は、リンク先のページで対応機種を自分で確かめたかどうか。今は全て未確認。

| 対象 | 名前 | 配布元 | ライセンス | 確認状況 |
| --- | --- | --- | --- | --- |
| ER605 + Omada 機器 | 10in Server Rack TP-Link Omada（OC200 と ER605 に対応するとの記載） | [MakerWorld](https://makerworld.com/en/models/664449) | 未確認 | 未確認 |
| ThinkCentre Tiny | Lenovo ThinkCentre Tiny half-width rack mount | [Printables](https://www.printables.com/model/971551-lenovo-thinkcentre-tiny-half-width-rack-mount) | 未確認 | 未確認。M70q が対応表にあるか確認する |
| ThinkCentre Tiny | ThinkCentre 向け 10 インチラックマウント（検索結果の 1 件。名前は未確認） | [MakerWorld](https://makerworld.com/models/1141511) | 未確認 | 未確認。M70q 対応と、どの作者のモデルかを確認する |
| SG2210P | TP-Link Omada 2x TL-SG2210P 19" Rackmount Rack Adapter（2 台用。19 インチ向けで、10 インチには使えない可能性が高い） | [stlfinder（Printables のミラー）](https://stlfinder.com/model/marie/3985288) | CC BY-NC（検索結果の記載） | 未確認。元の Printables のページを探して差し替える |

候補を足すときは、この表に 1 行追加する。目的の機器に対応しない・ライセンスが合わないと分かったものも、理由を書いて残す。

## 検索のメモ

- 検索では、SG2210P・ER605・Raspberry Pi 4 を 1 つにまとめた Thingiverse のモデル（2026 年 3 月）も見つかった。レビューに「穴の間隔が違い、ネジを 2 本しか締められない」とあるので、使わない方針。
- ER605 だけを 10 インチラックに載せる Printables のモデル（3U 用アダプター）も見つかっている。リンクは未取得。
- 3 機種を 1 つにまとめたモデルは見つからなかった。機器ごとにモデルを選び、1 つのラックに並べる。

## 運用のルール

- 置くデータの扱いは [models/README.md](models/README.md) に従う。**このリポジトリは公開なので、ライセンスを確認してから置く。**
- 実機に合わせて寸法や穴位置を直したら、元のデータを残したまま、直したデータを別名で置く。何を直したかは [models/README.md](models/README.md) の一覧に書く。
- 機器を変える（SG2008P → SG2210P のような変更）ときは、この文書の「対象機器」を更新する。
- ラックの構成が決まったら、[構成図](../../docs/architecture/01-overview.md)に反映する。

## 未決事項

- [ ] ラック本体（10 インチ、何 U か）を何にするか。市販品か、3D プリントか
- [ ] 各機器の配布元モデルを 1 つずつ選び、対応機種とライセンスを確認する
- [ ] M70q の実機の穴位置・寸法を測って、選んだモデルと合うか確認する
- [ ] SG2210P の版数と寸法を、購入前に販売ページで確認する
