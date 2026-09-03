#!/usr/bin/env python3
"""storyboard_html.py — 把 storyboard_plan.md 转成可编辑的创作规划书 HTML。

用法:
    python3 tools/storyboard_html.py <storyboard_plan.md> [-o 输出.html]

不加 -o 时，输出到 md 同目录的 storyboard_plan.html。
"""
import json
import re
import sys
from pathlib import Path

TEMPLATE = Path(__file__).with_name("storyboard_template.html")


def extract_storyboard_json(md_text: str) -> dict:
    """取 md 里含 "scenes" 的 ```json 代码块。"""
    for m in re.finditer(r"```json\s*\n(.*?)```", md_text, re.S):
        try:
            obj = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and "scenes" in obj:
            return obj
    raise SystemExit("错误: 未在 md 中找到含 scenes 的 json 代码块")


def extract_title(md_text: str) -> str:
    m = re.search(r"视频标题[：:]\s*(.+)", md_text)
    return m.group(1).strip() if m else "未命名"


def extract_visual_style(md_text: str) -> dict:
    """取含 visual_style 的 json 代码块。"""
    for m in re.finditer(r"```json\s*\n(.*?)```", md_text, re.S):
        try:
            obj = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and "visual_style" in obj:
            return obj
    return {}


def extract_plan(md_text: str) -> dict:
    """解析『一、成片需求』下的各 ### 小节，返回展示用结构。"""
    m = re.search(r"##\s*一、成片需求.*?(?=^##\s)", md_text, re.S | re.M)
    chunk = m.group(0) if m else md_text
    # 抠掉 json 代码块，避免被当成正文行
    chunk = re.sub(r"```json.*?```", "", chunk, flags=re.S)

    sections, style_notes = [], []
    for sm in re.finditer(r"###\s*([^\n]+)\n(.*?)(?=^###|\Z)", chunk, re.S | re.M):
        title = sm.group(1).strip()
        lines = [
            ln.strip().lstrip("- ").strip()
            for ln in sm.group(2).strip().splitlines()
            if ln.strip().startswith("- ")
        ]
        if not lines:
            continue
        if "画风" in title:
            style_notes = lines
        else:
            sections.append({"title": title, "lines": lines, "wide": len(lines) <= 2})
    return {
        "sections": sections,
        "style_notes": style_notes,
        "visual_style": extract_visual_style(md_text),
    }


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    md_path = Path(sys.argv[1]).expanduser().resolve()
    out_path = None
    if "-o" in sys.argv:
        out_path = Path(sys.argv[sys.argv.index("-o") + 1]).expanduser().resolve()
    else:
        out_path = md_path.with_name("storyboard_plan.html")

    md_text = md_path.read_text(encoding="utf-8")
    data = extract_storyboard_json(md_text)
    title = extract_title(md_text)

    html = TEMPLATE.read_text(encoding="utf-8")
    # json.dumps 保证转义安全;</script> 防御性转义
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    plan = json.dumps(extract_plan(md_text), ensure_ascii=False).replace("</", "<\\/")
    html = (html
            .replace("__DATA__", payload)
            .replace("__PLAN__", plan)
            .replace("__TITLE__", title))
    out_path.write_text(html, encoding="utf-8")

    n = sum(len(sc.get("shots", [])) for sc in data["scenes"])
    print(f"OK · {len(data['scenes'])} 场景 / {n} 分镜 -> {out_path}")


if __name__ == "__main__":
    main()
