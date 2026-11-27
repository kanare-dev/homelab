# Omada の設定値（書き出し）

Omada コントローラーの設定値を、Open API で取り出したもの。`make omada-export`（`tools/omada-export.py`）が書き出す。手で編集しない。

正は [Omada コントローラーの設定値](../../omada-controller.md)（パラメーターシート）で、このファイル群は実機の姿である。両者の食い違いが、ずれである（[ADR-0041](../../../../../adr/0041-omada-settings-exported-by-open-api.md)）。Omada の設定を変えたら、書き出し直して `git diff` を確かめ、パラメーターシートと同じ変更でコミットする。

秘密の値、シリアル番号、実行のたびに変わる値は落としてある。機器の MAC アドレスは、機器の名前（`rtr01`、`sw01`）に置き換えてある。
