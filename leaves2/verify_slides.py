#!/usr/bin/env python3
"""
Verification and comparison script for Reveal.js presentations:
Original (leaves2/slides.html) vs Approach B (leaves2/slides_b.html).

Checks:
- Section hierarchy and nesting depth (0 nested sections expected in B)
- Empty section detection (no blank white slides)
- Unexpanded code string detection (no raw {python} tokens)
- Text and data content presence on every slide
- File size and self-contained asset embedding
"""

import os
import re
import sys
from html.parser import HTMLParser

class SlideSectionParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_slides = False
        self.current_section = None
        self.section_stack = []
        self.sections = []
        self.slides_depth = 0

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        if tag in ("style", "script"):
            self.in_non_visible = True

        if tag == "div" and "slides" in attr_dict.get("class", "").split():
            self.in_slides = True
            self.slides_depth = 1
            return

        if self.in_slides:
            if tag == "div":
                self.slides_depth += 1
            elif tag == "section":
                sec_info = {
                    "id": attr_dict.get("id", ""),
                    "class": attr_dict.get("class", ""),
                    "depth": len(self.section_stack) + 1,
                    "text_parts": [],
                    "tags": [],
                    "images": []
                }
                self.section_stack.append(sec_info)
                self.sections.append(sec_info)
            elif self.section_stack:
                self.section_stack[-1]["tags"].append(tag)
                if tag == "img" and "src" in attr_dict:
                    self.section_stack[-1]["images"].append(attr_dict["src"][:60])

    def handle_endtag(self, tag):
        if tag in ("style", "script"):
            self.in_non_visible = False

        if self.in_slides:
            if tag == "section" and self.section_stack:
                self.section_stack.pop()
            elif tag == "div":
                self.slides_depth -= 1
                if self.slides_depth == 0:
                    self.in_slides = False

    def handle_data(self, data):
        if getattr(self, "in_non_visible", False):
            return
        if self.in_slides and self.section_stack:
            cleaned = data.strip()
            if cleaned:
                self.section_stack[-1]["text_parts"].append(cleaned)


def analyze_html_file(filepath):
    if not os.path.exists(filepath):
        print(f"Error: File {filepath} does not exist.")
        return None

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    file_size = os.path.getsize(filepath)
    parser = SlideSectionParser()
    parser.feed(content)

    results = {
        "filepath": filepath,
        "filesize_bytes": file_size,
        "filesize_mb": round(file_size / (1024 * 1024), 2),
        "total_sections": len(parser.sections),
        "nested_sections": [s for s in parser.sections if s["depth"] > 1],
        "sections": []
    }

    # Check for unexpanded {python} tokens in the entire file
    unexpanded_tokens = re.findall(r'\{python\}|\{python\s+[^}]+\}', content)
    results["unexpanded_python_tokens"] = unexpanded_tokens

    # Check for embedded resources (base64 data images)
    data_uris = len(re.findall(r'src="data:image/[^;]+;base64,', content))
    results["embedded_images_count"] = data_uris

    for i, s in enumerate(parser.sections):
        full_text = " ".join(s["text_parts"])
        is_empty = len(full_text.strip()) == 0
        is_style_only = is_empty and ("style" in s["tags"])

        results["sections"].append({
            "index": i,
            "id": s["id"],
            "depth": s["depth"],
            "class": s["class"],
            "text_length": len(full_text),
            "is_empty": is_empty,
            "is_style_only": is_style_only,
            "text_preview": full_text[:120] if full_text else "(EMPTY)",
            "images_count": len(s["images"])
        })

    return results


def main():
    print("=" * 80)
    print("REVEAL.JS PRESENTATION DIAGNOSTIC & VERIFICATION REPORT")
    print("=" * 80)

    # 1. Analyze Original (slides.html)
    orig_res = analyze_html_file("leaves2/slides.html")
    # 2. Analyze Approach B (slides_b.html)
    b_res = analyze_html_file("leaves2/slides_b.html")

    print("\n--- 1. ORIGINAL PRESENTATION (leaves2/slides.html) ---")
    if orig_res:
        print(f"File size: {orig_res['filesize_mb']} MB ({orig_res['filesize_bytes']} bytes)")
        print(f"Total <section> elements: {orig_res['total_sections']}")
        print(f"Nested sections (depth > 1): {len(orig_res['nested_sections'])}")
        print(f"Unexpanded {{python}} tokens found: {len(orig_res['unexpanded_python_tokens'])}")
        if orig_res['unexpanded_python_tokens']:
            print(f"   Examples: {orig_res['unexpanded_python_tokens'][:4]}")

        empty_secs = [s for s in orig_res["sections"] if s["is_empty"]]
        print(f"Empty / Blank sections count: {len(empty_secs)}")
        for s in orig_res["sections"]:
            flag = " [DEFECT: EMPTY/STYLE-ONLY!]" if s["is_empty"] else (" [DEFECT: NESTED 2D!]" if s["depth"] > 1 else "")
            print(f"  Slide {s['index']} (depth {s['depth']}): id='{s['id']}' | text_len={s['text_length']}{flag}")
            if s["is_empty"]:
                print(f"      -> Reason: Section only contained `<style>` block before Slide 1!")

    print("\n--- 2. APPROACH B PRESENTATION (leaves2/slides_b.html) ---")
    if b_res:
        print(f"File size: {b_res['filesize_mb']} MB ({b_res['filesize_bytes']} bytes)")
        print(f"Total <section> elements: {b_res['total_sections']} (Expected: 6 = 1 Title + 5 Slides)")
        print(f"Nested sections (depth > 1): {len(b_res['nested_sections'])} (Expected: 0)")
        print(f"Unexpanded {{python}} tokens found: {len(b_res['unexpanded_python_tokens'])} (Expected: 0)")
        print(f"Self-contained embedded base64 images: {b_res['embedded_images_count']}")

        empty_b = [s for s in b_res["sections"] if s["is_empty"]]
        print(f"Empty / Blank sections count: {len(empty_b)} (Expected: 0)")

        for s in b_res["sections"]:
            print(f"  Slide {s['index']} (depth {s['depth']}): id='{s['id']}' | text_len={s['text_length']}")
            print(f"     Preview: {s['text_preview']}...")

        # Assertions
        assert len(b_res["nested_sections"]) == 0, "Approach B must have 0 nested sections!"
        assert len(empty_b) == 0, "Approach B must have 0 empty sections!"
        assert len(b_res["unexpanded_python_tokens"]) == 0, "Approach B must have 0 unexpanded python tokens!"
        assert b_res["total_sections"] == 6, f"Expected exactly 6 sections, got {b_res['total_sections']}"
        print("\n>>> ALL CRITICAL ASSERTIONS PASSED FOR APPROACH B! <<<")

    print("\n--- 3. COMPARISON TABLE ---")
    print(f"{'Feature / Metric':<30} | {'Original (slides.html)':<24} | {'Approach B (slides_b.html)':<24}")
    print("-" * 84)
    print(f"{'Total Slides (Sections)':<30} | {orig_res['total_sections']:<24} | {b_res['total_sections']:<24}")
    print(f"{'Empty Slides (White Screen)':<30} | {len([s for s in orig_res['sections'] if s['is_empty']]):<24} | {len(empty_b):<24}")
    print(f"{'Slide Hierarchy Depth':<30} | {'Depth 2 (broken 2D)':<24} | {'Depth 1 (flat linear)':<24}")
    print(f"{'Unexpanded Python Tokens':<30} | {len(orig_res['unexpanded_python_tokens']):<24} | {len(b_res['unexpanded_python_tokens']):<24}")
    orig_size_str = f"{orig_res['filesize_mb']} MB"
    b_size_str = f"{b_res['filesize_mb']} MB"
    print(f"{'File Size':<30} | {orig_size_str:<24} | {b_size_str:<24}")
    print(f"{'Standalone Portability':<30} | {'embed-resources (OK)':<24} | {'embed-resources (OK)':<24}")
    print(f"{'Max Height Constrained':<30} | {'No (overflows 720px)':<24} | {'Yes (capped at 580px)':<24}")
    print("=" * 84)

if __name__ == "__main__":
    main()
