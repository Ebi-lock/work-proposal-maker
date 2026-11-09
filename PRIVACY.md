# プライバシーポリシー / Privacy Policy

最終更新日：2026年11月10日

このドキュメントは、Claude Code プラグイン「proposal-maker」（以下「本プラグイン」）が扱うデータについて説明します。

## 1. 扱うデータ

本プラグインは、企画書・提案書を作るために、ユーザーが Claude Code との対話で入力した情報を扱います。この中には、次のような個人に関する情報が含まれることがあります。

- 作成者の氏名・部署
- 提案先の会社名・担当者名
- 実施体制に記載する担当者の氏名
- 問い合わせ先（電話番号・内線番号・メールアドレスなど）
- ユーザーが指定した画像ファイル（商品写真・ロゴなど）

本プラグインが、ユーザーの指定なしにファイル・アカウント・外部サービスから個人データを集めることはありません。

## 2. データの使い方

入力された情報は、次の目的にだけ使います。

- スライドの内容（JSON）を組み立て、PowerPoint ファイル（.pptx）を生成する
- 生成したスライドの見た目を確認する（プレビュー）

## 3. データの保存

- 入力された情報は、ユーザーが指定した場所に保存する .pptx ファイルと、生成に使う作業用の JSON ファイルにだけ書き込まれます。どちらもユーザーのコンピューター上にあり、ユーザーが管理します
- プレビュー機能（macOS と Microsoft PowerPoint がある場合のみ）は、PowerPoint のサンドボックス内の作業フォルダに一時ファイルを作り、PDF と画像に変換したあと、一時ファイルを削除します
- 本プラグインは、データベースやサーバーなど、独自の保存場所を持ちません。データを保持しません

## 4. 外部への送信

- 本プラグインに含まれるスクリプト（`build_deck.py`、`icons.py`、`preview.sh`、`pdf2png.swift`）は、すべてユーザーのコンピューター上で動作し、ネットワーク通信を行いません
- 本プラグインは、外部のサービス・サーバー・解析ツールにデータを送信しません
- 本プラグインの開発者が、ユーザーのデータを受け取ることはありません

なお、Claude Code との対話の内容は、Claude Code（Anthropic）によって処理されます。その扱いは Anthropic のプライバシーポリシーに従います：https://www.anthropic.com/legal/privacy

## 5. 認証情報

本プラグインは、パスワード・API キー・トークンなどの認証情報を読み取ったり、送信したりしません。

## 6. 対象年齢

本プラグインは、業務用の資料作成を目的としており、18歳未満の利用を想定していません。

## 7. お問い合わせ

本ポリシーに関するお問い合わせは、GitHub の Issues で受け付けます：
https://github.com/Ebi-lock/work-proposal-maker/issues

## 8. 変更

本ポリシーを変更する場合は、このファイルを更新し、最終更新日を改めます。変更の履歴は、このリポジトリのコミット履歴で確認できます。

---

## English summary

- **Data handled:** Information the user enters during the conversation, which may include names, company names, contact details and user-supplied images. It is used only to build a PowerPoint (.pptx) deck.
- **Storage:** Data is written only to the .pptx file and a working JSON file at locations the user chooses on their own computer. The optional macOS preview creates temporary files inside PowerPoint's sandbox and deletes them after conversion. The plugin has no database or server and retains no data.
- **Transmission:** All bundled scripts run locally and make no network requests. The plugin sends no data to any external service, and the developer receives no user data. Conversations with Claude are processed by Anthropic under its own privacy policy.
- **Credentials:** The plugin does not read or transmit passwords, API keys or tokens.
- **Audience:** Intended for business use and not for users under 18.
- **Contact:** https://github.com/Ebi-lock/work-proposal-maker/issues
