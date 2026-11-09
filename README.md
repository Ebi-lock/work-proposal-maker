# proposal-maker

企画書・提案書を PowerPoint（.pptx）で作る [Claude Code](https://claude.com/claude-code) 用のスキルです。
Claude と対話しながらセクションごとに内容を固め、雛形に沿ったスライドを生成し、提出前のチェックまで行います。

## できること

- **3種類の資料に対応**
  | 種類 | 用途 | 標準構成 |
  |---|---|---|
  | 企画書 | 新商品・新サービス・施策を社内で通す | 15枚（目次・3C・SWOT・As-Is/To-Be・6W2H・4P・スケジュール・予算・効果とリスク など） |
  | 提案書（社外向け） | クライアントへの営業・サービス導入提案 | 11枚（目次・課題の共有・解決策・導入プロセス・効果・費用・スケジュール・会社概要と実績 など） |
  | 提案書（社内向け） | 上司・決裁者への稟議・業務改善提案 | 12枚（目次・結論・現状の課題・代替案比較・費用対効果・体制・リスク など） |
- **最初に種類を確認**：企画書か提案書か、提案書なら社外向けか社内向けかを最初に聞き、それに合った型で進めます
- **セクションごとの対話**：下書きを示し、足りない情報だけを質問します。分からない数字は作らず【要確認】として残し、最後に一覧で示します
- **提出前チェック**：共通項目に加え、社外向け（宛名・敬称、税別/税込、見積の有効期限、事例掲載の許可など）と社内向け（結論が先か、金額換算・ROI、代替案、決裁権限、関連部署の合意など）のチェックリストで確認します
- **統一されたデザイン**
  - フォントはメイリオ1種類のみ
  - 色はベース・サブ・ポイントの3色だけ（毎回ユーザーに確認。決まっていなければ候補を提案）
  - 1スライド1メッセージ（見出しにそのスライドの結論を1文で書く）
  - 文字のはみ出しを自動で縮小・警告し、配色のコントラストも自動調整
- **シンプルなアイコンと画像**
  - 図形で描く単色アイコン（36種）を、見出しや数字の横など一部だけに付けます。画像ファイルが要らず、色は資料の3色に自動で合わせます
  - 商品写真・画面イメージ・ロゴなど、手元の画像を表紙や画像スライドに貼れます
- **文字を詰め込まない**
  - 箇条書きは1枠3〜4項目・1項目30字程度、1枚の本文は200字前後を目安にします
  - 項目数・長すぎる項目・1枚の総字数が目安を超えると警告し、文字を12pt未満には縮めません
- **導線が分かりやすい**
  - 表紙の次に目次を置き、右上の現在地バーで「今どこか」を示します
  - 1枚の中は「見出し（結論）→ 本文（根拠）→ 示唆（だから何か）」の順に、本文から示唆へ矢印でつなぎます

## 必要なもの

- [Claude Code](https://claude.com/claude-code)
- Python 3.9 以上と [python-pptx](https://python-pptx.readthedocs.io/)
  ```bash
  pip install python-pptx
  ```
- （任意）プレビュー機能：macOS と Microsoft PowerPoint。生成した .pptx を PNG にして、Claude が見た目を確認します。無い環境ではこの手順を飛ばします

> 資料のフォントはメイリオです。メイリオが入っていない環境（macOS など）で開くと代替フォントで表示されますが、Windows では指定どおりに表示されます。

## インストール

### プラグインとして入れる（おすすめ）

Claude Code の中で、次の2行を実行します。

```
/plugin marketplace add Ebi-lock/work-proposal-maker
/plugin install proposal-maker@work-proposal-maker
```

Claude Code 2.1.275 以降なら、1行でも入れられます。

```
/plugin install proposal-maker --marketplace Ebi-lock/work-proposal-maker
```

更新は `/plugin marketplace update work-proposal-maker`、削除は `/plugin uninstall proposal-maker@work-proposal-maker` で行えます。

### フォルダをコピーして入れる

プラグインを使わない場合は、スキルのフォルダを Claude Code が読み込む場所にコピーします。

**特定のプロジェクトだけで使う場合**
```bash
git clone https://github.com/Ebi-lock/work-proposal-maker.git
mkdir -p <あなたのプロジェクト>/.claude/skills
cp -r work-proposal-maker/skills/proposal-maker <あなたのプロジェクト>/.claude/skills/
```

**すべてのプロジェクトで使う場合**
```bash
mkdir -p ~/.claude/skills
cp -r work-proposal-maker/skills/proposal-maker ~/.claude/skills/
```

コピー後に Claude Code を起動し直すと、スキル一覧に `proposal-maker` が表示されます。

## 使い方

Claude Code に、作りたい資料を伝えるだけです。

```
新商品の企画書を作りたい
クライアントに出す勤怠システムの提案書を作って
経費精算を電子化する稟議資料を上司に出したい
```

直接呼び出すこともできます。プラグインで入れた場合は `/proposal-maker:proposal-maker`、フォルダをコピーした場合は `/proposal-maker` です。

進め方は次のとおりです。

1. 資料の種類（企画書／提案書、社外向け／社内向け）を確認
2. 概要（テーマ・相手・目的・期限など）をヒアリング
3. 使う3色（ベース・サブ・ポイント）を確認
4. セクションごとに下書きを示し、足りない情報を質問
5. 各スライドの見出しで骨子を確認し、チェックリストで点検
6. .pptx を生成し、見た目を確認して修正
7. 完成ファイルのパス・残った要対応項目・【要確認】の一覧を報告

## スクリプトを直接使う

Claude を介さず、JSON から直接スライドを生成することもできます。

```bash
cd skills/proposal-maker
python3 scripts/build_deck.py assets/example_kikaku.json -o 企画書_サンプル.pptx
```

JSON の書き方は [`references/schema.md`](skills/proposal-maker/references/schema.md) を、完成例は `assets/` の3ファイルを参照してください。

プレビュー（macOS ＋ PowerPoint）：
```bash
bash scripts/preview.sh 企画書_サンプル.pptx ./preview
```

## ファイル構成

```
.claude-plugin/
├── plugin.json                    # プラグインの設定
├── marketplace.json               # マーケットプレイスの設定
└── icon.png
skills/proposal-maker/
├── SKILL.md                       # スキル本体（進め方・デザインルール）
├── references/
│   ├── kikakusho.md               # 企画書のセクション別ヒアリングガイド
│   ├── teiansho.md                # 提案書（社外・社内）の構成とヒアリングガイド
│   ├── checklist.md               # 提出前チェックリスト
│   └── schema.md                  # スライド JSON の仕様
├── scripts/
│   ├── build_deck.py              # JSON → .pptx 生成
│   ├── icons.py                   # 図形で描くアイコン集
│   ├── preview.sh                 # .pptx → PNG（macOS ＋ PowerPoint）
│   └── pdf2png.swift              # preview.sh が使う PDF → PNG 変換
└── assets/
    ├── example_kikaku.json        # 商品企画書の例
    ├── example_teian_external.json # 社外向け提案書の例
    └── example_teian_internal.json # 社内向け提案書の例
```

## 注意事項

- サンプルに出てくる会社名・商品名・数値はすべて架空です
- このスキルは、根拠のない数字や事例を作らないように作られています。生成された資料の数値・固有名詞は、提出前に必ずご自身で確認してください

## ライセンス

[MIT License](LICENSE)
