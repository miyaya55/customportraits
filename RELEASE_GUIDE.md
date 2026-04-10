# Release Guide

GitHub Releases に配布版を載せるときの簡易手順です。

## 推奨バージョン表記

- タグ名: `v1.0.0`
- Release タイトル: `v1.0.0`
- exe ファイル名: `CustomPortraitTool.exe`

## 手順

1. `VERSION` の番号を更新します
2. 必要なら README の配布情報も更新します
3. `build_exe.bat` か PyInstaller で exe を再ビルドします
4. GitHub で新しい Release を作成します
5. タグ名とタイトルを `v1.0.0` 形式で入力します
6. `RELEASE_NOTES_v1.0.0.md` をベースに本文を貼ります
7. `dist/CustomPortraitTool.exe` を添付します
8. 公開します

## 今回の初回公開向けメモ

- 現在のバージョン: `v1.0.0`
- Release 本文: `RELEASE_NOTES_v1.0.0.md`
- 添付ファイル: `dist/CustomPortraitTool.exe`

## 更新時の目安

- 小さな修正: `v1.0.1`, `v1.0.2`
- 機能追加: `v1.1.0`
- 大きな変更: `v2.0.0`
