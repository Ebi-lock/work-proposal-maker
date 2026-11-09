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
| image | | 表紙の右側に出す画像のパス（商品写真・パッケージ案など）。JSON ファイルからの相対パスか絶対パス |
| logo | | 表紙の右下に出すロゴ画像のパス |
| icon | | image が無いとき、表紙の右側に大きく出すアイコン名（下記「アイコン」） |

## theme
| キー | 必須 | 内容 |
|---|---|---|
| base | ○ | ベース色（例: "#1F4E5F"）。見出し帯、セクション名、表のヘッダー |
| sub | ○ | サブ色。補助の見出し帯（SWOTの下段、As-Is など）、ガントバー。薄めた色はカード背景 |
| accent | ○ | ポイント色。示唆ボックス、highlight 指定の数字、締切、表紙のライン |
| font | | 既定 "Meiryo"（メイリオ）。変更しない |
| progress | | 既定 true。右上の「現在地バー」（全体の何枚目か）を出す。false で消す |

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

箇条書きの項目は文字列の配列で渡す。

## 文字量の目安（書き込みすぎない）
スライドは読ませる資料ではなく、見て分かる資料にする。説明は口頭か補足資料に回す。
| 対象 | 目安 | 超えたとき |
|---|---|---|
| 見出し（message） | 40字前後・1行 | 警告 |
| 箇条書き1項目 | 30字程度（45字を超えると警告） | 警告 |
| 1つの枠の箇条書き | 3〜4項目（6項目以上で警告） | 警告 |
| 1枚の本文の合計 | 150〜200字（250字を超えると警告） | 警告 |
| 最小の文字サイズ | 本文12pt（これ以上は縮めず、はみ出す場合は警告） | 警告 |

## アイコン
シンプルな単色アイコンを、図形で描いて入れられる（画像ファイルは不要。色は資料の3色から自動で決まる）。
アイコンは「一部」に使う。見出しの横や数字の上など、内容の種類を一目で区別したい所だけに付け、全部の項目に付けない。

使える名前（英小文字）：
| 分類 | 名前 |
|---|---|
| 人・組織 | user（人）、users（チーム）、building（会社）、store（店舗）、award（実績・受賞） |
| 分析・目標 | chart（棒グラフ）、trend（成長）、target（目標）、search（調査・分析）、checklist（一覧・手順）、check（完了・OK）、idea（アイデア・解決策）、flag（ゴール・競合） |
| お金・時間・計画 | yen（お金・費用）、clock（時間）、calendar（日程）、document（書類・計画）、package（商品・梱包） |
| 状態・注意 | warning（課題・リスク）、shield（安全・対策）、lock（セキュリティ）、up（増加）、down（減少）、star（おすすめ）、heart（満足）、bolt（スピード） |
| 仕組み・手段 | gear（仕組み・設定）、cloud（クラウド）、globe（海外・全国）、phone（スマホ）、mail（メール）、chat（相談・声）、cart（購入）、truck（配送）、leaf（環境）、picture（画像） |

別名も使える（例：money→yen、time→clock、risk→warning、team→users、product→package）。不明な名前は警告が出て、アイコンなしで作られる。

`icon` を付けられる場所：
- summary の items と kpis、background の data、goals の quantitative、budget の metrics、company の achievements
- current_issues の issues と data、solution の items、process の steps、benefits の metrics
- agenda の items（省略時は自動）

最初からアイコンが付くスライド：three_c（users・flag・building）、product_4p（package・yen・store・chat）、target_concept（ペルソナに user）。
変えるときは `"icons": {"customer": "user"}` のように上書きし、消すときは `"icons": false` を付ける。

## 画像
ユーザーの手元にある画像（商品写真・試作品・パッケージ案・画面イメージ・ロゴなど）を貼れる。PNG・JPEG が使える。
- パスは JSON ファイルからの相対パス、または絶対パス
- 枠に収まるよう縦横比を保って縮小する（切り抜かない）
- ファイルが見つからない場合は、枠と「画像：ファイル名」を置き、【要確認】の一覧に出す
- 画像を作ったり、ネットから拾ったりしない。ユーザーが用意したものだけを使う

使える場所：表紙（meta.image・meta.logo）、bullets の image、visual スライド

## スライド種類

### cover
`{"type": "cover"}`。meta の内容で表紙を作る。slides の先頭に無ければ自動で追加される。

### agenda（目次）
```json
{"type": "agenda", "message": "市場の空白を確認し、商品・計画・投資判断の順にご説明します"}
```
表紙の次に置く。items を省くと、後ろのスライドのセクション名とアイコンから自動で作る（同じセクション名が続く場合は1つにまとめる）。
自分で書く場合：`"items": [{"label": "課題の確認", "icon": "warning", "text": "補足（任意）"}]`。7項目以上は2列になる。
目次は、左上のセクション番号（01, 02…）と現在地バーの数には入らない。

### summary（エグゼクティブサマリー）
```json
{"type": "summary", "message": "...",
 "items": [{"label": "目的", "text": "...", "icon": "target"}, {"label": "施策", "text": "...", "icon": "idea"}, {"label": "期待効果", "text": "...", "icon": "trend"}],
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
{"type": "bullets", "section": "補足：市場規模の試算", "message": "...", "bullets": ["..."], "image": "images/chart.png"}
```
image は任意。あると右半分に画像、左半分に箇条書きになる。

### visual（画像が主役のスライド）
商品イメージ・画面イメージ・店頭イメージ・写真など、見せた方が早い内容に使う。
```json
{"type": "visual", "section": "商品イメージ", "message": "...",
 "images": [{"path": "images/package.png", "caption": "5袋入りパック"}, {"path": "images/serve.jpg", "caption": "1袋＝1杯分"}]}
```
images は1〜3枚。caption は短く（15字程度）。

## 導線（読む順番）を分かりやすくする仕組み
スクリプトが自動で入れるもの：
- 右上の現在地バー：全体の何枚目かが分かる
- 本文 → 示唆ボックスの間の小さな下向き矢印：「この情報から、こう言える」という流れを示す
- process の矢羽根、asis_tobe の矢印、課題・解決策の番号

JSON を書く側で気をつけること：
- 左から右、上から下の順に読まれる前提で並べる（原因 → 結果、課題 → 解決策、現状 → 目指す姿）
- solution の各項目には issue を書き、どの課題に対応するかを結ぶ
- 前のスライドの示唆（insight）が、次のスライドの見出しにつながるようにする

## highlight（ポイント色）の使い方
ポイント色は「一番見てほしい所」だけに使う。1枚につき highlight は1か所までが目安。示唆ボックスもポイント色を使うので、示唆があるスライドでは数字の highlight を控えめにする。
