# content.json の形式

`scripts/build_deck.py` に渡す JSON の仕様。完成例：
- `assets/example_kikaku.json`：商品企画書
- `assets/example_teian_external.json`：社外向け提案書（クライアント営業）
- `assets/example_teian_internal.json`：社内向け提案書（稟議・改善提案）

## 全体構造
```json
{
  "meta":   { ... },   // 表紙・フッターの情報
  "theme":  { ... },   // 色とフォント
  "slides": [ ... ]    // スライドの配列（上から順に出力）
}
```

## meta
| キー | 必須 | 内容 |
|---|---|---|
| title | ○ | 企画名・提案名（表紙とフッターに出る） |
| subtitle | | サブタイトル |
| category | | 表紙の小見出し（例: "商品企画書" "ご提案書" "改善提案書"） |
| to | | 宛先（提案書で使う。例: "株式会社〇〇 御中" "管理本部長 殿"）。表紙の左上に出る |
| company | | 自社名（社外向け提案書で使う） |
| department | ○ | 提出部署 |
| author | ○ | 氏名 |
| date | ○ | 提出日（例: "2026年11月9日"） |
| confidential | | true で「社外秘」、文字列ならその文言 |

## theme
| キー | 必須 | 内容 |
|---|---|---|
| base | ○ | ベース色（例: "#1F4E5F"）。見出し帯、セクション名、表のヘッダー |
| sub | ○ | サブ色。補助の見出し帯（SWOTの下段、As-Is など）、ガントバー。薄めた色はカード背景 |
| accent | ○ | ポイント色。示唆ボックス、highlight 指定の数字、締切、表紙のライン |
| font | | 既定 "Meiryo"（メイリオ）。変更しない |

本文は濃いグレー（#333333）、背景は白で固定。淡い背景色は3色を薄めて自動生成するため、色数は増えない。

## slides 共通
すべてのスライド（cover 以外）で使えるキー：
| キー | 内容 |
|---|---|
| type | スライドの種類（下記） |
| message | このスライドで言いたいこと1文（見出しに大きく出る）。**必須**。40字前後で1行に収める（超えると警告） |
| section | 左上のセクション名。省略時は種類ごとの既定名 |
| insight | 下部の示唆ボックス（ポイント色）。文字列または文字列の配列 |
| insight_label | 示唆ボックスのラベル（既定は種類ごと：「示唆」「成功のカギ（KSF）」など） |
| sources | 出典。文字列または配列。下部に小さく出る |

箇条書きの項目は文字列の配列で渡す。1項目は全角40字以内を目安に。

## スライド種類

### cover
`{"type": "cover"}`。meta の内容で表紙を作る。slides の先頭に無ければ自動で追加される。

### summary（エグゼクティブサマリー）
```json
{"type": "summary", "message": "...",
 "items": [{"label": "目的", "text": "..."}, {"label": "施策", "text": "..."}, {"label": "期待効果", "text": "..."}],
 "kpis": [{"value": "1.2億円", "label": "初年度売上目標", "highlight": true}]}
```
items は2〜4個。kpis は任意（0〜4個）。

### background（背景・現状分析）
```json
{"type": "background", "message": "...",
 "points": ["...", "..."],
 "data": [{"value": "30%", "label": "...", "highlight": true}],
 "sources": ["..."]}
```
data は任意（0〜3個）。無ければ本文が全幅になる。

### three_c（3C分析）
```json
{"type": "three_c", "message": "...",
 "customer": ["..."], "competitor": ["..."], "company": ["..."],
 "insight": "成功のカギ（1文）"}
```

### swot（SWOT分析）
```json
{"type": "swot", "message": "...",
 "strengths": ["..."], "weaknesses": ["..."], "opportunities": ["..."], "threats": ["..."],
 "insight": ["SO：...", "WT：..."]}
```

### asis_tobe（As-Is / To-Be）
```json
{"type": "asis_tobe", "message": "...",
 "asis": ["..."], "tobe": ["..."], "gaps": ["...", "..."]}
```
gaps は下部に「ギャップ＝解決すべき課題」として番号付きで出る。

### goals（課題とゴール）
```json
{"type": "goals", "message": "...",
 "issues": ["..."],
 "quantitative": [{"metric": "売上", "target": "1.2億円", "deadline": "2027年度末", "highlight": true}],
 "qualitative": ["..."]}
```
quantitative は1〜3個。

### target_concept（ターゲット・コンセプト）
```json
{"type": "target_concept", "message": "...",
 "persona": {"profile": "34歳・共働き…", "attributes": ["..."], "needs": ["..."]},
 "concept": {"catch": "20字前後の一文", "description": "2文程度", "values": ["..."]}}
```

### plan_6w2h（企画内容）
```json
{"type": "plan_6w2h", "message": "...",
 "rows": {"why": "...", "whom": "...", "what": "...", "how": "...",
          "how_much": "...", "when": "...", "where": "...", "who": "..."}}
```
各値は文字列（全角50字以内目安）か配列。空欄は【要確認】と表示される。

### product_4p（商品戦略）
```json
{"type": "product_4p", "message": "...",
 "product": ["..."], "price": ["..."], "place": ["..."], "promotion": ["..."]}
```

### schedule（スケジュール・体制）
```json
{"type": "schedule", "message": "...",
 "periods": ["12月", "1月", "2月"],
 "phases": [{"name": "商品開発", "owner": "商品開発部", "start": "12月", "end": "1月",
             "highlight": false, "label": "バー上の注記（任意）"}],
 "team": [{"role": "プロジェクト責任者", "name": "山田 花子（商品開発部）"}]}
```
start / end は periods のラベル、または0始まりの番号。phases は8行以内、team は5人以内が見やすい。

### budget（予算・収支計画）
```json
{"type": "budget", "message": "...",
 "costs": [{"item": "商品開発費", "amount": "600万円", "note": "..."}],
 "total": "3,000万円",
 "plan": {"title": "収支計画", "headers": ["", "1年目", "2年目"], "rows": [["売上", "1.2億円", "1.8億円"]]},
 "metrics": [{"value": "18か月", "label": "投資回収期間", "highlight": true}]}
```
plan・metrics は任意。costs は7行以内が見やすい。

### effect_risk（期待効果とリスク・対策）
```json
{"type": "effect_risk", "message": "...",
 "effects": ["..."],
 "risks": [{"risk": "...", "impact": "大", "countermeasure": "..."}]}
```
impact は任意（1つでもあれば「影響度」列が出る）。

effect_risk は `effects_label` で左カードの見出しを変えられる（社内向け提案書では「関連部署への影響」など）。

### next_action（ネクストアクション／まとめ）
```json
{"type": "next_action", "message": "...",
 "conclusion": "提案の総括（任意。上部に大きく出る）",
 "asks": [{"text": "本企画の承認", "deadline": "11月20日まで"}],
 "contact": "お問い合わせ：..."}
```
asks は conclusion がある場合は3件以内に。

---
## 提案書向けのスライド

### current_issues（背景・現状の課題）
```json
{"type": "current_issues", "message": "...",
 "issues": [{"title": "集計の手間", "detail": ["...", "..."], "impact": "締め日前の残業が常態化"}],
 "data": [{"value": "40時間", "label": "月間の集計作業"}],
 "insight": "このままにした場合の損失（1文）",
 "sources": ["2026年10月 ヒアリングより"]}
```
issues は2〜4個（5個以上は2段になる）。data は任意。insight の既定ラベルは「このままにした場合」。

### solution（提案内容）
```json
{"type": "solution", "message": "...",
 "overview": "提案の要点を1〜2文（任意）",
 "items": [{"title": "ICカード打刻", "issue": "集計の手間", "text": ["...", "..."]}]}
```
items は2〜4個。issue に対応する課題名を書くと、カードの上に「対応する課題：〜」と出る。

### process（導入ステップ）
```json
{"type": "process", "message": "...",
 "steps": [{"title": "要件確認", "period": "1月", "text": ["...", "..."], "highlight": false}]}
```
steps は3〜5段階。

### benefits（期待される効果）
```json
{"type": "benefits", "message": "...",
 "metrics": [{"label": "月間の集計作業", "value": "▲38時間", "before": "40時間", "after": "2時間", "highlight": true}],
 "points": ["数字にしにくい効果"],
 "points_label": "その他の効果",
 "sources": ["試算の前提"]}
```
metrics は1〜3個。before と after の両方があると「40時間 → 2時間」と出る。片方だけなら補足として出る。

### options（プラン比較／比較検討した案）
```json
{"type": "options", "message": "...",
 "plans": [{"name": "スタンダード", "price": "月額 100,000円", "note": "1名400円×250名",
            "features": ["..."], "recommended": true, "tag": "おすすめ"}],
 "sources": ["価格は税別。見積有効期限：…"]}
```
plans は2〜3案。recommended は1案だけ（ポイント色の枠と「推奨」タグが付く）。

### company（会社概要・実績）
```json
{"type": "company", "message": "...",
 "profile": [{"label": "会社名", "value": "..."}],
 "achievements": [{"value": "1,200社", "label": "導入企業数"}],
 "cases": ["物流A社：集計作業を月60時間削減"],
 "cases_label": "主な導入事例"}
```

### bullets（汎用）
上記に当てはまらない内容（補足資料など）用。
```json
{"type": "bullets", "section": "補足：市場規模の試算", "message": "...", "bullets": ["..."]}
```

## highlight（ポイント色）の使い方
ポイント色は「一番見てほしい所」だけに使う。1枚につき highlight は1か所までが目安。示唆ボックスもポイント色を使うので、示唆があるスライドでは数字の highlight を控えめにする。
