#!/usr/bin/env python3
"""Проверка пояснительной записки перед подачей.

Три вещи, которые реально ловили дефекты в живых работах:

  1. stats   — объём и структура собранного docx (абзацы, таблицы, заголовки,
               оценки страниц), чтобы сверить с лимитом конкурса.
  2. leaks   — поиск внутренних пометок, которых не должно быть в документе:
               имена тестов и скриптов, dev-сервер, пути, происхождение данных,
               «агент/ИИ/промпт», TODO, имена временных файлов.
  3. sums    — арифметика таблиц: строки с процентами в столбце «Доля» должны
               давать около 100 (ловушка унаследованных таблиц вида 78,9 +
               17,5 + 12,8 = 109,2).

Запуск:
  python pz_check.py work.docx [--md source.md] [--extra-words a,b,c]
                                [--sum-tolerance 1.0]
"""
import argparse
import re
import sys
from pathlib import Path

try:
    from docx import Document
except ImportError:  # pragma: no cover
    sys.exit("нужен python-docx: pip install python-docx")

DEFAULT_LEAK_WORDS = [
    # внутренняя машинерия и её следы
    "test_", "tests/", ".py", ".cjs", "http.server", "dev-сервер", "localhost",
    "127.0.0.1", "порт 87", "CDP", "git", "commit", "скрипт", "генератор",
    # разговор с ИИ / условия для агента
    "агент", "промпт", "prompt", "ИИ", "нейросет", "ассистент",
    "TODO", "FIXME", "сессия", "условие для агента", "проверка агента",
    # происхождение данных, которое не должно быть в UI/документе
    "WMS", "GetFeatureInfo", "официальный слой", "источник данных ЗИС", "nipd",
]

APPENDIX_MARKERS = ("приложение", "исходный код")


def make_pattern(word):
    """Слово — с границами (чтобы «ИИ» не ловилось в «информации»),
    код-подобный маркер — простой подстрокой."""
    codeish = any(ch in word for ch in "_./()@-0123456789")
    if codeish or " " in word:
        return re.compile(re.escape(word), re.I)
    return re.compile(rf"(?<![A-Za-zА-Яа-яЁё]){re.escape(word)}(?![A-Za-zА-Яа-яЁё])", re.I)


def build_matchers(words):
    return [(w, make_pattern(w)) for w in words]


def is_appendix(text):
    low = text.strip().lower()
    return len(low) < 60 and any(m in low for m in APPENDIX_MARKERS)



def docx_stats(doc):
    page_h = doc.sections[0].page_height.cm
    usable = page_h - doc.sections[0].top_margin.cm - doc.sections[0].bottom_margin.cm
    body_chars = sum(len(p.text) for p in doc.paragraphs)
    body_lines = 0
    for p in doc.paragraphs:
        spacing = p.paragraph_format.line_spacing or 1.0
        # грубая оценка: 90 знаков на строку при TNR 14 и одинарном интервале
        body_lines += max(1, len(p.text) // 90 + 1) * (spacing if isinstance(spacing, float) else 1.0)
    line_h = 14 * 1.15 / 28.35  # см: кегль 14 пт с межстрочным
    pages = body_lines * line_h / usable if usable > 0 else 0
    return {
        "paragraphs": len(doc.paragraphs),
        "tables": len(doc.tables),
        "inline_images": len(doc.inline_shapes),
        "chars": body_chars,
        "estimated_pages": round(pages, 1),
        "page_numbers": "PAGE" in doc.sections[0].footer.paragraphs[0]._p.xml,
        "toc_field": "instrText" in doc.element.xml or "TOC" in doc.element.xml,
        "title_lines": sum(1 for p in doc.paragraphs if p.style.name.startswith("Heading 0")),
    }


def find_leaks(doc, matchers):
    """Возвращает (тело, приложение): утечки в теле — дефект, в приложении
    (исходный код) — повод посмотреть глазами."""
    body, appendix = [], []
    in_appendix = False
    for i, p in enumerate(doc.paragraphs):
        text = p.text.strip()
        if is_appendix(text):
            in_appendix = True
            continue
        if not text:
            continue
        for w, pat in matchers:
            if pat.search(text):
                (appendix if in_appendix else body).append((i, w, text[:140]))
                break
    return body, appendix


def parse_percent(text):
    m = re.fullmatch(r"\s*~?\s*(\d+[.,]?\d*)\s*%\s*", text.replace("\u00a0", " "))
    return float(m.group(1).replace(",", ".")) if m else None


def table_sums(doc, tolerance):
    problems = []
    for ti, t in enumerate(doc.tables, start=1):
        if len(t.rows) < 3:
            continue
        header = [c.text.strip().lower() for c in t.rows[0].cells]
        pct_cols = [ci for ci, h in enumerate(header) if "дол" in h or "процент" in h or "%" in h]
        if not pct_cols:
            continue
        for ci in pct_cols:
            vals, labels = [], []
            for r in t.rows[1:]:
                if ci >= len(r.cells):
                    continue
                v = parse_percent(r.cells[ci].text)
                if v is not None:
                    vals.append(v)
                    labels.append(r.cells[0].text.strip())
            if len(vals) >= 2:
                total = round(sum(vals), 2)
                if abs(total - 100) > tolerance:
                    problems.append({
                        "table": ti, "column": header[ci], "sum": total,
                        "rows": list(zip(labels, vals)),
                    })
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("docx", type=Path)
    ap.add_argument("--extra-words", default="", help="дополнительные слова-маркеры через запятую")
    ap.add_argument("--sum-tolerance", type=float, default=1.0)
    ap.add_argument("--md", type=Path, default=None, help="исходный md (проверяется вместе с docx)")
    args = ap.parse_args()

    doc = Document(args.docx)
    words = list(DEFAULT_LEAK_WORDS) + [w.strip() for w in args.extra_words.split(",") if w.strip()]
    matchers = build_matchers(words)
    stats = docx_stats(doc)
    leaks, appendix_hits = find_leaks(doc, matchers)
    sums = table_sums(doc, args.sum_tolerance)
    md_leaks = []
    if args.md and args.md.exists():
        md_leaks = [(-1, w, t) for w, t in find_md_leaks(args.md.read_text(encoding="utf-8"), matchers)]

    print("=== СТРУКТУРА ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    print(f"\n=== ВНУТРЕННИЕ УТЕЧКИ В ТЕКСТЕ ({len(leaks)} docx + {len(md_leaks)} md) ===")
    for i, w, t in leaks[:40]:
        print(f"  [абз.{i}] «{w}» -> {t}")
    for i, w, t in md_leaks[:40]:
        print(f"  [md] «{w}» -> {t}")
    if appendix_hits:
        print(f"\n=== В ПРИЛОЖЕНИИ ({len(appendix_hits)}) — код, смотреть глазами ===")
        for i, w, t in appendix_hits[:10]:
            print(f"  [абз.{i}] «{w}» -> {t}")
    print(f"\n=== АРИФМЕТИКА ТАБЛИЦ ({len(sums)} проблем) ===")
    for p in sums:
        rows = ", ".join(f"{lbl}={v}" for lbl, v in p["rows"])
        print(f"  таблица {p['table']}, столбец «{p['column']}»: сумма {p['sum']}% ({rows})")
    body_ok = not leaks and not md_leaks and not sums
    print("\nВЕРДИКТ:", "OK по телу документа" if body_ok else "ЕСТЬ НАХОДКИ")
    return 0 if body_ok else 1


def find_md_leaks(text, matchers):
    out = []
    for line in text.splitlines():
        for w, pat in matchers:
            if pat.search(line):
                out.append((w, line.strip()[:140]))
                break
    return out


if __name__ == "__main__":
    sys.exit(main())
