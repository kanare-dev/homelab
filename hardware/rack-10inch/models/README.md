# models

3D プリント用のデータ（STL、3MF、STEP、元の CAD ファイルなど）を置く。配布元へのリンクは [../README.md](../README.md) にある。

## 置くもの

- 自分で作ったデータ、または自分で寸法を直したデータ
- 配布元のライセンスが再配布を許すデータ（CC BY、CC BY-SA、CC0 など）

## 置かないもの

- 再配布を禁じるライセンスのデータ、ライセンスが書かれていないデータ。リポジトリは公開なので、リンクだけを [../README.md](../README.md) に残す
- 営利目的で使うことになったときの CC BY-NC のデータ（リンクだけに切り替える）

## このディレクトリのライセンス

**このディレクトリのデータは、リポジトリの他の部分とは別のライセンスで提供されている。** 各サブディレクトリの `SOURCE.md` に、作者、元の URL、ライセンス、改変の有無を書いている。再利用するときは、必ずそのファイルを見る。

- `m70q/`: CC BY-SA 4.0（作者名の表示と、改変時の継承が条件）
- `er605/`、`sg2210p/`: CC BY-NC 4.0（作者名の表示が条件。**営利目的では使えない**）

## ライセンスごとの扱い

詳しい判断は [../README.md](../README.md#ライセンスとこのリポジトリに載せてよいか) にある。

| ライセンス | 置いてよいか | 条件 |
| --- | --- | --- |
| CC BY-SA 4.0 | 置いてよい | 作者名、元の URL、ライセンスを明記する。改変したデータも CC BY-SA 4.0 にする |
| CC BY-NC 4.0 | 非営利なら置いてよい | 作者名、元の URL、ライセンスを明記する。営利目的では使わない。迷うときはリンクだけにする |
| CC BY、CC0 | 置いてよい | CC BY は作者名、元の URL、ライセンスを明記する |
| 上記以外、または不明 | 置かない | リンクだけにする |

## 置き方

機器ごとにディレクトリを分ける。

```text
models/
├── m70q/
├── er605/
├── sg2210p/
└── rack/           # 機器に依らない部品（パネル、ブランクなど。まだ無い）
```

- ファイル名は `<モデル名>-<版>.stl` のようにする（例: `m70q-mount-v2.stl`）。
- 配布元から取ったデータは、機器のディレクトリに、次の内容の `SOURCE.md` を添える。
  - 配布元の URL、作者、取得した日
  - ライセンス（名称と URL）
  - 改変の有無と、改変した内容
- 数十 MB を超えるデータは、Git LFS を使うか、リンクだけにする。

## 一覧

| ファイル | 機器 | 出所 | ライセンス | プリント済み |
| --- | --- | --- | --- | --- |
| [m70q/Tiny_Rack_Mount_left_Keystone.stl](m70q/Tiny_Rack_Mount_left_Keystone.stl) | M70q | Tim、[Printables](https://www.printables.com/model/1040412-lenovo-thinkcentre-tiny-10-rack-mount-now-with-opt)（[詳細](m70q/SOURCE.md)） | CC BY-SA 4.0 | 未 |
| [er605/er605-rackmount.stl](er605/er605-rackmount.stl) | ER605 | Jimmi（DivinePrint）、[Printables](https://www.printables.com/model/548330-10-rack-mount-for-tp-link-er605-router-omada)（[詳細](er605/SOURCE.md)） | CC BY-NC 4.0（非営利のみ） | 未 |
| [sg2210p/sg2210p-rackmount.stl](sg2210p/sg2210p-rackmount.stl) | SG2210P | Jimmi（DivinePrint）、[Printables](https://www.printables.com/model/548332-10-rack-mount-for-tp-link-tl-sg2210p-switch-omada)（[詳細](sg2210p/SOURCE.md)） | CC BY-NC 4.0（非営利のみ） | 未 |

3 つとも、配布元のファイルを改変せずに置いている（ファイル名のスペースをハイフンにした 2 つを除き、名前も同じ）。バイト単位で同一であることは、各 `SOURCE.md` の SHA-256 で確かめられる。
