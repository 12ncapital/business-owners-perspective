#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
appendix_moat_tracker.py
=====================================================================
「ビジネスオーナーの視座」
巻末付録：モート動的可視化スクリプト（四則演算数理モデルの軌跡トラッカー）
=====================================================================

Copyright (c) 2026 Hayato Ichijo
Released under the MIT License.
https://opensource.org/licenses/MIT

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
# 0. ユーザー設定
# ---------------------------------------------------------------------------
# EDINET API キー（無料）。取得手順はファイル冒頭の docstring を参照。
EDINET_API_KEY = "YOUR_EDINET_API_KEY"

# フォーカス銘柄（ラベルと太い軌跡を追従表示する銘柄）のデフォルト
DEFAULT_FOCUS_CODE = "7011"

# 精鋭16銘柄（第3章 図1と同一）：証券コード -> 表示名
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
TARGET_STOCK_CODES = list(STOCK_NAMES)

# 精鋭16銘柄の決算期末月（これ以外の銘柄は EDINET コードリストから自動取得する）
FISCAL_END_MONTH = {
    "8035": 3, "6857": 3, "6920": 6, "6146": 3, "2802": 3, "7011": 3,
    "7012": 3, "7013": 3, "6501": 3, "7735": 3, "285A": 3, "4776": 12,
    "4063": 3, "4768": 12, "6861": 3, "6503": 3,
}

# 取得する報告書：直近(0)と5年前(5)が基本（重複を除いて約8〜10期分）。各報告書が過去5期を持つ。
# 10年前(10)相当は、取得できた場合のみ取り込む（最大で10年超〜14年程度）。
# 見つからなければ繰り上げて再探索し、それでも無ければ警告のうえ省略する。
REPORT_OFFSETS = (0, 5, 10)
# 10年前相当が見つからない場合に、何年まで繰り上げて再探索するか
OFFSET_FALLBACK_YEARS = 3

# EDINET API v2
EDINET_API_BASE = "https://api.edinet-fsa.go.jp/api/v2"
EDINET_CODELIST_URL = (
    "https://disclosure2dl.edinet-fsa.go.jp/searchdocument/codelist/Edinetcode.zip"
)
REQUEST_INTERVAL_SEC = 0.25  # サーバー負荷への配慮（連続アクセスの間隔）
REQUEST_TIMEOUT_SEC = 90
MAX_RETRY = 3
# 期末から提出日の中心までの日数（有報提出期限＝期末+3か月に対し、ピークは約85日後）
FILING_CENTER_DAYS = 85
FILING_RADIUS_LATEST = 50   # 直近報告書の探索半径（日）
FILING_RADIUS_PAST = 45     # 過去報告書の探索半径（日）

# ---------------------------------------------------------------------------
# 1. 配当レーン定義（make_fig01_portfolio_matrix.py と同一）
# ---------------------------------------------------------------------------
# 配当レーン: d(%) -> (色, 凡例ラベル, 線種)
LANES = {
    50: ("#e8685a", "高還元ロケットレーン (d = 50% → k = 2.000)", "-."),
    35: ("#a66fc7", "積極還元レーン (d = 35% → k ≈ 0.828)", "--"),
    30: ("#3fbf7f", "標準優良レーン (d = 30% → k ≈ 0.612)", ":"),
    0: ("#8a9199", "地表レーン (d = 0% → k = 0.000)", "-"),
}
OUTER_COLOR = "#3b82d6"  # 4大レーンの外側（低配当性向。例：アドバンテスト）
OUTER_PAYOUT = 0.1145    # 外側軌道の基準配当性向（第3章：d = 11.45%、k ≈ 0.146）

LANE_SHORT_LABEL = {
    50: "高還元ロケット (d≈50%)",
    35: "積極還元 (d≈35%)",
    30: "標準優良 (d≈30%)",
    0: "地表 (d=0%)",
    "outer": "外側の低角度軌道 (d<20%)",
}

# 団子ゾーン（SGR 7〜14%、CS 35〜110）
DANGO_ZONE = dict(x=7.0, y=35.0, w=7.0, h=75.0)

JP_FONT_CANDIDATES = [
    "Hiragino Sans", "Hiragino Kaku Gothic ProN", "Yu Gothic", "Meiryo",
    "Noto Sans CJK JP", "Noto Sans JP", "IPAexGothic", "IPAGothic",
    "TakaoGothic", "VL Gothic", "MS Gothic", "Arial Unicode MS",
]


# ---------------------------------------------------------------------------
# 2. 四則演算数理モデル（第3章の定義をそのまま関数化）
# ---------------------------------------------------------------------------
def calc_lbs(roe, doe):
    """＋【LBS（総合推進力）】= ROE + DOE。バブル面積に対応する。"""
    return np.asarray(roe, dtype=float) + np.asarray(doe, dtype=float)


def calc_sgr(roe, doe):
    """－【SGR（サステナブル内部成長力）】= ROE - DOE。横軸 X に対応する。"""
    return np.asarray(roe, dtype=float) - np.asarray(doe, dtype=float)


def calc_cs(roe, doe):
    """×【CS（複利増幅インデックス）】= DOE x ROE（％表記のまま乗じる。単位 %^2）。

    縦軸 Y に対応する。CS = 配当性向 x ROE^2 と展開できる。
    """
    return np.asarray(roe, dtype=float) * np.asarray(doe, dtype=float)


def calc_osm(roe, doe):
    """÷【OSM（防衛安全倍率）】= ROE / DOE。DOE = 0 は算出不能（NaN）。"""
    roe = np.asarray(roe, dtype=float)
    doe = np.asarray(doe, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(doe != 0, roe / doe, np.nan)


def calc_payout_pct(roe, doe):
    """配当性向 d (%) = DOE / ROE x 100。

    DOE = 0 は d = 0（地表レーン）。ROE <= 0 かつ DOE > 0 は定義不能（NaN）。
    """
    roe = np.asarray(roe, dtype=float)
    doe = np.asarray(doe, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        d = np.where(roe > 0, doe / roe * 100.0, np.nan)
    return np.where(doe == 0, 0.0, d)


def k_of(d):
    """配当レーン（放物線 Y = k X^2）の係数 k(d) = d / (1 - d)^2。d は小数（0〜1未満）。"""
    return d / (1 - d) ** 2


def lane_of(d_pct):
    """最も近い4大レーンを返す最近傍ロジック（図1スクリプトと同一）。

    0 < d < 20% は外側軌道（"outer"）として扱う。
    追記：配当性向が定義不能（NaN：赤字等）の点も、外側軌道として扱う。
    """
    if d_pct is None or not np.isfinite(d_pct):
        return "outer"
    if abs(d_pct) < 1e-9:
        return 0
    if d_pct < 20:
        return "outer"
    return min((30, 35, 50), key=lambda x: abs(x - d_pct))


def lane_color(lane):
    """レーンキー -> 描画色。"""
    return OUTER_COLOR if lane == "outer" else LANES[lane][0]


def compute_average_equity(df):
    """期中平均自己資本（百万円）を返す。年度昇順の表を前提とする。

    avg = (当期末 + 前期末) / 2。前期末（＝当期の期首）が無い最古年度、年度が連続しない行、
    前期末が正値でない行は、当期末の自己資本で代用する。
    """
    eq = df["equity_mn"].astype(float)
    prev = eq.shift(1)
    contiguous = df["fiscal_year"].astype(float).diff() == 1
    prev = prev.where(contiguous & (prev > 0))
    return ((eq + prev) / 2.0).fillna(eq)


def compute_moat_table(df):
    """ROE / DOE（％）の列を持つ表に、四則演算指標・レーン判定を追加して返す。

    ROE / DOE の分母は期中平均自己資本とする。取得時の算出（derive_roe_doe）は期末自己資本
    ベースなので、その値を roe_end_pct / doe_end_pct として保持し、分母の比 (期末 / 平均) を
    掛けて roe_pct / doe_pct を求める（純利益・配当金総額の分子は共通のため、
    NI / 平均自己資本、総額 / 平均自己資本と等価）。CSV を読み直して再実行しても冪等である。
    """
    out = df.sort_values("fiscal_year").reset_index(drop=True)
    if "roe_end_pct" not in out.columns:  # 新規取得・旧キャッシュ：roe_pct / doe_pct は期末ベース
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
    """CSV 経由で文字列化された lane（"30" / "outer"）をキーへ戻す。"""
    return label if label == "outer" else int(float(label))


# ---------------------------------------------------------------------------
# 3. EDINET API v2 クライアント
# ---------------------------------------------------------------------------
def resolve_api_key(cli_key=None):
    """APIキーを 引数 > 環境変数 > Colabシークレット > 定数 の順で解決する。"""
    candidates = [cli_key, os.environ.get("EDINET_API_KEY")]
    try:  # Google Colab のシークレット機能
        from google.colab import userdata  # type: ignore

        candidates.append(userdata.get("EDINET_API_KEY"))
    except Exception:
        pass
    candidates.append(EDINET_API_KEY)
    for key in candidates:
        if key and key.strip() and key.strip() != "YOUR_EDINET_API_KEY":
            return key.strip()
    raise RuntimeError(
        "EDINET API キーが未設定です。ファイル冒頭の手順に従ってキーを取得し、"
        "EDINET_API_KEY に設定するか、環境変数 / --api-key で指定してください。"
    )


class EdinetClient:
    """EDINET API v2 の最小クライアント（書類一覧・XBRL取得）。"""

    def __init__(self, api_key, interval=REQUEST_INTERVAL_SEC):
        self.api_key = api_key
        self.interval = interval
        self.session = requests.Session()
        self._day_cache = {}
        self._last_request = 0.0

    def _get(self, url, params=None):
        """リトライ・間隔制御付きの GET。認証エラーは即座に例外とする。"""
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
            except requests.RequestException as exc:  # 通信断などは指数バックオフ
                last_error = exc
                time.sleep(2 ** attempt)
                continue
            if resp.status_code in (401, 403):
                raise PermissionError(
                    f"EDINET API 認証エラー（HTTP {resp.status_code}）。"
                    "APIキーが正しいか、有効期限内かを確認してください。"
                )
            if resp.status_code >= 500 or resp.status_code == 429:
                last_error = RuntimeError(f"HTTP {resp.status_code}")
                time.sleep(2 ** attempt)
                continue
            return resp
        raise ConnectionError(f"EDINET API への接続に失敗しました: {last_error}")

    def list_documents(self, day):
        """指定提出日の書類一覧（メタデータ）を返す。同一実行内ではキャッシュする。"""
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
            raise PermissionError("EDINET API 認証エラー。APIキーを確認してください。")
        if resp.status_code == 200 and status == "200":
            results = body.get("results", []) or []
        # 404（範囲外の日付）などは「該当なし」として扱う
        self._day_cache[day] = results
        return results

    def download_xbrl_zip(self, doc_id):
        """書類管理番号から XBRL 一式の ZIP（type=1）を取得する。"""
        resp = self._get(f"{EDINET_API_BASE}/documents/{doc_id}", {"type": 1})
        if resp.status_code != 200 or not zipfile.is_zipfile(io.BytesIO(resp.content)):
            raise RuntimeError(f"XBRL の取得に失敗しました: docID={doc_id}")
        return resp.content


_CODELIST_CACHE = {}


def lookup_edinet_codelist(code5):
    """EDINET コードリストから (決算期末月, 提出者名) を引く。失敗時は (None, None)。"""
    try:
        if "df" not in _CODELIST_CACHE:
            resp = requests.get(EDINET_CODELIST_URL, timeout=REQUEST_TIMEOUT_SEC)
            resp.raise_for_status()
            with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
                csv_name = next(n for n in zf.namelist() if n.lower().endswith(".csv"))
                raw = zf.read(csv_name)
            # 1行目はダウンロード日等のメタ情報、2行目が見出し
            _CODELIST_CACHE["df"] = pd.read_csv(
                io.BytesIO(raw), encoding="cp932", skiprows=1, dtype=str
            )
        df = _CODELIST_CACHE["df"]
        hit = df[df["証券コード"] == code5]
        if hit.empty:
            return None, None
        row = hit.iloc[0]
        m = re.search(r"(\d+)月", str(row.get("決算日", "")))
        return (int(m.group(1)) if m else None), row.get("提出者名")
    except Exception as exc:  # ネットワーク・書式変更など：自動探索へフォールバック
        print(f"  [情報] EDINETコードリストを参照できませんでした（{exc}）")
        return None, None


# ---------------------------------------------------------------------------
# 4. 報告書の探索（提出日の窓を走査）
# ---------------------------------------------------------------------------
def month_end(year, month):
    """year年month月の末日。"""
    nxt = date(year + (month == 12), month % 12 + 1, 1)
    return nxt - timedelta(days=1)


def fiscal_year_of(period_end):
    """決算期末日 -> 年度（期首の属する暦年）。

    2026年3月期 -> 2025年度、2025年12月期 -> 2025年度。3月期と12月期の企業を
    同一の時間軸（年度）へ揃え、先頭フレームで全銘柄が同時に登場できるようにする。
    """
    return period_end.year if period_end.month == 12 else period_end.year - 1


def shift_years(d, years):
    """日付を years 年ずらす（2月29日は28日へ丸める）。"""
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        return d.replace(year=d.year + years, day=28)


def latest_fiscal_year_candidates(fye_month, today, lag_days=40):
    """直近の有報が提出済みと見込まれる決算年（期末の暦年）の候補を新しい順に返す。"""
    out = []
    for year in (today.year, today.year - 1, today.year - 2):
        if month_end(year, fye_month) + timedelta(days=lag_days) <= today:
            out.append(year)
    return out[:2]


def find_annual_report(client, code5, end_year, fye_month, center, radius, today):
    """center を中心に外側へ向けて提出日を走査し、該当の有価証券報告書を探す。

    docTypeCode 120 = 有価証券報告書（訂正報告書 130 は除外）。
    見つかった時点で打ち切るため、提出日が中心に近いほど API 呼び出しは少ない。
    """
    nominal_end = month_end(end_year, fye_month)
    for offset in sorted(range(-radius, radius + 1), key=lambda d: (abs(d), d)):
        day = center + timedelta(days=offset)
        if day > today or day.weekday() >= 5:  # 未来日と土日は書類が存在しない
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
# 5. XBRL「主要な経営指標等の推移」のパース
# ---------------------------------------------------------------------------
XSI_NIL = "{http://www.w3.org/2001/XMLSchema-instance}nil"
SUMMARY_SUFFIX = "SummaryOfBusinessResults"
# 連結の事実は修飾なしのコンテキスト、提出会社（単体）の事実は _NonConsolidatedMember が付く
CONTEXT_RE = re.compile(
    r"^(CurrentYear|Prior(\d+)Year)(Duration|Instant)(_NonConsolidatedMember)?$"
)
SCOPE_CONSOLIDATED = "consolidated"  # 「連結経営指標等」
SCOPE_SOLO = "solo"                  # 「提出会社の経営指標等」（単体要約表）
# デバッグ用に、インスタンス全体から収集する要素名のキーワード
DEBUG_NAME_KEYWORDS = ("Dividend", "Payout")
DEBUG_MAX_NAMES = 80
DEBUG_MAX_CONTEXTS = 4

# --- 配当金総額（株数に依存しない総額ベース）の抽出定義 --------------------------------
# 探索優先順位：(1) キャッシュ・フロー計算書の配当金支払額 (2) 株主資本等変動計算書の剰余金の配当
#               (3) 提出会社情報（配当政策等）の総額要素。連結 > 単体の順に探す。
# 要素名は taxonomy の版・会計基準で揺れるため、ローカル名の正規表現で照合する。
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
# 株主資本等変動計算書で、親会社株主の配当を表す列（上から優先）
EQUITY_COMPONENT_PRIORITY = (
    "ShareholdersEquityMember", "RetainedEarningsMember", "NetAssetsMember",
    "EquityAttributableToOwnersOfParentIFRSMember", "RetainedEarningsIFRSMember",
)
MAX_DIV_CANDIDATES = 3000
TOTAL_DIV_MAX_PAYOUT = 5.0   # 総額/純利益がこれを超える値は取得ミスとみなす（500%）
TOTAL_DIV_MAX_DOE = 0.5      # 総額/自己資本がこれを超える値は取得ミスとみなす（50%）
POLICY_TOLERANCE = (0.6, 1.6)  # 配当政策表由来の総額は、他の配当性向と概ね一致する場合のみ採用

# 要素名（ローカル名）の候補。上から順に最初に見つかったものを採用する。
# 名前空間（taxonomy の年版）は毎年変わるため、ローカル名のみで照合する。
_STD = r"(IFRS|USGAAP)?"
PATTERNS = {
    "net_income": [
        rf"^ProfitLossAttributableToOwnersOfParent{_STD}{SUMMARY_SUFFIX}$",
        rf"^NetIncomeLoss{_STD}{SUMMARY_SUFFIX}$",
        rf"^ProfitLoss{_STD}{SUMMARY_SUFFIX}$",
    ],
    "equity_direct": [  # 要約表の親会社帰属持分（IFRS 本則の直接タグ。最優先）
        rf"^EquityAttributableToOwnersOfParent{_STD}{SUMMARY_SUFFIX}$",
    ],
    "equity_bs": [  # 連結貸借対照表の本表の親会社帰属持分（要約表に無い場合の直接タグ）
        rf"^EquityAttributableToOwnersOfParent{_STD}$",
    ],
    "owners_equity": [  # 要約表の自己資本（OwnersEquity）。載っていれば金額そのものを直接採用する
        rf"^OwnersEquity{_STD}{SUMMARY_SUFFIX}$",
    ],
    # 自己資本比率。親会社所有者帰属持分比率（RatioOfOwnersEquityToGrossAssets）を優先する。
    # EquityToAssetRatio には比率でない値（1株当たり純資産と思われる 600〜1,100 等）が入る
    # 報告書があり、これを先に拾うと自己資本が桁違いに膨らむため、順位を分けて固定する。
    "equity_ratio": [
        rf"^RatioOfOwnersEquityToGrossAssets{_STD}{SUMMARY_SUFFIX}$",
        rf"^EquityToAssetRatio{_STD}{SUMMARY_SUFFIX}$",
    ],
    "total_assets": [rf"^TotalAssets{_STD}{SUMMARY_SUFFIX}$"],
    "total_equity": [  # 資本合計。非支配株主持分を含むため、親会社帰属持分より後順位で使う
        rf"^(TotalEquity|Equity){_STD}{SUMMARY_SUFFIX}$",
        rf"^(TotalEquity|Equity){_STD}$",
    ],
    "net_assets": [rf"^NetAssets{_STD}{SUMMARY_SUFFIX}$"],
    # --- 日本基準（J-GAAP）の連結貸借対照表の本表（要約表に自己資本の金額が無いため）---------
    "equity_bs_total": [  # 株主資本及び評価・換算差額等合計（あれば、非支配株主持分控除後の自己資本）
        r"^(Total)?ShareholdersEquityAndValuationAndTranslationAdjustments$",
    ],
    "shareholders_equity_bs": [r"^ShareholdersEquity$"],  # 株主資本合計
    "valuation_bs": [  # 評価・換算差額等合計（その他の包括利益累計額）
        r"^(ValuationAndTranslationAdjustments|AccumulatedOtherComprehensiveIncome)$",
    ],
    "net_assets_bs": [r"^(NetAssets|TotalNetAssets)$"],  # 純資産合計
    "nci_bs": [r"^(NonControllingInterests|MinorityInterests)(IFRS|USGAAP)?$"],  # 非支配株主持分
    "rights_bs": [r"^SubscriptionRightsToShares$"],  # 新株予約権
    "eps": [
        rf"^BasicEarningsLossPerShare{_STD}{SUMMARY_SUFFIX}$",
        rf"^(NetIncomeLossPerShare|EarningsLossPerShare){_STD}{SUMMARY_SUFFIX}$",
    ],
    "dps": [
        rf"^(DividendPaidPerShare|DividendsPerShare|CashDividendsPerShare"
        rf"|CashDividendsPaidPerShare|DividendsPaidPerShare){_STD}{SUMMARY_SUFFIX}$",
        # 最終手段：名称揺れを吸収する。中間配当・配当性向・予想値は除外する。
        rf"^(?!.*(Interim|Payout|Ratio|Forecast)).*Dividend.*PerShare.*{SUMMARY_SUFFIX}$",
    ],
    "payout": [
        rf"^(Consolidated)?(Dividend)?PayoutRatio{_STD}{SUMMARY_SUFFIX}$",
        # 名称揺れ（連結配当性向・提出会社の配当性向等）を吸収する。予想値は除外する。
        rf"^(?!.*Forecast).*Payout.*{SUMMARY_SUFFIX}$",
    ],
}
# 期間概念：損益・配当は Duration、貸借対照表項目は Instant
# 連結側に無い場合に、提出会社（単体）の要約表まで探索する項目
# （配当は「提出会社の経営指標等」にのみ掲載される有価証券報告書が多い）
SOLO_FALLBACK_KEYS = ("dps", "payout")
# 株式分割・併合による EPS / DPS の基準不一致への対策
PAYOUT_SANITY_MAX = 1.5            # 黒字期の配当性向がこれを超えたら異常値とみなす（150%）
SPLIT_FACTORS = (10, 5, 4, 3, 2)   # 補正に用いる分割倍率の候補
TYPICAL_PAYOUT = 0.35              # 候補が複数あるとき、最も近いものを選ぶ基準
PERIOD_KIND = {
    "net_income": "Duration", "eps": "Duration", "dps": "Duration", "payout": "Duration",
    "equity_direct": "Instant", "owners_equity": "Instant", "equity_bs": "Instant",
    "equity_bs_total": "Instant", "shareholders_equity_bs": "Instant", "valuation_bs": "Instant",
    "net_assets_bs": "Instant", "nci_bs": "Instant", "rights_bs": "Instant",
    "equity_ratio": "Instant", "total_assets": "Instant", "total_equity": "Instant",
    "net_assets": "Instant",
}
# 連結貸借対照表の本表の自己資本系キー。1つの報告書から「まとめて」採用する（resolve_bs_bundle）
BS_EQUITY_KEYS = ("equity_bs", "equity_bs_total", "shareholders_equity_bs", "valuation_bs",
                  "net_assets_bs", "nci_bs", "rights_bs")
# 連結貸借対照表の本表から拾う自己資本系の要素（要約表の接尾辞を持たないもの）。
# 要約表に自己資本の金額が載らない企業（IFRS・日本基準とも）で、金額を直接取得するための経路。
# ディメンション付きのコンテキスト（株主資本等変動計算書の列など）は CONTEXT_RE で除外される。
BS_EQUITY_LOCAL = re.compile(
    r"^(EquityAttributableToOwnersOfParent|TotalEquity|Equity)(IFRS|USGAAP)?$"
    r"|^(NetAssets|TotalNetAssets|ShareholdersEquity|ValuationAndTranslationAdjustments"
    r"|AccumulatedOtherComprehensiveIncome|SubscriptionRightsToShares"
    r"|(Total)?ShareholdersEquityAndValuationAndTranslationAdjustments)$"
    r"|^(NonControllingInterests|MinorityInterests)(IFRS|USGAAP)?$")

# --- 単独決算（非連結）・連結移行前の年度への年度単位フォールバック --------------------------
# 損益計算書本表の当期純利益。要約表（SummaryOfBusinessResults）に純利益が載らない単独決算企業向け。
# 連結が存在する年度では一切使わない（_pick_scoped の fallback 年度のみ参照する）。
NET_INCOME_PL_LOCAL = re.compile(
    r"^(ProfitLossAttributableToOwnersOfParent|NetIncomeLoss|ProfitLoss)(IFRS|USGAAP)?$")
NET_INCOME_PL_PATTERNS = [  # 優先順（連結の親会社株主帰属 > 当期純利益）
    r"^ProfitLossAttributableToOwnersOfParent(IFRS|USGAAP)?$",
    r"^NetIncomeLoss(IFRS|USGAAP)?$",
    r"^ProfitLoss(IFRS|USGAAP)?$",
]
# 「その年度に連結データが存在するか」の判定に使う項目（純利益・自己資本系・総資産）。
# いずれか1つでも連結スコープで取得できれば、その年度は連結年度として従来処理のみを行う。
CONSOLIDATED_PRESENCE_KEYS = (
    "net_income", "equity_direct", "owners_equity", "equity_bs", "equity_bs_total",
    "shareholders_equity_bs", "net_assets_bs", "total_equity", "net_assets", "total_assets",
)
SOLO_FALLBACK_NOTE = "scope=nonconsolidated_fallback"


def classify_dividend_element(local):
    """要素名から配当金総額の区分（cf / ss / policy）を判定する。該当しなければ None。"""
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
    """XBRL インスタンスを1回走査し、要約表の事実・配当金総額・診断情報を取り出す。

    戻り値：(facts, debug, total_dividends)
        facts = {(スコープ, 周期種別, n): {ローカル名: 値}}（n = 0 が当期、k が k期前）
                「主要な経営指標等の推移」の要素。連結は修飾なし、提出会社（単体）は
                *_NonConsolidatedMember のコンテキスト。
        debug = 取得失敗時のログ用情報（要約表の要素名、配当関連の要素名とコンテキスト）
        total_dividends = {n: (配当金総額[円・正値], 取得元ラベル)}（CF/SS等は直近2期分）
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
            if local == "context":  # コンテキスト定義（期間・ディメンション）を保持する
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
            # 配当関連の要素は、要約表以外も含めて名前とコンテキストだけ記録する（診断用）
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
                    if m and m.group(3) == "Instant":  # 期末時点・ディメンション無しの本表の値
                        n = 0 if m.group(1) == "CurrentYear" else int(m.group(2))
                        scope = SCOPE_SOLO if m.group(4) else SCOPE_CONSOLIDATED
                        facts.setdefault((scope, "Instant", n), {}).setdefault(local, value)
                        debug["equity_names"].add(local)
                elif NET_INCOME_PL_LOCAL.match(local):
                    m = CONTEXT_RE.match(context)
                    if m and m.group(3) == "Duration":  # 損益計算書本表の当期純利益（通期）
                        n = 0 if m.group(1) == "CurrentYear" else int(m.group(2))
                        scope = SCOPE_SOLO if m.group(4) else SCOPE_CONSOLIDATED
                        facts.setdefault((scope, "Duration", n), {}).setdefault(local, value)
                else:
                    category = classify_dividend_element(local)
                    if category and len(candidates) < MAX_DIV_CANDIDATES:
                        candidates.append(
                            (category, local, context, value, elem.get("unitRef") or ""))
        elem.clear()  # 数十MBに及ぶインスタンスでもメモリを抑える
    return facts, debug, resolve_total_dividends(candidates, contexts, report_end)


def _best_by_pattern(items, patterns):
    """候補（local, dims, ctx_id, value）から、要素名パターンの優先順に1件選ぶ。"""
    for rx in patterns:
        for item in sorted(items, key=lambda it: it[0]):
            if rx.match(item[0]):
                return item
    return sorted(items, key=lambda it: it[0])[0]


def resolve_total_dividends(candidates, contexts, report_end):
    """配当金総額の候補を、年度（n）ごとに優先順位に従って1つへ確定する。

    符号：CF の支払額・株主資本等変動計算書の減少は負値で記載されるため、絶対値へ変換する。
    単位：unitRef が円（JPY）のものだけを採用する（呼び出し側で百万円へ換算する）。
    戻り値：{n: (配当金総額[円・正値], "cf:consolidated" 等の取得元ラベル)}
    """
    buckets = {}
    for category, local, ctx_id, value, unit in candidates:
        if unit and "JPY" not in unit.upper():
            continue
        ctx = contexts.get(ctx_id)
        if not ctx or not ctx["start"] or not ctx["end"]:
            continue
        if not 330 <= (ctx["end"] - ctx["start"]).days <= 400:  # 通期のみ
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
                if category == "cf":  # 財務活動CFの合計値：ディメンション修飾なし
                    plain = [it for it in items if not it[1]]
                    if plain:
                        value = _best_by_pattern(plain, patterns)[3]
                elif category == "ss":  # 株主資本等変動計算書：構成要素の列を優先順に選ぶ
                    for member in EQUITY_COMPONENT_PRIORITY:
                        col = [it for it in items if it[1] == {EQUITY_AXIS: member}]
                        if col:
                            value = _best_by_pattern(col, patterns)[3]
                            break
                else:  # 配当政策等：決議ごとの総額を通期コンテキスト単位で合算する
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
    """ローカル名の辞書から、候補パターン順に最初に一致した値を返す。"""
    for pattern in patterns:
        rx = re.compile(pattern)
        for local, value in bucket.items():
            if rx.match(local):
                return value
    return None


def has_consolidated_data(facts, n):
    """n 期前の年度に、連結の純利益・自己資本系・総資産のいずれかが存在するかを返す。

    これが False の年度（完全な単独決算企業、または連結へ移行する前の年度）だけが、
    個別（NonConsolidated）データへの年度単位フォールバック対象になる。
    """
    for key in CONSOLIDATED_PRESENCE_KEYS:
        bucket = facts.get((SCOPE_CONSOLIDATED, PERIOD_KIND[key], n), {})
        if _pick(bucket, PATTERNS[key]) is not None:
            return True
    return False


def _pick_scoped(facts, key, n, solo_year=False):
    """項目 key の値を、連結 -> （配当系、または solo_year なら全項目）単体の順に探す。

    solo_year=True は「その年度に連結データが無い」年度（has_consolidated_data が False）で、
    連結を先に探したうえで、個別（NonConsolidated）の要約表 -> 個別の損益計算書本表
    （純利益のみ：ProfitLoss / NetIncomeLoss）の順にフォールバックする。
    連結年度（solo_year=False）の挙動は従来のまま。戻り値：(値, スコープ)。
    """
    scopes = [SCOPE_CONSOLIDATED]
    if solo_year or key in SOLO_FALLBACK_KEYS:
        scopes.append(SCOPE_SOLO)
    for scope in scopes:
        value = _pick(facts.get((scope, PERIOD_KIND[key], n), {}), PATTERNS[key])
        if value is not None:
            return value, scope
    if solo_year and key == "net_income":
        # 要約表に純利益が無い単独決算企業：損益計算書本表。
        # 個別コンテキストを優先し、連結が無い年度なので修飾なしのコンテキストも許容する。
        for scope in (SCOPE_SOLO, SCOPE_CONSOLIDATED):
            bucket = facts.get((scope, "Duration", n), {})
            value = _pick(bucket, NET_INCOME_PL_PATTERNS)
            if value is not None:
                return value, scope
    return None, None


def normalize_ratio(value, limit=1.0):
    """割合系タグに百分率（例 50.0）が混在していても、小数（0.50）へ正規化する。

    EDINET の割合タグ（自己資本比率・配当性向）は、単位 pure で百分率の数値が入る場合がある。
    これを小数と見なして金額に掛けると、100倍規模の過大値になる。
    絶対値が limit を超えたら百分率と判定して 100 で割る。
    ・None は None のまま返す（「タグ無し」を 0 に潰すと、配当性向タグの欠落が無配に化けるため）。
    ・limit：自己資本比率は 1.0（100% 超は有り得ない）。配当性向は赤字・特別配当で 100% 超
      （例 1.34 = 134%）が有り得るため、呼び出し側で 5.0 を指定する。
    """
    if value is None:
        return None
    return value / 100.0 if abs(value) > limit else value


_as_ratio = normalize_ratio  # 旧名の互換エイリアス


def detect_accounting_standard(facts):
    """要素名から会計基準（日本基準 / IFRS / 米国基準）を推定する。"""
    names = [name for bucket in facts.values() for name in bucket]
    if any("IFRS" in n for n in names):
        return "IFRS"
    if any("USGAAP" in n for n in names):
        return "US-GAAP"
    return "日本基準"


EQUITY_MAX_YEN = 5e13             # 50兆円超の自己資本は非現実的な過大値とみなす
EQUITY_ASSETS_TOLERANCE = 1.0001  # 自己資本が総資産を超えることは有り得ない（丸め誤差のみ許容）
EQUITY_VS_TOTAL_TOLERANCE = 1.05  # 推計値が資本合計（純資産）を5%超えたら異常（親会社持分 <= 合計）


def equity_sanity_problem(equity, assets, total_equity=None, estimated=False):
    """自己資本の候補値が非現実的なら理由の文字列を、問題なければ None を返す。

    ・総資産を上回る（自己資本比率 > 100% 相当）
    ・桁が非現実的（EQUITY_MAX_YEN 超）
    ・推計値（比率 x 総資産）が資本合計・純資産を上回る（親会社持分は合計を超えない）
    直接タグの値は、他の項目と食い違っても（非支配株主持分がマイナス等）棄却しない。
    """
    if equity > EQUITY_MAX_YEN:
        return f"implausible_magnitude({equity / 1e12:.1f}兆円)"
    if assets and equity > assets * EQUITY_ASSETS_TOLERANCE:
        return f"equity>total_assets({equity / 1e6:,.0f}>{assets / 1e6:,.0f}百万円)"
    if estimated and total_equity and equity > total_equity * EQUITY_VS_TOTAL_TOLERANCE:
        return f"equity>total_equity({equity / 1e6:,.0f}>{total_equity / 1e6:,.0f}百万円)"
    return None


# True にすると、資本合計・純資産合計（非支配株主持分を含む）より先に ratio*assets を使う。
# 日本基準で要約表の純資産額しか無い年度（BS本表が2期分しか無いため古い年度に多い）では、
# 自己資本比率 x 総資産のほうが親会社株主持分に近い。既定は「直接タグ優先」。
RATIO_BEFORE_TOTAL_EQUITY = False
EQUITY_RATIO_GAP_WARN = 0.03  # 直接値と比率推計の乖離がこれを超えたら備考に残す（監査用）


class EquityResolution(NamedTuple):
    equity: float | None   # 期末自己資本（円）
    source: str | None     # 取得元ラベル（direct(summary) / direct(bs) / ...）
    details: list          # 備考に残す補足（組み立て根拠など）
    problems: list         # 異常値ガードで棄却した候補とその理由


def derive_bs_owners_equity(values):
    """連結BS本表の金額から、親会社株主に帰属する自己資本を組み立てる。

    戻り値：(金額, 根拠) / 取得できなければ (None, None)。優先順位：
      (a) 親会社の所有者に帰属する持分（IFRS）
      (b) 株主資本及び評価・換算差額等合計
      (c) 株主資本 + 評価・換算差額等
      (d) 純資産合計 - 非支配株主持分（少数株主持分）- 新株予約権
          控除対象の要素が本表に無ければ、純資産合計そのまま（要素が無いのは該当なしのため）
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
    """期末自己資本（円）を、信頼できる順に確定する（IFRS・日本基準共通）。

    優先順位：
      (1) direct(summary)  要約表の親会社所有者帰属持分（EquityAttributableToOwnersOfParent）・自己資本
      (2) direct(bs)       連結BS本表（IFRS は親会社持分、日本基準は株主資本+評価・換算差額等、
                           または 純資産合計 - 非支配株主持分 - 新株予約権。derive_bs_owners_equity）
      (3) total_equity     資本合計（要約表）/ net_assets 純資産額（要約表）…非支配株主持分を含む
      (4) ratio*assets     上記が全て無い場合の最終フォールバック（normalize_ratio と
                           比率の範囲チェックを通す）
    候補が異常値ガード（equity_sanity_problem）に掛かれば棄却して次順位へ進む。
    戻り値：EquityResolution(自己資本, 取得元ラベル, 補足, 棄却理由)。取得できなければ equity=None。
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
        if value <= 0:  # 債務超過：ROE 算出不能として呼び出し側で扱う
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
    """抽出値から ROE / DOE（％）を再構成する。

    戻り値：(roe_pct, doe_pct, 期末自己資本, 備考)。算出不能なら roe/doe は None。
    備考には自己資本の取得元（equity=...）と、異常値ガードで棄却した候補（equity_rejected(...)）を残す。
    """
    notes = [SOLO_FALLBACK_NOTE] if values.get("solo_fallback") else []
    net_income = values.get("net_income")

    # 期末自己資本：直接タグを最優先し、推計（比率 x 総資産）は異常値ガード付きの後順位とする
    resolved = resolve_equity(values)
    equity = resolved.equity
    if resolved.source:
        notes.append(f"equity={resolved.source}")
    notes.extend(resolved.details)
    notes.extend(f"equity_rejected({p.replace(';', ',')})" for p in resolved.problems)
    if net_income is None or not equity or equity <= 0:
        return None, None, equity, ";".join(notes + ["roe_unavailable"])

    roe = net_income / equity * 100.0

    # DOE の算出カスケード（上位ほど優先）：
    #   (1) 配当金総額（CF計算書 > 株主資本等変動計算書 > 配当政策表）…株数に依存しない総額ベース
    #         payout = 配当金総額 / 純利益（黒字期のみ）、DOE = 配当金総額 / 期末自己資本
    #   (2) 要約表の配当性向タグ（連結 > 提出会社）…株式分割・併合の影響を受けない比率
    #   (3) DPS / EPS …EPS が遡及修正済みでも DPS が当時の実額のままの報告書があり、
    #       分割・併合の倍率だけ狂う。異常値は補正または除外する（最終フォールバック）。
    eps, dps = values.get("eps"), values.get("dps")
    tag = normalize_ratio(values.get("payout"), limit=5.0)
    if tag is not None and not 0.0 <= tag <= PAYOUT_SANITY_MAX:
        tag = None  # 範囲外のタグ値（単位違い等）は採用しない
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
            # 配当政策表の合算は構造が不確かなため、他の配当性向と概ね一致する場合のみ採用
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
        # 赤字期（EPS <= 0 または ROE <= 0）：配当総額 = 純利益 x DPS / EPS は符号が相殺され成立する
        doe = roe * dps / eps
        notes.append("doe=roe*dps/eps(赤字期)")
        if values.get("dps_scope") == SCOPE_SOLO:
            notes.append("dps=solo_table")
    elif eps:
        # 連結・単体のどちらにも配当要素が無い。無配（表中「－」）と推定して 0 とするが、
        # 要素名の未対応でも同じ結果になるため、呼び出し側で必ず診断ログを出す。
        doe = 0.0
        notes.append("dps_absent->0")
    else:
        return roe, None, equity, ";".join(notes + ["doe_unavailable"])
    return roe, doe, equity, ";".join(notes)


def correct_payout_for_split(p_raw):
    """DPS / EPS から求めた配当性向の、株式分割・併合による基準不一致を補正する。

    黒字期（EPS > 0）の配当性向が PAYOUT_SANITY_MAX（150%）以内なら、そのまま採用する。
    超過する場合は、分割倍率 f（10, 5, 4, 3, 2）で割り戻した値が 100% 以内に収まり、
    かつ典型的な配当性向（35%）に最も近いものを採用する。該当が無ければ None（算出除外）。
    戻り値：(配当性向, 備考サフィックス)
    注意：基準不一致が 0.1 倍方向（株式併合）で低く出る場合は、比率だけでは判別できない。
    その場合は配当性向タグ（上記 (1)）が取得できることが補正の前提となる。
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
    """報告書ZIPから、主要な経営指標等の推移（最大5期）と配当金総額を「生値の行」として抽出する。

    各行は fiscal_year（年度）と、抽出値 values（円・円/株・比率）を持つ。ROE / DOE の算出は
    複数報告書の結合後（finalize_rows）に行う。配当金総額は CF / 株主資本等変動計算書が
    直近2期分しか持たないため、報告書ごとに取れる年度が異なるからである。
    """
    period_end = date.fromisoformat(doc["periodEnd"])
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        candidates = [
            n for n in zf.namelist()
            if "/PublicDoc/" in n and n.lower().endswith(".xbrl")
        ]
        if not candidates:
            raise RuntimeError(f"PublicDoc 配下に XBRL が見つかりません: {doc.get('docID')}")
        # 有価証券報告書本体（asr）を優先
        candidates.sort(key=lambda n: ("asr" not in n.lower(), n))
        with zf.open(candidates[0]) as fp:
            facts, debug, total_dividends = parse_report_xbrl(fp, period_end)

    standard = detect_accounting_standard(facts)
    rows = []
    for n in range(0, 5):
        values = {}
        # 年度単位の判定：連結データがある年度は従来どおり連結のみ（既存結果は不変）。
        # 連結データが無い年度（単独決算企業・連結移行前）だけ個別へフォールバックする。
        solo_year = not has_consolidated_data(facts, n)
        for key in PATTERNS:
            values[key], values[f"{key}_scope"] = _pick_scoped(facts, key, n, solo_year)
        # solo_year では連結に純利益・自己資本系が無いため、これらが取れたなら個別由来である
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
    """複数報告書の生値の行を年度単位に結合し、ROE / DOE を算出して返す。

    - 要約表の値（純利益・自己資本・EPS・DPS 等）は、より新しい報告書（offset が小さい）を採用
    - 配当金総額は、年度ごとに全報告書から探し、当期（n が小さい）で記載された値を優先
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
        # BS本表は当期・前期の2期分しか載らないため、最新の報告書だけでは直近2年しか取れない。
        # その年度が最も当期に近い形（n が小さい）で載る報告書から、BS系の値を一括で採用する
        # （純資産・非支配株主持分などを別々の報告書から拾って食い違うのを避ける）。
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
            log(f"  [補正] {row['fiscal_year']}年度 (docID {row['source_doc_id']}): "
                f"EPS={row['eps']} DPS={row['dps']} 総額={row['total_dividends_mn']} -> {text}")
    absent = [r for r in rows if "dps_absent" in str(r["note"])]
    if absent:
        first = absent[0]["_primary"]
        log_dividend_debug(first["doc"], first["accounting_standard"], first["debug"],
                           [r["fiscal_year"] for r in absent], log)
    log_equity_diagnostics(rows, code, log)
    for row in rows:
        row.pop("_primary")
    return rows


def _equity_source_of(note):
    """備考から自己資本の取得元ラベルを取り出す（equity_rejected(...) 内の記述は無視する）。"""
    for part in str(note).split(";"):
        if part.startswith("equity="):
            return part[len("equity="):]
    return "取得不能"


def log_equity_diagnostics(rows, code, log=print):
    """自己資本の取得元の内訳と、異常値ガードに掛かった年度の診断ログを出力する。

    ratio*assets への落ち込み・棄却・算出不能、または直接タグを拾えない IFRS の行がある場合は、
    入力値（比率・総資産・BS本表の各項目）と、報告書内の自己資本系の要素名も出す。
    """
    counts = {}
    for r in rows:
        label = _equity_source_of(r["note"])
        counts[label] = counts.get(label, 0) + 1
    log("  [自己資本] 取得元の内訳: "
        + " / ".join(f"{k} {n}年" for k, n in sorted(counts.items())))
    flagged = []
    for r in rows:
        text = str(r["note"])
        if "equity_rejected" in text:
            log(f"  [警告] {r['fiscal_year']}年度 (docID {r['source_doc_id']}): "
                f"自己資本の異常値を棄却しました -> {text}")
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
        return "なし" if x is None else f"{x / 1e6:,.0f}"

    log(f"  [DEBUG] 自己資本の入力値（{first['fiscal_year']}年度, {first['accounting_standard']}, "
        f"百万円）: 比率(生値)={values.get('equity_ratio')} "
        f"正規化後={normalize_ratio(values.get('equity_ratio'))} "
        f"総資産={mn(values.get('total_assets'))} 資本合計={mn(values.get('total_equity'))} "
        f"純資産(要約表)={mn(values.get('net_assets'))} 直接(要約表)={mn(values.get('equity_direct'))}")
    log(f"  [DEBUG] BS本表: 親会社持分={mn(values.get('equity_bs'))} "
        f"純資産={mn(values.get('net_assets_bs'))} 株主資本={mn(values.get('shareholders_equity_bs'))} "
        f"評価・換算差額等={mn(values.get('valuation_bs'))} 非支配株主持分={mn(values.get('nci_bs'))} "
        f"新株予約権={mn(values.get('rights_bs'))}")
    names = sorted(n for n in debug["summary_names"][SCOPE_CONSOLIDATED]
                   if re.search(r"Equity|Assets|Ratio|Capital|Interest|Rights", n))
    log("  [DEBUG] 連結の要約表の自己資本系要素: "
        + (", ".join(n.replace(SUMMARY_SUFFIX, "") for n in names) or "なし")
        + " / BS本表の自己資本系要素: "
        + (", ".join(sorted(debug["equity_names"])) or "なし"))
    log("  [DEBUG] 直接タグが見つからない場合は、上記の要素名を PATTERNS の equity_direct / "
        "equity_bs 系へ追記してください。")


def log_dividend_debug(doc, standard, debug, absent_years, log=print):
    """配当（総額・DPS・配当性向）をいずれも取得できなかった場合の診断ログを出力する。

    ここに出る要素名が、本来拾うべき配当要素の手掛かりになる。配当金総額なら
    CF_DIV_PATTERNS / SS_DIV_PATTERNS、DPS なら PATTERNS["dps"] へ名称を追記すれば対応できる。
    """
    def fmt(names):
        names = sorted(names)
        shown = ", ".join(n.replace(SUMMARY_SUFFIX, "") for n in names[:30])
        return shown + (f" …他{len(names) - 30}件" if len(names) > 30 else "")

    solo_dps = [n for n in debug["summary_names"][SCOPE_SOLO] if "Dividend" in n]
    log(f"  [DEBUG] 配当を取得できませんでした: docID={doc.get('docID')} "
        f"({doc.get('periodEnd')}期, {standard}) 対象年度={sorted(absent_years)}")
    log(f"  [DEBUG] 連結の要約表の要素（{SUMMARY_SUFFIX}を省略）: "
        f"{fmt(debug['summary_names'][SCOPE_CONSOLIDATED]) or 'なし'}")
    log(f"  [DEBUG] 単体の要約表の要素: {fmt(debug['summary_names'][SCOPE_SOLO]) or 'なし'}"
        f"（うち配当系: {fmt(solo_dps) or 'なし'}）")
    if debug["dividend_names"]:
        log("  [DEBUG] 報告書内の配当・配当性向を含む全要素名とコンテキスト例:")
        for name, ctxs in sorted(debug["dividend_names"].items()):
            log(f"    - {name}: {', '.join(ctxs)}")
    else:
        log("  [DEBUG] 報告書内に配当・配当性向を含む要素が1つもありません（無配の可能性）。")
    log("  [DEBUG] 無配ではない場合は上記の要素名を CF_DIV_PATTERNS / SS_DIV_PATTERNS / "
        "PATTERNS['dps'] へ追記してください。取得できなかった年度の DOE は 0 として扱われています。")


# ---------------------------------------------------------------------------
# 6. 銘柄ごとの時系列取得（直近・5年前を基本に、取得できれば10年前も結合）
# ---------------------------------------------------------------------------
CSV_COLUMNS = [
    "code", "name", "fiscal_year", "period_end", "accounting_standard",
    "net_income_mn", "equity_mn", "avg_equity_mn", "total_dividends_mn", "eps", "dps",
    "roe_end_pct", "doe_end_pct", "roe_pct", "doe_pct",
    "lbs_pct", "sgr_pct", "cs", "osm", "payout_pct", "lane",
    "source_doc_id", "note",
]


def normalize_code(code):
    """証券コードを4桁（英字含む）へ正規化する。5桁（末尾0）入力も許容。"""
    c = str(code).strip().upper()
    if len(c) == 5 and c.endswith("0"):
        c = c[:4]
    if not re.fullmatch(r"[0-9A-Z]{4}", c):
        raise ValueError(f"証券コードの形式が不正です: {code!r}")
    return c


def fetch_company_series(client, code, fye_month=None, today=None, log=print,
                         full_dividend_coverage=True):
    """EDINET から有報を取得し、取得できた全年度の ROE / DOE 時系列を返す。

    直近・5年前の2本を基本に（重複を除いて約8〜10期分）、10年前相当の報告書が取得できれば
    それも加えて（最大で10年超〜14年程度）、「主要な経営指標等の推移」（各5期）を取得する。
    配当金総額（CF計算書等）は各報告書に当期と前期の2期分しか載らないため、
    full_dividend_coverage=True の場合は、総額が欠ける年度を埋める報告書を追加で取得する
    （通常は2・4・7年前などが加わる）。False なら基本の2〜3本のみ（API呼び出し最小）。
    """
    today = today or date.today()
    code5 = code + "0"

    if fye_month is None:
        fye_month = FISCAL_END_MONTH.get(code)
    if fye_month is None:
        fye_month, _ = lookup_edinet_codelist(code5)
    months = [fye_month] if fye_month else [3, 12, 9, 6, 2, 11, 1, 4, 5, 7, 8, 10]
    if not fye_month:
        log("  決算期末月が不明のため全月を試行します（時間がかかります）。"
            "--fye-month の指定を推奨します。")

    # (1) 直近の有価証券報告書
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
        raise LookupError(f"{code}: 直近の有価証券報告書が見つかりません。")
    latest_end = date.fromisoformat(latest["periodEnd"])
    latest_submit = datetime.fromisoformat(latest["submitDateTime"]).date()
    log(f"  直近: {latest['periodEnd']} 期 / 提出 {latest_submit} / docID {latest['docID']}")

    # (2) 5年前・10年前（取得できなければ年を繰り上げて再探索）
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
                suffix = "" if step == 0 else f"（{offset}年前相当が見つからないため{eff}年前で代替）"
                log(f"  {eff}年前: {doc['periodEnd']} 期 / docID {doc['docID']}{suffix}")
                break
        else:
            log(f"  [警告] {offset}年前の有価証券報告書が見つかりませんでした。")

    # (2b) 配当金総額が欠ける年度を埋める追加報告書（各報告書は当期・前期の2期分を持つ）
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
                log(f"  {offset}年前（配当金総額の補完）: {doc['periodEnd']} 期 / "
                    f"docID {doc['docID']}")
            else:
                log(f"  [警告] {offset}年前の報告書が見つからず、その年度の配当金総額は"
                    "取得できません。")

    # (3) パースして年度単位に結合し、ROE / DOE を算出
    raw_rows = []
    for offset, doc in found:
        zip_bytes = client.download_xbrl_zip(doc["docID"])
        raw_rows.extend(extract_report_rows(zip_bytes, doc, offset, code))
    rows = finalize_rows(raw_rows, code, latest.get("filerName", ""), log=log)
    df = pd.DataFrame(rows)
    df = df[df["fiscal_year"] >= fiscal_year_of(latest_end) - 14]
    return df.sort_values("fiscal_year").reset_index(drop=True)


# ---------------------------------------------------------------------------
# 7. ローカルキャッシュ（moat_data_{証券コード}.csv）
# ---------------------------------------------------------------------------
def csv_path(datadir, code):
    return Path(datadir) / f"moat_data_{code}.csv"


def is_legacy_cache(df):
    """配当金総額ベースの算出に対応していない旧版キャッシュか、不正確な配当を含むかを判定する。"""
    if "total_dividends_mn" not in df.columns:  # 総額ベース導入前のCSV
        return True
    if "note" not in df.columns:
        return False
    if df["note"].astype(str).str.contains("dps_missing->0", regex=False).any():
        return True
    # 株式分割補正の導入前に保存された、黒字期なのに配当性向が異常値の行を含むキャッシュ
    if {"eps", "payout_pct"} <= set(df.columns):
        bad = (df["eps"] > 0) & (df["payout_pct"] > PAYOUT_SANITY_MAX * 100)
        if bad.any():
            return True
    return False


def log_dividend_coverage(code, table, log=print):
    """配当金総額の取得年数と、各年度の算出根拠の内訳をログに出す。"""
    n_all = len(table)
    n_total = int(table["total_dividends_mn"].notna().sum())
    log(f"[{code}] 配当金総額取得 {n_total}/{n_all}年")
    notes = table["note"].astype(str)
    counts = {
        "総額ベース（CF計算書）": notes.str.contains(r"total_div\(cf", regex=True).sum(),
        "総額ベース（株主資本等変動計算書）": notes.str.contains(r"total_div\(ss", regex=True).sum(),
        "総額ベース（配当政策表）": notes.str.contains(r"total_div\(policy", regex=True).sum(),
        "配当性向タグ": notes.str.contains("payout=tag", regex=False).sum(),
        "DPS/EPS（フォールバック）": notes.str.contains("payout=dps/eps", regex=False).sum(),
        "赤字期の比率計算": notes.str.contains("赤字期", regex=False).sum(),
        "配当要素なし（DOE=0）": notes.str.contains("dps_absent", regex=False).sum(),
        "算出除外": notes.str.contains("payout_unresolved", regex=False).sum(),
    }
    log(f"[{code}] 算出根拠の内訳: "
        + " / ".join(f"{k} {int(v)}年" for k, v in counts.items() if v))
    if n_total < n_all:
        missing = sorted(table.loc[table["total_dividends_mn"].isna(), "fiscal_year"])
        log(f"[{code}] 総額が未取得の年度（配当性向タグ・DPS/EPSで代替）: "
            f"{', '.join(str(int(y)) for y in missing)}")


def trim_to_primary_statements(table, code="", log=print):
    """描画対象を「配当金総額を一次諸表（CF計算書等）から取得できた期間」に絞る。

    古い年度（10年前相当の報告書の過年度分など）は配当金総額が取れず、DPS/EPS・配当性向タグの
    フォールバックになる（株式分割・併合で歪む）。最初に総額が取れた年度より前の年度を描画から外す。
    CSV 本体は監査用に全年度を保持したまま、プロット用のテーブルだけを絞る。
    総額が1年も取れない銘柄は、絞ると空になるため全年度を維持する。
    """
    if "total_dividends_mn" not in table.columns:
        return table
    has_total = table["total_dividends_mn"].notna()
    if not has_total.any():
        log(f"[{code}] 配当金総額が全年度で未取得のため、期間を絞らずフォールバック値で描画します。")
        return table
    first_year = table.loc[has_total, "fiscal_year"].min()
    dropped = sorted(int(y) for y in table.loc[table["fiscal_year"] < first_year, "fiscal_year"])
    if dropped:
        log(f"[{code}] 一次諸表で総額が確認できる {int(first_year)}年度以降に限定"
            f"（除外: {', '.join(str(y) for y in dropped)}年度）")
    return table[table["fiscal_year"] >= first_year].reset_index(drop=True)


def load_or_fetch(code, datadir, force_update, get_client, fye_month=None, log=print,
                  full_dividend_coverage=True):
    """CSV（datadir 配下）があれば API 通信を行わず読み込み、無ければ EDINET から取得して保存する。"""
    path = csv_path(datadir, code)
    if path.exists() and not force_update:
        df = pd.read_csv(path, dtype={"code": str, "lane": str})
        if len(df) == 0:
            log(f"[{code}] キャッシュが空のため再取得します。")
        elif is_legacy_cache(df):
            log(f"[{code}] 不正確な配当データを含む旧版キャッシュを検出しました。"
                "削除せずに再取得して上書きします。")
        else:
            log(f"[{code}] キャッシュ読込（API通信なし）: {path}")
            return compute_moat_table(df)

    log(f"[{code}] EDINET から取得します…")
    raw = fetch_company_series(get_client(), code, fye_month=fye_month, log=log,
                               full_dividend_coverage=full_dividend_coverage)
    table = compute_moat_table(raw)
    table = table.reindex(columns=CSV_COLUMNS)
    Path(datadir).mkdir(parents=True, exist_ok=True)
    table.to_csv(path, index=False, encoding="utf-8")
    log(f"[{code}] 保存: {path}（{len(table)}年分）")
    log_dividend_coverage(code, table, log)
    return compute_moat_table(table.drop(columns=["lane"]))


# ---------------------------------------------------------------------------
# 8. 補間（取得できた全年度を滑らかに繋ぐ）
# ---------------------------------------------------------------------------
def pchip_interpolate(x, y, xq):
    """単調性を保つ区分3次エルミート補間（Fritsch-Carlson 法）。

    スプライン補間のようなオーバーシュート（DOE が負へ潜る等）を起こさない。
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
    """1銘柄の補間済み軌跡（全フレーム時刻 t_grid に対応する配列）。"""

    code: str
    name: str
    valid: np.ndarray      # その時刻に描画対象か（上場前・データ開始前は False）
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
    """各銘柄の ROE / DOE を年次→サブフレームへ補間し、毎フレームの座標・レーンを算出する。

    ROE / DOE を補間してから四則演算とレーン判定を適用するため、
    バブルの位置・大きさ・色は毎フレーム同一のモデルで一貫して決まる。
    """
    years = [int(y) for t in tables.values() for y in t["fiscal_year"]]
    # 時間軸の起点はフォーカス銘柄の最古年度。他銘柄は、その年度より後に開示が始まる場合
    # （上場が新しい等）のみ、データ開始年度から登場する。
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
        tq = np.clip(t_grid, yrs[0], yrs[-1])  # 最新値以降は最終値で保持
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
            lane=[lane_of(d) for d in payout],  # 最近傍レーンを毎フレーム再判定
            first_year=int(yrs[0]),
            last_year=int(yrs[-1]),
        )
    return t_grid, trajs


# ---------------------------------------------------------------------------
# 9. 描画の共通部品
# ---------------------------------------------------------------------------
def setup_japanese_font():
    """日本語フォントを設定する。見つからなければ False（英語ラベルへ切替）。"""
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
    try:  # Colab 等：システムに入っている CJK フォントを登録し直す
        for path in font_manager.findSystemFonts():
            if any(k in os.path.basename(path).lower() for k in keywords):
                font_manager.fontManager.addfont(path)
    except Exception:
        pass
    if apply():
        return True
    try:  # 最後の手段：japanize-matplotlib が導入済みなら利用する
        importlib.import_module("japanize_matplotlib")
        return True
    except Exception:
        return False


AXIS_MARGIN = 0.12      # 動的スケーリングで上下左右に付加する余白（データ範囲に対する比率）
AXIS_MIN_SPAN_X = 5.0   # 余白計算に使う最小スパン（SGR, %）。データが狭いときの過剰な拡大を防ぐ
AXIS_MIN_SPAN_Y = 50.0  # 同（CS, %^2）


def axis_limits(tables, trajs=None, min_year=None):
    """描画対象の全銘柄・全年度の SGR / CS から、動的スケーリングの軸範囲を返す。

    データ全体の min / max を走査し、上下左右に AXIS_MARGIN の余白を付けて範囲を決める。
    範囲は常に 0 を含む（SGR=0 線、CS=0 線が基準として見える）。
    余白の基準スパンには下限（AXIS_MIN_SPAN_*）を設け、データの散らばりが小さい場合に
    軸が不自然に拡大・縮小しないようにする。
    trajs（build_trajectories の戻り値）を渡すと、PCHIP 補間で年次の節点の外へはみ出す経路
    （GIF のフレーム）も含めて走査する。Plotly は年次の節点のみで足りる。
    min_year を渡すと、それより前の年度（フォーカス銘柄の開始前で描画されない行）は無視する。
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


ZOOM_ZERO_PAD_RATIO = 0.05  # ズーム窓が 0 を跨ぐとき、0 線が見える程度に残す下端余白（span 比）


def zoom_limits(tables, focus_code, span, log=print):
    """フォーカス銘柄の最新年度座標 (SGR, CS) を中心とするズーム窓 (xlim, ylim) を返す。

    窓は [中心 - span, 中心 + span]。中心が 0 以上で下端が 0 を下回る場合は、
    負領域を大きく映さないよう下端を -span * ZOOM_ZERO_PAD_RATIO に切り詰める。
    中心が負（赤字等）の場合は切り詰めず、窓の幅をそのまま保つ。
    座標が取得できない・span が不正なときは None を返す（呼び出し側で全体描画へ戻す）。
    """
    if not np.isfinite(span) or span <= 0:
        log(f"  [警告] --zoom-span={span} は正の有限値ではないため、全体描画で実行します。")
        return None
    tbl = tables[focus_code].dropna(subset=["roe_pct", "doe_pct"]).sort_values("fiscal_year")
    if tbl.empty:
        return None
    last = tbl.iloc[-1]
    cx, cy = float(last["sgr_pct"]), float(last["cs"])
    if not (np.isfinite(cx) and np.isfinite(cy)):
        log(f"  [警告] {focus_code} の最新年度座標が有限値でないため、全体描画で実行します。")
        return None

    def window(center):
        lo, hi = center - span, center + span
        if center >= 0 and lo < 0:
            lo = -span * ZOOM_ZERO_PAD_RATIO
        return lo, hi

    xlim, ylim = window(cx), window(cy)
    log(f"  [ズーム] {focus_code} FY{int(last['fiscal_year'])} 中心 (SGR {cx:.1f}, CS {cy:.1f}) "
        f"±{span:g}: SGR {xlim[0]:.1f} 〜 {xlim[1]:.1f} / CS {ylim[0]:.1f} 〜 {ylim[1]:.1f}")
    return xlim, ylim


def lane_curves(xmax, n=400):
    """背景に固定表示する5本の基準軌道（放物線4本＋X軸）を返す。

    戻り値：[(キー, 色, 凡例ラベル, 線種, x配列, y配列), ...]
    """
    x = np.linspace(0, xmax, n)
    curves = []
    for d_pct, (color, label, ls) in LANES.items():
        curves.append((d_pct, color, label, ls, x, k_of(d_pct / 100) * x**2))
    k_out = k_of(OUTER_PAYOUT)
    label = f"外側の低角度軌道 (d = 11.45% → k ≈ {k_out:.3f})"
    curves.append(("outer", OUTER_COLOR, label, ":", x, k_out * x**2))
    return curves


def layout_aligned_labels(points, ylim, gap=0.075, lo=0.04, hi=0.96):
    """全銘柄ラベルを左右の余白に縦一列で整列させる（重なり回避）。

    点のX座標の中央値で左右へ振り分け、各列で y 順を保ったまま最小間隔 gap を確保する。
    戻り値：{コード: ("left" | "right", 軸座標系のy)}
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
        if pos[-1] > hi:  # 上端を超えたら下方向へ押し戻す
            pos[-1] = hi
            for i in range(len(pos) - 2, -1, -1):
                pos[i] = min(pos[i], pos[i + 1] - g)
        for (code, _), p in zip(desired, pos):
            result[code] = (side, p)
    return result


def company_label(code, names):
    """タイトル・凡例用の表示名。「ストライク (6196)」形式（法人格表記は除去）。"""
    name = re.sub(r"株式会社|\(株\)|（株）|㈱", "", names.get(code, "") or "").strip()
    return f"{name} ({code})" if name else str(code)


def display_name(code, names, jp_ok):
    """日本語フォントが無い環境では銘柄名を省略（コードのみ）にする。"""
    name = names.get(code, "") if jp_ok else ""
    return f"{code} {name}".strip()


# ---------------------------------------------------------------------------
# 10. Matplotlib GIF アニメーション
# ---------------------------------------------------------------------------
def render_gif(tables, names, focus_code, out_path, steps=8, hold_frames=20,
               fps=20, dpi=100, log=print, view_limits=None):
    """取得できた全年度の軌跡を GIF で書き出す。

    ・背景の5本の基準軌道は全フレーム固定
    ・フォーカス銘柄のみラベルと太い軌跡（色は区間ごとの最寄りレーン）を追従表示
    ・他銘柄は半透明の参照点。最初と最後のフレームでのみ全銘柄の整列ラベルを表示
    """
    jp_ok = setup_japanese_font()
    if not jp_ok:
        log("  [情報] 日本語フォントが見つからないため、図中の文言を英語で描画します。")

    def tr(ja, en):
        return ja if jp_ok else en

    t_grid, trajs = build_trajectories(tables, names, steps, focus_code)
    if focus_code not in trajs:
        raise ValueError(f"フォーカス銘柄 {focus_code} の描画可能なデータがありません。")
    codes = list(trajs)
    others = [c for c in codes if c != focus_code]
    n_t = len(t_grid)
    if view_limits is None:
        xlim, ylim = axis_limits(tables, trajs=trajs, min_year=int(round(t_grid[0])))
        log(f"  [軸] 動的スケーリング: SGR {xlim[0]:.1f} 〜 {xlim[1]:.1f} / "
            f"CS {ylim[0]:.1f} 〜 {ylim[1]:.1f}")
    else:  # ズーム描画：軸範囲は呼び出し側（zoom_limits）の指定を使う
        xlim, ylim = view_limits

    def in_view(x, y):
        """ズーム時のみ窓内判定。通常描画では常に True（既存挙動を維持）。"""
        return view_limits is None or (xlim[0] <= x <= xlim[1] and ylim[0] <= y <= ylim[1])

    focus = trajs[focus_code]
    focus_tbl = tables[focus_code].dropna(subset=["roe_pct", "doe_pct"])

    # フレーム計画：先頭と末尾でホールド（全ラベル表示）、その間は通常再生
    if n_t == 1:
        plan = [(0, True)] * hold_frames
    else:
        plan = ([(0, True)] * hold_frames
                + [(j, False) for j in range(1, n_t - 1)]
                + [(n_t - 1, True)] * hold_frames)

    # 整列ラベルの配置（最初と最後の状態でそれぞれ計算）
    def label_layout(j):
        pts = {c: (trajs[c].sgr[j], trajs[c].cs[j]) for c in codes
               if trajs[c].valid[j] and in_view(trajs[c].sgr[j], trajs[c].cs[j])}
        return pts, layout_aligned_labels(pts, ylim)

    layouts = {0: label_layout(0), n_t - 1: label_layout(n_t - 1)}

    bubble_scale = 9.0  # バブル面積 = LBS x bubble_scale（pt^2）
    fig = Figure(figsize=(12, 7.6), dpi=dpi)
    FigureCanvasAgg(fig)
    fig.patch.set_facecolor("white")
    fig.subplots_adjust(left=0.20, right=0.80, top=0.90, bottom=0.10)
    ax = fig.add_subplot(111)
    ax.set_facecolor("#fafafa")

    # --- 静的な背景：団子ゾーン、5本の基準軌道（放物線4本＋X軸）-----------------
    ax.add_patch(Rectangle((DANGO_ZONE["x"], DANGO_ZONE["y"]), DANGO_ZONE["w"],
                           DANGO_ZONE["h"], facecolor="#f0c987", edgecolor="#d9a441",
                           linestyle="--", linewidth=1.0, alpha=0.28, zorder=0.5))
    legend_handles = []
    for key, color, label, ls, x, y in lane_curves(xlim[1]):
        ax.plot(x, y, ls, color=color, linewidth=1.5, alpha=0.9, zorder=1)
        legend_handles.append(plt_line(color, ls, label if jp_ok else LANE_SHORT_LABEL_EN[key]))
    ax.axhline(0, color="#8a9199", linewidth=1.2, zorder=1)
    legend_handles.append(Patch(facecolor="#f0c987", edgecolor="#d9a441", alpha=0.45,
                                linestyle="--",
                                label=tr("団子ゾーン (SGR 7〜14%、CS 35〜110)",
                                         "Dango zone (SGR 7-14%, CS 35-110)")))
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.yaxis.set_label_coords(-0.30, 0.5)  # 左余白の整列ラベル列と重ならない位置へ退避
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
        + f"  [{display_name(focus_code, names, jp_ok)}]",
        fontsize=14, fontweight="bold", color="#2c3e50", y=0.965)
    fig.text(0.99, 0.012,
             tr("バブル面積 ＝ LBS（ROE＋DOE）／出典：EDINET 有価証券報告書"
                "「主要な経営指標等の推移」（期中平均自己資本ベース、年次間はPCHIP補間）",
                "Bubble area = LBS (ROE+DOE) / Source: EDINET annual securities reports "
                "(average equity basis, PCHIP-interpolated between years)"),
             ha="right", va="bottom", fontsize=7.5, color="#5d6d7e")

    # --- 動的アーティスト（毎フレーム更新）-------------------------------------
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
    for yk in knot_years:  # 年ラベルは5年刻み（最新年起点）と開始年のみ。密集を避ける
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

        # 他銘柄：半透明の参照点（色は各フレームの最寄りレーン）
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

        # フォーカス銘柄：太い軌跡（区間ごとに最寄りレーン色）＋バブル
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

        # ラベル：通常はフォーカスのみ追従。先頭・末尾のホールド中のみ全銘柄を整列表示
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
                ann.set_text(f"{display_name(code, names, jp_ok)}\n"
                             f"(SGR:{tr_.sgr[j]:.1f}%, CS:{tr_.cs[j]:.1f})")
                ann.set_visible(True)
        elif focus.valid[j] and in_view(focus.sgr[j], focus.cs[j]):
            follow.xy = (focus.sgr[j], focus.cs[j])
            follow.set_text(
                f"{display_name(focus_code, names, jp_ok)}\n"
                f"ROE {focus.roe[j]:.1f}% / DOE {focus.doe[j]:.1f}%\n"
                f"SGR {focus.sgr[j]:.1f}% / CS {focus.cs[j]:.1f}")
            follow.set_visible(True)
        return []

    anim = FuncAnimation(fig, update, frames=len(plan), interval=1000 / fps,
                         blit=False, repeat=False)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    total = len(plan)
    log(f"  GIF を書き出し中…（{total}フレーム）")
    anim.save(str(out_path), writer=PillowWriter(fps=fps), dpi=dpi,
              progress_callback=lambda i, n: (log(f"    {i + 1}/{n}") if (i + 1) % 50 == 0
                                              else None))
    log(f"  保存: {out_path}")
    return out_path


def plt_line(color, linestyle, label):
    """凡例用の線ハンドル（pyplot を使わずに生成する）。"""
    from matplotlib.lines import Line2D

    return Line2D([0], [0], color=color, linestyle=linestyle, linewidth=1.8, label=label)


LANE_SHORT_LABEL_EN = {
    50: "d=50% lane (k=2.000)",
    35: "d=35% lane (k=0.828)",
    30: "d=30% lane (k=0.612)",
    0: "d=0% lane (k=0)",
    "outer": "outer low-angle lane (d=11.45%)",
}


# ---------------------------------------------------------------------------
# 11. Plotly インタラクティブ HTML
# ---------------------------------------------------------------------------
def build_plotly_html(tables, names, focus_code, out_path, include_plotlyjs="cdn",
                      log=print, view_limits=None):
    """ズーム・パン・ホバーで数値を確認できるインタラクティブHTMLを書き出す。

    年次の実測値のみをフレームとし（ホバー値は補間値ではなく一次データ由来）、
    フレーム間の移動は Plotly の遷移アニメーションで滑らかに繋ぐ。
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        log("  [警告] plotly が未導入のため HTML 出力をスキップします（pip install plotly）。")
        return None

    codes = list(tables)
    first_year = int(tables[focus_code]["fiscal_year"].min())
    years = sorted({int(y) for t in tables.values() for y in t["fiscal_year"]
                    if int(y) >= first_year})
    if view_limits is None:
        xlim, ylim = axis_limits(tables, min_year=first_year)
        log(f"  [軸] 動的スケーリング: SGR {xlim[0]:.1f} 〜 {xlim[1]:.1f} / "
            f"CS {ylim[0]:.1f} 〜 {ylim[1]:.1f}")
    else:  # ズーム描画：軸範囲は呼び出し側（zoom_limits）の指定を使う
        xlim, ylim = view_limits
    clean = {c: t.dropna(subset=["roe_pct", "doe_pct"]).sort_values("fiscal_year")
             for c, t in tables.items()}
    max_lbs = max(float(np.nanmax(np.maximum(t["lbs_pct"], 1.0))) for t in clean.values()
                  if not t.empty)
    sizeref = 2.0 * max_lbs / (58.0 ** 2)  # 最大バブルの直径を約58pxに揃える
    label_positions = ["top center", "bottom center", "middle right", "middle left"]

    def row_at(code, year):
        """その年の行。最新年以降は最終値を保持し、開始前は None。"""
        tbl = clean[code]
        if tbl.empty or year < tbl["fiscal_year"].min():
            return None
        sub = tbl[tbl["fiscal_year"] <= year]
        return sub.iloc[-1]

    def hover(code, row):
        lane = lane_key(str(row["lane"]))
        osm = "算出不能" if not np.isfinite(row["osm"]) else f"{row['osm']:.2f}倍"
        payout = "定義不能" if not np.isfinite(row["payout_pct"]) else f"{row['payout_pct']:.1f}%"
        return (f"<b>{code} {names.get(code, '')}</b><br>{int(row['fiscal_year'])}年度"
                f"（{row.get('accounting_standard', '')}）<br>"
                f"ROE {row['roe_pct']:.2f}% / DOE {row['doe_pct']:.2f}%<br>"
                f"＋LBS {row['lbs_pct']:.2f}% / －SGR {row['sgr_pct']:.2f}%<br>"
                f"×CS {row['cs']:.1f} / ÷OSM {osm}<br>配当性向 {payout}<br>"
                f"最寄りレーン：{LANE_SHORT_LABEL[lane]}")

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

    # 背景：5本の基準軌道（放物線4本＋X軸）。全フレームで固定。
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
        name=f"{company_label(focus_code, names)} 軌跡"))
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
            # 軸範囲は全年度のデータから決めた値を全フレームで共有する（再生中に軸が動かない）
            layout=dict(xaxis=dict(range=list(xlim)), yaxis=dict(range=list(ylim)))))

    slider_steps = [
        dict(method="animate", label=f"{y}年度",
             args=[[str(y)], dict(mode="immediate", frame=dict(duration=0, redraw=False),
                                  transition=dict(duration=500, easing="cubic-in-out"))])
        for y in years
    ]
    fig = go.Figure(data=traces, frames=frames)
    fig.update_layout(
        template="plotly_white", height=780,
        title=dict(text=f"{company_label(focus_code, names)} - モート推移"
                        f"　「四則演算数理モデル」", x=0.02),
        font=dict(family="Hiragino Sans, Yu Gothic, Meiryo, Noto Sans JP, sans-serif",
                  size=12, color="#2c3e50"),
        xaxis=dict(title="SGR (%)　［引き算：ROE − DOE］", range=list(xlim),
                   zeroline=True, gridcolor="#e5e8ec"),
        yaxis=dict(title="CS (%²)　［掛け算：DOE × ROE］", range=list(ylim),
                   zeroline=True, gridcolor="#e5e8ec"),
        legend=dict(title="配当レーン（バブル色＝最寄りレーン）", x=0.01, y=0.99,
                    bgcolor="rgba(255,255,255,0.85)", bordercolor="#c9ced4", borderwidth=1),
        updatemenus=[dict(
            type="buttons", direction="left", x=0.02, y=-0.12, xanchor="left",
            buttons=[
                dict(label="▶ 再生", method="animate",
                     args=[None, dict(fromcurrent=True, mode="immediate",
                                      frame=dict(duration=900, redraw=False),
                                      transition=dict(duration=700, easing="cubic-in-out"))]),
                dict(label="■ 停止", method="animate",
                     args=[[None], dict(mode="immediate", frame=dict(duration=0, redraw=False),
                                        transition=dict(duration=0))]),
            ])],
        sliders=[dict(active=0, steps=slider_steps, x=0.15, len=0.83, y=-0.08,
                      currentvalue=dict(prefix="", font=dict(size=14)))],
        annotations=[dict(
            text="バブル面積＝LBS（ROE＋DOE）／出典：EDINET 有価証券報告書「主要な経営指標等の推移」"
                 "（期中平均自己資本ベース）／ホバーで数値、ドラッグで拡大、ダブルクリックで全体表示",
            x=1.0, y=-0.2, xref="paper", yref="paper", xanchor="right", showarrow=False,
            font=dict(size=10, color="#5d6d7e"))],
        margin=dict(l=70, r=30, t=70, b=140),
    )
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(out_path), include_plotlyjs=include_plotlyjs, auto_play=False,
                   config={"scrollZoom": True, "displaylogo": False})
    log(f"  保存: {out_path}")
    return out_path


# ---------------------------------------------------------------------------
# 12. オーケストレーション
# ---------------------------------------------------------------------------
def _display_in_notebook(gif_path):
    """Jupyter / Colab 上で実行された場合のみ、GIF をセルに表示する。"""
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
        full_dividend_coverage=True, zoom=False, zoom_span=15.0):
    """データ取得（またはキャッシュ読込）→ 四則演算 → GIF / HTML 出力まで一括実行する。

    Parameters
    ----------
    codes : list[str] | None
        描画する証券コード。None なら図1の16銘柄。
    focus_code : str | None
        ラベルと太い軌跡を追従表示する銘柄。codes に含まれなければ自動で追加する。
        None なら codes の先頭銘柄、codes も省略時は DEFAULT_FOCUS_CODE（7011）。
    force_update : bool
        True ならキャッシュ（moat_data_{証券コード}.csv）を無視して再取得する。
    outdir : str | Path
        GIF / HTML の出力先フォルダ（既定 "output"。無ければ自動作成）。
    datadir : str | Path
        CSV キャッシュの保存・参照先フォルダ（既定 "data"。無ければ自動作成）。
    fye_month : int | None
        決算期末月（未知の銘柄を単独指定するときの探索高速化用）。
    full_dividend_coverage : bool
        True なら、配当金総額が欠ける年度を埋める追加報告書も取得する（既定）。
        False なら基本の有報のみ（API呼び出しは最小だが、総額が取れる年度は減る）。
    zoom : bool
        True ならフォーカス銘柄の最新年度座標を中心に ±zoom_span の窓で描画し、
        出力ファイル名に ``_zoom`` を付ける（全体描画の成果物は上書きしない）。
    zoom_span : float
        ズーム窓の半幅（SGR・CS 軸とも同じ値）。
    """
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

    tables, names = {}, dict(STOCK_NAMES)
    for code in codes:
        try:
            table = load_or_fetch(code, datadir, force_update, get_client,
                                  fye_month=fye_month if code == focus_code else None,
                                  log=log,
                                  full_dividend_coverage=full_dividend_coverage)
        except PermissionError as exc:
            raise SystemExit(f"[中断] {exc}")
        except (LookupError, ConnectionError, RuntimeError) as exc:
            if code == focus_code:
                raise SystemExit(f"[中断] フォーカス銘柄 {code} を取得できません: {exc}")
            log(f"[{code}] 取得失敗のため除外します: {exc}")
            continue
        table = trim_to_primary_statements(table, code, log=log)
        if table.dropna(subset=["roe_pct", "doe_pct"]).empty:
            log(f"[{code}] ROE/DOE を算出できるデータが無いため除外します。")
            continue
        tables[code] = table
        if code not in names and "name" in table.columns and len(table):
            names[code] = str(table["name"].iloc[0])

    if focus_code not in tables:
        raise SystemExit(f"[中断] フォーカス銘柄 {focus_code} の有効なデータがありません。")

    view_limits, suffix = None, ""
    if zoom:
        view_limits = zoom_limits(tables, focus_code, zoom_span, log=log)
        if view_limits is not None:
            suffix = "_zoom"

    gif_path = html_path = None
    if make_gif:
        log("[描画] Matplotlib GIF")
        gif_path = render_gif(tables, names, focus_code,
                              outdir / f"moat_animation_{focus_code}{suffix}.gif",
                              steps=steps, hold_frames=hold_frames, fps=fps, dpi=dpi, log=log,
                              view_limits=view_limits)
        _display_in_notebook(gif_path)
    if make_html:
        log("[描画] Plotly インタラクティブHTML")
        html_path = build_plotly_html(tables, names, focus_code,
                                      outdir / f"moat_animation_{focus_code}{suffix}.html",
                                      include_plotlyjs=include_plotlyjs, log=log,
                                      view_limits=view_limits)
    return tables, gif_path, html_path


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="モート動的可視化（EDINET → 四則演算 → GIF / HTML）")
    parser.add_argument("--codes", default=None,
                        help="カンマ区切りの証券コード（省略時は図1の16銘柄）。--focus 省略時は"
                             "先頭銘柄がアニメーションのフォーカス（出力ファイル名・タイトル）になる")
    # 既定値は None とし、明示指定の有無を --zoom の判定に使う（実効的な既定は DEFAULT_FOCUS_CODE）
    parser.add_argument("--focus", default=None,
                        help=f"フォーカス銘柄の証券コード（既定：--codes の先頭、"
                             f"両方省略時は {DEFAULT_FOCUS_CODE}）")
    parser.add_argument("--force-update", action="store_true",
                        help="CSVキャッシュを無視して EDINET から再取得する")
    parser.add_argument("--datadir", default="data",
                        help="CSVキャッシュの保存・参照先フォルダ（既定：data。無ければ自動作成）")
    parser.add_argument("--outdir", default="output",
                        help="GIF / HTML の出力先フォルダ（既定：output。無ければ自動作成）")
    parser.add_argument("--api-key", default=None, help="EDINET APIキー")
    parser.add_argument("--fye-month", type=int, default=None, help="フォーカス銘柄の決算期末月")
    parser.add_argument("--minimal-reports", action="store_true",
                        help="基本の有報（直近・5年前・取得できれば10年前）のみ取得する（配当金総額が取れる年度は減る）")
    parser.add_argument("--no-gif", action="store_true", help="GIF出力を行わない")
    parser.add_argument("--no-html", action="store_true", help="HTML出力を行わない")
    parser.add_argument("--steps", type=int, default=8, help="1年あたりの補間フレーム数")
    parser.add_argument("--fps", type=int, default=20, help="GIFのフレームレート")
    parser.add_argument("--dpi", type=int, default=100, help="GIFの解像度（dpi）")
    parser.add_argument("--zoom", action="store_true",
                        help="--focus 銘柄の最新年度座標を中心にズーム描画する"
                             "（出力ファイル名に _zoom を付与）")
    parser.add_argument("--zoom-span", type=float, default=15.0,
                        help="ズーム窓の半幅（既定 15.0）。中心 ±span を SGR・CS 軸に適用")
    # Jupyter / Colab のカーネル引数（-f ...）を無視できるよう parse_known_args を使う
    args, _ = parser.parse_known_args(argv)
    codes = [c for c in args.codes.split(",") if c.strip()] if args.codes else None
    # フォーカス銘柄：--focus > --codes の先頭 > 既定（7011）の順に決める
    focus = args.focus or (codes[0] if codes else None)
    zoom = args.zoom
    if zoom and focus is None:
        print("[警告] --zoom には --focus <CODE>（または --codes）の指定が必要です。"
              "全体描画で実行します。")
        zoom = False
    run(codes=codes, focus_code=focus, force_update=args.force_update,
        outdir=args.outdir, datadir=args.datadir, api_key=args.api_key, fye_month=args.fye_month,
        make_gif=not args.no_gif, make_html=not args.no_html, steps=args.steps,
        fps=args.fps, dpi=args.dpi, full_dividend_coverage=not args.minimal_reports,
        zoom=zoom, zoom_span=args.zoom_span)


if __name__ == "__main__":
    main(sys.argv[1:])
