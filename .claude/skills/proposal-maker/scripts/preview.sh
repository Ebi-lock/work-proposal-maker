#!/bin/bash
# 生成した .pptx を Microsoft PowerPoint (macOS) で PDF 化し、ページごとの PNG に変換する。
# 使い方: bash preview.sh <deck.pptx> <出力ディレクトリ>
# PowerPoint はサンドボックス内でしか書き込めないため、コンテナ内の作業フォルダを経由する。
set -euo pipefail
PPTX="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
OUT="$2"
HERE="$(cd "$(dirname "$0")" && pwd)"
if [ ! -d "/Applications/Microsoft PowerPoint.app" ]; then
  echo "[スキップ] Microsoft PowerPoint が見つからないため、プレビュー画像は作れません。"; exit 2
fi
WORK="$HOME/Library/Containers/com.microsoft.Powerpoint/Data/Documents/proposal-maker-preview"
mkdir -p "$WORK" "$OUT"
NAME="preview_$$"
cp "$PPTX" "$WORK/$NAME.pptx"
osascript <<OSA
with timeout of 180 seconds
tell application "Microsoft PowerPoint"
  open POSIX file "$WORK/$NAME.pptx"
  delay 3
  save active presentation in POSIX file "$WORK/$NAME.pdf" as save as PDF
  close active presentation saving no
end tell
end timeout
OSA
cp "$WORK/$NAME.pdf" "$OUT/preview.pdf"
rm -f "$WORK/$NAME.pptx" "$WORK/$NAME.pdf"
swift "$HERE/pdf2png.swift" "$OUT/preview.pdf" "$OUT"
ls "$OUT"/p*.png
