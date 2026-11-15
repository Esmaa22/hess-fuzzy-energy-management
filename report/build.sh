#!/usr/bin/env bash
# report/report.md -> report/report.pdf
# Gereksinim: pandoc (>= 2.9) ve xelatex (TeX Live: fontspec, polyglossia, titlesec, caption, booktabs, xurl, fancyhdr)
# Kullanım (repo kökünden): bash report/build.sh
set -euo pipefail
cd "$(dirname "$0")"
pandoc report.md \
  --from markdown \
  --pdf-engine=xelatex \
  --include-in-header=header.tex \
  --number-sections \
  --resource-path=.:.. \
  -o report.pdf
echo "report/report.pdf üretildi"
