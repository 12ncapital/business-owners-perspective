#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
appendix_moat_tracker.py
=====================================================================
"The Business Owner's Perspective"
Appendix: Moat Tracker -- dynamic visualization script
(trajectory tracker for the four-operations mathematical model)
=====================================================================

Copyright (c) 2026 Hayato Ichijo
Released under the MIT License.
https://opensource.org/licenses/MIT

This file has an English section (below) followed by a Japanese section (日本語版).
Output language: --lang en|ja, or the environment variable MOAT_LANG (default: en).

=====================================================================
[English]
=====================================================================
This script applies the "four-operations mathematical model" of the book (Chapter 3 of the
Japanese edition; Chapter 2 of the English edition) to primary data taken from the annual
securities reports (有価証券報告書) filed on EDINET (the disclosure system of Japan's Financial
Services Agency), and animates the trajectory of a company on the state-space matrix over all
the fiscal years that could be obtained (normally about 8-10 periods; up to roughly 14 years
when the conditions are met).

    X axis : SGR = ROE - DOE      (subtraction: sustainable internal growth rate)
    Y axis : CS  = ROE x DOE      (multiplication: compounding supercharger index, unit %^2)
    Area   : LBS = ROE + DOE      (addition: leveraged boost score, overall driving force)
    Color  : the dividend lane nearest to the payout ratio d = DOE / ROE (nearest-neighbor rule)
    Aux.   : OSM = ROE / DOE      (division: owner safety margin; shown on hover)

=====================================================================
[Setup]  Google Colab / local
=====================================================================
1. Required libraries (mostly preinstalled on Colab; run the following locally)
       pip install requests pandas numpy matplotlib plotly pillow

2. How to obtain an EDINET API key (free)
       (1) EDINET API user registration page
           https://api.edinet-fsa.go.jp/api/auth/index.aspx?mode=1
           (searching for "EDINET API key" also leads there; the screen layout may change)
       (2) Sign in with a Microsoft account or similar as instructed, and accept the terms of use
       (3) Copy the string issued under "Issue API key"
       (4) Paste it into EDINET_API_KEY below. It can also be given through the environment
           variable EDINET_API_KEY, a Colab secret (key icon -> EDINET_API_KEY), or the
           command-line argument --api-key (priority: argument > environment variable >
           Colab secret > the constant below)
       Note: do not show the key to third parties. Never paste it into books, social media
       or public repositories.

3. Fonts
       English output (the default) needs no special font.
       For Japanese output (--lang ja), Mac / Windows standard fonts are detected automatically.
       On Colab, run the following first:
           !apt-get -qq install -y fonts-noto-cjk
       If no Japanese font is found, the script keeps drawing with English labels.

=====================================================================
[How to run]
=====================================================================
    # Local: default (the 16 companies of Figure 1, focus 7011 Mitsubishi Heavy Industries)
    python appendix_moat_tracker.py

    # Japanese output (original file names; no "_en" suffix)
    python appendix_moat_tracker.py --lang ja
    export MOAT_LANG=ja        # or set it once in your shell profile

    # Focus on any securities code (the 16 companies are shown as reference points)
    python appendix_moat_tracker.py --focus 8035

    # Zoom around the focus company's latest-year coordinates
    # (outputs moat_animation_8035_en_zoom.gif / .html; with --lang ja: moat_animation_8035_zoom.*)
    python appendix_moat_tracker.py --focus 8035 --zoom --zoom-span 15

    # Draw a single company only (e.g. Toyota 7203; if --focus is omitted, the first of --codes is the focus)
    python appendix_moat_tracker.py --codes 7203
    python appendix_moat_tracker.py --codes 6196 --force-update   # moat_animation_6196_en.html

    # Fetch again (ignore the CSV cache and re-fetch from EDINET)
    python appendix_moat_tracker.py --force-update

    # Colab / Jupyter (after pasting the contents of this file into a cell)
    run(focus_code="7011", force_update=False)            # English
    run(focus_code="7011", force_update=False, lang="ja") # Japanese

    Output file names: English moat_animation_{code}_en.gif / .html,
                       Japanese moat_animation_{code}.gif / .html (original names)
    The CSV cache (data/moat_data_{code}.csv) is shared by both languages. Company names inside the
    CSV are the Japanese names from EDINET; English output shows English names for the 16 selected
    companies and the securities code only for any other company.

=====================================================================
[Data acquisition strategy]
=====================================================================
Instead of scanning the reports of every year, the script basically fetches the "latest" and the
"5 years back" annual securities reports (two in total). The "Summary of Business Results"
(主要な経営指標等の推移) at the beginning of an annual report lists the latest 5 periods, so after
removing overlapping years the two reports give a time series of about 8-10 periods.
Because of the statutory public-inspection period (5 years), reports can be traced directly up to
about 4-5 years before the filing year.
- Baseline: fetch the latest and the 5-years-back reports (two in total) and build a series of
  about 8-10 periods after removing duplicates.
- Extension: if a report from about 10 years back can be obtained (from the cache or within the
  searchable range), the earlier-year data it contains (4 more years before its filing year) are
  taken in automatically, restoring a series of more than 10 years, up to about 14 years.
  If it cannot be obtained, a warning is printed and the run continues with the two reports.

The EDINET API v2 has no entry point to search by securities code; it can only list documents
by filing date. The script therefore scans a window of filing dates back-calculated from the
fiscal-year end (centered on the period end + about 85 days) from the center outward, and stops as
soon as the matching document is found. For the second and later reports, the window is narrowed
around the filing date of the latest report (listed companies file at almost the same time every year).
If the "10 years back" report is not found in the search range, the script steps forward
automatically to 9, 8 and 7 years back (for overlapping years, the value from the newer report is used).

The time axis is unified by "fiscal year" (the calendar year in which the fiscal year starts). The
period ending March 2026 and the period ending December 2025 both land at the same position as FY2025,
so companies with different fiscal-year ends can be compared in the same frame.

From the XBRL elements of the "Summary of Business Results" (...SummaryOfBusinessResults), ROE / DOE
are reconstructed with the following definitions (the official basis for investment analysis and
annual reports = average-equity basis):

    ROE = net income attributable to owners of the parent / average equity over the period
    DOE = total dividends / average equity over the period
    Payout ratio = total dividends / net income attributable to owners of the parent (profitable periods only)

    Period-end equity (direct amounts first; the ratio-based estimate is the last fallback):
        (1) direct(summary)  equity attributable to owners of the parent in the summary table
                             (IFRS: EquityAttributableToOwnersOfParent)
        (2) direct(bs)       consolidated balance sheet (main statement). IFRS: equity attributable
                             to the parent; Japanese GAAP: "shareholders' equity + valuation and
                             translation adjustments" or "total net assets - non-controlling
                             interests - share subscription rights"
                             (the main balance sheet has only two periods, current and previous,
                             so for each year the report closest to the current period is used)
        (3) total_equity     total equity / net assets (summary table; includes non-controlling interests)
        (4) ratio*assets     "equity ratio x total assets" (percentages are normalized by
                             normalize_ratio; out-of-range values are rejected)
        Outliers such as equity above total assets or above 50 trillion JPY are rejected with a warning.
        The source can be audited through the CSV note column (equity=...) and the log ([equity]).
    Average equity over the period = (equity at the current period end + equity at the previous period end) / 2
                  The oldest year (no previous period end) and rows with non-consecutive years use
                  the current period-end value instead.
                  Period-end-based values are kept in the CSV columns roe_end_pct / doe_end_pct, and
                  avg_equity_mn records the denominator (for audit). The payout ratio is unchanged,
                  because the denominator cancels out.

DOE and the payout ratio are derived through a three-step cascade whose first priority is the "total
dividends" amount, which does not depend on share counts. This fundamentally removes the risk that
per-share indicators (DPS / EPS) are or are not retroactively adjusted at each stock split or
reverse split and end up off by a factor of 10 or 1/10.

    (1) Total-amount basis   total dividends (dividends paid in the CF statement > dividends of surplus
                             in the statement of changes in equity > total in the dividend-policy table;
                             consolidated > solo). note: payout=total_div(...)
                             Payments recorded as negative values are converted to absolute values,
                             and JPY to million JPY.
                             Each report carries only two periods (current and previous) of totals, so
                             by default the additional reports that fill the missing years (normally
                             2, 4 and 7 years back) are also fetched.
                             With --minimal-reports, only the baseline annual reports (latest, 5 years
                             back, and 10 years back if available) are used (fewer years are obtained).
    (2) Payout-ratio tag     payout ratio in the summary table (consolidated > filer-only).
                             DOE = ROE x payout ratio. note: payout=tag(...)
    (3) DPS / EPS            last fallback. DOE = ROE x DPS / EPS. Outliers above 150% in a profitable
                             period are corrected by dividing back with a split ratio (10, 5, 4, 3, 2);
                             if no correction works, DOE for that year is treated as not computable
                             and excluded. If the consolidated summary table has no DPS, it is
                             supplemented from the filer-only (solo) summary table.
                             note: payout=dps/eps(...)

For a year with no usable basis, DOE = 0 (presumed no dividend) and the element names are printed in
the diagnostic log ([DEBUG]).
The CSV columns total_dividends_mn and note let you audit the basis of every year.

Note: the numbers in the book (total dividends aggregated directly from the financial statements
themselves) may differ after the decimal point from this script's approximation. The purpose is to
grasp the tendency and the trajectory.

=====================================================================
[日本語版]  (the original Japanese text follows)
=====================================================================
「ビジネスオーナーの視座」
巻末付録：モート動的可視化スクリプト（四則演算数理モデルの軌跡トラッカー）
=====================================================================

注：日本語版で出力するには --lang ja（または環境変数 MOAT_LANG=ja）を指定する。
    既定は英語で、英語の出力ファイル名には _en が付く（日本語は従来のファイル名）。

-------------------------------------
『ビジネスオーナーの視座』第3章の「四則演算数理モデル」を、EDINET（金融庁）の
有価証券報告書から取得した一次データに適用し、企業が状態空間マトリクス上を
取得できた全年度（基本は約8〜10期、条件が揃えば最大14年程度）の軌跡をアニメーションとして描画する。

    横軸 X : SGR = ROE - DOE      （引き算：サステナブル内部成長力）
    縦軸 Y : CS  = ROE x DOE      （掛け算：複利増幅インデックス、単位 %^2）
    面積   : LBS = ROE + DOE      （足し算：総合推進力）
    色     : 配当性向 d = DOE / ROE に最も近い配当レーン（最近傍判定）
    補助   : OSM = ROE / DOE      （割り算：防衛安全倍率、ホバー表示に使用）

=====================================================================
【セットアップ】 Google Colab / ローカル共通
=====================================================================
1. 必要ライブラリ（Colab ではほぼ導入済み。ローカルでは下記を実行）
       pip install requests pandas numpy matplotlib plotly pillow

2. EDINET API キー（無料）の取得手順
       (1) EDINET の API 利用者登録ページ
           https://api.edinet-fsa.go.jp/api/auth/index.aspx?mode=1
           （検索語「EDINET API キー 取得」でも辿れる。画面構成は改訂されうる）
       (2) 画面の案内に従い Microsoft アカウント等でサインインし、利用規約に同意する
       (3) 「APIキー発行」から発行された文字列をコピーする
       (4) 下の EDINET_API_KEY に貼り付ける。環境変数 EDINET_API_KEY、
           Colab のシークレット（鍵アイコン → EDINET_API_KEY）、
           コマンド引数 --api-key でも指定できる（優先順位：引数 > 環境変数 >
           Colab シークレット > 下の定数）
       ※ キーは第三者に見せない。書籍・SNS・公開リポジトリへ貼り付けてはならない。

3. 日本語フォント（グラフ内の日本語表示）
       Mac / Windows は標準フォントを自動検出する。Colab では次を先に実行すると良い。
           !apt-get -qq install -y fonts-noto-cjk
       日本語フォントが見つからない場合、本スクリプトは英語ラベルで描画を継続する。

=====================================================================
【実行方法】
=====================================================================
    # ローカル：デフォルト（図1の16銘柄、フォーカス 7011 三菱重工業）
    python appendix_moat_tracker.py

    # 任意の証券コードをフォーカス（16銘柄を参照点として表示）
    python appendix_moat_tracker.py --focus 8035

    # フォーカス銘柄の最新年度座標を中心にズーム（出力は moat_animation_8035_zoom.gif / .html）
    python appendix_moat_tracker.py --focus 8035 --zoom --zoom-span 15

    # 単独銘柄（例：トヨタ 7203）だけを描画（--focus 省略時は --codes の先頭がフォーカス）
    python appendix_moat_tracker.py --codes 7203
    python appendix_moat_tracker.py --codes 6196 --force-update   # moat_animation_6196.html

    # 再取得（CSVキャッシュを無視して EDINET から取り直す）
    python appendix_moat_tracker.py --force-update

    # Colab / Jupyter（セルにこのファイルの内容を貼り付けた後）
    run(focus_code="7011", force_update=False)

=====================================================================
【データ取得戦略】
=====================================================================
全年度の報告書を走査せず、「直近」と「5年前」の有価証券報告書（計2本）を基本として取得する。
有価証券報告書の冒頭「主要な経営指標等の推移」は直近5期分を並べるため、
重複する年度を除くと、2本で約8〜10期分の時系列になる。
法定縦覧期間（5年）の制約から、提出年の約4〜5年前までが有報から直接たどれる範囲の目安である。
・基本：直近と5年前の有報（計2本）を取得し、重複を除いて約8〜10期分の時系列を構築する。
・拡張：キャッシュや探索可能な範囲で「10年前相当」の報告書が取得できた場合は、その有報が内包する
  過年度データ（提出年のさらに4年前）まで自動で取り込み、最大で10年超〜14年程度の時系列を復元する。
  取得できなければ警告を出して2本のまま続行する。

EDINET API v2 には証券コードで検索する口がなく、提出日ごとの書類一覧しか引けない。
そこで決算期末から逆算した提出日の窓（期末 + 約85日を中心に前後）を、
中心から外側へ向けて走査し、該当書類が見つかった時点で打ち切る。
2本目以降は、直近報告書の提出日を中心に窓を絞る（上場企業の提出時期は毎年ほぼ同じ）。
「10年前」の報告書が探索範囲で見つからない場合は、
9年前、8年前、7年前の順に自動で繰り上げる（重複する年は新しい報告書側の値を採用する）。

時間軸は「年度」（期首の属する暦年）で統一する。2026年3月期も2025年12月期も
2025年度として同じ位置に載るため、決算期の異なる銘柄を同一フレームで比較できる。

「主要な経営指標等の推移」の XBRL 要素（...SummaryOfBusinessResults）から、
次の定義で ROE / DOE を再構成する（投資分析・有報の公式基準＝期中平均自己資本ベース）。

    ROE = 親会社株主に帰属する当期純利益 / 期中平均自己資本
    DOE = 配当金総額 / 期中平均自己資本
    配当性向 = 配当金総額 / 親会社株主に帰属する当期純利益（黒字期のみ）

    期末自己資本（金額の直接取得を優先し、比率推計は最終フォールバック）：
        (1) direct(summary)  要約表の親会社所有者帰属持分（IFRS：EquityAttributableToOwnersOfParent）
        (2) direct(bs)       連結BS本表。IFRS は親会社持分、日本基準は「株主資本 + 評価・換算差額等」
                             または「純資産合計 - 非支配株主持分 - 新株予約権」
                             （BS本表は当期・前期の2期分のみのため、年度ごとに最も当期に近い報告書を採用）
        (3) total_equity     資本合計・純資産額（要約表。非支配株主持分を含む）
        (4) ratio*assets     「自己資本比率 x 総資産」（normalize_ratio で百分率を正規化し、範囲外は棄却）
        総資産超過・50兆円超などの異常値は棄却して警告を出す。
        取得元は CSV の note（equity=...）とログ（[自己資本]）で監査できる。
    期中平均自己資本 = (当期末自己資本 + 前期末自己資本) / 2
                  前期末が無い最古年度（および年度が連続しない行）は当期末で代用する。
                  期末ベースの値は CSV の roe_end_pct / doe_end_pct に残し、
                  avg_equity_mn に分母を記録する（監査用）。配当性向は分母が相殺されるため不変。

DOE・配当性向は、株数に依存しない「配当金総額」を第一優先とする3段のカスケードで求める。
株式分割・併合のたびに1株当たり指標（DPS / EPS）が遡及修正されたりされなかったりして、
10倍・1/10倍にずれるリスクを根本から排除するためである。

    (1) 総額ベース   配当金総額（CF計算書の配当金支払額 > 株主資本等変動計算書の剰余金の配当
                     > 配当政策表の総額。連結 > 単体）。note: payout=total_div(...)
                     負値で記載される支払額は絶対値へ、円は百万円へ換算する。
                     総額は各報告書に当期・前期の2期分しか載らないため、既定では欠ける
                     年度を埋める追加報告書（通常 2・4・7年前）も取得する。
                     --minimal-reports で基本の有報（直近・5年前・取得できれば10年前）のみに抑えられる（取得年度は減る）。
    (2) 配当性向タグ 要約表の配当性向（連結 > 提出会社）。DOE = ROE x 配当性向。
                     note: payout=tag(...)
    (3) DPS / EPS    最終フォールバック。DOE = ROE x DPS / EPS。黒字期に150%を超える
                     異常値は、分割倍率（10, 5, 4, 3, 2）で割り戻して補正し、補正できなければ
                     その年度の DOE は算出不能として除外する。DPS は連結側の要約表に無ければ
                     提出会社（単体）の要約表から補う。note: payout=dps/eps(...)

どの根拠も得られない年度は DOE = 0（無配と推定）とし、診断ログ（[DEBUG]）に要素名を出力する。
CSV の total_dividends_mn と note 列で、各年度の算出根拠を監査できる。

注意：第3章の数値（有価証券報告書の財務諸表本体から配当総額を直接集計したもの）とは、
本スクリプトの近似により小数点以下で差が生じうる。傾向と軌跡の把握が目的である。
"""
from __future__ import annotations

import argparse
import importlib
import io
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from typing import NamedTuple
from datetime import date, datetime, timedelta
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
import requests
from matplotlib import font_manager
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.collections import LineCollection
from matplotlib.colors import to_rgba
from matplotlib.figure import Figure
from matplotlib.patches import Patch, Rectangle

# ---------------------------------------------------------------------------
# Language switching (English by default; Japanese is opt-in)
# ---------------------------------------------------------------------------
SUPPORTED_LANGS = ("en", "ja")
DEFAULT_LANG = "en"
LANG_ENV_VAR = "MOAT_LANG"
_LANG = DEFAULT_LANG


def resolve_lang(cli_lang=None, warn=print):
    """Resolve the output language: ``--lang`` > environment variable ``MOAT_LANG`` > ``en``.

    An unsupported value falls back to English with a warning.
    """
    for source, value in (("--lang", cli_lang), (LANG_ENV_VAR, os.environ.get(LANG_ENV_VAR))):
        if value is None or not str(value).strip():
            continue
        lang = str(value).strip().lower()
        if lang in SUPPORTED_LANGS:
            return lang
        warn(f"[warning] Unsupported language {value!r} (from {source}); falling back to "
             f"'{DEFAULT_LANG}'. Supported: {', '.join(SUPPORTED_LANGS)}.")
        return DEFAULT_LANG
    return DEFAULT_LANG


def set_lang(lang=None, warn=print):
    """Set the active language (see resolve_lang) and return it."""
    global _LANG
    _LANG = resolve_lang(lang, warn)
    return _LANG


def is_ja():
    """True when the active language is Japanese."""
    return _LANG == "ja"


def T(ja, en):
    """Return the Japanese or the English string, depending on the active language."""
    return ja if _LANG == "ja" else en


# ---------------------------------------------------------------------------
# 0. User settings
# ---------------------------------------------------------------------------
# EDINET API key (free). See the module docstring for how to obtain one.
EDINET_API_KEY = "YOUR_EDINET_API_KEY"

# Default focus company (the one that gets the label and the thick trajectory)
DEFAULT_FOCUS_CODE = "7011"

# The 16 selected companies (same as Figure 1 of the book): securities code -> display name.
# STOCK_NAMES holds the Japanese names; STOCK_NAMES_EN holds the English ones.
STOCK_NAMES = {
    "8035": "東京エレクトロン",
    "6857": "アドバンテスト",
    "6920": "レーザーテック",
    "6146": "ディスコ",
    "2802": "味の素",
    "7011": "三菱重工業",
    "7012": "川崎重工業",
    "7013": "IHI",
    "6501": "日立製作所",
    "7735": "SCREEN HD",
    "285A": "キオクシアHD",
    "4776": "サイボウズ",
    "4063": "信越化学",
    "4768": "大塚商会",
    "6861": "キーエンス",
    "6503": "三菱電機",
}
# Short forms are used for the longest names so that the aligned labels fit in the figure margins.
STOCK_NAMES_EN = {
    "8035": "Tokyo Electron",
    "6857": "Advantest",
    "6920": "Lasertec",
    "6146": "DISCO",
    "2802": "Ajinomoto",
    "7011": "Mitsubishi Heavy",
    "7012": "Kawasaki Heavy",
    "7013": "IHI",
    "6501": "Hitachi",
    "7735": "SCREEN Holdings",
    "285A": "Kioxia Holdings",
    "4776": "Cybozu",
    "4063": "Shin-Etsu Chemical",
    "4768": "Otsuka Corp.",
    "6861": "Keyence",
    "6503": "Mitsubishi Electric",
}


def stock_names():
    """Display names of the 16 selected companies in the active language."""
    return dict(STOCK_NAMES if is_ja() else STOCK_NAMES_EN)
TARGET_STOCK_CODES = list(STOCK_NAMES)

# Fiscal-year-end months of the 16 selected companies (other companies are looked up
# automatically from the EDINET code list)
FISCAL_END_MONTH = {
    "8035": 3, "6857": 3, "6920": 6, "6146": 3, "2802": 3, "7011": 3,
    "7012": 3, "7013": 3, "6501": 3, "7735": 3, "285A": 3, "4776": 12,
    "4063": 3, "4768": 12, "6861": 3, "6503": 3,
}

# Reports to fetch: the latest (0) and the one from 5 years back (5) are the baseline
# (about 8-10 fiscal years after removing overlaps); each report carries the past 5 periods.
# A report from about 10 years back (10) is used only when it can be retrieved
# (up to roughly 10-14 years in total).
# If it is not found, the search steps forward year by year; if it still is not found,
# it is skipped with a warning.
REPORT_OFFSETS = (0, 5, 10)
# How many years to step forward when the report from about 10 years back is not found
OFFSET_FALLBACK_YEARS = 3

# EDINET API v2
EDINET_API_BASE = "https://api.edinet-fsa.go.jp/api/v2"
EDINET_CODELIST_URL = (
    "https://disclosure2dl.edinet-fsa.go.jp/searchdocument/codelist/Edinetcode.zip"
)
REQUEST_INTERVAL_SEC = 0.25  # be gentle to the server (minimum gap between requests)
REQUEST_TIMEOUT_SEC = 90
MAX_RETRY = 3
# Days from the fiscal-year end to the center of the filing-date window (the statutory
# deadline is the period end + 3 months; filings peak about 85 days after the period end)
FILING_CENTER_DAYS = 85
FILING_RADIUS_LATEST = 50   # search radius for the latest report (days)
FILING_RADIUS_PAST = 45     # search radius for past reports (days)

# ---------------------------------------------------------------------------
# 1. Dividend lane definitions (identical to make_fig01_portfolio_matrix.py)
# ---------------------------------------------------------------------------
# Dividend lanes: d (%) -> (color, Japanese legend label, line style).
# The English legend labels are in LANE_SHORT_LABEL_EN below.
LANES = {
    50: ("#e8685a", "高還元ロケットレーン (d = 50% → k = 2.000)", "-."),
    35: ("#a66fc7", "積極還元レーン (d = 35% → k ≈ 0.828)", "--"),
    30: ("#3fbf7f", "標準優良レーン (d = 30% → k ≈ 0.612)", ":"),
    0: ("#8a9199", "地表レーン (d = 0% → k = 0.000)", "-"),
}
OUTER_COLOR = "#3b82d6"  # outside the four main lanes (low payout, e.g. Advantest)
OUTER_PAYOUT = 0.1145    # reference payout of the outer orbit (in the book: d = 11.45%, k ~ 0.146)

LANE_SHORT_LABEL = {
    50: "高還元ロケット (d≈50%)",
    35: "積極還元 (d≈35%)",
    30: "標準優良 (d≈30%)",
    0: "地表 (d=0%)",
    "outer": "外側の低角度軌道 (d<20%)",
}
LANE_SHORT_LABEL_EN = {
    50: "d=50% lane (k=2.000)",
    35: "d=35% lane (k=0.828)",
    30: "d=30% lane (k=0.612)",
    0: "d=0% lane (k=0)",
    "outer": "outer low-angle lane (d=11.45%)",
}
# Short lane names for hover text (English)
LANE_HOVER_LABEL_EN = {
    50: "high-return rocket (d~50%)",
    35: "aggressive return (d~35%)",
    30: "standard quality (d~30%)",
    0: "ground level (d=0%)",
    "outer": "outer low-angle orbit (d<20%)",
}


def lane_hover_label(key):
    """Short lane name for hover text in the active language."""
    return LANE_SHORT_LABEL[key] if is_ja() else LANE_HOVER_LABEL_EN[key]

# Dango (dumpling) zone: SGR 7-14%, CS 35-110
DANGO_ZONE = dict(x=7.0, y=35.0, w=7.0, h=75.0)

JP_FONT_CANDIDATES = [
    "Hiragino Sans", "Hiragino Kaku Gothic ProN", "Yu Gothic", "Meiryo",
    "Noto Sans CJK JP", "Noto Sans JP", "IPAexGothic", "IPAGothic",
    "TakaoGothic", "VL Gothic", "MS Gothic", "Arial Unicode MS",
]


# 2. Four-operations model (the book's definitions, implemented as functions)
# ---------------------------------------------------------------------------
def calc_lbs(roe, doe):
    """+ LBS (Leveraged Boost Score; overall driving force) = ROE + DOE. Maps to the bubble area."""
    return np.asarray(roe, dtype=float) + np.asarray(doe, dtype=float)


def calc_sgr(roe, doe):
    """- SGR (Sustainable Growth Rate; sustainable internal growth) = ROE - DOE. Maps to the X axis."""
    return np.asarray(roe, dtype=float) - np.asarray(doe, dtype=float)


def calc_cs(roe, doe):
    """x CS (Compounding Supercharger; compounding amplification index) = DOE x ROE.

    Multiplied in percent as-is (unit: %^2). Maps to the Y axis. It expands to
    CS = payout ratio x ROE^2.
    """
    return np.asarray(roe, dtype=float) * np.asarray(doe, dtype=float)


def calc_osm(roe, doe):
    """/ OSM (Owner Safety Margin; defensive safety multiple) = ROE / DOE. DOE = 0 gives NaN."""
    roe = np.asarray(roe, dtype=float)
    doe = np.asarray(doe, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(doe != 0, roe / doe, np.nan)


def calc_payout_pct(roe, doe):
    """Payout ratio d (%) = DOE / ROE x 100.

    DOE = 0 gives d = 0 (ground-level lane). ROE <= 0 with DOE > 0 is undefined (NaN).
    """
    roe = np.asarray(roe, dtype=float)
    doe = np.asarray(doe, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        d = np.where(roe > 0, doe / roe * 100.0, np.nan)
    return np.where(doe == 0, 0.0, d)


def k_of(d):
    """Coefficient k(d) = d / (1 - d)^2 of a dividend lane (parabola Y = k X^2); d is a fraction in [0, 1)."""
    return d / (1 - d) ** 2


def lane_of(d_pct):
    """Nearest-neighbour rule that returns the closest of the four main lanes (same as the Figure 1 script).

    0 < d < 20% is treated as the outer orbit ("outer").
    Note: points whose payout ratio is undefined (NaN: loss-making periods, etc.) are also
    treated as the outer orbit.
    """
    if d_pct is None or not np.isfinite(d_pct):
        return "outer"
    if abs(d_pct) < 1e-9:
        return 0
    if d_pct < 20:
        return "outer"
    return min((30, 35, 50), key=lambda x: abs(x - d_pct))


def lane_color(lane):
    """Lane key -> drawing color."""
    return OUTER_COLOR if lane == "outer" else LANES[lane][0]


def compute_average_equity(df):
    """Return the average equity over the period (million JPY). Expects a table sorted by fiscal year.

    avg = (equity at period end + equity at previous period end) / 2. The oldest year (no previous
    period end, i.e. no opening balance), rows whose fiscal years are not consecutive, and rows
    whose previous period-end equity is not positive fall back to the current period-end equity.
    """
    eq = df["equity_mn"].astype(float)
    prev = eq.shift(1)
    contiguous = df["fiscal_year"].astype(float).diff() == 1
    prev = prev.where(contiguous & (prev > 0))
    return ((eq + prev) / 2.0).fillna(eq)


def compute_moat_table(df):
    """Add the four-operations metrics and the lane assignment to a table that has ROE / DOE (%).

    The denominator of ROE / DOE is the average equity over the period. The values computed at
    fetch time (derive_roe_doe) are period-end based, so they are kept as roe_end_pct / doe_end_pct
    and multiplied by the denominator ratio (period-end / average) to obtain roe_pct / doe_pct
    (the numerators, net income and total dividends, are common, so this is equivalent to
    NI / average equity and total dividends / average equity). Re-running on a CSV that has
    been read back is idempotent.
    """
    out = df.sort_values("fiscal_year").reset_index(drop=True)
    if "roe_end_pct" not in out.columns:  # fresh fetch / legacy cache: roe_pct / doe_pct are period-end based
        out["roe_end_pct"] = out["roe_pct"]
        out["doe_end_pct"] = out["doe_pct"]
    equity = out["equity_mn"].astype(float)
    avg_equity = compute_average_equity(out)
    ratio = (equity / avg_equity).where((equity > 0) & (avg_equity > 0), 1.0)
    out["avg_equity_mn"] = avg_equity
    out["roe_pct"] = out["roe_end_pct"].astype(float) * ratio
    out["doe_pct"] = out["doe_end_pct"].astype(float) * ratio
    roe = out["roe_pct"].to_numpy(dtype=float)
    doe = out["doe_pct"].to_numpy(dtype=float)
    out["lbs_pct"] = calc_lbs(roe, doe)
    out["sgr_pct"] = calc_sgr(roe, doe)
    out["cs"] = calc_cs(roe, doe)
    out["osm"] = calc_osm(roe, doe)
    out["payout_pct"] = calc_payout_pct(roe, doe)
    out["lane"] = [str(lane_of(d)) for d in out["payout_pct"]]
    return out


def lane_key(label):
    """Convert a lane stringified via CSV ("30" / "outer") back to its key."""
    return label if label == "outer" else int(float(label))


# ---------------------------------------------------------------------------
# 3. EDINET API v2 client
# ---------------------------------------------------------------------------
def resolve_api_key(cli_key=None):
    """Resolve the API key in the order: argument > environment variable > Colab secret > constant."""
    candidates = [cli_key, os.environ.get("EDINET_API_KEY")]
    try:  # Google Colab secrets
        from google.colab import userdata  # type: ignore

        candidates.append(userdata.get("EDINET_API_KEY"))
    except Exception:
        pass
    candidates.append(EDINET_API_KEY)
    for key in candidates:
        if key and key.strip() and key.strip() != "YOUR_EDINET_API_KEY":
            return key.strip()
    raise RuntimeError(T(
        "EDINET API キーが未設定です。ファイル冒頭の手順に従ってキーを取得し、"
        "EDINET_API_KEY に設定するか、環境変数 / --api-key で指定してください。",
        "The EDINET API key is not set. Obtain a key following the steps at the top of "
        "this file, then set EDINET_API_KEY, or pass it via the environment variable or "
        "--api-key."))


class EdinetClient:
    """Minimal EDINET API v2 client (document list and XBRL download)."""

    def __init__(self, api_key, interval=REQUEST_INTERVAL_SEC):
        self.api_key = api_key
        self.interval = interval
        self.session = requests.Session()
        self._day_cache = {}
        self._last_request = 0.0

    def _get(self, url, params=None):
        """GET with retries and request spacing. Authentication errors raise immediately."""
        params = dict(params or {})
        params["Subscription-Key"] = self.api_key
        last_error = None
        for attempt in range(MAX_RETRY):
            wait = self.interval - (time.monotonic() - self._last_request)
            if wait > 0:
                time.sleep(wait)
            try:
                resp = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT_SEC)
                self._last_request = time.monotonic()
            except requests.RequestException as exc:  # network failures etc.: exponential backoff
                last_error = exc
                time.sleep(2 ** attempt)
                continue
            if resp.status_code in (401, 403):
                raise PermissionError(T(
                    f"EDINET API 認証エラー（HTTP {resp.status_code}）。"
                    "APIキーが正しいか、有効期限内かを確認してください。",
                    f"EDINET API authentication error (HTTP {resp.status_code}). "
                    "Check that the API key is correct and has not expired."))
            if resp.status_code >= 500 or resp.status_code == 429:
                last_error = RuntimeError(f"HTTP {resp.status_code}")
                time.sleep(2 ** attempt)
                continue
            return resp
        raise ConnectionError(T(f"EDINET API への接続に失敗しました: {last_error}",
                                f"Failed to connect to the EDINET API: {last_error}"))

    def list_documents(self, day):
        """Return the document list (metadata) for a filing date. Cached within a run."""
        if day in self._day_cache:
            return self._day_cache[day]
        resp = self._get(
            f"{EDINET_API_BASE}/documents.json",
            {"date": day.isoformat(), "type": 2},
        )
        results = []
        try:
            body = resp.json()
        except ValueError:
            body = {}
        status = str(body.get("metadata", {}).get("status", resp.status_code))
        if status in ("401", "403"):
            raise PermissionError(T("EDINET API 認証エラー。APIキーを確認してください。",
                                    "EDINET API authentication error. Check the API key."))
        if resp.status_code == 200 and status == "200":
            results = body.get("results", []) or []
        # 404 (date out of range) and the like are treated as "nothing found"
        self._day_cache[day] = results
        return results

    def download_xbrl_zip(self, doc_id):
        """Download the ZIP of the full XBRL set (type=1) by document ID."""
        resp = self._get(f"{EDINET_API_BASE}/documents/{doc_id}", {"type": 1})
        if resp.status_code != 200 or not zipfile.is_zipfile(io.BytesIO(resp.content)):
            raise RuntimeError(T(f"XBRL の取得に失敗しました: docID={doc_id}",
                                 f"Failed to download XBRL: docID={doc_id}"))
        return resp.content


_CODELIST_CACHE = {}


def lookup_edinet_codelist(code5):
    """Look up (fiscal-year-end month, filer name) in the EDINET code list. Returns (None, None) on failure."""
    try:
        if "df" not in _CODELIST_CACHE:
            resp = requests.get(EDINET_CODELIST_URL, timeout=REQUEST_TIMEOUT_SEC)
            resp.raise_for_status()
            with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
                csv_name = next(n for n in zf.namelist() if n.lower().endswith(".csv"))
                raw = zf.read(csv_name)
            # Row 1 is metadata such as the download date; row 2 is the header.
            # The code list is distributed in Shift_JIS (cp932) with Japanese column names,
            # so the encoding and the Japanese keys below are intentional.
            _CODELIST_CACHE["df"] = pd.read_csv(
                io.BytesIO(raw), encoding="cp932", skiprows=1, dtype=str
            )
        df = _CODELIST_CACHE["df"]
        hit = df[df["証券コード"] == code5]
        if hit.empty:
            return None, None
        row = hit.iloc[0]
        m = re.search(r"(\d+)月", str(row.get("決算日", "")))  # "決算日" holds e.g. "3月31日"
        return (int(m.group(1)) if m else None), row.get("提出者名")
    except Exception as exc:  # network failure, format change, etc.: fall back to automatic search
        print(T(f"  [情報] EDINETコードリストを参照できませんでした（{exc}）",
                f"  [info] Could not read the EDINET code list ({exc})"))
        return None, None


# ---------------------------------------------------------------------------
# 4. Searching for reports (scanning a window of filing dates)
# ---------------------------------------------------------------------------
def month_end(year, month):
    """Last day of the given month in the given year."""
    nxt = date(year + (month == 12), month % 12 + 1, 1)
    return nxt - timedelta(days=1)


def fiscal_year_of(period_end):
    """Fiscal-year-end date -> fiscal year (the calendar year in which the fiscal year starts).

    The period ending March 2026 -> FY2025; the period ending December 2025 -> FY2025.
    This aligns companies with March and December year ends on one time axis (fiscal year),
    so that all companies can appear together in the first frame.
    """
    return period_end.year if period_end.month == 12 else period_end.year - 1


def shift_years(d, years):
    """Shift a date by `years` years (February 29 is rounded to the 28th)."""
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        return d.replace(year=d.year + years, day=28)


def latest_fiscal_year_candidates(fye_month, today, lag_days=40):
    """Candidate year-end calendar years whose latest annual report is presumed filed, newest first."""
    out = []
    for year in (today.year, today.year - 1, today.year - 2):
        if month_end(year, fye_month) + timedelta(days=lag_days) <= today:
            out.append(year)
    return out[:2]


def find_annual_report(client, code5, end_year, fye_month, center, radius, today):
    """Scan filing dates outward from `center` and look for the annual securities report (有価証券報告書).

    docTypeCode 120 = annual securities report (amended reports, 130, are excluded).
    The scan stops as soon as a match is found, so the closer the filing date is to the center,
    the fewer API calls are needed.
    """
    nominal_end = month_end(end_year, fye_month)
    for offset in sorted(range(-radius, radius + 1), key=lambda d: (abs(d), d)):
        day = center + timedelta(days=offset)
        if day > today or day.weekday() >= 5:  # no documents on future dates or weekends
            continue
        for doc in client.list_documents(day):
            if doc.get("secCode") != code5 or doc.get("docTypeCode") != "120":
                continue
            if doc.get("withdrawalStatus") == "1" or doc.get("xbrlFlag") == "0":
                continue
            period_end = doc.get("periodEnd")
            if not period_end:
                continue
            if abs((date.fromisoformat(period_end) - nominal_end).days) <= 31:
                return doc
    return None


# ---------------------------------------------------------------------------
# 5. Parsing the XBRL "Summary of Business Results" (主要な経営指標等の推移)
# ---------------------------------------------------------------------------
XSI_NIL = "{http://www.w3.org/2001/XMLSchema-instance}nil"
SUMMARY_SUFFIX = "SummaryOfBusinessResults"
# Consolidated facts use the unqualified context; filer-only (提出会社, non-consolidated) facts carry _NonConsolidatedMember
CONTEXT_RE = re.compile(
    r"^(CurrentYear|Prior(\d+)Year)(Duration|Instant)(_NonConsolidatedMember)?$"
)
SCOPE_CONSOLIDATED = "consolidated"  # "Consolidated financial indicators" (連結経営指標等)
SCOPE_SOLO = "solo"                  # "Filer-only indicators" (提出会社の経営指標等; non-consolidated summary table)
# Keywords for element names collected across the whole instance, for debugging
DEBUG_NAME_KEYWORDS = ("Dividend", "Payout")
DEBUG_MAX_NAMES = 80
DEBUG_MAX_CONTEXTS = 4

# --- Extraction rules for total dividends (total amount, independent of share counts) -------
# Search priority: (1) dividends paid in the cash-flow statement
#                  (2) dividends of surplus in the statement of changes in equity
#                  (3) total-amount elements in the filer information (dividend policy etc.).
# Consolidated is searched before non-consolidated (solo).
# Element names vary with the taxonomy edition and accounting standard, so they are matched by
# regular expressions on the local name.
CONSOLIDATION_AXIS = "ConsolidatedOrNonConsolidatedAxis"
EQUITY_AXIS = "ComponentsOfEquityAxis"
TOTAL_DIV_EXCLUDE = re.compile(
    r"(PerShare|Interim|Forecast|Ratio|NonControlling|Noncontrolling|MinorityInterest"
    r"|MinorityShareholders|Payable|Liabilit|Receivable|Accrued|Abstract|TextBlock"
    r"|ToNon|Subsidiar|Guarantee|Yield)", re.I)
CF_DIV_PATTERNS = [
    re.compile(r"^(CashDividendsPaid|PaymentsOfDividendsPaid|PaymentsOfDividends"
               r"|PaymentOfDividends|DividendsPaid)(FinCF)?(IFRS|USGAAP)?$"),
    re.compile(r"^[A-Za-z]*(DividendsPaid|PaymentsOfDividends|PaymentOfDividends)"
               r"[A-Za-z]*(FinCF|FinancingCF)[A-Za-z]*$"),
]
SS_DIV_PATTERNS = [
    re.compile(r"^DividendsOfSurplus(IFRS|USGAAP)?$"),
    re.compile(r"^DividendsPaidEquity[A-Za-z]*$"),
]
POLICY_DIV_PATTERN = re.compile(
    r"^(?=.*Dividend)(?=.*(TotalAmount|AmountOfDividends|TotalDividends|TotalOfDividends)).*$")
# Columns of the statement of changes in equity that represent dividends to the parent's shareholders (highest priority first)
EQUITY_COMPONENT_PRIORITY = (
    "ShareholdersEquityMember", "RetainedEarningsMember", "NetAssetsMember",
    "EquityAttributableToOwnersOfParentIFRSMember", "RetainedEarningsIFRSMember",
)
MAX_DIV_CANDIDATES = 3000
TOTAL_DIV_MAX_PAYOUT = 5.0   # a total / net income above this is treated as an extraction error (500%)
TOTAL_DIV_MAX_DOE = 0.5      # a total / equity above this is treated as an extraction error (50%)
POLICY_TOLERANCE = (0.6, 1.6)  # a total from the dividend-policy table is used only if it roughly agrees with other payout ratios

# Candidate element (local) names. The first one found, from the top, is used.
# The namespace (taxonomy edition) changes every year, so only local names are matched.
_STD = r"(IFRS|USGAAP)?"
PATTERNS = {
    "net_income": [
        rf"^ProfitLossAttributableToOwnersOfParent{_STD}{SUMMARY_SUFFIX}$",
        rf"^NetIncomeLoss{_STD}{SUMMARY_SUFFIX}$",
        rf"^ProfitLoss{_STD}{SUMMARY_SUFFIX}$",
    ],
    "equity_direct": [  # equity attributable to owners of the parent in the summary table (direct IFRS tag; top priority)
        rf"^EquityAttributableToOwnersOfParent{_STD}{SUMMARY_SUFFIX}$",
    ],
    "equity_bs": [  # equity attributable to owners of the parent in the consolidated balance sheet (direct tag when the summary table lacks it)
        rf"^EquityAttributableToOwnersOfParent{_STD}$",
    ],
    "owners_equity": [  # owners' equity in the summary table (OwnersEquity); used directly as an amount when present
        rf"^OwnersEquity{_STD}{SUMMARY_SUFFIX}$",
    ],
    # Equity ratio. RatioOfOwnersEquityToGrossAssets (ratio of equity attributable to owners
    # of the parent) takes priority. Some reports put a non-ratio value in EquityToAssetRatio
    # (apparently net assets per share, e.g. 600-1,100); picking it first inflates the equity
    # by orders of magnitude, so the order is fixed explicitly.
    "equity_ratio": [
        rf"^RatioOfOwnersEquityToGrossAssets{_STD}{SUMMARY_SUFFIX}$",
        rf"^EquityToAssetRatio{_STD}{SUMMARY_SUFFIX}$",
    ],
    "total_assets": [rf"^TotalAssets{_STD}{SUMMARY_SUFFIX}$"],
    "total_equity": [  # total equity; includes non-controlling interests, so it ranks below equity attributable to the parent
        rf"^(TotalEquity|Equity){_STD}{SUMMARY_SUFFIX}$",
        rf"^(TotalEquity|Equity){_STD}$",
    ],
    "net_assets": [rf"^NetAssets{_STD}{SUMMARY_SUFFIX}$"],
    # --- Consolidated balance sheet (main statement) under Japanese GAAP
    #     (the summary table has no equity amount) -----------------------------------------
    "equity_bs_total": [  # shareholders' equity plus valuation and translation adjustments (equity after deducting non-controlling interests, when present)
        r"^(Total)?ShareholdersEquityAndValuationAndTranslationAdjustments$",
    ],
    "shareholders_equity_bs": [r"^ShareholdersEquity$"],  # total shareholders' equity
    "valuation_bs": [  # total valuation and translation adjustments (accumulated other comprehensive income)
        r"^(ValuationAndTranslationAdjustments|AccumulatedOtherComprehensiveIncome)$",
    ],
    "net_assets_bs": [r"^(NetAssets|TotalNetAssets)$"],  # total net assets
    "nci_bs": [r"^(NonControllingInterests|MinorityInterests)(IFRS|USGAAP)?$"],  # non-controlling interests
    "rights_bs": [r"^SubscriptionRightsToShares$"],  # share subscription rights
    "eps": [
        rf"^BasicEarningsLossPerShare{_STD}{SUMMARY_SUFFIX}$",
        rf"^(NetIncomeLossPerShare|EarningsLossPerShare){_STD}{SUMMARY_SUFFIX}$",
    ],
    "dps": [
        rf"^(DividendPaidPerShare|DividendsPerShare|CashDividendsPerShare"
        rf"|CashDividendsPaidPerShare|DividendsPaidPerShare){_STD}{SUMMARY_SUFFIX}$",
        # Last resort: absorb naming variations. Interim dividends, payout ratios and forecasts are excluded.
        rf"^(?!.*(Interim|Payout|Ratio|Forecast)).*Dividend.*PerShare.*{SUMMARY_SUFFIX}$",
    ],
    "payout": [
        rf"^(Consolidated)?(Dividend)?PayoutRatio{_STD}{SUMMARY_SUFFIX}$",
        # Absorb naming variations (consolidated payout ratio, filer's payout ratio, etc.). Forecasts are excluded.
        rf"^(?!.*Forecast).*Payout.*{SUMMARY_SUFFIX}$",
    ],
}
# Period concept: profit/loss and dividends are Duration; balance-sheet items are Instant.
# Items searched down to the filer-only (solo) summary table when the consolidated side lacks them
# (for dividends, many annual reports show them only under "filer-only indicators" (提出会社の経営指標等))
SOLO_FALLBACK_KEYS = ("dps", "payout")
# Countermeasures for EPS / DPS basis mismatches caused by stock splits and reverse splits
PAYOUT_SANITY_MAX = 1.5            # a payout ratio above this in a profitable period is treated as abnormal (150%)
SPLIT_FACTORS = (10, 5, 4, 3, 2)   # candidate split ratios used for correction
TYPICAL_PAYOUT = 0.35              # reference used to choose the closest candidate when there are several
PERIOD_KIND = {
    "net_income": "Duration", "eps": "Duration", "dps": "Duration", "payout": "Duration",
    "equity_direct": "Instant", "owners_equity": "Instant", "equity_bs": "Instant",
    "equity_bs_total": "Instant", "shareholders_equity_bs": "Instant", "valuation_bs": "Instant",
    "net_assets_bs": "Instant", "nci_bs": "Instant", "rights_bs": "Instant",
    "equity_ratio": "Instant", "total_assets": "Instant", "total_equity": "Instant",
    "net_assets": "Instant",
}
# Equity-related keys from the consolidated balance sheet (main statement), adopted "as a bundle" from one report (resolve_bs_bundle)
BS_EQUITY_KEYS = ("equity_bs", "equity_bs_total", "shareholders_equity_bs", "valuation_bs",
                  "net_assets_bs", "nci_bs", "rights_bs")
# Equity-related elements picked from the consolidated balance sheet (main statement) that do
# not carry the summary-table suffix. This is the route for obtaining equity amounts directly
# for companies whose summary table has no equity amount (both IFRS and Japanese GAAP).
# Contexts with dimensions (e.g. columns of the statement of changes in equity) are excluded by CONTEXT_RE.
BS_EQUITY_LOCAL = re.compile(
    r"^(EquityAttributableToOwnersOfParent|TotalEquity|Equity)(IFRS|USGAAP)?$"
    r"|^(NetAssets|TotalNetAssets|ShareholdersEquity|ValuationAndTranslationAdjustments"
    r"|AccumulatedOtherComprehensiveIncome|SubscriptionRightsToShares"
    r"|(Total)?ShareholdersEquityAndValuationAndTranslationAdjustments)$"
    r"|^(NonControllingInterests|MinorityInterests)(IFRS|USGAAP)?$")

# --- Per-year fallback for non-consolidated (solo) filers and years before consolidation ----
# Net income in the income statement (main statement). For solo filers whose summary table
# (SummaryOfBusinessResults) has no net income.
# Never used in years where consolidated data exist (only the fallback years of _pick_scoped refer to it).
NET_INCOME_PL_LOCAL = re.compile(
    r"^(ProfitLossAttributableToOwnersOfParent|NetIncomeLoss|ProfitLoss)(IFRS|USGAAP)?$")
NET_INCOME_PL_PATTERNS = [  # priority order (consolidated profit attributable to owners of the parent > net income)
    r"^ProfitLossAttributableToOwnersOfParent(IFRS|USGAAP)?$",
    r"^NetIncomeLoss(IFRS|USGAAP)?$",
    r"^ProfitLoss(IFRS|USGAAP)?$",
]
# Items used to decide whether consolidated data exist in a given year (net income, equity items, total assets).
# If any one of them is obtained at consolidated scope, that year is treated as a consolidated year and only the regular processing is done.
CONSOLIDATED_PRESENCE_KEYS = (
    "net_income", "equity_direct", "owners_equity", "equity_bs", "equity_bs_total",
    "shareholders_equity_bs", "net_assets_bs", "total_equity", "net_assets", "total_assets",
)
SOLO_FALLBACK_NOTE = "scope=nonconsolidated_fallback"


def classify_dividend_element(local):
    """Classify an element name into a total-dividend category (cf / ss / policy). None if none applies."""
    if local.endswith(SUMMARY_SUFFIX) or TOTAL_DIV_EXCLUDE.search(local):
        return None
    if any(rx.match(local) for rx in CF_DIV_PATTERNS):
        return "cf"
    if any(rx.match(local) for rx in SS_DIV_PATTERNS):
        return "ss"
    if POLICY_DIV_PATTERN.match(local):
        return "policy"
    return None


def parse_report_xbrl(xbrl_file, report_end):
    """Scan an XBRL instance once and extract summary-table facts, total dividends and diagnostics.

    Returns: (facts, debug, total_dividends)
        facts = {(scope, period kind, n): {local name: value}} (n = 0 is the current period,
                k is k periods earlier). Elements of the "Summary of Business Results"
                (主要な経営指標等の推移): consolidated facts use the unqualified context, filer-only
                (non-consolidated) facts use contexts with *_NonConsolidatedMember.
        debug = information for logging when extraction fails (summary-table element names,
                dividend-related element names and their contexts)
        total_dividends = {n: (total dividends [JPY, positive], source label)}
                (CF / SS etc. cover the latest two periods only)
    """
    facts = {}
    debug = {"summary_names": {SCOPE_CONSOLIDATED: set(), SCOPE_SOLO: set()},
             "dividend_names": {}, "equity_names": set()}
    contexts = {}
    candidates = []
    current = None
    period_keys = {"startDate": "start", "endDate": "end", "instant": "instant"}
    for event, elem in ET.iterparse(xbrl_file, events=("start", "end")):
        tag = elem.tag
        if not isinstance(tag, str):
            continue
        local = tag.rsplit("}", 1)[-1]
        if event == "start":
            if local == "context":  # keep the context definitions (period and dimensions)
                current = elem.get("id")
                contexts[current] = {"dims": {}, "start": None, "end": None, "instant": None}
            continue
        if local == "context":
            current = None
        elif current is not None:
            ctx = contexts[current]
            text = (elem.text or "").strip()
            if local == "explicitMember":
                axis = (elem.get("dimension") or "").rsplit(":", 1)[-1]
                ctx["dims"][axis] = text.rsplit(":", 1)[-1]
            elif local in period_keys:
                try:
                    ctx[period_keys[local]] = date.fromisoformat(text[:10])
                except ValueError:
                    pass
        else:
            context = elem.get("contextRef") or ""
            text = (elem.text or "").strip()
            is_nil = elem.get(XSI_NIL) == "true"
            # Record only the names and contexts of dividend-related elements, including those outside the summary table (diagnostics)
            if any(k in local for k in DEBUG_NAME_KEYWORDS):
                seen = debug["dividend_names"]
                if local in seen or len(seen) < DEBUG_MAX_NAMES:
                    ctxs = seen.setdefault(local, [])
                    if context not in ctxs and len(ctxs) < DEBUG_MAX_CONTEXTS:
                        ctxs.append(context)
            value = None
            if text and not is_nil and context:
                try:
                    value = float(text)
                except ValueError:
                    value = None
            if value is not None:
                if local.endswith(SUMMARY_SUFFIX):
                    m = CONTEXT_RE.match(context)
                    if m:
                        n = 0 if m.group(1) == "CurrentYear" else int(m.group(2))
                        scope = SCOPE_SOLO if m.group(4) else SCOPE_CONSOLIDATED
                        facts.setdefault((scope, m.group(3), n), {}).setdefault(local, value)
                        debug["summary_names"][scope].add(local)
                elif BS_EQUITY_LOCAL.match(local):
                    m = CONTEXT_RE.match(context)
                    if m and m.group(3) == "Instant":  # main-statement value at period end, without dimensions
                        n = 0 if m.group(1) == "CurrentYear" else int(m.group(2))
                        scope = SCOPE_SOLO if m.group(4) else SCOPE_CONSOLIDATED
                        facts.setdefault((scope, "Instant", n), {}).setdefault(local, value)
                        debug["equity_names"].add(local)
                elif NET_INCOME_PL_LOCAL.match(local):
                    m = CONTEXT_RE.match(context)
                    if m and m.group(3) == "Duration":  # full-year net income in the income statement (main statement)
                        n = 0 if m.group(1) == "CurrentYear" else int(m.group(2))
                        scope = SCOPE_SOLO if m.group(4) else SCOPE_CONSOLIDATED
                        facts.setdefault((scope, "Duration", n), {}).setdefault(local, value)
                else:
                    category = classify_dividend_element(local)
                    if category and len(candidates) < MAX_DIV_CANDIDATES:
                        candidates.append(
                            (category, local, context, value, elem.get("unitRef") or ""))
        elem.clear()  # keep memory low even for instances of tens of MB
    return facts, debug, resolve_total_dividends(candidates, contexts, report_end)


def _best_by_pattern(items, patterns):
    """From candidates (local, dims, ctx_id, value), choose one following the priority order of the element-name patterns."""
    for rx in patterns:
        for item in sorted(items, key=lambda it: it[0]):
            if rx.match(item[0]):
                return item
    return sorted(items, key=lambda it: it[0])[0]


def resolve_total_dividends(candidates, contexts, report_end):
    """Settle the total-dividend candidates into one value per fiscal period (n), by priority.

    Sign: CF payments and decreases in the statement of changes in equity are recorded as negative
    values, so they are converted to absolute values.
    Unit: only items whose unitRef is JPY are adopted (the caller converts to million JPY).
    Returns: {n: (total dividends [JPY, positive], source label such as "cf:consolidated")}
    """
    buckets = {}
    for category, local, ctx_id, value, unit in candidates:
        if unit and "JPY" not in unit.upper():
            continue
        ctx = contexts.get(ctx_id)
        if not ctx or not ctx["start"] or not ctx["end"]:
            continue
        if not 330 <= (ctx["end"] - ctx["start"]).days <= 400:  # full-year periods only
            continue
        n = round((report_end - ctx["end"]).days / 365.25)
        if not 0 <= n <= 4:
            continue
        dims = dict(ctx["dims"])
        solo = dims.pop(CONSOLIDATION_AXIS, "") == "NonConsolidatedMember"
        scope = SCOPE_SOLO if solo else SCOPE_CONSOLIDATED
        buckets.setdefault((category, scope, n), []).append((local, dims, ctx_id, value))

    result = {}
    for n in range(0, 5):
        for category, patterns in (("cf", CF_DIV_PATTERNS), ("ss", SS_DIV_PATTERNS),
                                   ("policy", [POLICY_DIV_PATTERN])):
            for scope in (SCOPE_CONSOLIDATED, SCOPE_SOLO):
                items = buckets.get((category, scope, n))
                if not items:
                    continue
                value = None
                if category == "cf":  # total of financing CF: no dimension qualification
                    plain = [it for it in items if not it[1]]
                    if plain:
                        value = _best_by_pattern(plain, patterns)[3]
                elif category == "ss":  # statement of changes in equity: choose the component column by priority
                    for member in EQUITY_COMPONENT_PRIORITY:
                        col = [it for it in items if it[1] == {EQUITY_AXIS: member}]
                        if col:
                            value = _best_by_pattern(col, patterns)[3]
                            break
                else:  # dividend policy etc.: sum the totals per resolution, once per full-year context
                    per_ctx = {}
                    for local, _, ctx_id, val in sorted(items, key=lambda it: (it[0], it[2])):
                        per_ctx.setdefault(ctx_id, val)
                    value = sum(per_ctx.values())
                if value is not None:
                    result[n] = (abs(value), f"{category}:{scope}")
                    break
            if n in result:
                break
    return result


def _pick(bucket, patterns):
    """From a dict of local names, return the first value matching the candidate patterns in order."""
    for pattern in patterns:
        rx = re.compile(pattern)
        for local, value in bucket.items():
            if rx.match(local):
                return value
    return None


def has_consolidated_data(facts, n):
    """Return whether consolidated net income, equity items or total assets exist for the period n years back.

    Only years where this is False (a purely solo-filing company, or years before consolidation)
    are subject to the per-year fallback to individual (NonConsolidated) data.
    """
    for key in CONSOLIDATED_PRESENCE_KEYS:
        bucket = facts.get((SCOPE_CONSOLIDATED, PERIOD_KIND[key], n), {})
        if _pick(bucket, PATTERNS[key]) is not None:
            return True
    return False


def _pick_scoped(facts, key, n, solo_year=False):
    """Look up the value of item `key` in the order consolidated -> solo (for dividend items, or for all items when solo_year).

    solo_year=True is for a year without consolidated data (has_consolidated_data is False):
    after looking at consolidated first, it falls back in the order individual (NonConsolidated)
    summary table -> individual income-statement main table (net income only: ProfitLoss /
    NetIncomeLoss). Behaviour for consolidated years (solo_year=False) is unchanged.
    Returns: (value, scope).
    """
    scopes = [SCOPE_CONSOLIDATED]
    if solo_year or key in SOLO_FALLBACK_KEYS:
        scopes.append(SCOPE_SOLO)
    for scope in scopes:
        value = _pick(facts.get((scope, PERIOD_KIND[key], n), {}), PATTERNS[key])
        if value is not None:
            return value, scope
    if solo_year and key == "net_income":
        # Solo filers whose summary table has no net income: use the income statement (main statement).
        # Prefer the individual context; because the year has no consolidated data, the unqualified context is also accepted.
        for scope in (SCOPE_SOLO, SCOPE_CONSOLIDATED):
            bucket = facts.get((scope, "Duration", n), {})
            value = _pick(bucket, NET_INCOME_PL_PATTERNS)
            if value is not None:
                return value, scope
    return None, None


def normalize_ratio(value, limit=1.0):
    """Normalize ratio tags to fractions (0.50) even when percentages (e.g. 50.0) are mixed in.

    EDINET ratio tags (equity ratio, payout ratio) sometimes carry percentage values with unit pure.
    Treating those as fractions and multiplying them into an amount yields a value 100x too large.
    If the absolute value exceeds `limit`, it is judged to be a percentage and divided by 100.
    - None is returned as None (collapsing "no tag" to 0 would turn a missing payout-ratio tag into "no dividend").
    - limit: 1.0 for the equity ratio (above 100% is impossible). A payout ratio can exceed 100%
      (e.g. 1.34 = 134%) in loss-making periods or with special dividends, so the caller passes 5.0.
    """
    if value is None:
        return None
    return value / 100.0 if abs(value) > limit else value


_as_ratio = normalize_ratio  # backward-compatible alias for the old name


def detect_accounting_standard(facts):
    """Infer the accounting standard (Japanese GAAP / IFRS / US GAAP) from the element names.

    The returned labels are stored in the CSV (accounting_standard column); "日本基準" means Japanese GAAP.
    """
    names = [name for bucket in facts.values() for name in bucket]
    if any("IFRS" in n for n in names):
        return "IFRS"
    if any("USGAAP" in n for n in names):
        return "US-GAAP"
    return "日本基準"


EQUITY_MAX_YEN = 5e13             # equity above 50 trillion JPY is treated as an unrealistic outlier
EQUITY_ASSETS_TOLERANCE = 1.0001  # equity cannot exceed total assets (only rounding error is tolerated)
EQUITY_VS_TOTAL_TOLERANCE = 1.05  # an estimate more than 5% above total equity is abnormal (parent's equity <= total)


def equity_sanity_problem(equity, assets, total_equity=None, estimated=False):
    """Return a reason string if the candidate equity value is unrealistic, otherwise None.

    - exceeds total assets (equivalent to an equity ratio above 100%)
    - unrealistic magnitude (above EQUITY_MAX_YEN)
    - an estimate (ratio x total assets) exceeds total equity / net assets (the parent's equity
      cannot exceed the total)
    Values from direct tags are not rejected even if they disagree with other items
    (e.g. negative non-controlling interests).
    The reason strings are written to the CSV note column, so they are kept as-is.
    """
    if equity > EQUITY_MAX_YEN:
        return f"implausible_magnitude({equity / 1e12:.1f}兆円)"
    if assets and equity > assets * EQUITY_ASSETS_TOLERANCE:
        return f"equity>total_assets({equity / 1e6:,.0f}>{assets / 1e6:,.0f}百万円)"
    if estimated and total_equity and equity > total_equity * EQUITY_VS_TOTAL_TOLERANCE:
        return f"equity>total_equity({equity / 1e6:,.0f}>{total_equity / 1e6:,.0f}百万円)"
    return None


# If True, ratio*assets is used before total equity / total net assets (which include
# non-controlling interests). For years under Japanese GAAP where the summary table has only the
# net-assets amount (common in older years, since the balance-sheet main statement covers only two
# periods), equity ratio x total assets is closer to the parent's equity. Default: "direct tags first".
RATIO_BEFORE_TOTAL_EQUITY = False
EQUITY_RATIO_GAP_WARN = 0.03  # leave a note when the direct value and the ratio-based estimate differ by more than this (for audit)


class EquityResolution(NamedTuple):
    equity: float | None   # period-end equity (JPY)
    source: str | None     # source label (direct(summary) / direct(bs) / ...)
    details: list          # supplementary notes to keep in the remarks (how it was assembled, etc.)
    problems: list         # candidates rejected by the outlier guard, with the reasons


def derive_bs_owners_equity(values):
    """Assemble the equity attributable to the parent's shareholders from consolidated balance-sheet amounts.

    Returns: (amount, basis) / (None, None) when unavailable. Priority:
      (a) equity attributable to owners of the parent (IFRS)
      (b) total shareholders' equity and valuation and translation adjustments
      (c) shareholders' equity + valuation and translation adjustments
      (d) total net assets - non-controlling (minority) interests - share subscription rights
          If the deducted elements are absent from the main statement, total net assets as-is
          (an absent element simply does not apply)
    The basis labels below are data (stored in the CSV note column) and are kept in Japanese.
    """
    for key, basis in (("equity_bs", "親会社の所有者に帰属する持分"),
                       ("equity_bs_total", "株主資本及び評価・換算差額等合計")):
        if values.get(key) is not None:
            return values[key], basis
    shareholders, valuation = values.get("shareholders_equity_bs"), values.get("valuation_bs")
    if shareholders is not None and valuation is not None:
        return shareholders + valuation, "株主資本+評価・換算差額等"
    net_assets = values.get("net_assets_bs")
    if net_assets is not None:
        nci, rights = values.get("nci_bs") or 0.0, values.get("rights_bs") or 0.0
        parts = ["純資産"] + (["非支配株主持分"] if nci else []) + (["新株予約権"] if rights else [])
        return net_assets - nci - rights, "-".join(parts)
    return None, None


def resolve_equity(values):
    """Settle the period-end equity (JPY) in order of reliability (common to IFRS and Japanese GAAP).

    Priority:
      (1) direct(summary)  equity attributable to owners of the parent in the summary table
                           (EquityAttributableToOwnersOfParent) / owners' equity
      (2) direct(bs)       consolidated balance-sheet main statement (IFRS: equity attributable to
                           the parent; Japanese GAAP: shareholders' equity + valuation and
                           translation adjustments, or total net assets - non-controlling
                           interests - share subscription rights. See derive_bs_owners_equity)
      (3) total_equity     total equity (summary table) / net_assets (summary table) ... includes
                           non-controlling interests
      (4) ratio*assets     last-resort fallback when none of the above exist (goes through
                           normalize_ratio and a range check on the ratio)
    A candidate caught by the outlier guard (equity_sanity_problem) is rejected and the next
    one is tried.
    Returns: EquityResolution(equity, source label, details, rejection reasons). equity=None if unavailable.
    """
    assets = values.get("total_assets")
    total_equity_ref = (values.get("total_equity") or values.get("net_assets")
                        or values.get("net_assets_bs"))
    problems, details = [], []

    estimate = None
    raw_ratio = values.get("equity_ratio")
    ratio = normalize_ratio(raw_ratio)
    if ratio and assets:
        if 0.0 < ratio <= 1.0:
            estimate = ratio * assets
        else:
            problems.append(f"equity=ratio*assets:ratio_out_of_range({raw_ratio})")

    owners = values.get("equity_direct")
    if owners is None:
        owners = values.get("owners_equity")
    bs_value, bs_basis = derive_bs_owners_equity(values)

    # The labels below are written to the CSV note column (data), so they are kept as-is.
    candidates = [
        ("direct(summary)", owners, False, None),
        ("direct(bs)", bs_value, False, bs_basis),
        ("total_equity(非支配株主持分を含む)", values.get("total_equity"), False, None),
        ("net_assets(非支配株主持分を含む)", values.get("net_assets"), False, None),
    ]
    ratio_candidate = ("ratio*assets", estimate, True, None)
    if RATIO_BEFORE_TOTAL_EQUITY:
        candidates.insert(2, ratio_candidate)
    else:
        candidates.append(ratio_candidate)

    for label, value, estimated, basis in candidates:
        if value is None:
            continue
        if value <= 0:  # capital deficit: the caller treats ROE as unavailable
            return EquityResolution(value, label, details, problems)
        problem = equity_sanity_problem(value, assets, total_equity_ref, estimated)
        if problem:
            problems.append(f"equity={label}:{problem}")
            continue
        if basis:
            details.append(f"equity_basis={basis}")
        if estimate and label.startswith("direct"):
            gap = value / estimate - 1.0
            if abs(gap) > EQUITY_RATIO_GAP_WARN:
                details.append(f"equity_vs_ratio({gap:+.1%})")
        return EquityResolution(value, label, details, problems)
    return EquityResolution(None, None, details, problems)


def derive_roe_doe(values):
    """Reconstruct ROE / DOE (%) from the extracted values.

    Returns: (roe_pct, doe_pct, period-end equity, note). roe/doe are None when unavailable.
    The note keeps the equity source (equity=...) and the candidates rejected by the outlier
    guard (equity_rejected(...)).
    """
    notes = [SOLO_FALLBACK_NOTE] if values.get("solo_fallback") else []
    net_income = values.get("net_income")

    # Period-end equity: direct tags first; an estimate (ratio x total assets) comes later, behind the outlier guard
    resolved = resolve_equity(values)
    equity = resolved.equity
    if resolved.source:
        notes.append(f"equity={resolved.source}")
    notes.extend(resolved.details)
    notes.extend(f"equity_rejected({p.replace(';', ',')})" for p in resolved.problems)
    if net_income is None or not equity or equity <= 0:
        return None, None, equity, ";".join(notes + ["roe_unavailable"])

    roe = net_income / equity * 100.0

    # DOE cascade (higher entries take priority):
    #   (1) total dividends (CF statement > statement of changes in equity > dividend-policy table)
    #       ... total-amount basis, independent of share counts
    #         payout = total dividends / net income (profitable periods only),
    #         DOE = total dividends / period-end equity
    #   (2) payout-ratio tag in the summary table (consolidated > filer-only) ... a ratio that is
    #       unaffected by stock splits and reverse splits
    #   (3) DPS / EPS ... some reports have a retroactively adjusted EPS while DPS stays at the
    #       then-actual amount, which distorts the result by exactly the split ratio.
    #       Outliers are corrected or excluded (last-resort fallback).
    eps, dps = values.get("eps"), values.get("dps")
    tag = normalize_ratio(values.get("payout"), limit=5.0)
    if tag is not None and not 0.0 <= tag <= PAYOUT_SANITY_MAX:
        tag = None  # out-of-range tag values (unit mix-ups etc.) are not adopted
    p_raw = dps / eps if (eps and eps > 0 and dps is not None and dps >= 0) else None

    total = values.get("total_dividends")
    source = values.get("total_dividends_source") or ""
    if total is not None and total >= 0:
        reason = None
        if total / equity > TOTAL_DIV_MAX_DOE:
            reason = f"DOE={total / equity:.0%}"
        elif net_income > 0 and total / net_income > TOTAL_DIV_MAX_PAYOUT:
            reason = f"payout={total / net_income:.0%}"
        elif source.startswith("policy") and net_income > 0:
            # The structure of summed dividend-policy tables is uncertain, so adopt only when it roughly agrees with other payout ratios
            ref = tag if tag is not None else (
                correct_payout_for_split(p_raw)[0] if p_raw is not None else None)
            if ref and not POLICY_TOLERANCE[0] <= (total / net_income) / ref \
                    <= POLICY_TOLERANCE[1]:
                reason = "policy_table_inconsistent"
        if reason is None:
            notes.append(f"payout=total_div({source})")
            return roe, total / equity * 100.0, equity, ";".join(notes)
        notes.append(f"total_div_rejected({reason})")

    if roe > 0 and tag is not None:
        doe = roe * tag
        notes.append("payout=tag(" + ("solo" if values.get("payout_scope") == SCOPE_SOLO
                                      else "consol") + ")")
        if p_raw is not None and tag > 0 and p_raw > 0 \
                and not 0.5 <= p_raw / tag <= 2.0:
            notes.append(f"dps_eps_basis_mismatch(x{p_raw / tag:.2g})")
    elif roe > 0 and p_raw is not None:
        payout, fix = correct_payout_for_split(p_raw)
        if payout is None:
            return roe, None, equity, ";".join(
                notes + [f"payout_unresolved(dps/eps={p_raw:.0%})"])
        doe = roe * payout
        notes.append("payout=dps/eps" + fix)
        if values.get("dps_scope") == SCOPE_SOLO:
            notes.append("dps=solo_table")
    elif eps and dps is not None:
        # Loss-making period (EPS <= 0 or ROE <= 0): total dividends = net income x DPS / EPS still holds because the signs cancel
        doe = roe * dps / eps
        notes.append("doe=roe*dps/eps(赤字期)")
        if values.get("dps_scope") == SCOPE_SOLO:
            notes.append("dps=solo_table")
    elif eps:
        # Neither consolidated nor solo has a dividend element. Presumed no dividend ("-" in the table) and set to 0,
        # but an unsupported element name gives the same result, so the caller must always emit a diagnostic log.
        doe = 0.0
        notes.append("dps_absent->0")
    else:
        return roe, None, equity, ";".join(notes + ["doe_unavailable"])
    return roe, doe, equity, ";".join(notes)


def correct_payout_for_split(p_raw):
    """Correct the stock-split / reverse-split basis mismatch in the payout ratio derived from DPS / EPS.

    If the payout ratio in a profitable period (EPS > 0) is within PAYOUT_SANITY_MAX (150%), it is
    adopted as-is. Otherwise, among the split ratios f (10, 5, 4, 3, 2), the one for which the
    divided value falls within 100% and is closest to the typical payout ratio (35%) is adopted.
    If none qualifies, None is returned (excluded from the calculation).
    Returns: (payout ratio, note suffix)
    Caution: when the mismatch goes in the 0.1x direction (reverse split) and the value comes out
    low, the ratio alone cannot detect it. In that case the correction presupposes that the
    payout-ratio tag (1 above) is available.
    """
    if p_raw <= PAYOUT_SANITY_MAX:
        return p_raw, ""
    candidates = [(abs(p_raw / f - TYPICAL_PAYOUT), f) for f in SPLIT_FACTORS
                  if p_raw / f <= 1.0]
    if not candidates:
        return None, ""
    f = min(candidates)[1]
    return p_raw / f, f"/split{f}"


def extract_report_rows(zip_bytes, doc, offset, code):
    """Extract the Summary of Business Results (up to 5 periods) and total dividends from a report ZIP as "raw-value rows".

    Each row has a fiscal_year and the extracted values (JPY, JPY/share, ratios). ROE / DOE are
    computed after combining several reports (finalize_rows). This is because the CF statement and
    the statement of changes in equity hold only the latest two periods, so the years available
    differ from report to report.
    """
    period_end = date.fromisoformat(doc["periodEnd"])
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        candidates = [
            n for n in zf.namelist()
            if "/PublicDoc/" in n and n.lower().endswith(".xbrl")
        ]
        if not candidates:
            raise RuntimeError(T(f"PublicDoc 配下に XBRL が見つかりません: {doc.get('docID')}",
                                 f"No XBRL file found under PublicDoc: {doc.get('docID')}"))
        # Prefer the main body of the annual securities report (asr)
        candidates.sort(key=lambda n: ("asr" not in n.lower(), n))
        with zf.open(candidates[0]) as fp:
            facts, debug, total_dividends = parse_report_xbrl(fp, period_end)

    standard = detect_accounting_standard(facts)
    rows = []
    for n in range(0, 5):
        values = {}
        # Per-year decision: years with consolidated data use consolidated only, as before (existing results unchanged).
        # Only years without consolidated data (solo filers, pre-consolidation) fall back to individual data.
        solo_year = not has_consolidated_data(facts, n)
        for key in PATTERNS:
            values[key], values[f"{key}_scope"] = _pick_scoped(facts, key, n, solo_year)
        # In solo_year there is no consolidated net income / equity item, so values obtained here come from individual data
        values["solo_fallback"] = solo_year and any(
            values.get(k) is not None
            for k in ("net_income", "net_assets", "net_assets_bs", "total_equity",
                      "equity_direct", "equity_bs", "owners_equity"))
        total, source = total_dividends.get(n, (None, None))
        values["total_dividends"], values["total_dividends_source"] = total, source
        rows.append({
            "n": n,
            "source_offset": offset,
            "fiscal_year": fiscal_year_of(period_end) - n,
            "period_end": f"{period_end.year - n}-{period_end.month:02d}",
            "accounting_standard": standard,
            "source_doc_id": doc.get("docID"),
            "values": values,
            "doc": doc,
            "debug": debug,
        })
    return rows


def finalize_rows(raw_rows, code, name, log=print):
    """Combine the raw-value rows of several reports per fiscal year, compute ROE / DOE and return the rows.

    - Summary-table values (net income, equity, EPS, DPS, etc.) come from the newer report (smaller offset)
    - Total dividends are searched across all reports per year; the value stated for the nearest period (smaller n) takes priority
    """
    by_year = {}
    for r in raw_rows:
        by_year.setdefault(r["fiscal_year"], []).append(r)

    rows = []
    for fiscal_year in sorted(by_year):
        group = by_year[fiscal_year]
        primary = sorted(group, key=lambda r: (r["source_offset"], r["n"]))[0]
        values = dict(primary["values"])
        for r in sorted(group, key=lambda r: (r["n"], r["source_offset"])):
            if r["values"].get("total_dividends") is not None:
                values["total_dividends"] = r["values"]["total_dividends"]
                values["total_dividends_source"] = r["values"]["total_dividends_source"]
                break
        else:
            values["total_dividends"] = values["total_dividends_source"] = None
        # The balance-sheet main statement covers only two periods (current and previous), so the latest report alone yields only
        # the latest two years. BS-related values are adopted as a bundle from the report in which that year appears
        # nearest to the current period (smaller n)
        # (this avoids inconsistencies from picking net assets, non-controlling interests, etc. from different reports).
        for r in sorted(group, key=lambda r: (r["n"], r["source_offset"])):
            if any(r["values"].get(k) is not None for k in BS_EQUITY_KEYS):
                for k in BS_EQUITY_KEYS:
                    values[k] = r["values"].get(k)
                break

        roe, doe, equity, note = derive_roe_doe(values)
        net_income, total = values["net_income"], values["total_dividends"]
        rows.append({
            "code": code,
            "name": name,
            "fiscal_year": fiscal_year,
            "period_end": primary["period_end"],
            "accounting_standard": primary["accounting_standard"],
            "net_income_mn": None if net_income is None else net_income / 1e6,
            "equity_mn": None if equity is None else equity / 1e6,
            "total_dividends_mn": None if total is None else total / 1e6,
            "eps": values["eps"],
            "dps": values["dps"],
            "roe_pct": roe,
            "doe_pct": doe,
            "source_doc_id": primary["source_doc_id"],
            "note": note,
            "_primary": primary,
        })

    for row in rows:
        text = str(row["note"])
        if any(k in text for k in ("split", "basis_mismatch", "payout_unresolved",
                                   "total_div_rejected")):
            log(T(f"  [補正] {row['fiscal_year']}年度 (docID {row['source_doc_id']}): "
                  f"EPS={row['eps']} DPS={row['dps']} 総額={row['total_dividends_mn']} -> {text}",
                  f"  [adjustment] FY{row['fiscal_year']} (docID {row['source_doc_id']}): "
                  f"EPS={row['eps']} DPS={row['dps']} total={row['total_dividends_mn']} -> "
                  f"{note_for_log(text)}"))
    absent = [r for r in rows if "dps_absent" in str(r["note"])]
    if absent:
        first = absent[0]["_primary"]
        log_dividend_debug(first["doc"], first["accounting_standard"], first["debug"],
                           [r["fiscal_year"] for r in absent], log)
    log_equity_diagnostics(rows, code, log)
    for row in rows:
        row.pop("_primary")
    return rows


# Japanese tokens inside the CSV note column (data written at fetch time) and their English
# renderings. The CSV itself is never changed; this is applied only when printing English logs,
# so that English output stays ASCII-clean (safe for consoles / redirects that cannot encode Japanese).
_NOTE_TOKENS_EN = (
    ("株主資本及び評価・換算差額等合計", "shareholders' equity and valuation/translation adjustments"),
    ("株主資本+評価・換算差額等", "shareholders' equity + valuation/translation adjustments"),
    ("親会社の所有者に帰属する持分", "equity attributable to owners of the parent"),
    ("非支配株主持分を含む", "includes non-controlling interests"),
    ("非支配株主持分", "non-controlling interests"),
    ("新株予約権", "subscription rights"),
    ("純資産", "net assets"),
    ("赤字期", "loss-making period"),
    ("兆円", " trillion JPY"),
    ("百万円", " million JPY"),
)


def note_for_log(text):
    """Return a CSV note / label as shown in logs: unchanged in Japanese, ASCII English otherwise."""
    text = str(text)
    if is_ja():
        return text
    for ja, en in _NOTE_TOKENS_EN:
        text = text.replace(ja, en)
    return text


def _equity_source_of(note):
    """Extract the equity source label from a note (ignores text inside equity_rejected(...))."""
    for part in str(note).split(";"):
        if part.startswith("equity="):
            return part[len("equity="):]
    return T("取得不能", "unavailable")


def log_equity_diagnostics(rows, code, log=print):
    """Log the breakdown of equity sources and diagnostics for years caught by the outlier guard.

    When some rows fell back to ratio*assets, were rejected, were not computable, or are IFRS
    rows whose direct tag could not be picked up, it also prints the input values (ratio, total
    assets, balance-sheet items) and the equity-related element names in the report.
    """
    counts = {}
    for r in rows:
        label = _equity_source_of(r["note"])
        counts[label] = counts.get(label, 0) + 1
    log(T("  [自己資本] 取得元の内訳: ", "  [equity] source breakdown: ")
        + " / ".join(T(f"{k} {n}年", f"{note_for_log(k)}: {n} yr")
                  for k, n in sorted(counts.items())))
    flagged = []
    for r in rows:
        text = str(r["note"])
        if "equity_rejected" in text:
            log(T(f"  [警告] {r['fiscal_year']}年度 (docID {r['source_doc_id']}): "
                  f"自己資本の異常値を棄却しました -> {text}",
                  f"  [warning] FY{r['fiscal_year']} (docID {r['source_doc_id']}): "
                  f"rejected an outlier equity value -> {note_for_log(text)}"))
        if ("equity_rejected" in text or "roe_unavailable" in text
                or _equity_source_of(text) == "ratio*assets"
                or (r["accounting_standard"] == "IFRS"
                    and not _equity_source_of(text).startswith("direct"))):
            flagged.append(r)
    if not flagged:
        return
    first = flagged[0]
    values, debug = first["_primary"]["values"], first["_primary"]["debug"]

    def mn(x):
        return T("なし", "none") if x is None else f"{x / 1e6:,.0f}"

    log(T(f"  [DEBUG] 自己資本の入力値（{first['fiscal_year']}年度, {standard_label(first['accounting_standard'])}, "
          f"百万円）: 比率(生値)={values.get('equity_ratio')} "
          f"正規化後={normalize_ratio(values.get('equity_ratio'))} "
          f"総資産={mn(values.get('total_assets'))} 資本合計={mn(values.get('total_equity'))} "
          f"純資産(要約表)={mn(values.get('net_assets'))} 直接(要約表)={mn(values.get('equity_direct'))}",
          f"  [DEBUG] equity inputs (FY{first['fiscal_year']}, {standard_label(first['accounting_standard'])}, "
          f"million JPY): ratio(raw)={values.get('equity_ratio')} "
          f"normalized={normalize_ratio(values.get('equity_ratio'))} "
          f"total assets={mn(values.get('total_assets'))} total equity={mn(values.get('total_equity'))} "
          f"net assets(summary)={mn(values.get('net_assets'))} "
          f"direct(summary)={mn(values.get('equity_direct'))}"))
    log(T(f"  [DEBUG] BS本表: 親会社持分={mn(values.get('equity_bs'))} "
          f"純資産={mn(values.get('net_assets_bs'))} 株主資本={mn(values.get('shareholders_equity_bs'))} "
          f"評価・換算差額等={mn(values.get('valuation_bs'))} 非支配株主持分={mn(values.get('nci_bs'))} "
          f"新株予約権={mn(values.get('rights_bs'))}",
          f"  [DEBUG] balance sheet (main): parent's equity={mn(values.get('equity_bs'))} "
          f"net assets={mn(values.get('net_assets_bs'))} "
          f"shareholders' equity={mn(values.get('shareholders_equity_bs'))} "
          f"valuation/translation adj.={mn(values.get('valuation_bs'))} "
          f"non-controlling interests={mn(values.get('nci_bs'))} "
          f"subscription rights={mn(values.get('rights_bs'))}"))
    names = sorted(n for n in debug["summary_names"][SCOPE_CONSOLIDATED]
                   if re.search(r"Equity|Assets|Ratio|Capital|Interest|Rights", n))
    none = T("なし", "none")
    log(T("  [DEBUG] 連結の要約表の自己資本系要素: ",
          "  [DEBUG] equity-related elements in the consolidated summary table: ")
        + (", ".join(n.replace(SUMMARY_SUFFIX, "") for n in names) or none)
        + T(" / BS本表の自己資本系要素: ", " / equity-related elements in the BS main statement: ")
        + (", ".join(sorted(debug["equity_names"])) or none))
    log(T("  [DEBUG] 直接タグが見つからない場合は、上記の要素名を PATTERNS の equity_direct / "
          "equity_bs 系へ追記してください。",
          "  [DEBUG] If no direct tag was found, add the element names above to the "
          "equity_direct / equity_bs entries of PATTERNS."))


def log_dividend_debug(doc, standard, debug, absent_years, log=print):
    """Log diagnostics when none of dividends (total, DPS, payout ratio) could be obtained.

    The element names printed here are the clue to the dividend element that should have been
    picked up. For total dividends, add the name to CF_DIV_PATTERNS / SS_DIV_PATTERNS; for DPS,
    add it to PATTERNS["dps"].
    """
    def fmt(names):
        names = sorted(names)
        shown = ", ".join(n.replace(SUMMARY_SUFFIX, "") for n in names[:30])
        return shown + (T(f" …他{len(names) - 30}件", f" ... and {len(names) - 30} more")
                        if len(names) > 30 else "")

    solo_dps = [n for n in debug["summary_names"][SCOPE_SOLO] if "Dividend" in n]
    none = T("なし", "none")
    log(T(f"  [DEBUG] 配当を取得できませんでした: docID={doc.get('docID')} "
          f"({doc.get('periodEnd')}期, {standard_label(standard)}) 対象年度={sorted(absent_years)}",
          f"  [DEBUG] Could not obtain dividends: docID={doc.get('docID')} "
          f"(period ending {doc.get('periodEnd')}, {standard_label(standard)}) affected years={sorted(absent_years)}"))
    log(T(f"  [DEBUG] 連結の要約表の要素（{SUMMARY_SUFFIX}を省略）: "
          f"{fmt(debug['summary_names'][SCOPE_CONSOLIDATED]) or none}",
          f"  [DEBUG] consolidated summary-table elements ({SUMMARY_SUFFIX} omitted): "
          f"{fmt(debug['summary_names'][SCOPE_CONSOLIDATED]) or none}"))
    log(T(f"  [DEBUG] 単体の要約表の要素: {fmt(debug['summary_names'][SCOPE_SOLO]) or none}"
          f"（うち配当系: {fmt(solo_dps) or none}）",
          f"  [DEBUG] solo summary-table elements: {fmt(debug['summary_names'][SCOPE_SOLO]) or none}"
          f" (dividend-related: {fmt(solo_dps) or none})"))
    if debug["dividend_names"]:
        log(T("  [DEBUG] 報告書内の配当・配当性向を含む全要素名とコンテキスト例:",
              "  [DEBUG] All element names containing dividend / payout in the report, with example contexts:"))
        for name, ctxs in sorted(debug["dividend_names"].items()):
            log(f"    - {name}: {', '.join(ctxs)}")
    else:
        log(T("  [DEBUG] 報告書内に配当・配当性向を含む要素が1つもありません（無配の可能性）。",
              "  [DEBUG] The report has no element containing dividend / payout (possibly no dividend)."))
    log(T("  [DEBUG] 無配ではない場合は上記の要素名を CF_DIV_PATTERNS / SS_DIV_PATTERNS / "
          "PATTERNS['dps'] へ追記してください。取得できなかった年度の DOE は 0 として扱われています。",
          "  [DEBUG] If the company does pay dividends, add the element names above to "
          "CF_DIV_PATTERNS / SS_DIV_PATTERNS / PATTERNS['dps']. DOE is currently treated "
          "as 0 for the affected years."))


# ---------------------------------------------------------------------------
# 6. Per-company time series (baseline: latest and 5 years back; also merges 10 years back when available)
# ---------------------------------------------------------------------------
CSV_COLUMNS = [
    "code", "name", "fiscal_year", "period_end", "accounting_standard",
    "net_income_mn", "equity_mn", "avg_equity_mn", "total_dividends_mn", "eps", "dps",
    "roe_end_pct", "doe_end_pct", "roe_pct", "doe_pct",
    "lbs_pct", "sgr_pct", "cs", "osm", "payout_pct", "lane",
    "source_doc_id", "note",
]


def normalize_code(code):
    """Normalize a securities code to 4 characters (letters allowed). 5-digit input (trailing 0) is also accepted."""
    c = str(code).strip().upper()
    if len(c) == 5 and c.endswith("0"):
        c = c[:4]
    if not re.fullmatch(r"[0-9A-Z]{4}", c):
        raise ValueError(T(f"証券コードの形式が不正です: {code!r}",
                           f"Invalid securities code format: {code!r}"))
    return c


def fetch_company_series(client, code, fye_month=None, today=None, log=print,
                         full_dividend_coverage=True):
    """Fetch annual reports from EDINET and return the ROE / DOE time series for all obtainable years.

    The baseline is two reports (latest and 5 years back; about 8-10 periods after removing
    overlaps); if a report from about 10 years back can be obtained, it is added too (up to about
    10-14 years in total), taking the "Summary of Business Results" (5 periods each).
    Total dividends (from the CF statement etc.) appear in each report for only two periods
    (current and previous), so with full_dividend_coverage=True additional reports are fetched to
    fill the years missing a total (typically 2, 4 and 7 years back are added). With False, only
    the 2-3 baseline reports are used (minimum API calls).
    """
    today = today or date.today()
    code5 = code + "0"

    if fye_month is None:
        fye_month = FISCAL_END_MONTH.get(code)
    if fye_month is None:
        fye_month, _ = lookup_edinet_codelist(code5)
    months = [fye_month] if fye_month else [3, 12, 9, 6, 2, 11, 1, 4, 5, 7, 8, 10]
    if not fye_month:
        log(T("  決算期末月が不明のため全月を試行します（時間がかかります）。"
              "--fye-month の指定を推奨します。",
              "  The fiscal-year-end month is unknown, so all months will be tried (this takes "
              "a while). Specifying --fye-month is recommended."))

    # (1) Latest annual securities report
    latest = None
    for month in months:
        for fiscal_year in latest_fiscal_year_candidates(month, today):
            center = month_end(fiscal_year, month) + timedelta(days=FILING_CENTER_DAYS)
            latest = find_annual_report(
                client, code5, fiscal_year, month, center, FILING_RADIUS_LATEST, today
            )
            if latest:
                fye_month = month
                break
        if latest:
            break
    if not latest:
        raise LookupError(T(f"{code}: 直近の有価証券報告書が見つかりません。",
                            f"{code}: the latest annual securities report was not found."))
    latest_end = date.fromisoformat(latest["periodEnd"])
    latest_submit = datetime.fromisoformat(latest["submitDateTime"]).date()
    log(T(f"  直近: {latest['periodEnd']} 期 / 提出 {latest_submit} / docID {latest['docID']}",
          f"  latest: period ending {latest['periodEnd']} / filed {latest_submit} / "
          f"docID {latest['docID']}"))

    # (2) 5 and 10 years back (if not found, step the year forward and search again)
    found = [(0, latest)]
    used_offsets = {0}
    for offset in REPORT_OFFSETS[1:]:
        for step in range(0, OFFSET_FALLBACK_YEARS + 1):
            eff = offset - step
            if eff <= 0 or eff in used_offsets:
                continue
            center = shift_years(latest_submit, -eff)
            doc = find_annual_report(
                client, code5, latest_end.year - eff, fye_month, center,
                FILING_RADIUS_PAST, today,
            )
            if doc:
                found.append((eff, doc))
                used_offsets.add(eff)
                suffix = "" if step == 0 else T(
                    f"（{offset}年前相当が見つからないため{eff}年前で代替）",
                    f" (no report about {offset} years back was found; using {eff} years back instead)")
                log(T(f"  {eff}年前: {doc['periodEnd']} 期 / docID {doc['docID']}{suffix}",
                      f"  {eff} years back: period ending {doc['periodEnd']} / "
                      f"docID {doc['docID']}{suffix}"))
                break
        else:
            log(T(f"  [警告] {offset}年前の有価証券報告書が見つかりませんでした。",
                  f"  [warning] No annual securities report found for {offset} years back."))

    # (2b) Additional reports to fill years missing total dividends (each report holds two periods: current and previous)
    if full_dividend_coverage:
        covered = set()
        for offset, _ in found:
            covered |= {offset, offset + 1}
        for offset in range(1, max(o for o, _ in found) + 1):
            if offset in covered:
                continue
            doc = find_annual_report(
                client, code5, latest_end.year - offset, fye_month,
                shift_years(latest_submit, -offset), FILING_RADIUS_PAST, today,
            )
            if doc:
                found.append((offset, doc))
                covered |= {offset, offset + 1}
                log(T(f"  {offset}年前（配当金総額の補完）: {doc['periodEnd']} 期 / "
                      f"docID {doc['docID']}",
                      f"  {offset} years back (to fill total dividends): period ending "
                      f"{doc['periodEnd']} / docID {doc['docID']}"))
            else:
                log(T(f"  [警告] {offset}年前の報告書が見つからず、その年度の配当金総額は"
                      "取得できません。",
                      f"  [warning] The report for {offset} years back was not found, so total "
                      "dividends for that year cannot be obtained."))

    # (3) Parse, combine per fiscal year and compute ROE / DOE
    raw_rows = []
    for offset, doc in found:
        zip_bytes = client.download_xbrl_zip(doc["docID"])
        raw_rows.extend(extract_report_rows(zip_bytes, doc, offset, code))
    rows = finalize_rows(raw_rows, code, latest.get("filerName", ""), log=log)
    df = pd.DataFrame(rows)
    df = df[df["fiscal_year"] >= fiscal_year_of(latest_end) - 14]
    return df.sort_values("fiscal_year").reset_index(drop=True)


# ---------------------------------------------------------------------------
# 7. Local cache (moat_data_{securities code}.csv)
# The cache is language-independent: the same CSV is shared by --lang en and --lang ja.
def csv_path(datadir, code):
    return Path(datadir) / f"moat_data_{code}.csv"


def is_legacy_cache(df):
    """Detect an old-format cache that predates the total-dividend basis, or one that contains inaccurate dividends."""
    if "total_dividends_mn" not in df.columns:  # CSV from before the total-amount basis was introduced
        return True
    if "note" not in df.columns:
        return False
    if df["note"].astype(str).str.contains("dps_missing->0", regex=False).any():
        return True
    # A cache saved before the stock-split correction, containing rows with an abnormal payout ratio in a profitable period
    if {"eps", "payout_pct"} <= set(df.columns):
        bad = (df["eps"] > 0) & (df["payout_pct"] > PAYOUT_SANITY_MAX * 100)
        if bad.any():
            return True
    return False


def log_dividend_coverage(code, table, log=print):
    """Log the number of years with total dividends and the breakdown of the calculation basis per year."""
    n_all = len(table)
    n_total = int(table["total_dividends_mn"].notna().sum())
    log(T(f"[{code}] 配当金総額取得 {n_total}/{n_all}年",
          f"[{code}] total dividends obtained: {n_total}/{n_all} years"))
    notes = table["note"].astype(str)
    # The match strings are the data stored in the CSV note column (including the Japanese
    # "赤字期" = loss-making period), so the patterns are kept as-is; only the labels are localized.
    counts = {
        T("総額ベース（CF計算書）", "total basis (CF statement)"):
            notes.str.contains(r"total_div\(cf", regex=True).sum(),
        T("総額ベース（株主資本等変動計算書）", "total basis (statement of changes in equity)"):
            notes.str.contains(r"total_div\(ss", regex=True).sum(),
        T("総額ベース（配当政策表）", "total basis (dividend-policy table)"):
            notes.str.contains(r"total_div\(policy", regex=True).sum(),
        T("配当性向タグ", "payout-ratio tag"):
            notes.str.contains("payout=tag", regex=False).sum(),
        T("DPS/EPS（フォールバック）", "DPS/EPS (fallback)"):
            notes.str.contains("payout=dps/eps", regex=False).sum(),
        T("赤字期の比率計算", "ratio computation in loss-making periods"):
            notes.str.contains("赤字期", regex=False).sum(),
        T("配当要素なし（DOE=0）", "no dividend element (DOE=0)"):
            notes.str.contains("dps_absent", regex=False).sum(),
        T("算出除外", "excluded from calculation"):
            notes.str.contains("payout_unresolved", regex=False).sum(),
    }
    log(T(f"[{code}] 算出根拠の内訳: "
          + " / ".join(f"{k} {int(v)}年" for k, v in counts.items() if v),
          f"[{code}] calculation basis breakdown: "
          + " / ".join(f"{k}: {int(v)} yr" for k, v in counts.items() if v)))
    if n_total < n_all:
        missing = sorted(table.loc[table["total_dividends_mn"].isna(), "fiscal_year"])
        log(T(f"[{code}] 総額が未取得の年度（配当性向タグ・DPS/EPSで代替）: "
              f"{', '.join(str(int(y)) for y in missing)}",
              f"[{code}] years without a total amount (substituted by the payout-ratio tag / "
              f"DPS/EPS): {', '.join(str(int(y)) for y in missing)}"))


def trim_to_primary_statements(table, code="", log=print):
    """Restrict the plotted period to "years whose total dividends come from primary statements (CF statement etc.)".

    Older years (e.g. prior-year data inside the report from about 10 years back) have no total
    dividends and rely on the DPS/EPS or payout-ratio-tag fallbacks (which stock splits and
    reverse splits distort). Years before the first year with a total are dropped from plotting.
    Only the plotting table is trimmed; the CSV itself keeps all years for auditing.
    For a company with no total in any year, trimming would leave nothing, so all years are kept.
    """
    if "total_dividends_mn" not in table.columns:
        return table
    has_total = table["total_dividends_mn"].notna()
    if not has_total.any():
        log(T(f"[{code}] 配当金総額が全年度で未取得のため、期間を絞らずフォールバック値で描画します。",
              f"[{code}] No total dividends in any year; plotting all years with fallback values "
              "(period not trimmed)."))
        return table
    first_year = table.loc[has_total, "fiscal_year"].min()
    dropped = sorted(int(y) for y in table.loc[table["fiscal_year"] < first_year, "fiscal_year"])
    if dropped:
        log(T(f"[{code}] 一次諸表で総額が確認できる {int(first_year)}年度以降に限定"
              f"（除外: {', '.join(str(y) for y in dropped)}年度）",
              f"[{code}] Restricted to FY{int(first_year)} onward, where the total is confirmed "
              f"in primary statements (excluded: FY{', FY'.join(str(y) for y in dropped)})"))
    return table[table["fiscal_year"] >= first_year].reset_index(drop=True)


def load_or_fetch(code, datadir, force_update, get_client, fye_month=None, log=print,
                  full_dividend_coverage=True):
    """Read the CSV under datadir without any API call if it exists; otherwise fetch from EDINET and save it."""
    path = csv_path(datadir, code)
    if path.exists() and not force_update:
        df = pd.read_csv(path, dtype={"code": str, "lane": str})
        if len(df) == 0:
            log(T(f"[{code}] キャッシュが空のため再取得します。",
                  f"[{code}] The cache is empty; fetching again."))
        elif is_legacy_cache(df):
            log(T(f"[{code}] 不正確な配当データを含む旧版キャッシュを検出しました。"
                  "削除せずに再取得して上書きします。",
                  f"[{code}] Detected an old-format cache with inaccurate dividend data. "
                  "Fetching again and overwriting it (no deletion needed)."))
        else:
            log(T(f"[{code}] キャッシュ読込（API通信なし）: {path}",
                  f"[{code}] Loaded from cache (no API calls): {path}"))
            return compute_moat_table(df)

    log(T(f"[{code}] EDINET から取得します…", f"[{code}] Fetching from EDINET..."))
    raw = fetch_company_series(get_client(), code, fye_month=fye_month, log=log,
                               full_dividend_coverage=full_dividend_coverage)
    table = compute_moat_table(raw)
    table = table.reindex(columns=CSV_COLUMNS)
    Path(datadir).mkdir(parents=True, exist_ok=True)
    table.to_csv(path, index=False, encoding="utf-8")
    log(T(f"[{code}] 保存: {path}（{len(table)}年分）",
          f"[{code}] saved: {path} ({len(table)} years)"))
    log_dividend_coverage(code, table, log)
    return compute_moat_table(table.drop(columns=["lane"]))


# ---------------------------------------------------------------------------
# 8. Interpolation (smoothly connecting all obtained fiscal years)
# ---------------------------------------------------------------------------
def pchip_interpolate(x, y, xq):
    """Monotonicity-preserving piecewise cubic Hermite interpolation (Fritsch-Carlson method).

    Unlike spline interpolation, it does not overshoot (e.g. DOE dipping below zero).
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    xq = np.asarray(xq, dtype=float)
    n = len(x)
    if n == 1:
        return np.full_like(xq, y[0], dtype=float)
    h = np.diff(x)
    delta = np.diff(y) / h
    if n == 2:
        return y[0] + delta[0] * (xq - x[0])

    slope = np.zeros(n)
    for k in range(1, n - 1):
        if delta[k - 1] * delta[k] > 0:
            w1 = 2 * h[k] + h[k - 1]
            w2 = h[k] + 2 * h[k - 1]
            slope[k] = (w1 + w2) / (w1 / delta[k - 1] + w2 / delta[k])

    def end_slope(h0, h1, d0, d1):
        s = ((2 * h0 + h1) * d0 - h0 * d1) / (h0 + h1)
        if np.sign(s) != np.sign(d0):
            return 0.0
        if np.sign(d0) != np.sign(d1) and abs(s) > 3 * abs(d0):
            return 3 * d0
        return s

    slope[0] = end_slope(h[0], h[1], delta[0], delta[1])
    slope[-1] = end_slope(h[-1], h[-2], delta[-1], delta[-2])

    idx = np.clip(np.searchsorted(x, xq, side="right") - 1, 0, n - 2)
    t = (xq - x[idx]) / h[idx]
    h00 = 2 * t**3 - 3 * t**2 + 1
    h10 = t**3 - 2 * t**2 + t
    h01 = -2 * t**3 + 3 * t**2
    h11 = t**3 - t**2
    return (h00 * y[idx] + h10 * h[idx] * slope[idx]
            + h01 * y[idx + 1] + h11 * h[idx] * slope[idx + 1])


@dataclass
class Trajectory:
    """Interpolated trajectory of one company (arrays aligned with the frame times t_grid)."""

    code: str
    name: str
    valid: np.ndarray      # whether it is drawn at that time (False before listing / before the data start)
    roe: np.ndarray
    doe: np.ndarray
    sgr: np.ndarray
    cs: np.ndarray
    lbs: np.ndarray
    payout: np.ndarray
    lane: list
    first_year: int
    last_year: int


def build_trajectories(tables, names, steps, focus_code):
    """Interpolate each company's ROE / DOE from annual to sub-frames and compute per-frame coordinates and lanes.

    ROE / DOE are interpolated first and the four operations and the lane assignment are applied
    afterwards, so the position, size and color of a bubble are decided by the same model in
    every frame.
    """
    years = [int(y) for t in tables.values() for y in t["fiscal_year"]]
    # The time axis starts at the focus company's oldest fiscal year. Other companies appear from their own data start
    # only if their disclosure starts after that year (e.g. recently listed).
    focus_years = tables[focus_code]["fiscal_year"].dropna()
    t0, t1 = int(focus_years.min()), max(years)
    n_t = max(1, (t1 - t0) * steps + 1)
    t_grid = np.linspace(t0, t1, n_t)

    trajs = {}
    for code, tbl in tables.items():
        tbl = tbl.dropna(subset=["roe_pct", "doe_pct"]).sort_values("fiscal_year")
        if tbl.empty:
            continue
        yrs = tbl["fiscal_year"].to_numpy(dtype=float)
        tq = np.clip(t_grid, yrs[0], yrs[-1])  # hold the last value after the latest year
        roe = pchip_interpolate(yrs, tbl["roe_pct"].to_numpy(dtype=float), tq)
        doe = pchip_interpolate(yrs, tbl["doe_pct"].to_numpy(dtype=float), tq)
        payout = calc_payout_pct(roe, doe)
        trajs[code] = Trajectory(
            code=code,
            name=names.get(code, ""),
            valid=t_grid >= yrs[0] - 1e-9,
            roe=roe,
            doe=doe,
            sgr=calc_sgr(roe, doe),
            cs=calc_cs(roe, doe),
            lbs=calc_lbs(roe, doe),
            payout=payout,
            lane=[lane_of(d) for d in payout],  # re-decide the nearest lane every frame
            first_year=int(yrs[0]),
            last_year=int(yrs[-1]),
        )
    return t_grid, trajs


# ---------------------------------------------------------------------------
# 9. Shared drawing components
# ---------------------------------------------------------------------------
def setup_japanese_font():
    """Set a Japanese font. Returns False if none is found (switch to English labels)."""
    matplotlib.rcParams["axes.unicode_minus"] = False

    def apply():
        available = {f.name for f in font_manager.fontManager.ttflist}
        for name in JP_FONT_CANDIDATES:
            if name in available:
                matplotlib.rcParams["font.family"] = [name, "DejaVu Sans"]
                return True
        return False

    if apply():
        return True
    keywords = ("notosanscjk", "notosansjp", "ipaexg", "ipag", "takao", "vlgothic",
                "meiryo", "yugoth", "hiragino", "msgothic")
    try:  # Colab etc.: re-register CJK fonts installed on the system
        for path in font_manager.findSystemFonts():
            if any(k in os.path.basename(path).lower() for k in keywords):
                font_manager.fontManager.addfont(path)
    except Exception:
        pass
    if apply():
        return True
    try:  # last resort: use japanize-matplotlib if it is installed
        importlib.import_module("japanize_matplotlib")
        return True
    except Exception:
        return False


AXIS_MARGIN = 0.12      # margin added on all four sides by dynamic scaling (fraction of the data range)
AXIS_MIN_SPAN_X = 5.0   # minimum span (SGR, %) used for the margin; avoids excessive zoom when the data are narrow
AXIS_MIN_SPAN_Y = 50.0  # same for CS (%^2)


def axis_limits(tables, trajs=None, min_year=None):
    """Return the dynamic-scaling axis ranges from SGR / CS of all plotted companies and years.

    The min / max of the whole data set are scanned and a margin of AXIS_MARGIN is added on all
    sides. The range always contains 0 (so the SGR=0 and CS=0 lines are visible as references).
    A lower bound (AXIS_MIN_SPAN_*) on the reference span keeps the axes from stretching or
    shrinking unnaturally when the data are tightly clustered.
    If trajs (the return value of build_trajectories) is given, paths that overshoot the annual
    knots through PCHIP interpolation (the GIF frames) are scanned too. Plotly needs only the
    annual knots.
    If min_year is given, years before it (rows before the focus company's start, which are not
    drawn) are ignored.
    """
    sub = {c: (t if min_year is None else t[t["fiscal_year"] >= min_year])
           for c, t in tables.items()}
    xs = [t["sgr_pct"].to_numpy(float) for t in sub.values()]
    ys = [t["cs"].to_numpy(float) for t in sub.values()]
    for tj in (trajs or {}).values():
        xs.append(np.asarray(tj.sgr, dtype=float)[tj.valid])
        ys.append(np.asarray(tj.cs, dtype=float)[tj.valid])
    sgr = np.concatenate(xs)
    cs = np.concatenate(ys)
    sgr, cs = sgr[np.isfinite(sgr)], cs[np.isfinite(cs)]
    if sgr.size == 0 or cs.size == 0:
        return (-1.0, AXIS_MIN_SPAN_X), (-5.0, AXIS_MIN_SPAN_Y)

    def limits(values, min_span):
        lo, hi = min(float(values.min()), 0.0), max(float(values.max()), 0.0)
        margin = AXIS_MARGIN * max(hi - lo, min_span)
        return lo - margin, hi + margin

    return limits(sgr, AXIS_MIN_SPAN_X), limits(cs, AXIS_MIN_SPAN_Y)


ZOOM_ZERO_PAD_RATIO = 0.05  # when the zoom window crosses 0, keep just enough lower margin to see the 0 line (ratio of span)


def zoom_limits(tables, focus_code, span, log=print):
    """Return a zoom window (xlim, ylim) centered on the focus company's latest-year coordinates (SGR, CS).

    The window is [center - span, center + span]. When the center is >= 0 and the lower edge falls
    below 0, the lower edge is clipped to -span * ZOOM_ZERO_PAD_RATIO so the negative region is
    not shown at length. When the center is negative (loss-making etc.), the window is not clipped
    and keeps its full width.
    Returns None when the coordinates cannot be obtained or span is invalid (the caller falls back
    to the full view).
    """
    if not np.isfinite(span) or span <= 0:
        log(T(f"  [警告] --zoom-span={span} は正の有限値ではないため、全体描画で実行します。",
              f"  [warning] --zoom-span={span} is not a positive finite value; drawing the full view."))
        return None
    tbl = tables[focus_code].dropna(subset=["roe_pct", "doe_pct"]).sort_values("fiscal_year")
    if tbl.empty:
        return None
    last = tbl.iloc[-1]
    cx, cy = float(last["sgr_pct"]), float(last["cs"])
    if not (np.isfinite(cx) and np.isfinite(cy)):
        log(T(f"  [警告] {focus_code} の最新年度座標が有限値でないため、全体描画で実行します。",
              f"  [warning] The latest-year coordinates of {focus_code} are not finite; "
              "drawing the full view."))
        return None

    def window(center):
        lo, hi = center - span, center + span
        if center >= 0 and lo < 0:
            lo = -span * ZOOM_ZERO_PAD_RATIO
        return lo, hi

    xlim, ylim = window(cx), window(cy)
    log(T(f"  [ズーム] {focus_code} FY{int(last['fiscal_year'])} 中心 (SGR {cx:.1f}, CS {cy:.1f}) "
          f"±{span:g}: SGR {xlim[0]:.1f} 〜 {xlim[1]:.1f} / CS {ylim[0]:.1f} 〜 {ylim[1]:.1f}",
          f"  [zoom] {focus_code} FY{int(last['fiscal_year'])} center (SGR {cx:.1f}, CS {cy:.1f}) "
          f"+/-{span:g}: SGR {xlim[0]:.1f} to {xlim[1]:.1f} / CS {ylim[0]:.1f} to {ylim[1]:.1f}"))
    return xlim, ylim


def lane_curves(xmax, n=400, ja=None):
    """Return the five reference orbits fixed in the background (four parabolas plus the X axis).

    Returns: [(key, color, legend label, line style, x array, y array), ...]
    ja: True for Japanese legend labels, False for English; None follows the active language.
    """
    ja = is_ja() if ja is None else ja
    x = np.linspace(0, xmax, n)
    curves = []
    for d_pct, (color, label, ls) in LANES.items():
        curves.append((d_pct, color, label if ja else LANE_SHORT_LABEL_EN[d_pct], ls, x,
                       k_of(d_pct / 100) * x**2))
    k_out = k_of(OUTER_PAYOUT)
    label = (f"外側の低角度軌道 (d = 11.45% → k ≈ {k_out:.3f})" if ja
             else LANE_SHORT_LABEL_EN["outer"])
    curves.append(("outer", OUTER_COLOR, label, ":", x, k_out * x**2))
    return curves


def layout_aligned_labels(points, ylim, gap=0.075, lo=0.04, hi=0.96):
    """Align the labels of all companies in one vertical column in the left / right margins (avoids overlap).

    Companies are split left / right at the median of the points' X coordinates; within each
    column the y order is preserved while a minimum spacing `gap` is secured.
    Returns: {code: ("left" | "right", y in axes coordinates)}
    """
    items = sorted(points.items(), key=lambda kv: kv[1][0])
    half = (len(items) + 1) // 2
    result = {}
    for side, group in (("left", items[:half]), ("right", items[half:])):
        if not group:
            continue
        span = ylim[1] - ylim[0]
        desired = sorted(
            ((code, float(np.clip((y - ylim[0]) / span, lo, hi))) for code, (_, y) in group),
            key=lambda t: t[1],
        )
        g = min(gap, (hi - lo) / max(len(desired) - 1, 1))
        pos = [p for _, p in desired]
        for i in range(1, len(pos)):
            pos[i] = max(pos[i], pos[i - 1] + g)
        if pos[-1] > hi:  # if it exceeds the top, push back downward
            pos[-1] = hi
            for i in range(len(pos) - 2, -1, -1):
                pos[i] = min(pos[i], pos[i + 1] - g)
        for (code, _), p in zip(desired, pos):
            result[code] = (side, p)
    return result


def company_label(code, names):
    """Display name for titles and legends, in the form "Strike (6196)" (corporate-form suffixes removed).

    The regex removes Japanese corporate-form suffixes (株式会社 etc.); English names pass through unchanged.
    """
    name = re.sub(r"株式会社|\(株\)|（株）|㈱", "", names.get(code, "") or "").strip()
    return f"{name} ({code})" if name else str(code)


def display_name(code, names, names_ok):
    """Return "code name". If names_ok is False (no Japanese font), the name is omitted (code only)."""
    name = names.get(code, "") if names_ok else ""
    return f"{code} {name}".strip()


def standard_label(standard):
    """Display label of an accounting standard. The CSV keeps "日本基準"; English shows "Japanese GAAP"."""
    if standard == "日本基準" and not is_ja():
        return "Japanese GAAP"
    return standard
# ---------------------------------------------------------------------------
# 10. Matplotlib GIF animation
# ---------------------------------------------------------------------------
def render_gif(tables, names, focus_code, out_path, steps=8, hold_frames=20,
               fps=20, dpi=100, log=print, view_limits=None):
    """Write the trajectories of all obtained fiscal years as a GIF.

    - The five reference orbits in the background are fixed in every frame
    - Only the focus company gets a label and a thick trajectory (colored by the nearest lane per segment) that follow it
    - Other companies are semi-transparent reference points; aligned labels of all companies appear only in the first and last frames
    """
    font_ok = setup_japanese_font() if is_ja() else False
    if not is_ja():
        matplotlib.rcParams["axes.unicode_minus"] = False
    ja_mode = is_ja() and font_ok       # draw Japanese text in the figure
    names_ok = (not is_ja()) or font_ok  # company names can be rendered (English names always can)
    if is_ja() and not font_ok:
        log("  [情報] 日本語フォントが見つからないため、図中の文言を英語で描画します。")

    def tr(ja, en):
        return ja if ja_mode else en

    t_grid, trajs = build_trajectories(tables, names, steps, focus_code)
    if focus_code not in trajs:
        raise ValueError(T(f"フォーカス銘柄 {focus_code} の描画可能なデータがありません。",
                           f"The focus company {focus_code} has no drawable data."))
    codes = list(trajs)
    others = [c for c in codes if c != focus_code]
    n_t = len(t_grid)
    if view_limits is None:
        xlim, ylim = axis_limits(tables, trajs=trajs, min_year=int(round(t_grid[0])))
        log(T(f"  [軸] 動的スケーリング: SGR {xlim[0]:.1f} 〜 {xlim[1]:.1f} / "
              f"CS {ylim[0]:.1f} 〜 {ylim[1]:.1f}",
              f"  [axes] dynamic scaling: SGR {xlim[0]:.1f} to {xlim[1]:.1f} / "
              f"CS {ylim[0]:.1f} to {ylim[1]:.1f}"))
    else:  # zoomed drawing: use the axis ranges specified by the caller (zoom_limits)
        xlim, ylim = view_limits

    def in_view(x, y):
        """Window check, only when zoomed. Always True in normal drawing (keeps the existing behavior)."""
        return view_limits is None or (xlim[0] <= x <= xlim[1] and ylim[0] <= y <= ylim[1])

    focus = trajs[focus_code]
    focus_tbl = tables[focus_code].dropna(subset=["roe_pct", "doe_pct"])

    # Frame plan: hold at the start and end (all labels shown), normal playback in between
    if n_t == 1:
        plan = [(0, True)] * hold_frames
    else:
        plan = ([(0, True)] * hold_frames
                + [(j, False) for j in range(1, n_t - 1)]
                + [(n_t - 1, True)] * hold_frames)

    # Placement of the aligned labels (computed separately for the first and last states)
    def label_layout(j):
        pts = {c: (trajs[c].sgr[j], trajs[c].cs[j]) for c in codes
               if trajs[c].valid[j] and in_view(trajs[c].sgr[j], trajs[c].cs[j])}
        return pts, layout_aligned_labels(pts, ylim)

    layouts = {0: label_layout(0), n_t - 1: label_layout(n_t - 1)}

    bubble_scale = 9.0  # bubble area = LBS x bubble_scale (pt^2)
    fig = Figure(figsize=(12, 7.6), dpi=dpi)
    FigureCanvasAgg(fig)
    fig.patch.set_facecolor("white")
    fig.subplots_adjust(left=0.20, right=0.80, top=0.90, bottom=0.10)
    ax = fig.add_subplot(111)
    ax.set_facecolor("#fafafa")

    # --- Static background: dango zone and the five reference orbits (four parabolas plus the X axis) ---
    ax.add_patch(Rectangle((DANGO_ZONE["x"], DANGO_ZONE["y"]), DANGO_ZONE["w"],
                           DANGO_ZONE["h"], facecolor="#f0c987", edgecolor="#d9a441",
                           linestyle="--", linewidth=1.0, alpha=0.28, zorder=0.5))
    legend_handles = []
    for key, color, label, ls, x, y in lane_curves(xlim[1], ja=ja_mode):
        ax.plot(x, y, ls, color=color, linewidth=1.5, alpha=0.9, zorder=1)
        legend_handles.append(plt_line(color, ls, label))
    ax.axhline(0, color="#8a9199", linewidth=1.2, zorder=1)
    legend_handles.append(Patch(facecolor="#f0c987", edgecolor="#d9a441", alpha=0.45,
                                linestyle="--",
                                label=tr("団子ゾーン (SGR 7〜14%、CS 35〜110)",
                                         "Dango zone (SGR 7-14%, CS 35-110)")))
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.yaxis.set_label_coords(-0.30, 0.5)  # move it out of the way of the aligned-label column in the left margin
    ax.set_xlabel(
        tr("Sustainable Growth Rate : SGR (%)  [引き算：サステナブル内部成長力 ＝ ROE − DOE]",
           "Sustainable Growth Rate : SGR (%)  [ROE - DOE]"),
        fontsize=10.5, fontweight="bold", color="#34495e", labelpad=8)
    ax.set_ylabel(
        tr("Compounding Supercharger : CS (%²)  [掛け算：複利増幅インデックス ＝ DOE × ROE]",
           "Compounding Supercharger : CS (%^2)  [DOE x ROE]"),
        fontsize=10.5, fontweight="bold", color="#34495e", labelpad=8)
    legend = ax.legend(handles=legend_handles, loc="upper left", fontsize=7.6, frameon=True,
                       framealpha=0.95, edgecolor="#c9ced4",
                       title=tr("配当レーン（バブル色 ＝ 最寄りレーン）",
                                "Dividend lanes (bubble color = nearest lane)"),
                       title_fontsize=8)
    legend.get_frame().set_linewidth(0.8)
    fig.suptitle(
        tr("「四則演算数理モデル」モート軌跡", "Four-operations model: moat trajectory")
        + f"  [{display_name(focus_code, names, names_ok)}]",
        fontsize=14, fontweight="bold", color="#2c3e50", y=0.965)
    fig.text(0.99, 0.012,
             tr("バブル面積 ＝ LBS（ROE＋DOE）／出典：EDINET 有価証券報告書"
                "「主要な経営指標等の推移」（期中平均自己資本ベース、年次間はPCHIP補間）",
                "Bubble area = LBS (ROE+DOE) / Source: EDINET annual securities reports "
                "(average equity basis, PCHIP-interpolated between years)"),
             ha="right", va="bottom", fontsize=7.5, color="#5d6d7e")

    # --- Dynamic artists (updated every frame) -------------------------------------
    year_text = ax.text(0.985, 0.04, "", transform=ax.transAxes, ha="right", va="bottom",
                        fontsize=34, fontweight="bold", color="#2c3e50", alpha=0.22, zorder=0.8)
    others_sc = ax.scatter(np.empty((0, 2))[:, 0], np.empty((0, 2))[:, 1], s=[], zorder=2)
    trail = LineCollection([], linewidths=4.2, capstyle="round", zorder=4, alpha=0.9)
    ax.add_collection(trail)
    knots_sc = ax.scatter([], [], s=22, color="#2c3e50", zorder=5)
    focus_sc = ax.scatter([], [], s=[], edgecolors="white", linewidths=1.6, zorder=6)

    knot_years = [int(y) for y in focus_tbl["fiscal_year"]]
    knot_xy = {int(r.fiscal_year): (r.sgr_pct, r.cs) for r in focus_tbl.itertuples()}
    knot_texts = {}
    label_years = {yk for yk in knot_years
                   if (knot_years[-1] - yk) % 5 == 0 or yk == knot_years[0]}
    for yk in knot_years:  # year labels only every 5 years (counted from the latest year) and at the start; avoids crowding
        knot_texts[yk] = ax.text(knot_xy[yk][0], knot_xy[yk][1], f" '{yk % 100:02d}",
                                 fontsize=7, color="#2c3e50", zorder=5, visible=False)

    follow = ax.annotate(
        "", xy=(0, 0), xytext=(18, 20), textcoords="offset points", ha="left", va="bottom",
        fontsize=9, fontweight="bold", color="#2c3e50", zorder=8, annotation_clip=False,
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#2c3e50", alpha=0.95, lw=1.0),
        arrowprops=dict(arrowstyle="-", color="#2c3e50", lw=1.0, shrinkA=0, shrinkB=4))
    follow.set_visible(False)

    aligned = {}
    for code in codes:
        aligned[code] = ax.annotate(
            "", xy=(0, 0), xytext=(0, 0), textcoords="axes fraction", va="center",
            fontsize=7.6, fontweight="bold", color="#2c3e50", zorder=7,
            annotation_clip=False,
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#c9ced4", alpha=0.95, lw=0.8),
            arrowprops=dict(arrowstyle="-", color="#7f8c8d", lw=0.7, shrinkA=0, shrinkB=3))
        aligned[code].set_visible(False)

    def lane_rgba(lane, alpha):
        return to_rgba(lane_color(lane), alpha)

    def update(frame_no):
        j, show_all = plan[frame_no]
        year_text.set_text(tr(f"{int(round(t_grid[j]))}年度", f"FY{int(round(t_grid[j]))}"))

        # Other companies: semi-transparent reference points (colored by each frame's nearest lane)
        vis = [c for c in others if trajs[c].valid[j]]
        if vis:
            others_sc.set_offsets(np.column_stack([[trajs[c].sgr[j] for c in vis],
                                                   [trajs[c].cs[j] for c in vis]]))
            others_sc.set_sizes([max(trajs[c].lbs[j], 1.0) * bubble_scale * 0.55 for c in vis])
            others_sc.set_facecolors([lane_rgba(trajs[c].lane[j], 0.30) for c in vis])
            others_sc.set_edgecolors([lane_rgba(trajs[c].lane[j], 0.55) for c in vis])
        else:
            others_sc.set_offsets(np.empty((0, 2)))
            others_sc.set_sizes([])

        # Focus company: thick trajectory (colored by the nearest lane per segment) plus the bubble
        idx = np.flatnonzero(focus.valid[:j + 1])
        if focus.valid[j]:
            pts = np.column_stack([focus.sgr[idx], focus.cs[idx]])
            if len(pts) >= 2:
                trail.set_segments(np.stack([pts[:-1], pts[1:]], axis=1))
                trail.set_color([lane_rgba(focus.lane[i], 0.85) for i in idx[1:]])
            else:
                trail.set_segments([])
            focus_sc.set_offsets([[focus.sgr[j], focus.cs[j]]])
            focus_sc.set_sizes([max(focus.lbs[j], 1.0) * bubble_scale])
            focus_sc.set_facecolors([lane_rgba(focus.lane[j], 0.92)])
            focus_sc.set_edgecolors(["white"])
            reached = [yk for yk in knot_years if t_grid[j] >= yk - 1e-9]
            knots_sc.set_offsets(np.array([knot_xy[yk] for yk in reached]).reshape(-1, 2))
            for yk, text in knot_texts.items():
                text.set_visible(yk in reached and yk in label_years)
        else:
            trail.set_segments([])
            focus_sc.set_offsets(np.empty((0, 2)))
            focus_sc.set_sizes([])
            knots_sc.set_offsets(np.empty((0, 2)))

        # Labels: normally only the focus company follows; all companies are aligned only while holding at the start / end
        for ann in aligned.values():
            ann.set_visible(False)
        follow.set_visible(False)
        if show_all:
            pts, layout = layouts[0 if j == 0 else n_t - 1]
            for code, (side, ypos) in layout.items():
                ann = aligned[code]
                x, y = pts[code]
                tr_ = trajs[code]
                ann.xy = (x, y)
                ann.set_position((-0.075 if side == "left" else 1.02, ypos))
                ann.set_ha("right" if side == "left" else "left")
                ann.set_text(f"{display_name(code, names, names_ok)}\n"
                             f"(SGR:{tr_.sgr[j]:.1f}%, CS:{tr_.cs[j]:.1f})")
                ann.set_visible(True)
        elif focus.valid[j] and in_view(focus.sgr[j], focus.cs[j]):
            follow.xy = (focus.sgr[j], focus.cs[j])
            follow.set_text(
                f"{display_name(focus_code, names, names_ok)}\n"
                f"ROE {focus.roe[j]:.1f}% / DOE {focus.doe[j]:.1f}%\n"
                f"SGR {focus.sgr[j]:.1f}% / CS {focus.cs[j]:.1f}")
            follow.set_visible(True)
        return []

    anim = FuncAnimation(fig, update, frames=len(plan), interval=1000 / fps,
                         blit=False, repeat=False)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    total = len(plan)
    log(T(f"  GIF を書き出し中…（{total}フレーム）", f"  Writing the GIF... ({total} frames)"))
    anim.save(str(out_path), writer=PillowWriter(fps=fps), dpi=dpi,
              progress_callback=lambda i, n: (log(f"    {i + 1}/{n}") if (i + 1) % 50 == 0
                                              else None))
    log(T(f"  保存: {out_path}", f"  saved: {out_path}"))
    return out_path


def plt_line(color, linestyle, label):
    """Line handle for the legend (created without using pyplot)."""
    from matplotlib.lines import Line2D

    return Line2D([0], [0], color=color, linestyle=linestyle, linewidth=1.8, label=label)


# ---------------------------------------------------------------------------
# 11. Plotly interactive HTML
# ---------------------------------------------------------------------------
def build_plotly_html(tables, names, focus_code, out_path, include_plotlyjs="cdn",
                      log=print, view_limits=None):
    """Write interactive HTML in which values can be inspected by zooming, panning and hovering.

    Only the annual observed values are used as frames (hover values come from primary data, not
    from interpolation), and movement between frames is connected smoothly by Plotly's
    transition animation.
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        log(T("  [警告] plotly が未導入のため HTML 出力をスキップします（pip install plotly）。",
              "  [warning] plotly is not installed, so the HTML output is skipped (pip install plotly)."))
        return None

    codes = list(tables)
    first_year = int(tables[focus_code]["fiscal_year"].min())
    years = sorted({int(y) for t in tables.values() for y in t["fiscal_year"]
                    if int(y) >= first_year})
    if view_limits is None:
        xlim, ylim = axis_limits(tables, min_year=first_year)
        log(T(f"  [軸] 動的スケーリング: SGR {xlim[0]:.1f} 〜 {xlim[1]:.1f} / "
              f"CS {ylim[0]:.1f} 〜 {ylim[1]:.1f}",
              f"  [axes] dynamic scaling: SGR {xlim[0]:.1f} to {xlim[1]:.1f} / "
              f"CS {ylim[0]:.1f} to {ylim[1]:.1f}"))
    else:  # zoomed drawing: use the axis ranges specified by the caller (zoom_limits)
        xlim, ylim = view_limits
    clean = {c: t.dropna(subset=["roe_pct", "doe_pct"]).sort_values("fiscal_year")
             for c, t in tables.items()}
    max_lbs = max(float(np.nanmax(np.maximum(t["lbs_pct"], 1.0))) for t in clean.values()
                  if not t.empty)
    sizeref = 2.0 * max_lbs / (58.0 ** 2)  # make the largest bubble about 58 px in diameter
    label_positions = ["top center", "bottom center", "middle right", "middle left"]

    def row_at(code, year):
        """The row for that year. Keeps the last value after the latest year; None before the start."""
        tbl = clean[code]
        if tbl.empty or year < tbl["fiscal_year"].min():
            return None
        sub = tbl[tbl["fiscal_year"] <= year]
        return sub.iloc[-1]

    def hover(code, row):
        lane = lane_key(str(row["lane"]))
        osm = (T("算出不能", "n/a") if not np.isfinite(row["osm"])
               else T(f"{row['osm']:.2f}倍", f"{row['osm']:.2f}x"))
        payout = (T("定義不能", "undefined") if not np.isfinite(row["payout_pct"])
                  else f"{row['payout_pct']:.1f}%")
        standard = standard_label(row.get('accounting_standard', ''))
        return (f"<b>{code} {names.get(code, '')}</b><br>"
                + T(f"{int(row['fiscal_year'])}年度（{standard}）<br>",
                    f"FY{int(row['fiscal_year'])} ({standard})<br>")
                + f"ROE {row['roe_pct']:.2f}% / DOE {row['doe_pct']:.2f}%<br>"
                + T(f"＋LBS {row['lbs_pct']:.2f}% / －SGR {row['sgr_pct']:.2f}%<br>"
                    f"×CS {row['cs']:.1f} / ÷OSM {osm}<br>配当性向 {payout}<br>"
                    f"最寄りレーン：{LANE_SHORT_LABEL[lane]}",
                    f"+LBS {row['lbs_pct']:.2f}% / -SGR {row['sgr_pct']:.2f}%<br>"
                    f"×CS {row['cs']:.1f} / ÷OSM {osm}<br>Payout ratio {payout}<br>"
                    f"Nearest lane: {lane_hover_label(lane)}"))

    def company_payload(code, year, show_label, order):
        row = row_at(code, year)
        is_focus = code == focus_code
        if row is None:
            return dict(x=[None], y=[None], text=[""], hovertext=[""],
                        marker=dict(size=[0], color=["rgba(0,0,0,0)"]))
        lane = lane_key(str(row["lane"]))
        label = f"{code} {names.get(code, '')}".strip()
        return dict(
            x=[float(row["sgr_pct"])], y=[float(row["cs"])],
            text=[label if (is_focus or show_label) else ""],
            hovertext=[hover(code, row)],
            marker=dict(size=[max(float(row["lbs_pct"]), 1.0)],
                        color=[lane_color(lane)], sizemode="area", sizeref=sizeref,
                        opacity=0.92 if is_focus else 0.45,
                        line=dict(width=2.5 if is_focus else 1, color="#2c3e50" if is_focus
                                  else "white")),
            textposition=label_positions[order % len(label_positions)])

    def trail_payload(year):
        tbl = clean[focus_code]
        sub = tbl[tbl["fiscal_year"] <= year]
        return dict(
            x=sub["sgr_pct"].tolist(), y=sub["cs"].tolist(),
            text=[f"'{int(y) % 100:02d}" for y in sub["fiscal_year"]],
            hovertext=[hover(focus_code, r) for _, r in sub.iterrows()],
            marker=dict(size=9, color=[lane_color(lane_key(str(v))) for v in sub["lane"]],
                        line=dict(width=1, color="white")))

    # Background: the five reference orbits (four parabolas plus the X axis). Fixed in all frames.
    traces = []
    for key, color, label, ls, x, y in lane_curves(xlim[1]):
        dash = {"-": "solid", "--": "dash", ":": "dot", "-.": "dashdot"}[ls]
        traces.append(go.Scatter(x=x, y=y, mode="lines", name=label, hoverinfo="skip",
                                 line=dict(color=color, width=1.6, dash=dash)))
    n_lane = len(traces)

    def show_label_flag(year):
        return year in (years[0], years[-1])

    first = years[0]
    for order, code in enumerate(codes):
        p = company_payload(code, first, show_label_flag(first), order)
        traces.append(go.Scatter(
            x=p["x"], y=p["y"], mode="markers+text", text=p["text"], hovertext=p["hovertext"],
            hoverinfo="text", marker=p["marker"], textposition=p.get(
                "textposition", "top center"),
            textfont=dict(size=11, color="#2c3e50"), showlegend=False, name=code))
    tp = trail_payload(first)
    traces.append(go.Scatter(
        x=tp["x"], y=tp["y"], mode="lines+markers+text", text=tp["text"],
        hovertext=tp["hovertext"], hoverinfo="text", marker=tp["marker"],
        line=dict(color="rgba(44,62,80,0.75)", width=4), textposition="bottom right",
        textfont=dict(size=9, color="#2c3e50"), showlegend=True,
        name=T(f"{company_label(focus_code, names)} 軌跡",
               f"{company_label(focus_code, names)} trajectory")))
    company_idx = list(range(n_lane, n_lane + len(codes)))
    trail_idx = n_lane + len(codes)

    frames = []
    for year in years:
        data = []
        for order, code in enumerate(codes):
            p = company_payload(code, year, show_label_flag(year), order)
            data.append(go.Scatter(x=p["x"], y=p["y"], text=p["text"],
                                   hovertext=p["hovertext"], marker=p["marker"]))
        tp = trail_payload(year)
        data.append(go.Scatter(x=tp["x"], y=tp["y"], text=tp["text"],
                               hovertext=tp["hovertext"], marker=tp["marker"]))
        frames.append(go.Frame(
            data=data, traces=company_idx + [trail_idx], name=str(year),
            # The axis range, decided from the data of all years, is shared by all frames (the axes do not move during playback)
            layout=dict(xaxis=dict(range=list(xlim)), yaxis=dict(range=list(ylim)))))

    slider_steps = [
        dict(method="animate", label=T(f"{y}年度", f"FY{y}"),
             args=[[str(y)], dict(mode="immediate", frame=dict(duration=0, redraw=False),
                                  transition=dict(duration=500, easing="cubic-in-out"))])
        for y in years
    ]
    fig = go.Figure(data=traces, frames=frames)
    fig.update_layout(
        template="plotly_white", height=780,
        title=dict(text=T(f"{company_label(focus_code, names)} - モート推移"
                          f"　「四則演算数理モデル」",
                          f"{company_label(focus_code, names)} - Moat trajectory: "
                          f"four-operations model"), x=0.02),
        font=dict(family="Hiragino Sans, Yu Gothic, Meiryo, Noto Sans JP, sans-serif",
                  size=12, color="#2c3e50"),
        xaxis=dict(title=T("SGR (%)　［引き算：ROE − DOE］", "SGR (%)  [ROE - DOE]"),
                   range=list(xlim),
                   zeroline=True, gridcolor="#e5e8ec"),
        yaxis=dict(title=T("CS (%²)　［掛け算：DOE × ROE］", "CS (%²)  [DOE × ROE]"),
                   range=list(ylim),
                   zeroline=True, gridcolor="#e5e8ec"),
        legend=dict(title=T("配当レーン（バブル色＝最寄りレーン）",
                            "Dividend lanes (bubble color = nearest lane)"), x=0.01, y=0.99,
                    bgcolor="rgba(255,255,255,0.85)", bordercolor="#c9ced4", borderwidth=1),
        updatemenus=[dict(
            type="buttons", direction="left", x=0.02, y=-0.12, xanchor="left",
            buttons=[
                dict(label=T("▶ 再生", "▶ Play"), method="animate",
                     args=[None, dict(fromcurrent=True, mode="immediate",
                                      frame=dict(duration=900, redraw=False),
                                      transition=dict(duration=700, easing="cubic-in-out"))]),
                dict(label=T("■ 停止", "■ Stop"), method="animate",
                     args=[[None], dict(mode="immediate", frame=dict(duration=0, redraw=False),
                                        transition=dict(duration=0))]),
            ])],
        sliders=[dict(active=0, steps=slider_steps, x=0.15, len=0.83, y=-0.08,
                      currentvalue=dict(prefix="", font=dict(size=14)))],
        annotations=[dict(
            text=T("バブル面積＝LBS（ROE＋DOE）／出典：EDINET 有価証券報告書「主要な経営指標等の推移」"
                   "（期中平均自己資本ベース）／ホバーで数値、ドラッグで拡大、ダブルクリックで全体表示",
                   "Bubble area = LBS (ROE+DOE) / Source: EDINET annual securities reports, "
                   "Summary of Business Results (average equity basis) / Hover for values, drag "
                   "to zoom, double-click to reset"),
            x=1.0, y=-0.2, xref="paper", yref="paper", xanchor="right", showarrow=False,
            font=dict(size=10, color="#5d6d7e"))],
        margin=dict(l=70, r=30, t=70, b=140),
    )
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(out_path), include_plotlyjs=include_plotlyjs, auto_play=False,
                   config={"scrollZoom": True, "displaylogo": False})
    log(T(f"  保存: {out_path}", f"  saved: {out_path}"))
    return out_path


# ---------------------------------------------------------------------------
# 12. Orchestration
# ---------------------------------------------------------------------------
def _display_in_notebook(gif_path):
    """Display the GIF in a cell only when running in Jupyter / Colab."""
    try:
        from IPython import get_ipython
        from IPython.display import Image, display

        if get_ipython() is None:
            return
        display(Image(filename=str(gif_path)))
    except Exception:
        pass


def run(codes=None, focus_code=None, force_update=False, outdir="output",
        datadir="data", api_key=None, fye_month=None, make_gif=True, make_html=True, steps=8,
        hold_frames=20, fps=20, dpi=100, include_plotlyjs="cdn", log=print,
        full_dividend_coverage=True, zoom=False, zoom_span=15.0, lang=None):
    """Run everything: fetch data (or read the cache) -> four operations -> GIF / HTML output.

    Parameters
    ----------
    codes : list[str] | None
        Securities codes to draw. None means the 16 companies of Figure 1.
    focus_code : str | None
        The company whose label and thick trajectory follow it. Added automatically if it is
        not in codes. None means the first of codes; if codes is also omitted, DEFAULT_FOCUS_CODE (7011).
    force_update : bool
        If True, ignore the cache (moat_data_{securities code}.csv) and fetch again.
    outdir : str | Path
        Output folder for GIF / HTML (default "output"; created automatically if missing).
    datadir : str | Path
        Folder where the CSV cache is saved and read (default "data"; created automatically if missing).
    fye_month : int | None
        Fiscal-year-end month (speeds up the search when specifying an unknown company on its own).
    full_dividend_coverage : bool
        If True, also fetch the additional reports that fill years lacking total dividends (default).
        If False, only the baseline annual reports (minimum API calls, but fewer years with a total).
    zoom : bool
        If True, draw a window of +/-zoom_span centered on the focus company's latest-year
        coordinates and add ``_zoom`` to the output file names (the full-view outputs are not overwritten).
    zoom_span : float
        Half-width of the zoom window (the same value for the SGR and CS axes).
    lang : str | None
        Output language, "en" or "ja". None resolves it from the environment variable MOAT_LANG,
        then falls back to "en". Japanese output keeps the original file names
        (moat_animation_{code}.gif / .html); English output adds an ``_en`` suffix.
        The CSV cache is shared by both languages.
    """
    set_lang(lang)
    outdir = Path(outdir)
    datadir = Path(datadir)
    outdir.mkdir(parents=True, exist_ok=True)
    datadir.mkdir(parents=True, exist_ok=True)
    focus_code = normalize_code(focus_code or (codes[0] if codes else DEFAULT_FOCUS_CODE))
    codes = [normalize_code(c) for c in (codes or TARGET_STOCK_CODES)]
    if focus_code not in codes:
        codes.append(focus_code)

    client_holder = {}

    def get_client():
        if "client" not in client_holder:
            client_holder["client"] = EdinetClient(resolve_api_key(api_key))
        return client_holder["client"]

    tables, names = {}, stock_names()
    for code in codes:
        try:
            table = load_or_fetch(code, datadir, force_update, get_client,
                                  fye_month=fye_month if code == focus_code else None,
                                  log=log,
                                  full_dividend_coverage=full_dividend_coverage)
        except PermissionError as exc:
            raise SystemExit(T(f"[中断] {exc}", f"[aborted] {exc}"))
        except (LookupError, ConnectionError, RuntimeError) as exc:
            if code == focus_code:
                raise SystemExit(T(f"[中断] フォーカス銘柄 {code} を取得できません: {exc}",
                                   f"[aborted] Cannot fetch the focus company {code}: {exc}"))
            log(T(f"[{code}] 取得失敗のため除外します: {exc}",
                  f"[{code}] Excluded because fetching failed: {exc}"))
            continue
        table = trim_to_primary_statements(table, code, log=log)
        if table.dropna(subset=["roe_pct", "doe_pct"]).empty:
            log(T(f"[{code}] ROE/DOE を算出できるデータが無いため除外します。",
                  f"[{code}] Excluded because no data allow ROE/DOE to be computed."))
            continue
        tables[code] = table
        # The EDINET filer name is Japanese, so it is used only for the Japanese output;
        # English output shows the code alone for companies outside the 16 selected ones.
        if is_ja() and code not in names and "name" in table.columns and len(table):
            names[code] = str(table["name"].iloc[0])

    if focus_code not in tables:
        raise SystemExit(T(f"[中断] フォーカス銘柄 {focus_code} の有効なデータがありません。",
                           f"[aborted] The focus company {focus_code} has no valid data."))

    view_limits, suffix = None, "" if is_ja() else "_en"  # English outputs carry "_en"
    if zoom:
        view_limits = zoom_limits(tables, focus_code, zoom_span, log=log)
        if view_limits is not None:
            suffix += "_zoom"

    gif_path = html_path = None
    if make_gif:
        log(T("[描画] Matplotlib GIF", "[render] Matplotlib GIF"))
        gif_path = render_gif(tables, names, focus_code,
                              outdir / f"moat_animation_{focus_code}{suffix}.gif",
                              steps=steps, hold_frames=hold_frames, fps=fps, dpi=dpi, log=log,
                              view_limits=view_limits)
        _display_in_notebook(gif_path)
    if make_html:
        log(T("[描画] Plotly インタラクティブHTML", "[render] Plotly interactive HTML"))
        html_path = build_plotly_html(tables, names, focus_code,
                                      outdir / f"moat_animation_{focus_code}{suffix}.html",
                                      include_plotlyjs=include_plotlyjs, log=log,
                                      view_limits=view_limits)
    return tables, gif_path, html_path


def main(argv=None):
    # Pre-parse only --lang so that --help can be shown in the requested language.
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--lang", default=None)
    pre_args, _ = pre.parse_known_args(argv)
    set_lang(pre_args.lang, warn=lambda message: None)

    parser = argparse.ArgumentParser(
        description=T("モート動的可視化（EDINET → 四則演算 → GIF / HTML）",
                      "Dynamic moat visualization (EDINET -> four operations -> GIF / HTML)"))
    parser.add_argument("--lang", choices=SUPPORTED_LANGS, default=None,
                        help=T(f"出力言語。既定は環境変数 {LANG_ENV_VAR}、未設定なら {DEFAULT_LANG}。"
                               "en の出力ファイル名には _en が付く（ja は従来のファイル名）",
                               f"Output language. Default: environment variable {LANG_ENV_VAR}, "
                               f"otherwise {DEFAULT_LANG}. English output files get an _en "
                               "suffix (ja keeps the original file names)"))
    parser.add_argument("--codes", default=None,
                        help=T("カンマ区切りの証券コード（省略時は図1の16銘柄）。--focus 省略時は"
                               "先頭銘柄がアニメーションのフォーカス（出力ファイル名・タイトル）になる",
                               "Comma-separated securities codes (default: the 16 companies of "
                               "Figure 1). If --focus is omitted, the first code becomes the "
                               "animation's focus (output file name and title)"))
    # The default is None so that whether it was given explicitly can drive the --zoom check
    # (the effective default is DEFAULT_FOCUS_CODE)
    parser.add_argument("--focus", default=None,
                        help=T(f"フォーカス銘柄の証券コード（既定：--codes の先頭、"
                               f"両方省略時は {DEFAULT_FOCUS_CODE}）",
                               f"Securities code of the focus company (default: the first of "
                               f"--codes; {DEFAULT_FOCUS_CODE} if both are omitted)"))
    parser.add_argument("--force-update", action="store_true",
                        help=T("CSVキャッシュを無視して EDINET から再取得する",
                               "Ignore the CSV cache and fetch again from EDINET"))
    parser.add_argument("--datadir", default="data",
                        help=T("CSVキャッシュの保存・参照先フォルダ（既定：data。無ければ自動作成）",
                               "Folder for saving and reading the CSV cache (default: data; "
                               "created if missing)"))
    parser.add_argument("--outdir", default="output",
                        help=T("GIF / HTML の出力先フォルダ（既定：output。無ければ自動作成）",
                               "Output folder for GIF / HTML (default: output; created if missing)"))
    parser.add_argument("--api-key", default=None,
                        help=T("EDINET APIキー", "EDINET API key"))
    parser.add_argument("--fye-month", type=int, default=None,
                        help=T("フォーカス銘柄の決算期末月",
                               "Fiscal-year-end month of the focus company"))
    parser.add_argument("--minimal-reports", action="store_true",
                        help=T("基本の有報（直近・5年前・取得できれば10年前）のみ取得する"
                               "（配当金総額が取れる年度は減る）",
                               "Fetch only the baseline annual reports (latest, 5 years back, and "
                               "10 years back if available); fewer years will have total dividends"))
    parser.add_argument("--no-gif", action="store_true",
                        help=T("GIF出力を行わない", "Do not write the GIF"))
    parser.add_argument("--no-html", action="store_true",
                        help=T("HTML出力を行わない", "Do not write the HTML"))
    parser.add_argument("--steps", type=int, default=8,
                        help=T("1年あたりの補間フレーム数", "Interpolated frames per year"))
    parser.add_argument("--fps", type=int, default=20,
                        help=T("GIFのフレームレート", "GIF frame rate"))
    parser.add_argument("--dpi", type=int, default=100,
                        help=T("GIFの解像度（dpi）", "GIF resolution (dpi)"))
    parser.add_argument("--zoom", action="store_true",
                        help=T("--focus 銘柄の最新年度座標を中心にズーム描画する"
                               "（出力ファイル名に _zoom を付与）",
                               "Zoom in around the latest-year coordinates of the --focus company "
                               "(adds _zoom to the output file names)"))
    parser.add_argument("--zoom-span", type=float, default=15.0,
                        help=T("ズーム窓の半幅（既定 15.0）。中心 ±span を SGR・CS 軸に適用",
                               "Half-width of the zoom window (default 15.0). Applies center "
                               "+/-span to both the SGR and CS axes"))
    # Use parse_known_args so that Jupyter / Colab kernel arguments (-f ...) are ignored
    args, _ = parser.parse_known_args(argv)
    codes = [c for c in args.codes.split(",") if c.strip()] if args.codes else None
    # Focus company: decided in the order --focus > first of --codes > default (7011)
    focus = args.focus or (codes[0] if codes else None)
    zoom = args.zoom
    if zoom and focus is None:
        print(T("[警告] --zoom には --focus <CODE>（または --codes）の指定が必要です。"
                "全体描画で実行します。",
                "[warning] --zoom requires --focus <CODE> (or --codes). "
                "Drawing the full view."))
        zoom = False
    run(codes=codes, focus_code=focus, force_update=args.force_update,
        outdir=args.outdir, datadir=args.datadir, api_key=args.api_key, fye_month=args.fye_month,
        make_gif=not args.no_gif, make_html=not args.no_html, steps=args.steps,
        fps=args.fps, dpi=args.dpi, full_dividend_coverage=not args.minimal_reports,
        zoom=zoom, zoom_span=args.zoom_span, lang=args.lang)


if __name__ == "__main__":
    main(sys.argv[1:])
