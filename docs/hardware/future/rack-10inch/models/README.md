# models

3D プリント用のデータ（STL、3MF、STEP など）の置き場所。**データ本体は Git 管理しない**（`.gitignore`。2026-11-20 に外した）。リポジトリに載るのは、この README と、出所を書いた各 `SOURCE.md` だけ。配布元へのリンクは [../README.md](../README.md) にある。

## Git 管理しない理由

- 3 つとも、他の作者のモデルで、リポジトリ本体（MIT。`LICENSE`）とは別のライセンス（CC BY-SA 4.0、CC BY-NC 4.0）。ライセンスを混ぜないため、リポジトリには、データを置かない。
- 手元には、ファイルがある（`.gitignore` で、Git には入らない）。無くしたときは、各 `SOURCE.md` の配布元から取り直す。SHA-256 で、同じファイルかを確かめられる。
- **過去のコミット（2026-11-01〜11-20）には、データが入ったまま**（履歴からは消していない）。

## 置き方（手元）

機器ごとにディレクトリを分ける。

```text
models/
├── m70q/
├── er605/
├── sg2210p/
└── rack/           # 機器に依らない部品（パネル、ブランクなど。まだ無い）
```

- ファイル名は `<モデル名>-<版>.stl` のようにする（例: `m70q-mount-v2.stl`）。
- 配布元から取ったデータは、機器のディレクトリに、次の内容の `SOURCE.md` を添える（`SOURCE.md` は Git 管理する）。
  - 配布元の URL、作者、取得した日
  - ライセンス（名称と URL）
  - 改変の有無と、改変した内容
  - SHA-256

## 一覧（データは、手元にあり、Git 管理外）

| ファイル | 機器 | 出所 | ライセンス | プリント済み |
| --- | --- | --- | --- | --- |
| `m70q/Tiny_Rack_Mount_left_Keystone.stl` | M70q | Tim、[Printables](https://www.printables.com/model/1040412-lenovo-thinkcentre-tiny-10-rack-mount-now-with-opt)（[詳細](m70q/SOURCE.md)） | CC BY-SA 4.0 | 未 |
| `er605/er605-rackmount.stl` | ER605 | Jimmi（DivinePrint）、[Printables](https://www.printables.com/model/548330-10-rack-mount-for-tp-link-er605-router-omada)（[詳細](er605/SOURCE.md)） | CC BY-NC 4.0（非営利のみ） | 未 |
| `sg2210p/sg2210p-rackmount.stl` | SG2210P | Jimmi（DivinePrint）、[Printables](https://www.printables.com/model/548332-10-rack-mount-for-tp-link-tl-sg2210p-switch-omada)（[詳細](sg2210p/SOURCE.md)） | CC BY-NC 4.0（非営利のみ） | 未 |

3 つとも、配布元のファイルを改変せずに、手元に置いている（ファイル名のスペースをハイフンにした 2 つを除き、名前も同じ）。バイト単位で同一であることは、各 `SOURCE.md` の SHA-256 で確かめられる。

## ライセンスごとの扱い（もう一度、リポジトリに載せるときの判断）

詳しい判断は [../README.md](../README.md#ライセンスとこのリポジトリに載せてよいか) にある。

| ライセンス | 置いてよいか | 条件 |
| --- | --- | --- |
| CC BY-SA 4.0 | 置いてよい | 作者名、元の URL、ライセンスを明記する。改変したデータも CC BY-SA 4.0 にする |
| CC BY-NC 4.0 | 非営利なら置いてよい | 作者名、元の URL、ライセンスを明記する。営利目的では使わない。迷うときはリンクだけにする |
| CC BY、CC0 | 置いてよい | CC BY は作者名、元の URL、ライセンスを明記する |
| 上記以外、または不明 | 置かない | リンクだけにする |

ただし、リポジトリ本体を MIT にしたので、**他の作者のデータは、Git 管理しない**方針（上）。
