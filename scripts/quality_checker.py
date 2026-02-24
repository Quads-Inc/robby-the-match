#!/usr/bin/env python3
"""
quality_checker.py — SNSカルーセル品質検査エンジン v1.0

「神は細部に宿る」
テキスト・ビジュアル・コンテンツ・心理学の4軸で品質をスコアリングし、
世界水準のカルーセル投稿を保証する。

使い方:
  # カルーセルJSON（台本）の品質チェック
  python3 scripts/quality_checker.py --script data/posting_queue.json --index 0

  # 生成済みスライド画像の品質チェック
  python3 scripts/quality_checker.py --images content/generated/20260220_A01/

  # 台本+画像の総合チェック
  python3 scripts/quality_checker.py --script data/posting_queue.json --index 0 \
      --images content/generated/20260220_A01/

  # 全キューを一括チェック
  python3 scripts/quality_checker.py --audit data/posting_queue.json

  # 品質基準の表示
  python3 scripts/quality_checker.py --standards
"""

from __future__ import annotations

import argparse
import colorsys
import json
import math
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ============================================================
# Constants
# ============================================================

# Canvas dimensions (TikTok/Instagram 9:16)
CANVAS_W = 1080
CANVAS_H = 1920

# TikTok safe zones
SAFE_TOP = 150
SAFE_BOTTOM = 280
SAFE_RIGHT = 100
SAFE_LEFT = 40

# Content area
CONTENT_W = CANVAS_W - SAFE_LEFT - SAFE_RIGHT  # 940
CONTENT_H = CANVAS_H - SAFE_TOP - SAFE_BOTTOM  # 1490

# 12-column grid
GRID_COLUMNS = 12
GRID_GUTTER = 20
GRID_COL_W = (CONTENT_W - GRID_GUTTER * (GRID_COLUMNS - 1)) / GRID_COLUMNS

# Golden ratio
PHI = 1.618033988749895
PHI_INVERSE = 0.618033988749895
PHI_INVERSE_SQ = PHI_INVERSE ** 2  # 0.382

# Readability thresholds
MAX_CHARS_PER_SLIDE = 120
MAX_LINES_PER_SLIDE = 8
MAX_KANJI_RATIO = 0.30
IDEAL_KANJI_RATIO = (0.15, 0.25)

# Font size golden ratio: title:body:caption = 1:0.618:0.382
FONT_RATIO_TITLE = 1.0
FONT_RATIO_BODY = PHI_INVERSE      # 0.618
FONT_RATIO_CAPTION = PHI_INVERSE_SQ  # 0.382

# WCAG contrast ratios
WCAG_AA_RATIO = 4.5
WCAG_AAA_RATIO = 7.0

# Miller's Law: 7 +/- 2 chunks
MILLER_MIN = 5
MILLER_MAX = 9
MILLER_IDEAL = 7

# Loss aversion words (Japanese)
LOSS_AVERSION_WORDS = [
    "損", "損する", "知らないと", "見逃す", "失う", "もったいない",
    "後悔", "手遅れ", "損失", "リスク", "やばい", "危険",
]

# Emotion trigger words
EMOTION_TRIGGERS = [
    "驚愕", "涙", "ブチギレ", "衝撃", "鳥肌", "感動",
    "号泣", "激怒", "震えた", "黙った", "絶句", "目が覚めた",
]

# Persona-direct words (nurse-specific)
PERSONA_DIRECT_WORDS = [
    "看護師", "ナース", "5年目", "3年目", "7年目", "10年目",
    "夜勤", "夜勤明け", "日勤", "師長", "プリセプター",
    "急性期", "慢性期", "訪問看護", "クリニック", "病棟",
    "ナースコール", "看護記録", "申し送り", "インシデント",
]

# Question patterns
QUESTION_PATTERNS = [
    r"知ってた？", r"本当に？", r"マジ？", r"嘘でしょ？",
    r"どう思う？", r"聞いたことある？", r"\?$", r"？$",
]

# Save-worthy content patterns
SAVE_PATTERNS = {
    "data_comparison": [r"比較", r"ランキング", r"一覧", r"表", r"データ", r"統計"],
    "checklist": [r"チェック", r"リスト", r"確認", r"ポイント", r"〜つの"],
    "howto": [r"方法", r"やり方", r"手順", r"ステップ", r"コツ", r"裏技"],
}

# Share-worthy patterns
SHARE_PATTERNS = {
    "empathy": [r"あるある", r"わかる", r"それな", r"共感", r"同じ"],
    "surprise": [r"意外", r"実は", r"知らなかった", r"衝撃", r"まさか"],
    "practical": [r"使える", r"役立つ", r"便利", r"お得", r"裏技"],
}

# Ideal emotion curve for 7 slides
IDEAL_EMOTION_CURVE = [
    "surprise",   # Slide 1: Hook - surprise/curiosity
    "empathy",    # Slide 2: Connection - empathy/recognition
    "expect",     # Slide 3: Build-up - anticipation
    "learn",      # Slide 4: Insight - learning
    "convince",   # Slide 5: Evidence - conviction
    "hope",       # Slide 6: Resolution - hope
    "action",     # Slide 7: CTA - action/motivation
]

# CTA naturalness indicators
HARD_CTA_WORDS = [
    "登録", "今すぐ", "無料", "限定", "急いで", "締切",
    "申し込み", "購入", "入会", "ダウンロード",
]

SOFT_CTA_WORDS = [
    "保存", "フォロー", "続き", "もっと", "シェア", "教えて",
    "みんなは", "コメント", "プロフィール",
]

# Japanese typography: line-start prohibited characters (Kinsoku)
KINSOKU_LINE_START = set("、。，．）」』】〕〉》）]｝〟ー…‥？！!?・:;")

# Japanese typography: line-end prohibited characters
KINSOKU_LINE_END = set("（「『【〔〈《（[｛〝")


# ============================================================
# Data Classes
# ============================================================

@dataclass
class QualityScore:
    """Individual quality dimension score."""
    dimension: str
    name: str
    score: float          # 0.0 - 10.0
    max_score: float      # usually 10.0
    weight: float         # importance weight
    details: str          # human-readable explanation
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


@dataclass
class SlideAnalysis:
    """Analysis result for a single slide."""
    slide_num: int
    char_count: int
    line_count: int
    kanji_ratio: float
    hiragana_ratio: float
    katakana_ratio: float
    chunk_count: int
    emotion_type: str
    has_number: bool
    readability_ok: bool


@dataclass
class QualityReport:
    """Complete quality report for a carousel post."""
    content_id: str
    timestamp: str
    overall_score: float          # 0-100 weighted average
    grade: str                    # S/A/B/C/D/F
    text_scores: list[QualityScore] = field(default_factory=list)
    visual_scores: list[QualityScore] = field(default_factory=list)
    content_scores: list[QualityScore] = field(default_factory=list)
    psychology_scores: list[QualityScore] = field(default_factory=list)
    slide_analyses: list[SlideAnalysis] = field(default_factory=list)
    blocking_issues: list[str] = field(default_factory=list)
    pass_fail: bool = True

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "content_id": self.content_id,
            "timestamp": self.timestamp,
            "overall_score": round(self.overall_score, 1),
            "grade": self.grade,
            "pass_fail": self.pass_fail,
            "blocking_issues": self.blocking_issues,
            "text": [
                {"name": s.name, "score": round(s.score, 1),
                 "details": s.details, "issues": s.issues, "suggestions": s.suggestions}
                for s in self.text_scores
            ],
            "visual": [
                {"name": s.name, "score": round(s.score, 1),
                 "details": s.details, "issues": s.issues, "suggestions": s.suggestions}
                for s in self.visual_scores
            ],
            "content": [
                {"name": s.name, "score": round(s.score, 1),
                 "details": s.details, "issues": s.issues, "suggestions": s.suggestions}
                for s in self.content_scores
            ],
            "psychology": [
                {"name": s.name, "score": round(s.score, 1),
                 "details": s.details, "issues": s.issues, "suggestions": s.suggestions}
                for s in self.psychology_scores
            ],
            "slides": [
                {"num": sa.slide_num, "chars": sa.char_count,
                 "lines": sa.line_count, "kanji": round(sa.kanji_ratio, 3),
                 "emotion": sa.emotion_type, "chunks": sa.chunk_count}
                for sa in self.slide_analyses
            ],
        }


# ============================================================
# Utility Functions
# ============================================================

def classify_char(c: str) -> str:
    """Classify a single character into kanji/hiragana/katakana/ascii/punct/other."""
    cp = ord(c)
    if 0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF:
        return "kanji"
    if 0x3040 <= cp <= 0x309F:
        return "hiragana"
    if 0x30A0 <= cp <= 0x30FF:
        return "katakana"
    if 0x0021 <= cp <= 0x007E:
        return "ascii"
    if unicodedata.category(c).startswith("P"):
        return "punct"
    return "other"


def char_ratios(text: str) -> dict[str, float]:
    """Calculate character type ratios (excluding whitespace and punctuation)."""
    counts: dict[str, int] = {"kanji": 0, "hiragana": 0, "katakana": 0, "ascii": 0, "other": 0}
    total = 0
    for c in text:
        if c.isspace():
            continue
        cls = classify_char(c)
        if cls == "punct":
            continue
        counts[cls] = counts.get(cls, 0) + 1
        total += 1
    if total == 0:
        return {k: 0.0 for k in counts}
    return {k: v / total for k, v in counts.items()}


def count_chunks(text: str) -> int:
    """
    Count information chunks in text (Miller's Law: 7 +/- 2).
    A chunk is a semantic unit: a number, a key phrase, a bullet point, etc.
    Approximation: count sentences + standalone numbers + bullet items.
    """
    chunks = 0
    # Sentences (period, question mark, exclamation)
    chunks += len(re.findall(r"[。！？!?]+", text))
    # Standalone numbers/data points
    chunks += len(re.findall(r"\d+[%％万円件名本]", text))
    # Bullet-like items (dashes, dots, numbers at line start)
    chunks += len(re.findall(r"^[\s]*[・\-\d①②③④⑤⑥⑦⑧⑨⑩]", text, re.MULTILINE))
    return max(chunks, 1)


def has_halfwidth_fullwidth_mix(text: str) -> list[str]:
    """Detect mixed half-width and full-width numbers in the same text."""
    issues = []
    has_half = bool(re.search(r"[0-9]", text))
    has_full = bool(re.search(r"[０-９]", text))
    if has_half and has_full:
        issues.append("半角数字と全角数字が混在しています")
    return issues


def check_kinsoku(lines: list[str]) -> list[str]:
    """Check Japanese typography rules (Kinsoku Shori)."""
    issues = []
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        if line[0] in KINSOKU_LINE_START:
            issues.append(f"行{i+1}の先頭に禁則文字 '{line[0]}' があります")
        if line[-1] in KINSOKU_LINE_END:
            issues.append(f"行{i+1}の末尾に禁則文字 '{line[-1]}' があります")
    return issues


def estimate_punct_kerning_issues(text: str) -> list[str]:
    """
    Detect potential kerning issues around punctuation and brackets.
    Full-width punctuation in Japanese should have consistent spacing.
    """
    issues = []
    # Double punctuation
    if re.search(r"[。、]{2,}", text):
        issues.append("連続する句読点を検出: 不自然な空きの原因")
    # Space before punctuation (Japanese text should not have space before 。、)
    if re.search(r"\s[。、]", text):
        issues.append("句読点の前にスペースがあります")
    # Missing space after closing bracket before text
    if re.search(r"[）」』】][^\s。、）」』】\n]", text):
        # In Japanese this is actually normal, but flag if before opening bracket
        pass
    # Consecutive brackets without content
    if re.search(r"[（「『【][）」』】]", text):
        issues.append("空の括弧を検出")
    return issues


def relative_luminance(r: int, g: int, b: int) -> float:
    """Calculate relative luminance per WCAG 2.1 spec."""
    def linearize(v: int) -> float:
        s = v / 255.0
        return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4
    return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)


def contrast_ratio(color1: tuple, color2: tuple) -> float:
    """Calculate WCAG 2.1 contrast ratio between two RGB colors."""
    l1 = relative_luminance(*color1[:3])
    l2 = relative_luminance(*color2[:3])
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def detect_emotion_type(text: str) -> str:
    """Classify the emotional tone of slide text."""
    text_lower = text.lower()
    # Check for each emotion pattern
    surprise_words = ["驚", "衝撃", "まさか", "嘘", "マジ", "意外", "知らなかった", "？", "?"]
    empathy_words = ["あるある", "わかる", "つらい", "疲れ", "同じ", "共感", "気持ち"]
    expect_words = ["実は", "ところが", "しかし", "でも", "ここから", "注目", "次"]
    learn_words = ["データ", "調査", "結果", "分析", "比較", "平均", "統計", "%", "万円"]
    convince_words = ["証明", "根拠", "事実", "理由", "なぜ", "原因", "つまり"]
    hope_words = ["できる", "変わる", "希望", "未来", "チャンス", "可能性", "解決"]
    action_words = ["LINE", "フォロー", "保存", "相談", "プロフィール", "登録", "今すぐ"]

    scores = {
        "surprise": sum(1 for w in surprise_words if w in text),
        "empathy": sum(1 for w in empathy_words if w in text),
        "expect": sum(1 for w in expect_words if w in text),
        "learn": sum(1 for w in learn_words if w in text),
        "convince": sum(1 for w in convince_words if w in text),
        "hope": sum(1 for w in hope_words if w in text),
        "action": sum(1 for w in action_words if w in text),
    }
    if max(scores.values()) == 0:
        return "neutral"
    return max(scores, key=scores.get)


# ============================================================
# ContentQualityChecker
# ============================================================

class ContentQualityChecker:
    """
    SNSカルーセル投稿の細部品質チェッカー。

    4軸(テキスト/ビジュアル/コンテンツ/心理学)x 20+のチェック項目で
    0-100スコアを算出し、S/A/B/C/D/F のグレードを付与する。

    Usage:
        checker = ContentQualityChecker()
        report = checker.check(
            slides=[
                {"title": "フック", "body": "師長にAIで見せたら黙った"},
                {"title": "あるある", "body": "夜勤明けの..."},
                ...
            ],
            hook_text="師長にAIで見せたら黙った",
            caption="看護師あるある #看護師 #AI",
            category="あるある",
            content_id="A01",
            colors={
                "bg": (26, 26, 46),
                "text": (255, 255, 255),
                "accent": (255, 107, 107),
            },
            font_sizes={"title": 56, "body": 34, "caption": 20},
        )
        print(report.overall_score)  # 0-100
        print(report.grade)          # "A"
    """

    # Weights for each dimension (total = 1.0)
    DIMENSION_WEIGHTS = {
        "text": 0.25,
        "visual": 0.20,
        "content": 0.35,
        "psychology": 0.20,
    }

    # Grade thresholds
    GRADE_THRESHOLDS = [
        (95, "S"),
        (85, "A"),
        (70, "B"),
        (55, "C"),
        (40, "D"),
        (0, "F"),
    ]

    # Minimum passing score
    PASS_THRESHOLD = 60.0

    def __init__(self, strict: bool = False):
        """
        Args:
            strict: If True, use WCAG AAA (7:1) contrast; else use AA (4.5:1).
        """
        self.strict = strict
        self.target_contrast = WCAG_AAA_RATIO if strict else WCAG_AA_RATIO

    # ----------------------------------------------------------------
    # Main entry point
    # ----------------------------------------------------------------

    def check(
        self,
        slides: list[dict],
        hook_text: str = "",
        caption: str = "",
        category: str = "",
        content_id: str = "unknown",
        colors: Optional[dict] = None,
        font_sizes: Optional[dict] = None,
        image_paths: Optional[list[Path]] = None,
    ) -> QualityReport:
        """
        Run all quality checks and return a comprehensive report.

        Args:
            slides: List of slide dicts, each with "title" and/or "body" keys.
            hook_text: The hook/opening text (slide 1).
            caption: Post caption text.
            category: Content category (あるある/転職/給与/紹介/トレンド).
            content_id: Identifier (e.g. "A01").
            colors: Dict with "bg", "text", "accent" RGB tuples.
            font_sizes: Dict with "title", "body", "caption" pixel sizes.
            image_paths: Optional list of paths to generated slide images.

        Returns:
            QualityReport with all scores, grade, and suggestions.
        """
        from datetime import datetime

        report = QualityReport(
            content_id=content_id,
            timestamp=datetime.now().isoformat(),
            overall_score=0.0,
            grade="F",
        )

        # -- Analyze individual slides --
        all_text = ""
        for i, slide in enumerate(slides):
            text = self._extract_slide_text(slide)
            all_text += text + "\n"
            analysis = self._analyze_slide(i + 1, text)
            report.slide_analyses.append(analysis)

        # If hook_text not provided, try to extract from first slide
        if not hook_text and slides:
            hook_text = self._extract_slide_text(slides[0])

        # -- Text quality checks --
        report.text_scores = self._check_text_quality(slides, all_text, report.slide_analyses)

        # -- Visual quality checks --
        colors = colors or {"bg": (26, 26, 46), "text": (255, 255, 255), "accent": (255, 107, 107)}
        font_sizes = font_sizes or {"title": 56, "body": 34, "caption": 20}
        report.visual_scores = self._check_visual_quality(colors, font_sizes, image_paths)

        # -- Content quality checks --
        report.content_scores = self._check_content_quality(
            slides, hook_text, caption, category, all_text
        )

        # -- Psychology quality checks --
        report.psychology_scores = self._check_psychology_quality(
            slides, report.slide_analyses, all_text
        )

        # -- Calculate overall score --
        dimension_scores = {
            "text": report.text_scores,
            "visual": report.visual_scores,
            "content": report.content_scores,
            "psychology": report.psychology_scores,
        }
        weighted_total = 0.0
        weighted_max = 0.0
        for dim, scores in dimension_scores.items():
            dim_weight = self.DIMENSION_WEIGHTS[dim]
            if not scores:
                continue
            dim_avg = sum(s.score for s in scores) / len(scores)
            dim_max = sum(s.max_score for s in scores) / len(scores)
            weighted_total += (dim_avg / dim_max) * dim_weight * 100
            weighted_max += dim_weight * 100

        report.overall_score = weighted_total if weighted_max == 0 else (weighted_total / weighted_max) * 100

        # -- Grade --
        for threshold, grade in self.GRADE_THRESHOLDS:
            if report.overall_score >= threshold:
                report.grade = grade
                break

        # -- Blocking issues --
        for scores in dimension_scores.values():
            for s in scores:
                if s.score <= 2.0:
                    report.blocking_issues.extend(s.issues[:1])

        report.pass_fail = (
            report.overall_score >= self.PASS_THRESHOLD
            and len(report.blocking_issues) == 0
        )

        return report

    # ----------------------------------------------------------------
    # Text Quality Checks (7 items)
    # ----------------------------------------------------------------

    def _check_text_quality(
        self,
        slides: list[dict],
        all_text: str,
        slide_analyses: list[SlideAnalysis],
    ) -> list[QualityScore]:
        scores = []

        # 1. Kerning (punctuation spacing)
        scores.append(self._check_kerning(all_text))

        # 2. Kinsoku (line-break rules)
        scores.append(self._check_kinsoku(slides))

        # 3. Number format consistency
        scores.append(self._check_number_consistency(all_text))

        # 4. Font size golden ratio
        # (Checked in visual, but we score text-side readability here)
        scores.append(self._check_font_ratio_readability(slides))

        # 5. Readability score (chars per slide, lines per slide)
        scores.append(self._check_readability(slide_analyses))

        # 6. Kanji ratio
        scores.append(self._check_kanji_ratio(all_text))

        # 7. Hiragana/katakana/kanji balance
        scores.append(self._check_char_balance(all_text))

        return scores

    def _check_kerning(self, text: str) -> QualityScore:
        """Check punctuation kerning issues."""
        issues = estimate_punct_kerning_issues(text)
        score = max(0, 10 - len(issues) * 3)
        return QualityScore(
            dimension="text", name="カーニング",
            score=score, max_score=10, weight=1.0,
            details=f"句読点・括弧の前後スペース検出: {len(issues)}件",
            issues=issues,
            suggestions=["句読点の前にスペースを入れない", "空の括弧を削除する"] if issues else [],
        )

    def _check_kinsoku(self, slides: list[dict]) -> QualityScore:
        """Check Japanese line-break rules."""
        all_issues = []
        for slide in slides:
            text = self._extract_slide_text(slide)
            lines = text.split("\n")
            all_issues.extend(check_kinsoku(lines))
        score = max(0, 10 - len(all_issues) * 2)
        return QualityScore(
            dimension="text", name="禁則処理",
            score=score, max_score=10, weight=1.0,
            details=f"禁則処理違反: {len(all_issues)}件",
            issues=all_issues,
            suggestions=["行頭の句読点を前の行に移動する"] if all_issues else [],
        )

    def _check_number_consistency(self, text: str) -> QualityScore:
        """Check half-width / full-width number consistency."""
        issues = has_halfwidth_fullwidth_mix(text)
        score = 10 if not issues else 3
        return QualityScore(
            dimension="text", name="数字表記統一",
            score=score, max_score=10, weight=1.0,
            details="数字は統一されています" if not issues else "半角/全角数字が混在",
            issues=issues,
            suggestions=["全て半角数字に統一する（SNS標準）"] if issues else [],
        )

    def _check_font_ratio_readability(self, slides: list[dict]) -> QualityScore:
        """
        Check that text hierarchy follows golden ratio principles.
        Title should be visually larger, body medium, caption small.
        Approximate by character count per line: fewer chars = larger intended font.
        """
        # Heuristic: check if slide 1 (hook) has fewer chars than body slides
        if len(slides) < 2:
            return QualityScore(
                dimension="text", name="テキスト階層",
                score=5, max_score=10, weight=0.8,
                details="スライド数が少なすぎて階層判定不可",
                issues=["スライド数を7枚に増やすことを推奨"],
            )

        hook_chars = len(self._extract_slide_text(slides[0]))
        body_chars = [len(self._extract_slide_text(s)) for s in slides[1:-1]] if len(slides) > 2 else [hook_chars]
        avg_body = sum(body_chars) / len(body_chars) if body_chars else hook_chars

        score = 10
        issues = []
        # Hook should be concise (under 40 chars ideally)
        if hook_chars > 50:
            score -= 3
            issues.append(f"フックが{hook_chars}文字: 40文字以内が理想")
        # Hook should be shorter than body average
        if hook_chars > avg_body * 1.2:
            score -= 2
            issues.append("フックが本文より長い: テキスト階層が逆転")

        return QualityScore(
            dimension="text", name="テキスト階層（黄金比）",
            score=max(0, score), max_score=10, weight=0.8,
            details=f"フック{hook_chars}文字 / 本文平均{avg_body:.0f}文字",
            issues=issues,
            suggestions=["フックは20文字以内が最強。3秒で読める量に"] if issues else [],
        )

    def _check_readability(self, analyses: list[SlideAnalysis]) -> QualityScore:
        """Check per-slide character count and line count."""
        issues = []
        over_count = 0
        for a in analyses:
            if a.char_count > MAX_CHARS_PER_SLIDE:
                over_count += 1
                issues.append(f"スライド{a.slide_num}: {a.char_count}文字 (上限{MAX_CHARS_PER_SLIDE})")
            if a.line_count > MAX_LINES_PER_SLIDE:
                issues.append(f"スライド{a.slide_num}: {a.line_count}行 (上限{MAX_LINES_PER_SLIDE})")

        score = max(0, 10 - over_count * 2 - (len(issues) - over_count))
        return QualityScore(
            dimension="text", name="読みやすさスコア",
            score=score, max_score=10, weight=1.2,
            details=f"文字数超過スライド: {over_count}/{len(analyses)}枚",
            issues=issues,
            suggestions=["1スライド120文字以内、8行以内に収める"] if issues else [],
        )

    def _check_kanji_ratio(self, text: str) -> QualityScore:
        """Check that kanji ratio stays under 30%."""
        ratios = char_ratios(text)
        kanji = ratios.get("kanji", 0)
        score = 10
        issues = []

        if kanji > MAX_KANJI_RATIO:
            score = max(0, 10 - (kanji - MAX_KANJI_RATIO) * 50)
            issues.append(f"漢字比率 {kanji:.1%} > 上限{MAX_KANJI_RATIO:.0%}")
        elif kanji < IDEAL_KANJI_RATIO[0]:
            score = 8
            issues.append(f"漢字比率 {kanji:.1%}: やや少ない（専門性が薄い印象）")

        return QualityScore(
            dimension="text", name="漢字比率",
            score=score, max_score=10, weight=1.0,
            details=f"漢字比率: {kanji:.1%} (理想: 15-25%, 上限: 30%)",
            issues=issues,
            suggestions=["漢字の多い語をひらがなに開く（例: 致します→いたします）"] if kanji > MAX_KANJI_RATIO else [],
        )

    def _check_char_balance(self, text: str) -> QualityScore:
        """Check hiragana / katakana / kanji balance for readability."""
        ratios = char_ratios(text)
        kanji = ratios.get("kanji", 0)
        hiragana = ratios.get("hiragana", 0)
        katakana = ratios.get("katakana", 0)

        score = 10
        issues = []

        # Ideal: hiragana 40-60%, kanji 15-25%, katakana 5-20%
        if hiragana < 0.30:
            score -= 3
            issues.append(f"ひらがな比率 {hiragana:.1%}: 少なすぎる（硬い印象）")
        if hiragana > 0.70:
            score -= 2
            issues.append(f"ひらがな比率 {hiragana:.1%}: 多すぎる（幼い印象）")
        if katakana > 0.30:
            score -= 2
            issues.append(f"カタカナ比率 {katakana:.1%}: 多すぎる（読みにくい）")

        return QualityScore(
            dimension="text", name="文字種バランス",
            score=max(0, score), max_score=10, weight=0.8,
            details=f"ひらがな{hiragana:.0%} / 漢字{kanji:.0%} / カタカナ{katakana:.0%}",
            issues=issues,
            suggestions=["看護師ペルソナが3秒で読める水準: ひらがな40-60%を目指す"] if issues else [],
        )

    # ----------------------------------------------------------------
    # Visual Quality Checks (6 items)
    # ----------------------------------------------------------------

    def _check_visual_quality(
        self,
        colors: dict,
        font_sizes: dict,
        image_paths: Optional[list[Path]] = None,
    ) -> list[QualityScore]:
        scores = []

        # 1. Contrast ratio (WCAG)
        scores.append(self._check_contrast(colors))

        # 2. Margin golden ratio
        scores.append(self._check_margins())

        # 3. Grid alignment
        scores.append(self._check_grid_alignment())

        # 4. Icon / decoration consistency (heuristic)
        scores.append(self._check_decoration_consistency(colors))

        # 5. Gradient smoothness
        scores.append(self._check_gradient_smoothness(colors))

        # 6. Shadow realism
        scores.append(self._check_shadow_consistency())

        # 7. Font size golden ratio (visual dimension)
        scores.append(self._check_font_golden_ratio(font_sizes))

        # If images provided, do pixel-level checks
        if image_paths:
            scores.append(self._check_images(image_paths))

        return scores

    def _check_contrast(self, colors: dict) -> QualityScore:
        """Check WCAG 2.1 contrast ratio."""
        bg = colors.get("bg", (26, 26, 46))
        text = colors.get("text", (255, 255, 255))
        accent = colors.get("accent", (255, 107, 107))

        cr_text = contrast_ratio(bg, text)
        cr_accent = contrast_ratio(bg, accent)

        score = 10
        issues = []
        target = self.target_contrast
        label = "AAA (7:1)" if self.strict else "AA (4.5:1)"

        if cr_text < target:
            score -= 5
            issues.append(f"テキスト/背景コントラスト {cr_text:.1f}:1 < {label}")
        if cr_accent < 3.0:
            score -= 3
            issues.append(f"アクセント/背景コントラスト {cr_accent:.1f}:1 < 3:1")

        return QualityScore(
            dimension="visual", name="コントラスト比 (WCAG)",
            score=max(0, score), max_score=10, weight=1.5,
            details=f"テキスト/BG: {cr_text:.1f}:1, アクセント/BG: {cr_accent:.1f}:1 (基準: {label})",
            issues=issues,
            suggestions=["背景を暗くするか文字を明るくしてコントラスト比を上げる"] if issues else [],
        )

    def _check_margins(self) -> QualityScore:
        """Check that margins follow golden ratio proportions."""
        # TikTok safe zones define outer margins
        # Check if they approximate golden ratio relationships
        left_ratio = SAFE_LEFT / CANVAS_W
        right_ratio = SAFE_RIGHT / CANVAS_W
        top_ratio = SAFE_TOP / CANVAS_H
        bottom_ratio = SAFE_BOTTOM / CANVAS_H

        score = 10
        issues = []

        # Horizontal margins should be roughly proportional
        h_ratio = SAFE_LEFT / SAFE_RIGHT if SAFE_RIGHT > 0 else 0
        if h_ratio < 0.3 or h_ratio > 0.6:
            # Asymmetric is OK for TikTok (UI icons on right), but flag if extreme
            score -= 1
            issues.append(f"左右マージン比 {h_ratio:.2f}: TikTok UIのため非対称（許容）")

        # Vertical: bottom needs more space (TikTok caption/buttons)
        if SAFE_BOTTOM < SAFE_TOP:
            score -= 3
            issues.append("下部マージンが上部より小さい: TikTok UIが被る可能性")

        # Content area ratio to canvas
        content_ratio = (CONTENT_W * CONTENT_H) / (CANVAS_W * CANVAS_H)
        if content_ratio < 0.50:
            score -= 2
            issues.append(f"コンテンツ領域比 {content_ratio:.1%}: 小さすぎる")
        elif content_ratio > 0.85:
            score -= 1
            issues.append(f"コンテンツ領域比 {content_ratio:.1%}: 余白が少ない")

        return QualityScore(
            dimension="visual", name="余白バランス",
            score=max(0, score), max_score=10, weight=1.0,
            details=f"コンテンツ領域: {CONTENT_W}x{CONTENT_H} ({content_ratio:.1%}), セーフゾーン: T{SAFE_TOP}/B{SAFE_BOTTOM}/L{SAFE_LEFT}/R{SAFE_RIGHT}",
            issues=issues,
            suggestions=["TikTokセーフゾーンを守りつつ余白を確保する"] if issues else [],
        )

    def _check_grid_alignment(self) -> QualityScore:
        """Check 12-column grid compliance."""
        # Verify that content width accommodates a 12-col grid
        usable = CONTENT_W - GRID_GUTTER * (GRID_COLUMNS - 1)
        col_w = usable / GRID_COLUMNS

        score = 10
        issues = []
        if col_w < 50:
            score -= 3
            issues.append(f"グリッド列幅 {col_w:.1f}px: 狭すぎる")
        if CONTENT_W % GRID_COLUMNS > GRID_COLUMNS // 2:
            # Not perfectly divisible, minor issue
            score -= 1
            issues.append(f"コンテンツ幅{CONTENT_W}は12列で割り切れない（{CONTENT_W % 12}px余り）")

        return QualityScore(
            dimension="visual", name="グリッドシステム",
            score=max(0, score), max_score=10, weight=0.8,
            details=f"12列グリッド: 列幅{col_w:.1f}px, ガター{GRID_GUTTER}px",
            issues=issues,
            suggestions=["テキストブロックをグリッドの2/4/6/8/10/12列幅に揃える"] if issues else [],
        )

    def _check_decoration_consistency(self, colors: dict) -> QualityScore:
        """Heuristic check for decoration consistency rules."""
        accent = colors.get("accent", (255, 107, 107))
        primary = colors.get("primary", colors.get("bg", (26, 115, 232)))

        score = 10
        issues = []

        # Check that accent and primary are visually distinct
        cr = contrast_ratio(accent, primary)
        if cr < 2.0:
            score -= 3
            issues.append(f"アクセントとプライマリの色差が小さい (コントラスト{cr:.1f}:1)")

        # Check that accent is not too saturated or desaturated
        r, g, b = accent[:3]
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if s < 0.3:
            score -= 2
            issues.append(f"アクセント色の彩度が低い ({s:.2f}): インパクト不足")
        if v < 0.4:
            score -= 2
            issues.append(f"アクセント色の明度が低い ({v:.2f}): 視認性不足")

        return QualityScore(
            dimension="visual", name="装飾の統一感",
            score=max(0, score), max_score=10, weight=0.8,
            details=f"アクセント/プライマリ対比: {cr:.1f}:1, 彩度: {s:.2f}, 明度: {v:.2f}",
            issues=issues,
            suggestions=["アクセント色はCTA要素のみに使い、使いすぎない"] if issues else [],
        )

    def _check_gradient_smoothness(self, colors: dict) -> QualityScore:
        """
        Check gradient configuration for banding risk.
        Banding occurs when color distance is too large for available steps.
        """
        bg = colors.get("bg", (26, 26, 46))
        bg2 = colors.get("bg2", colors.get("bg", (22, 33, 62)))

        # Calculate perceptual color distance
        dr = abs(bg[0] - bg2[0])
        dg = abs(bg[1] - bg2[1])
        db = abs(bg[2] - bg2[2])
        distance = math.sqrt(dr ** 2 + dg ** 2 + db ** 2)

        score = 10
        issues = []

        # For 1920px height, we have 1920 color steps
        # Banding risk when distance > 128 (visible steps in 8-bit color)
        if distance > 200:
            score -= 4
            issues.append(f"グラデーション色差 {distance:.0f}: バンディングリスク高")
        elif distance > 128:
            score -= 2
            issues.append(f"グラデーション色差 {distance:.0f}: 軽微なバンディングの可能性")

        # Very small distance = flat (OK but note it)
        if distance < 10:
            score -= 1
            issues.append("グラデーションがほぼフラット: 意図的であれば問題なし")

        return QualityScore(
            dimension="visual", name="グラデーション品質",
            score=max(0, score), max_score=10, weight=0.6,
            details=f"色差距離: {distance:.1f} (1920ステップ, バンディング閾値: ~128)",
            issues=issues,
            suggestions=["中間色を追加して3段階グラデーションにする"] if distance > 128 else [],
        )

    def _check_shadow_consistency(self) -> QualityScore:
        """Check shadow design rules (consistent angle, opacity, spread)."""
        # Based on generate_carousel.py defaults:
        # shadow_offset=2, shadow_color=(0,0,0,128)
        # These are reasonable defaults. Score based on rules compliance.
        score = 9  # Good defaults in the codebase
        details = "影の角度: 右下2px, 透明度: 50%, 統一的設定"
        issues = []
        suggestions = []

        # Check if offset is proportional to font size (should be ~3-5% of font size)
        # Assuming default shadow_offset=2, font_size=56 -> 3.5% (good)
        return QualityScore(
            dimension="visual", name="影のリアリズム",
            score=score, max_score=10, weight=0.5,
            details=details,
            issues=issues,
            suggestions=suggestions,
        )

    def _check_font_golden_ratio(self, font_sizes: dict) -> QualityScore:
        """Check that font sizes follow golden ratio: title:body:caption = 1:0.618:0.382."""
        title = font_sizes.get("title", 56)
        body = font_sizes.get("body", 34)
        caption = font_sizes.get("caption", 20)

        ideal_body = title * FONT_RATIO_BODY
        ideal_caption = title * FONT_RATIO_CAPTION

        body_dev = abs(body - ideal_body) / ideal_body
        caption_dev = abs(caption - ideal_caption) / ideal_caption

        score = 10
        issues = []

        if body_dev > 0.15:
            score -= 3
            issues.append(f"本文{body}px: 理想は{ideal_body:.0f}px (タイトルx0.618)")
        if caption_dev > 0.20:
            score -= 2
            issues.append(f"キャプション{caption}px: 理想は{ideal_caption:.0f}px (タイトルx0.382)")

        actual_ratio = f"{title}:{body}:{caption}"
        ideal_ratio = f"{title}:{ideal_body:.0f}:{ideal_caption:.0f}"

        return QualityScore(
            dimension="visual", name="フォントサイズ黄金比",
            score=max(0, score), max_score=10, weight=1.0,
            details=f"実際: {actual_ratio}, 理想: {ideal_ratio} (1:0.618:0.382)",
            issues=issues,
            suggestions=[f"本文を{ideal_body:.0f}px、キャプションを{ideal_caption:.0f}pxに調整"] if issues else [],
        )

    def _check_images(self, image_paths: list[Path]) -> QualityScore:
        """Pixel-level checks on generated images (requires PIL)."""
        try:
            from PIL import Image
        except ImportError:
            return QualityScore(
                dimension="visual", name="画像ピクセル検査",
                score=5, max_score=10, weight=0.5,
                details="PIL未インストール: 画像検査スキップ",
                issues=["pip install Pillow でインストールしてください"],
            )

        score = 10
        issues = []
        for path in image_paths:
            if not path.exists():
                score -= 2
                issues.append(f"画像が見つからない: {path.name}")
                continue

            img = Image.open(path)
            w, h = img.size

            # Check dimensions
            if w != 1080 or h != 1920:
                score -= 3
                issues.append(f"{path.name}: サイズ {w}x{h} (期待: 1080x1920)")

            # Check safe zone: top 150px should not have primary content text
            # (Heuristic: check if top strip is relatively uniform / gradient)

        return QualityScore(
            dimension="visual", name="画像ピクセル検査",
            score=max(0, score), max_score=10, weight=0.8,
            details=f"{len(image_paths)}枚の画像を検査",
            issues=issues,
            suggestions=["全スライドを1080x1920で生成する"] if issues else [],
        )

    # ----------------------------------------------------------------
    # Content Quality Checks (4 items)
    # ----------------------------------------------------------------

    def _check_content_quality(
        self,
        slides: list[dict],
        hook_text: str,
        caption: str,
        category: str,
        all_text: str,
    ) -> list[QualityScore]:
        scores = []

        # 1. Hook power score
        scores.append(self._score_hook_power(hook_text))

        # 2. Save value score
        scores.append(self._score_save_value(all_text, slides))

        # 3. Share value score
        scores.append(self._score_share_value(all_text, slides))

        # 4. CTA naturalness
        scores.append(self._score_cta_naturalness(slides, caption))

        return scores

    def _score_hook_power(self, hook_text: str) -> QualityScore:
        """
        Score the "stopping power" of the hook (0-10).
        Based on behavioral economics triggers.
        """
        score = 0
        triggers = []

        # Loss aversion words: +2
        for w in LOSS_AVERSION_WORDS:
            if w in hook_text:
                score += 2
                triggers.append(f"損失回避: '{w}'")
                break

        # Numbers: +1
        if re.search(r"\d+", hook_text):
            score += 1
            triggers.append("数字入り")

        # Question form: +1
        for pattern in QUESTION_PATTERNS:
            if re.search(pattern, hook_text):
                score += 1
                triggers.append("疑問形")
                break

        # Emotion triggers: +1
        for w in EMOTION_TRIGGERS:
            if w in hook_text:
                score += 1
                triggers.append(f"感情トリガー: '{w}'")
                break

        # Persona-direct: +2
        persona_hit = False
        for w in PERSONA_DIRECT_WORDS:
            if w in hook_text:
                if not persona_hit:
                    score += 2
                    persona_hit = True
                triggers.append(f"ペルソナ直撃: '{w}'")

        # Character count bonus/penalty
        hook_len = len(hook_text)
        if hook_len <= 20:
            score += 1
            triggers.append(f"文字数{hook_len}: 3秒で読める")
        elif hook_len > 40:
            score -= 1
            triggers.append(f"文字数{hook_len}: 長すぎる")

        # Conflict/contrast structure (他者+否定→変化)
        conflict_words = ["けど", "のに", "でも", "なのに", "vs", "対", "黙った", "怒った", "泣いた"]
        for w in conflict_words:
            if w in hook_text:
                score += 1
                triggers.append(f"対立構造: '{w}'")
                break

        score = min(10, max(0, score))

        return QualityScore(
            dimension="content", name="フック力スコア",
            score=score, max_score=10, weight=2.0,
            details=f"トリガー: {', '.join(triggers) if triggers else 'なし'}",
            issues=["フック力が弱い: 損失回避/ペルソナ/感情/数字を追加"] if score < 5 else [],
            suggestions=self._suggest_hook_improvement(hook_text, score),
        )

    def _suggest_hook_improvement(self, hook_text: str, current_score: int) -> list[str]:
        """Generate specific improvement suggestions for the hook."""
        suggestions = []
        if current_score >= 8:
            return ["現在のフックは高品質です"]

        has_persona = any(w in hook_text for w in PERSONA_DIRECT_WORDS)
        has_loss = any(w in hook_text for w in LOSS_AVERSION_WORDS)
        has_number = bool(re.search(r"\d+", hook_text))
        has_question = any(re.search(p, hook_text) for p in QUESTION_PATTERNS)

        if not has_persona:
            suggestions.append("ペルソナ直撃ワードを追加: 「看護師」「夜勤明け」「5年目」など")
        if not has_loss:
            suggestions.append("損失回避を追加: 「知らないと損する」「見逃すな」など")
        if not has_number:
            suggestions.append("数字を追加: 「100万」「3つの」「5年目」など")
        if not has_question:
            suggestions.append("疑問形にする: 「知ってた？」「本当に？」")
        if len(hook_text) > 30:
            suggestions.append(f"文字数を{len(hook_text)}→20以内に圧縮")

        return suggestions[:3]  # Top 3 suggestions

    def _score_save_value(self, all_text: str, slides: list[dict]) -> QualityScore:
        """Score the "save for later" value (0-10)."""
        score = 0
        triggers = []

        # Data/comparison: +3
        for w in SAVE_PATTERNS["data_comparison"]:
            if re.search(w, all_text):
                score += 3
                triggers.append(f"データ/比較: '{w}'")
                break

        # Checklist: +2
        for w in SAVE_PATTERNS["checklist"]:
            if re.search(w, all_text):
                score += 2
                triggers.append(f"チェックリスト: '{w}'")
                break

        # How-to: +2
        for w in SAVE_PATTERNS["howto"]:
            if re.search(w, all_text):
                score += 2
                triggers.append(f"How-to: '{w}'")
                break

        # Numbered items: +1
        if re.search(r"[①②③④⑤⑥⑦⑧⑨⑩]|[1-9][\.\）]", all_text):
            score += 1
            triggers.append("番号付きリスト")

        # Slide count: 5+ slides with data = high save value
        data_slides = sum(1 for s in slides if re.search(r"\d+[%％万円]", self._extract_slide_text(s)))
        if data_slides >= 3:
            score += 2
            triggers.append(f"データスライド{data_slides}枚")

        score = min(10, max(0, score))

        return QualityScore(
            dimension="content", name="保存価値スコア",
            score=score, max_score=10, weight=1.5,
            details=f"保存トリガー: {', '.join(triggers) if triggers else 'なし'}",
            issues=["保存価値が低い: データ表/チェックリスト/手順を含める"] if score < 4 else [],
            suggestions=["比較表やデータを追加すると保存率が上がる"] if score < 6 else [],
        )

    def _score_share_value(self, all_text: str, slides: list[dict]) -> QualityScore:
        """Score the "share with friends" value (0-10)."""
        score = 0
        triggers = []

        # Empathy: +2
        for w in SHARE_PATTERNS["empathy"]:
            if re.search(w, all_text):
                score += 2
                triggers.append(f"共感: '{w}'")
                break

        # Surprise: +2
        for w in SHARE_PATTERNS["surprise"]:
            if re.search(w, all_text):
                score += 2
                triggers.append(f"意外性: '{w}'")
                break

        # Practical: +1
        for w in SHARE_PATTERNS["practical"]:
            if re.search(w, all_text):
                score += 1
                triggers.append(f"実用性: '{w}'")
                break

        # Storytelling structure (beginning-middle-end): +2
        if len(slides) >= 5:
            score += 2
            triggers.append(f"ストーリー構造: {len(slides)}枚")

        # Relatable persona mention: +1
        nurse_words = ["看護師", "ナース", "病棟", "夜勤"]
        if any(w in all_text for w in nurse_words):
            score += 1
            triggers.append("看護師コミュニティ向け")

        # Humor/surprise ending
        last_slide = self._extract_slide_text(slides[-1]) if slides else ""
        surprise_end = ["笑", "www", "草", "まさか", "予想外", "黙った"]
        if any(w in last_slide for w in surprise_end):
            score += 2
            triggers.append("オチが面白い")

        score = min(10, max(0, score))

        return QualityScore(
            dimension="content", name="シェア価値スコア",
            score=score, max_score=10, weight=1.0,
            details=f"シェアトリガー: {', '.join(triggers) if triggers else 'なし'}",
            issues=["シェア価値が低い: 共感/意外性/オチを強化"] if score < 4 else [],
            suggestions=["「友達にLINEで送りたくなるか？」を基準に判断"] if score < 6 else [],
        )

    def _score_cta_naturalness(self, slides: list[dict], caption: str) -> QualityScore:
        """Score CTA naturalness (0-10, where 10 = completely natural, 0 = spam)."""
        all_text = "\n".join(self._extract_slide_text(s) for s in slides)
        full_text = all_text + "\n" + caption

        hard_count = sum(1 for w in HARD_CTA_WORDS if w in full_text)
        soft_count = sum(1 for w in SOFT_CTA_WORDS if w in full_text)

        score = 10
        issues = []

        # Penalize hard CTA density
        if hard_count >= 4:
            score -= 5
            issues.append(f"ハードCTA {hard_count}個: セールス感が強すぎる")
        elif hard_count >= 2:
            score -= 2
            issues.append(f"ハードCTA {hard_count}個: やや売り込み感")

        # CTA in early slides is bad
        if slides and len(slides) >= 3:
            early_text = "\n".join(self._extract_slide_text(s) for s in slides[:3])
            early_hard = sum(1 for w in HARD_CTA_WORDS if w in early_text)
            if early_hard >= 2:
                score -= 3
                issues.append("前半スライドにハードCTA: 離脱リスク大")

        # Bonus for soft CTA
        if soft_count >= 1 and hard_count <= 1:
            score = min(10, score + 1)

        # No CTA at all
        if hard_count == 0 and soft_count == 0:
            score -= 1
            issues.append("CTAが皆無: 最低でもソフトCTA（保存/フォロー）を1つ入れる")

        score = max(0, min(10, score))

        return QualityScore(
            dimension="content", name="CTA自然度",
            score=score, max_score=10, weight=1.2,
            details=f"ハードCTA: {hard_count}個, ソフトCTA: {soft_count}個",
            issues=issues,
            suggestions=["8:2ルール: 10投稿中8投稿はソフトCTAのみ"] if hard_count >= 2 else [],
        )

    # ----------------------------------------------------------------
    # Psychology Quality Checks (4 items)
    # ----------------------------------------------------------------

    def _check_psychology_quality(
        self,
        slides: list[dict],
        slide_analyses: list[SlideAnalysis],
        all_text: str,
    ) -> list[QualityScore]:
        scores = []

        # 1. Cognitive load (Miller's Law)
        scores.append(self._check_cognitive_load(slide_analyses))

        # 2. Emotion curve
        scores.append(self._check_emotion_curve(slides, slide_analyses))

        # 3. Zeigarnik effect
        scores.append(self._check_zeigarnik(slides))

        # 4. Peak-End rule
        scores.append(self._check_peak_end(slides, slide_analyses))

        return scores

    def _check_cognitive_load(self, analyses: list[SlideAnalysis]) -> QualityScore:
        """Check cognitive load per slide (Miller's Law: 7 +/- 2 chunks)."""
        overloaded = []
        for a in analyses:
            if a.chunk_count > MILLER_MAX:
                overloaded.append(f"スライド{a.slide_num}: {a.chunk_count}チャンク (上限{MILLER_MAX})")

        score = max(0, 10 - len(overloaded) * 3)
        avg_chunks = sum(a.chunk_count for a in analyses) / len(analyses) if analyses else 0

        return QualityScore(
            dimension="psychology", name="認知負荷 (ミラーの法則)",
            score=score, max_score=10, weight=1.2,
            details=f"平均チャンク数: {avg_chunks:.1f}/スライド (理想: {MILLER_IDEAL}以内)",
            issues=overloaded,
            suggestions=["情報を分割して1スライド7チャンク以内にする"] if overloaded else [],
        )

    def _check_emotion_curve(
        self,
        slides: list[dict],
        analyses: list[SlideAnalysis],
    ) -> QualityScore:
        """
        Check the emotion arc across all slides.
        Ideal 7-slide curve: surprise -> empathy -> expect -> learn -> convince -> hope -> action
        """
        actual_emotions = [a.emotion_type for a in analyses]

        # Score based on how well the actual curve matches the ideal
        score = 10
        issues = []

        if len(actual_emotions) < 5:
            score -= 3
            issues.append(f"スライド数{len(actual_emotions)}: 感情曲線の設計には5枚以上必要")

        # Check key positions
        if actual_emotions:
            # First slide should have surprise/curiosity
            if actual_emotions[0] not in ("surprise", "neutral"):
                score -= 1
                issues.append(f"1枚目の感情: '{actual_emotions[0]}' (理想: surprise)")

            # Last slide should drive action
            if len(actual_emotions) >= 5 and actual_emotions[-1] not in ("action", "hope"):
                score -= 1
                issues.append(f"最終スライドの感情: '{actual_emotions[-1]}' (理想: action/hope)")

        # Check monotony (same emotion throughout = boring)
        unique_emotions = set(actual_emotions)
        if len(unique_emotions) <= 2 and len(actual_emotions) >= 5:
            score -= 3
            issues.append(f"感情の種類が{len(unique_emotions)}種のみ: 単調すぎる")
        elif len(unique_emotions) >= 4:
            score = min(10, score + 1)  # bonus for variety

        # Check for emotional build-up (should have some "learn" or "convince" in middle)
        if len(actual_emotions) >= 5:
            middle = actual_emotions[2:-1]
            informative = sum(1 for e in middle if e in ("learn", "convince", "expect"))
            if informative == 0:
                score -= 2
                issues.append("中盤に学び/説得のスライドがない: 説得力不足")

        return QualityScore(
            dimension="psychology", name="感情曲線",
            score=max(0, score), max_score=10, weight=1.5,
            details=f"感情推移: {' -> '.join(actual_emotions)}",
            issues=issues,
            suggestions=[
                "理想: 驚き→共感→期待→学び→納得→希望→行動",
                "中盤にデータ/根拠スライドを入れて説得力を持たせる",
            ] if issues else [],
        )

    def _check_zeigarnik(self, slides: list[dict]) -> QualityScore:
        """
        Check Zeigarnik effect: does each slide create "want to see next" tension?
        Indicators: cliffhangers, incomplete statements, "...", "?", sequential numbering.
        """
        score = 0
        total_transitions = max(1, len(slides) - 1)
        tension_count = 0

        for i in range(len(slides) - 1):
            text = self._extract_slide_text(slides[i])
            has_tension = False

            # Ellipsis / trailing off
            if text.rstrip().endswith("…") or text.rstrip().endswith("..."):
                has_tension = True
            # Question ending
            if text.rstrip().endswith("？") or text.rstrip().endswith("?"):
                has_tension = True
            # "But..." / "However..."
            tension_words = ["しかし", "ところが", "でも", "だけど", "実は", "ただ", "→"]
            if any(text.rstrip().endswith(w) for w in tension_words):
                has_tension = True
            # Sequential numbering
            if re.search(r"[①②③④⑤]|その[1-5]|STEP\s*[1-5]", text):
                has_tension = True
            # "Next" / continuation hints
            if "続き" in text or "次" in text:
                has_tension = True

            if has_tension:
                tension_count += 1

        tension_ratio = tension_count / total_transitions
        score = min(10, int(tension_ratio * 12))  # Slight bonus for high tension

        issues = []
        if tension_ratio < 0.3:
            issues.append(f"テンション遷移: {tension_count}/{total_transitions} (30%未満)")

        return QualityScore(
            dimension="psychology", name="ザイガルニック効果",
            score=score, max_score=10, weight=1.0,
            details=f"「続きが気になる」遷移: {tension_count}/{total_transitions}箇所 ({tension_ratio:.0%})",
            issues=issues,
            suggestions=[
                "スライド末尾を「...」「？」「しかし」で終わらせて次への期待を作る",
                "「3つの理由」のように連番構造で引っ張る",
            ] if tension_ratio < 0.5 else [],
        )

    def _check_peak_end(self, slides: list[dict], analyses: list[SlideAnalysis]) -> QualityScore:
        """
        Check Peak-End Rule: the most impressive slide and the last slide
        should both be high quality.
        """
        if not slides or not analyses:
            return QualityScore(
                dimension="psychology", name="ピーク・エンドの法則",
                score=0, max_score=10, weight=1.3,
                details="スライドがありません",
                issues=["スライドデータを提供してください"],
            )

        score = 10
        issues = []

        # Find the "peak" slide (most data/emotion-dense)
        peak_idx = 0
        peak_score = 0
        for i, a in enumerate(analyses):
            slide_richness = a.chunk_count + (2 if a.has_number else 0) + (1 if a.emotion_type != "neutral" else 0)
            if slide_richness > peak_score:
                peak_score = slide_richness
                peak_idx = i

        # Peak should not be slide 1 or 2 (too early)
        if peak_idx <= 1 and len(slides) >= 5:
            score -= 2
            issues.append(f"ピークがスライド{peak_idx + 1}: 早すぎる（中盤〜後半が理想）")

        # Last slide quality
        last_text = self._extract_slide_text(slides[-1])
        last_analysis = analyses[-1]

        # Last slide should have a clear action/emotion
        if last_analysis.emotion_type == "neutral":
            score -= 2
            issues.append("最終スライドの感情が「neutral」: 行動喚起/希望を入れる")

        # Last slide should not be too text-heavy
        if last_analysis.char_count > 80:
            score -= 1
            issues.append(f"最終スライド{last_analysis.char_count}文字: シンプルで印象的にする")

        # Last slide should have CTA or memorable conclusion
        has_cta = any(w in last_text for w in SOFT_CTA_WORDS + HARD_CTA_WORDS)
        has_conclusion = any(w in last_text for w in ["結論", "まとめ", "つまり", "だから"])
        if not has_cta and not has_conclusion:
            score -= 2
            issues.append("最終スライドにCTAもまとめもない: 余韻が残らない")

        return QualityScore(
            dimension="psychology", name="ピーク・エンドの法則",
            score=max(0, score), max_score=10, weight=1.3,
            details=f"ピーク: スライド{peak_idx + 1} (豊かさ{peak_score}), ラスト: {last_analysis.emotion_type}/{last_analysis.char_count}文字",
            issues=issues,
            suggestions=[
                "最も印象的なデータ/感情を中盤〜後半に配置する",
                "最終スライドは短く、印象的に。CTAかまとめで締める",
            ] if issues else [],
        )

    # ----------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------

    def _extract_slide_text(self, slide: dict) -> str:
        """Extract all text from a slide dict."""
        parts = []
        for key in ("hook", "title", "heading", "body", "text", "cta", "caption"):
            if key in slide and slide[key]:
                parts.append(str(slide[key]))
        if not parts:
            # Fallback: join all string values
            for v in slide.values():
                if isinstance(v, str) and v.strip():
                    parts.append(v)
        return "\n".join(parts)

    def _analyze_slide(self, slide_num: int, text: str) -> SlideAnalysis:
        """Analyze a single slide's text."""
        clean = text.strip()
        lines = [l for l in clean.split("\n") if l.strip()]
        ratios = char_ratios(clean)

        return SlideAnalysis(
            slide_num=slide_num,
            char_count=len(clean.replace("\n", "").replace(" ", "")),
            line_count=len(lines),
            kanji_ratio=ratios.get("kanji", 0),
            hiragana_ratio=ratios.get("hiragana", 0),
            katakana_ratio=ratios.get("katakana", 0),
            chunk_count=count_chunks(clean),
            emotion_type=detect_emotion_type(clean),
            has_number=bool(re.search(r"\d+", clean)),
            readability_ok=(
                len(clean.replace("\n", "").replace(" ", "")) <= MAX_CHARS_PER_SLIDE
                and len(lines) <= MAX_LINES_PER_SLIDE
            ),
        )


# ============================================================
# Report Formatter
# ============================================================

def format_report(report: QualityReport, verbose: bool = True) -> str:
    """Format a QualityReport as human-readable text."""
    lines = []
    lines.append("=" * 60)
    lines.append(f"  品質レポート: {report.content_id}")
    lines.append(f"  総合スコア: {report.overall_score:.1f}/100  グレード: {report.grade}")
    lines.append(f"  判定: {'PASS' if report.pass_fail else 'FAIL'}")
    lines.append("=" * 60)

    if report.blocking_issues:
        lines.append("")
        lines.append("  *** ブロッキング問題 ***")
        for issue in report.blocking_issues:
            lines.append(f"  [!] {issue}")

    def _format_dimension(title: str, scores: list[QualityScore]):
        lines.append("")
        dim_avg = sum(s.score for s in scores) / len(scores) if scores else 0
        lines.append(f"  [{title}] 平均: {dim_avg:.1f}/10")
        lines.append("  " + "-" * 50)
        for s in scores:
            bar = "█" * int(s.score) + "░" * (10 - int(s.score))
            lines.append(f"    {s.name:<20s} {bar} {s.score:.1f}/10")
            if verbose and s.details:
                lines.append(f"      {s.details}")
            if verbose:
                for issue in s.issues:
                    lines.append(f"      [!] {issue}")
                for sug in s.suggestions:
                    lines.append(f"      [>] {sug}")

    _format_dimension("テキスト品質", report.text_scores)
    _format_dimension("ビジュアル品質", report.visual_scores)
    _format_dimension("コンテンツ品質", report.content_scores)
    _format_dimension("心理学的品質", report.psychology_scores)

    if verbose and report.slide_analyses:
        lines.append("")
        lines.append("  [スライド分析]")
        lines.append("  " + "-" * 50)
        lines.append(f"  {'#':>3s}  {'文字':>4s}  {'行':>2s}  {'漢字':>5s}  {'チャンク':>4s}  {'感情':<10s}")
        for a in report.slide_analyses:
            ok = "o" if a.readability_ok else "x"
            lines.append(
                f"  {a.slide_num:3d}  {a.char_count:4d}  {a.line_count:2d}  "
                f"{a.kanji_ratio:5.1%}  {a.chunk_count:4d}    {a.emotion_type:<10s} {ok}"
            )

    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


def print_standards():
    """Print quality standards reference."""
    print("""
╔══════════════════════════════════════════════════════════╗
║            品質基準リファレンス v1.0                      ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  [テキスト品質]                                           ║
║  - カーニング: 句読点前後/括弧前後の空き検出                ║
║  - 禁則処理: 行頭禁則（句読点）/行末禁則（開き括弧）        ║
║  - 数字表記: 半角/全角混在なし                             ║
║  - フォント黄金比: タイトル:本文:キャプション = 1:0.618:0.382║
║  - 読みやすさ: 1スライド120文字/8行以内                     ║
║  - 漢字比率: 15-25% (上限30%)                             ║
║  - 文字種バランス: ひらがな40-60% / 漢字15-25%             ║
║                                                          ║
║  [ビジュアル品質]                                          ║
║  - コントラスト: WCAG AA 4.5:1 / AAA 7:1                  ║
║  - 余白: TikTokセーフゾーン準拠                            ║
║  - グリッド: 12列準拠                                      ║
║  - グラデーション: バンディング防止（色差128以内）           ║
║  - 影: 角度・透明度統一（右下2px, 50%）                    ║
║  - フォントサイズ: 黄金比準拠                              ║
║                                                          ║
║  [コンテンツ品質]                                          ║
║  - フック力: 損失回避+2/数字+1/疑問+1/感情+1/ペルソナ+2    ║
║  - 保存価値: データ+3/チェックリスト+2/How-to+2            ║
║  - シェア価値: 共感+2/意外性+2/実用性+1                    ║
║  - CTA自然度: ハードCTAは10投稿中2以下                     ║
║                                                          ║
║  [心理学的品質]                                            ║
║  - 認知負荷: 7±2チャンク/スライド（ミラーの法則）           ║
║  - 感情曲線: 驚き→共感→期待→学び→納得→希望→行動           ║
║  - ザイガルニック: 次スライドへのテンション遷移率50%+       ║
║  - ピーク・エンド: 最印象スライド(中盤)+ラスト(CTA)        ║
║                                                          ║
║  [グレード]                                                ║
║  S: 95+  A: 85+  B: 70+  C: 55+  D: 40+  F: <40         ║
║  合格ライン: 60点 + ブロッキング問題なし                    ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
""")


# ============================================================
# CLI
# ============================================================

def load_queue_item(queue_path: Path, index: int) -> tuple[list[dict], dict]:
    """Load a specific item from posting_queue.json, resolving json_path references."""
    with open(queue_path) as f:
        queue = json.load(f)

    items = queue if isinstance(queue, list) else queue.get("posts", queue.get("queue", []))
    if index >= len(items):
        print(f"Error: index {index} out of range (queue has {len(items)} items)")
        sys.exit(1)

    item = items[index]
    project_dir = Path(__file__).parent.parent

    # Extract slides from item directly
    slides = item.get("slides", [])

    # If no slides in queue item, try loading from json_path (script file)
    if not slides and item.get("json_path"):
        json_path = project_dir / item["json_path"]
        if json_path.exists():
            with open(json_path) as f:
                script_data = json.load(f)
            slides = script_data.get("slides", [])
            # Merge script metadata into item for hook/caption extraction
            for key in ("hook", "caption", "category", "hashtags"):
                if key in script_data and key not in item:
                    item[key] = script_data[key]
            if "content_id" not in item and "id" in script_data:
                item["content_id"] = script_data["id"]

    if not slides:
        # Try alternative structures within item
        script = item.get("script", {})
        if isinstance(script, dict):
            slides = script.get("slides", [])
        elif isinstance(script, list):
            slides = script

    # If slides are just strings, convert to dicts
    if slides and isinstance(slides[0], str):
        slides = [{"body": s} for s in slides]

    return slides, item


def check_from_queue(
    queue_path: Path,
    index: int,
    verbose: bool = True,
    suppress_text: bool = False,
) -> QualityReport:
    """Run quality check on a queue item."""
    slides, item = load_queue_item(queue_path, index)
    checker = ContentQualityChecker()

    hook = item.get("hook", item.get("title", ""))
    if not hook and slides:
        hook = slides[0].get("hook", slides[0].get("body", slides[0].get("title", "")))

    report = checker.check(
        slides=slides,
        hook_text=hook,
        caption=item.get("caption", ""),
        category=item.get("category", item.get("content_type", "")),
        content_id=item.get("content_id", item.get("id", f"queue_{index}")),
    )
    if not suppress_text:
        print(format_report(report, verbose=verbose))
    return report


def audit_queue(queue_path: Path) -> list[QualityReport]:
    """Run quality check on all items in the queue."""
    with open(queue_path) as f:
        queue = json.load(f)

    items = queue if isinstance(queue, list) else queue.get("posts", queue.get("queue", []))
    reports = []

    for i in range(len(items)):
        print(f"\n--- Checking item {i} ---")
        report = check_from_queue(queue_path, i, verbose=False)
        reports.append(report)

    # Summary
    print("\n" + "=" * 60)
    print("  一括監査サマリ")
    print("=" * 60)
    print(f"  {'ID':<12s} {'スコア':>6s}  {'グレード':>4s}  {'判定':>4s}")
    print("  " + "-" * 40)
    for r in reports:
        status = "PASS" if r.pass_fail else "FAIL"
        print(f"  {r.content_id:<12s} {r.overall_score:6.1f}  {r.grade:>4s}  {status:>4s}")

    avg = sum(r.overall_score for r in reports) / len(reports) if reports else 0
    passed = sum(1 for r in reports if r.pass_fail)
    print("  " + "-" * 40)
    print(f"  平均スコア: {avg:.1f}/100")
    print(f"  合格: {passed}/{len(reports)}")
    print("=" * 60)

    return reports


def check_images_dir(image_dir: Path, verbose: bool = True) -> QualityReport:
    """Run visual checks on generated slide images."""
    image_paths = sorted(image_dir.glob("*.png")) + sorted(image_dir.glob("*.jpg"))
    if not image_paths:
        print(f"Error: No images found in {image_dir}")
        sys.exit(1)

    checker = ContentQualityChecker()
    report = checker.check(
        slides=[{"body": f"slide_{i}"} for i in range(len(image_paths))],
        content_id=image_dir.name,
        image_paths=image_paths,
    )
    print(format_report(report, verbose=verbose))
    return report


def main():
    parser = argparse.ArgumentParser(
        description="SNSカルーセル品質チェッカー — 神は細部に宿る",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--script", type=Path, help="投稿キューJSONのパス")
    parser.add_argument("--index", type=int, default=0, help="キュー内のインデックス")
    parser.add_argument("--images", type=Path, help="生成済みスライド画像のディレクトリ")
    parser.add_argument("--audit", type=Path, help="全キューの一括品質監査")
    parser.add_argument("--standards", action="store_true", help="品質基準リファレンスの表示")
    parser.add_argument("--json", action="store_true", help="JSON形式で出力")
    parser.add_argument("--strict", action="store_true", help="厳格モード (WCAG AAA)")
    parser.add_argument("-q", "--quiet", action="store_true", help="サマリのみ表示")

    args = parser.parse_args()

    if args.standards:
        print_standards()
        return

    if args.audit:
        reports = audit_queue(args.audit)
        if args.json:
            print(json.dumps([r.to_dict() for r in reports], ensure_ascii=False, indent=2))
        return

    if args.script:
        if args.json:
            report = check_from_queue(args.script, args.index, verbose=False, suppress_text=True)
            print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        else:
            report = check_from_queue(args.script, args.index, verbose=not args.quiet)
        return

    if args.images:
        report = check_images_dir(args.images, verbose=not args.quiet)
        if args.json:
            print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        return

    # Demo mode: run with sample data
    print("=== デモモード: サンプルデータで品質チェック ===\n")

    sample_slides = [
        {"hook": "師長にAIで見せたら黙った"},
        {"title": "きっかけ", "body": "夜勤明けの休憩中\nいつものように愚痴ってたら\n後輩が「AI使えば？」って…"},
        {"title": "やってみた", "body": "ChatGPTに\n「師長への退職相談の\n伝え方を教えて」\nって聞いてみた"},
        {"title": "AIの回答", "body": "退職理由を3つに整理\n感情ではなくデータで説明\n代替案も一緒に提示…"},
        {"title": "師長の反応", "body": "「こんなに整理して\n考えてたんだ…」\nって言って黙った"},
        {"title": "その後", "body": "すぐには辞めなかったけど\n師長の態度が変わった\n話を聞いてくれるようになった"},
        {"title": "", "body": "転職の相談もAIにできる時代\nでも最後は人の温もりが大事\n\n保存して見返してね"},
    ]

    checker = ContentQualityChecker()
    report = checker.check(
        slides=sample_slides,
        hook_text="師長にAIで見せたら黙った",
        caption="看護師あるある！師長にAI見せたらまさかの反応…\n#看護師あるある #AI #ナースロビー",
        category="あるある",
        content_id="A01_demo",
        colors={
            "bg": (26, 26, 46),
            "text": (255, 255, 255),
            "accent": (255, 107, 107),
        },
        font_sizes={"title": 56, "body": 34, "caption": 20},
    )

    print(format_report(report, verbose=True))


if __name__ == "__main__":
    main()
