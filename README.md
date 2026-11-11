# 機械設備 標準仕様書・標準図 工事別まとめ

国土交通省「公共建築工事標準仕様書（機械設備工事編）令和7年版（修補版）」と
「公共建築設備工事標準図（機械設備工事編）令和7年版」から、次の工事にかかわる条文・標準図を
工事別に整理した静的サイトです。スマホ・PCどちらでも閲覧できます。

| ページ | 内容 |
|---|---|
| `reibai.html` | 冷媒配管 |
| `drain.html` | ドレン配管 |
| `duct.html` | ダクト |
| `eisei.html` | 衛生配管（給水・給湯・排水・通気） |
| `kyotsu.html` | 共通事項（配管施工・保温の一般事項） |

各ページの構成
- **早見表**：主要な数値・ルールの要約（根拠条項つき）
- **標準仕様書 条文**：原本PDFからテキストを機械抽出（原本ページ画像へのリンク付き）
- **標準図**：該当図の画像（タップで拡大）

## GitHub Pages での公開
Settings → Pages → Build and deployment → Source: **Deploy from a branch** → Branch: `main` / `/ (root)` → Save

## 再生成（版が改定されたとき）
`tools/` のスクリプトで原本PDFから再生成できます（poppler-utils の `pdftotext` / `pdftoppm` と Python 3 が必要）。

```sh
mkdir src
# 国交省サイトから原本PDFを取得して src/spec.pdf, src/zu.pdf として保存
pdftotext -layout src/spec.pdf src/spec.txt
pdftotext -layout src/zu.pdf src/zu.txt
cd tools && python3 build.py ../src ..
```
掲載条項・早見表・標準図のページは `tools/content.py` で定義しています。

## 出典・注意
- 出典：「公共建築工事標準仕様書（機械設備工事編）令和7年版（修補版）」（国土交通省大臣官房官庁営繕部）
  https://www.mlit.go.jp/gobuild/gobuild_tk6_000058.html 、
  「公共建築設備工事標準図（機械設備工事編）令和7年版」（同）
  https://www.mlit.go.jp/gobuild/gobuild_tk4_000021.html を加工して作成。
- 国土交通省ウェブサイトの利用ルール（公共データ利用規約 第1.0版準拠）に基づき掲載しています。本サイトは国土交通省が作成・監修したものではありません。
- 早見表は要約です。実際の工事では設計図書（特記仕様・図面等）が標準仕様書に優先します。必ず原本・設計図書で確認してください。
