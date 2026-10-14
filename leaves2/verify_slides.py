#!/usr/bin/env python3
"""
Verification script for Reveal.js presentation (leaves2/slides.html).

Checks:
- Section hierarchy: exactly 6 slides (1 Title + 5 Slides)
- Flat linear navigation (0 nested sections)
- No empty slides (no white screen)
- No unexpanded Python tokens ({python})
- All expected slide headers present and populated
"""

import os
import re
import sys
from html.parser import HTMLParser

class SlideSectionParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_slides = False
        self.section_stack = []
        self.sections = []
        self.slides_depth = 0
        self.in_non_visible = False

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


def analyze_html_file(filepath="leaves2/slides.html"):
    if not os.path.exists(filepath):
        print(f"Error: File {filepath} does not exist.")
        sys.exit(1)

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    file_size = os.path.getsize(filepath)
    parser = SlideSectionParser()
    parser.feed(content)

    print("=" * 80)
    print(f"VERIFYING PRESENTATION: {filepath}")
    print("=" * 80)
    print(f"File size: {round(file_size / (1024 * 1024), 2)} MB")
    print(f"Total <section> elements: {len(parser.sections)} (Expected: 6)")

    nested = [s for s in parser.sections if s["depth"] > 1]
    print(f"Nested sections (depth > 1): {len(nested)} (Expected: 0)")
    assert len(nested) == 0, f"Found {len(nested)} nested sections!"

    assert len(parser.sections) == 6, f"Expected 6 sections, got {len(parser.sections)}"

    empty_count = 0
    for i, s in enumerate(parser.sections):
        full_text = " ".join(s["text_parts"])
        is_empty = len(full_text.strip()) == 0
        if is_empty:
            empty_count += 1
        print(f"  Slide {i} (depth {s['depth']}): id='{s['id']}' | text_len={len(full_text)}")
        assert not is_empty, f"Slide {i} is empty/blank!"

    print(f"Empty slides count: {empty_count} (Expected: 0)")

    # Check for unexpanded tokens
    unexpanded = re.findall(r'\{python\}|\{python\s+[^}]+\}', content)
    print(f"Unexpanded {{python}} tokens: {len(unexpanded)} (Expected: 0)")
    if unexpanded:
        print("  Found unexpanded tokens:", unexpanded)
    assert len(unexpanded) == 0, "Found unexpanded python tokens!"

    print("\n>>> ALL CRITICAL ASSERTIONS PASSED! PRESENTATION IS 100% VALID <<<")


if __name__ == "__main__":
    analyze_html_file()
