#!/usr/bin/env python
"""
Build Phenix documentation PDFs for NotebookLM Chat.

Reads the local Phenix documentation tree, categorizes pages by file path,
and generates ~20 topical PDFs with proper formatting (headings, lists,
code blocks).

Replaces the old pipeline:
  crawler.py -> sort_urls.py -> combine.csh -> browser "Save as PDF"

Usage:
  phenix.python build_chat_docs.py
  python build_chat_docs.py --docs-dir $PHENIX/doc
  python build_chat_docs.py --output-dir ./documentation/

Requirements: beautifulsoup4, reportlab
"""

from __future__ import absolute_import, division, print_function

import argparse
import os
import re
import sys
from collections import defaultdict, OrderedDict

# ---------------------------------------------------------------------------
# Category definitions
# ---------------------------------------------------------------------------

CATEGORIES = OrderedDict([
    ("tutorials", [r"/tutorials?/", r"tutorial"]),
    ("faqs", [r"/faqs?/", r"/faq[_\.]", r"frequently"]),
    ("cryoem_tools", [
        r"real_space_refine", r"dock_in_map", r"map_to_model",
        r"resolve_cryo_em", r"map_sharpening", r"map_symmetry",
        r"mtriage", r"cryo.?em", r"denmod", r"density_modif",
        r"auto_sharpen", r"local_resolution",
    ]),
    ("molecular_replacement", [
        r"phaser", r"molecular.replacement", r"mr[_\-]",
        r"ensembl", r"sculptor",
    ]),
    ("model_building", [
        r"autobuild", r"predict_and_build", r"alphafold",
        r"model.building", r"build_one_model", r"trace_and_build",
    ]),
    ("refinement", [
        r"phenix[\._]refine", r"/refine[_\.]", r"refinement",
        r"ensemble_refin", r"geometry_minim",
    ]),
    ("experimental_phasing", [
        r"autosol", r"\bsad\b", r"\bmad\b", r"experimental.phas",
        r"heavy.atom", r"anomalous", r"hyss", r"phassade",
    ]),
    ("ligands", [
        r"ligand", r"elbow", r"readyset", r"ready_set",
        r"polder", r"small.molecule", r"restraint",
    ]),
    ("validation", [
        r"molprobity", r"validation", r"clashscore",
        r"ramachandran", r"ramalyze", r"rotalyze",
        r"cablam", r"emringer", r"omegalyze",
    ]),
    ("data_analysis", [
        r"xtriage", r"data.analysis", r"data.quality",
        r"twinning", r"anisotropy", r"reflection",
        r"french_wilson", r"merging_stat", r"table_one",
    ]),
    ("model_tools", [
        r"pdbtools", r"process_predicted", r"model_vs_data",
        r"superpose", r"morph", r"sculpt", r"trim",
        r"chain_comparison", r"assign_sequence",
    ]),
    ("maps", [
        r"/maps?[_/\.]", r"density", r"composite.omit",
        r"feature_enhanced", r"fem\b", r"map_box",
        r"map_correlat", r"prime_and_switch",
    ]),
    ("phil_and_selections", [
        r"phil\b", r"parameter", r"atom.selection",
        r"selection.syntax", r"\.def\b",
    ]),
    ("gui", [r"\bgui\b", r"graphical", r"interface", r"wizard"]),
    ("installation", [
        r"install", r"download", r"getting.started",
        r"setup", r"license", r"conda",
    ]),
    ("ai_agent", [
        r"ai.agent", r"ai_agent", r"ai_analysis", r"automation",
    ]),
    ("developers", [
        r"developer", r"/api[_/\.]", r"scripting",
        r"command.line", r"cctbx", r"python",
    ]),
    ("overview", [
        r"overview", r"introduction", r"about\b",
        r"what.is", r"index\.html$", r"reference/",
    ]),
])

FALLBACK_CATEGORY = "general_reference"

CATEGORY_TITLES = {
    "tutorials":              "Phenix Tutorials",
    "faqs":                   "Phenix Frequently Asked Questions",
    "cryoem_tools":           "Phenix Cryo-EM Tools",
    "molecular_replacement":  "Phenix Molecular Replacement",
    "model_building":         "Phenix Model Building",
    "refinement":             "Phenix Refinement",
    "experimental_phasing":   "Phenix Experimental Phasing",
    "ligands":                "Phenix Ligand and Restraint Tools",
    "validation":             "Phenix Validation",
    "data_analysis":          "Phenix Data Analysis",
    "model_tools":            "Phenix Model Tools and Utilities",
    "maps":                   "Phenix Maps and Density",
    "phil_and_selections":    "Phenix PHIL Parameters and Atom Selections",
    "gui":                    "Phenix GUI",
    "installation":           "Phenix Installation and Setup",
    "ai_agent":               "Phenix AI Agent",
    "developers":             "Phenix Developer Reference",
    "overview":               "Phenix Overview and General Reference",
    "general_reference":      "Phenix Documentation (Miscellaneous)",
}


# ---------------------------------------------------------------------------
# Structured HTML extraction
# ---------------------------------------------------------------------------

# Tags that indicate the PHENIX acronym expansion — always remove
_PHENIX_ACRONYM = re.compile(
    r"P\s*ython-based\s+H\s*ierarchical\s+EN\s*vironment"
    r"\s+for\s+I\s*ntegrated\s+X\s*tallography",
    re.IGNORECASE)

# Bare .html filenames left over from link extraction
_BARE_HTML_LINK = re.compile(r"^\s*\S+\.html\s*$")

# Content block types for structured output
HEADING = "heading"
PARA = "para"
CODE = "code"
LIST_ITEM = "list_item"


def extract_structured_html(filepath):
    """Extract structured content from a Phenix HTML doc.

    Returns:
        tuple: (title, blocks) where blocks is a list of
               (block_type, text) tuples, or (None, []) on failure.
    """
    from bs4 import BeautifulSoup, NavigableString

    try:
        with open(filepath, "r", encoding="utf-8",
                  errors="ignore") as f:
            soup = BeautifulSoup(f, "html.parser")
    except Exception:
        return None, []

    # Extract title
    title = ""
    title_tag = soup.find("title")
    if title_tag:
        title = title_tag.get_text().strip()
        # Strip " — PHENIX documentation" suffix
        title = re.sub(
            r"\s*[—\-]\s*PHENIX\s+documentation\s*$",
            "", title, flags=re.IGNORECASE)

    # Find main content area (skip nav, sidebar, footer)
    main = (
        soup.find("div", class_="body") or
        soup.find("div", {"role": "main"}) or
        soup.find("main") or
        soup.find("article") or
        soup.find("div", class_="document") or
        soup.body or soup
    )

    # Remove unwanted elements
    for tag in main.find_all([
        "script", "style", "nav", "footer",
    ]):
        tag.extract()
    for tag in main.find_all(
        "div", class_=re.compile(
            r"navbar|sidebar|sphinxsidebar|"
            r"breadcrumb|headerlink|footer|"
            r"related")):
        tag.extract()
    # Remove permalink anchors (the little paragraph signs)
    for tag in main.find_all("a", class_="headerlink"):
        tag.extract()

    blocks = []
    seen_titles = set()

    def _clean(text):
        """Clean extracted text."""
        text = text.strip()
        # Remove PHENIX acronym expansion
        text = _PHENIX_ACRONYM.sub("", text).strip()
        # Collapse whitespace
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text

    def _add_block(btype, text):
        text = _clean(text)
        if not text:
            return
        # Skip bare .html links
        if _BARE_HTML_LINK.match(text):
            return
        # Skip duplicate titles
        if btype == HEADING:
            key = text.lower().strip()
            if key in seen_titles:
                return
            seen_titles.add(key)
        # Skip very short noise lines
        if len(text) < 3 and btype == PARA:
            return
        blocks.append((btype, text))

    # Walk the main content tree
    for element in main.find_all([
        "h1", "h2", "h3", "h4",
        "p", "li", "pre", "code",
        "dt", "dd", "blockquote",
    ]):
        tag_name = element.name

        # Headings
        if tag_name in ("h1", "h2", "h3", "h4"):
            text = element.get_text().strip()
            _add_block(HEADING, text)

        # Code blocks
        elif tag_name == "pre":
            text = element.get_text()
            if text.strip():
                _add_block(CODE, text.strip())

        # Inline code that's a direct child (not inside <pre>)
        elif tag_name == "code":
            # Skip if parent is <pre> (already handled)
            if element.parent and element.parent.name == "pre":
                continue
            # Small inline code — skip (handled as part of <p>)
            continue

        # List items
        elif tag_name == "li":
            text = element.get_text().strip()
            _add_block(LIST_ITEM, text)

        # Paragraphs and description terms
        elif tag_name in ("p", "dt", "dd", "blockquote"):
            text = element.get_text().strip()
            _add_block(PARA, text)

    # Fallback if no structured content found
    if not blocks:
        text = main.get_text(separator="\n")
        text = _clean(text)
        if text:
            for line in text.split("\n"):
                line = line.strip()
                if line and not _BARE_HTML_LINK.match(line):
                    _add_block(PARA, line)

    # Get title from first heading if not found
    if not title and blocks:
        for btype, text in blocks:
            if btype == HEADING:
                title = text
                break

    return title, blocks


def extract_structured_txt(filepath):
    """Extract structured content from a plain text file.

    Returns:
        tuple: (title, blocks)
    """
    try:
        with open(filepath, "r", encoding="utf-8",
                  errors="ignore") as f:
            text = f.read()
    except Exception:
        return None, []

    blocks = []
    title = ""

    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue

        # Detect headings (ALL CAPS lines, or lines followed
        # by === or ---)
        if (stripped.isupper() and len(stripped) > 3
                and len(stripped) < 80):
            blocks.append((HEADING, stripped))
            if not title:
                title = stripped
        elif stripped.startswith("# "):
            blocks.append((HEADING, stripped[2:].strip()))
            if not title:
                title = stripped[2:].strip()
        elif stripped.startswith("## "):
            blocks.append((HEADING, stripped[3:].strip()))
        elif stripped.startswith("- ") or stripped.startswith("* "):
            blocks.append((LIST_ITEM, stripped[2:].strip()))
        elif stripped.startswith("  ") and any(
                c in stripped for c in "=.("):
            blocks.append((CODE, stripped))
        else:
            blocks.append((PARA, stripped))

    if not title:
        title = os.path.splitext(
            os.path.basename(filepath)
        )[0].replace("_", " ").title()

    return title, blocks


# ---------------------------------------------------------------------------
# Document loading
# ---------------------------------------------------------------------------

def load_docs_structured(docs_dir, excluded_dirs=None):
    """Load all documents with structured extraction.

    Returns:
        list of (source_path, title, blocks) tuples
        where blocks is [(block_type, text), ...]
    """
    if excluded_dirs is None:
        excluded_dirs = {
            "api", "cctbx_api", "phenix_api", "ai_db",
            "__pycache__", ".git", "rst_bak",
        }
    else:
        excluded_dirs = set(excluded_dirs)

    result = []

    for dirpath, dirnames, filenames in os.walk(
            docs_dir, topdown=True):
        dirnames[:] = [
            d for d in dirnames
            if d not in excluded_dirs
            and not d.endswith("_api")
        ]
        for filename in sorted(filenames):
            if filename.startswith("."):
                continue
            filepath = os.path.join(dirpath, filename)
            ext = os.path.splitext(filename)[1].lower()

            try:
                if ext == ".html":
                    title, blocks = extract_structured_html(
                        filepath)
                elif ext == ".txt":
                    title, blocks = extract_structured_txt(
                        filepath)
                else:
                    continue

                if blocks and len(blocks) >= 2:
                    result.append((filepath, title, blocks))
            except Exception as e:
                print("  SKIP %s: %s" % (filepath, e))

    print("Loaded %d documents from %s" % (
        len(result), docs_dir))
    return result


# ---------------------------------------------------------------------------
# Categorizer
# ---------------------------------------------------------------------------

def categorize_by_path(source_path):
    """Assign a document to a category by file path."""
    path_lower = source_path.lower().replace("\\", "/")
    for cat_name, patterns in CATEGORIES.items():
        for pattern in patterns:
            if re.search(pattern, path_lower):
                return cat_name
    return FALLBACK_CATEGORY


# ---------------------------------------------------------------------------
# Rebalancing: split large groups, merge small ones
# ---------------------------------------------------------------------------

def rebalance_groups(groups, max_pages=20, min_pages=3):
    """Split large categories and merge small ones.

    Args:
        groups: dict {category: [(source, title, blocks), ...]}
        max_pages: Maximum docs per PDF (split if exceeded)
        min_pages: Minimum docs per PDF (merge if below)

    Returns:
        dict: Rebalanced groups, possibly with new keys like
              "overview_part1", "overview_part2" for splits, and
              "miscellaneous" for merged small groups.
    """
    result = OrderedDict()

    small_bucket = []   # Accumulate small categories here
    small_labels = []   # Track which categories were merged

    for cat in sorted(groups.keys()):
        pages = groups[cat]

        if len(pages) > max_pages:
            # Split into chunks of max_pages
            n_parts = (len(pages) + max_pages - 1) // max_pages
            chunk_size = (len(pages) + n_parts - 1) // n_parts
            for i in range(n_parts):
                start = i * chunk_size
                end = min(start + chunk_size, len(pages))
                chunk = pages[start:end]
                if not chunk:
                    continue
                part_key = "%s_part%d" % (cat, i + 1)
                result[part_key] = chunk
                # Register a display title for the part
                base_title = CATEGORY_TITLES.get(
                    cat, cat.replace("_", " ").title())
                CATEGORY_TITLES[part_key] = (
                    "%s (Part %d of %d)"
                    % (base_title, i + 1, n_parts))

        elif len(pages) < min_pages:
            # Too small — accumulate for merging
            small_bucket.extend(pages)
            small_labels.append(cat)

        else:
            # Normal size — keep as-is
            result[cat] = pages

    # Merge small categories
    if small_bucket:
        if len(small_bucket) > max_pages:
            # Even the merged bucket is large — split it too
            n_parts = (
                (len(small_bucket) + max_pages - 1)
                // max_pages)
            chunk_size = (
                (len(small_bucket) + n_parts - 1)
                // n_parts)
            for i in range(n_parts):
                start = i * chunk_size
                end = min(
                    start + chunk_size, len(small_bucket))
                chunk = small_bucket[start:end]
                if not chunk:
                    continue
                key = "miscellaneous_part%d" % (i + 1)
                result[key] = chunk
                CATEGORY_TITLES[key] = (
                    "Phenix Documentation — Miscellaneous"
                    " (Part %d of %d)" % (i + 1, n_parts))
        else:
            result["miscellaneous"] = small_bucket
            CATEGORY_TITLES["miscellaneous"] = (
                "Phenix Documentation — Miscellaneous")
        print("\n  Merged %d small categories into "
              "miscellaneous: %s"
              % (len(small_labels),
                 ", ".join(small_labels)))

    return result


# ---------------------------------------------------------------------------
# PDF generator with structured formatting
# ---------------------------------------------------------------------------

def _escape_xml(text):
    """Escape text for reportlab Paragraph XML."""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = re.sub(
        r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    return text


def generate_pdf(category, pages, output_dir):
    """Generate a well-formatted PDF.

    Args:
        category: Category name
        pages: list of (source_path, title, blocks) tuples
        output_dir: Where to write the PDF

    Returns:
        str: Path to PDF, or None
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer,
        PageBreak, Preformatted, HRFlowable,
    )
    from reportlab.lib.styles import (
        getSampleStyleSheet, ParagraphStyle,
    )

    if not pages:
        return None

    filename = "phenix_%s.pdf" % category
    filepath = os.path.join(output_dir, filename)

    doc = SimpleDocTemplate(
        filepath, pagesize=letter,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
        leftMargin=0.8 * inch,
        rightMargin=0.8 * inch,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    s_cover_title = ParagraphStyle(
        "CoverTitle", parent=styles["Title"],
        fontSize=22, spaceAfter=16,
        textColor=HexColor("#1a365d"))
    s_cover_sub = ParagraphStyle(
        "CoverSub", parent=styles["Normal"],
        fontSize=12, textColor=HexColor("#666666"),
        spaceAfter=6)
    s_doc_title = ParagraphStyle(
        "DocTitle", parent=styles["Heading1"],
        fontSize=16, spaceBefore=0, spaceAfter=8,
        textColor=HexColor("#1a365d"),
        borderWidth=0, borderPadding=0)
    s_source = ParagraphStyle(
        "Source", parent=styles["Normal"],
        fontSize=8, textColor=HexColor("#999999"),
        spaceAfter=10)
    s_heading = ParagraphStyle(
        "SectionHeading", parent=styles["Heading2"],
        fontSize=12, spaceBefore=14, spaceAfter=6,
        textColor=HexColor("#2c5282"))
    s_body = ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontSize=10, leading=14, alignment=TA_LEFT,
        spaceAfter=6)
    s_list = ParagraphStyle(
        "ListItem", parent=styles["Normal"],
        fontSize=10, leading=14, leftIndent=20,
        spaceAfter=4, bulletIndent=8)
    s_code = ParagraphStyle(
        "Code", parent=styles["Code"],
        fontSize=8, leading=10, leftIndent=16,
        spaceAfter=8, spaceBefore=4,
        backColor=HexColor("#f5f5f5"),
        borderWidth=0.5,
        borderColor=HexColor("#dddddd"),
        borderPadding=6)

    story = []

    # --- Cover page ---
    doc_title = CATEGORY_TITLES.get(
        category,
        category.replace("_", " ").title())
    story.append(Spacer(1, 2 * inch))
    story.append(
        Paragraph(doc_title, s_cover_title))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "%d documentation pages" % len(pages),
        s_cover_sub))
    story.append(Paragraph(
        "Generated from local Phenix documentation",
        s_cover_sub))

    # Table of contents
    story.append(Spacer(1, 36))
    story.append(Paragraph("Contents", s_heading))
    for i, (source, page_title, blocks) in enumerate(
            pages):
        safe = _escape_xml(page_title or "Untitled")
        story.append(Paragraph(
            "%d. %s" % (i + 1, safe), s_body))
    story.append(PageBreak())

    # --- Each document ---
    for i, (source, page_title, blocks) in enumerate(
            pages):
        if i > 0:
            story.append(PageBreak())

        # Document title
        safe_title = _escape_xml(
            page_title or "Untitled")
        story.append(
            Paragraph(safe_title, s_doc_title))

        # Thin separator line
        story.append(HRFlowable(
            width="100%", thickness=0.5,
            color=HexColor("#cccccc"),
            spaceAfter=8))

        # Source filename (small, gray)
        safe_source = _escape_xml(
            os.path.basename(source))
        story.append(
            Paragraph(safe_source, s_source))

        # Content blocks
        prev_type = None
        for btype, text in blocks:
            safe = _escape_xml(text)
            if not safe.strip():
                continue
            # Limit very long blocks
            if len(safe) > 4000:
                safe = safe[:4000] + "..."
            # Skip blocks that duplicate the document title
            if (text.lower().strip()
                    == (page_title or "").lower().strip()):
                continue

            try:
                if btype == HEADING:
                    story.append(
                        Paragraph(safe, s_heading))

                elif btype == CODE:
                    # Preformatted code block
                    story.append(Preformatted(
                        safe, s_code))

                elif btype == LIST_ITEM:
                    bullet = "\u2022 " + safe
                    story.append(
                        Paragraph(bullet, s_list))

                else:  # PARA
                    story.append(
                        Paragraph(safe, s_body))

            except Exception:
                pass  # Skip unparseable content

            prev_type = btype

    # Build PDF
    try:
        doc.build(story)
        size_mb = os.path.getsize(filepath) / 1024 / 1024
        print("  %-30s %3d pages  %.1f MB" % (
            filename, len(pages), size_mb))
        return filepath
    except Exception as e:
        print("  ERROR %s: %s" % (filename, e))
        return None


# ---------------------------------------------------------------------------
# Find Phenix docs directory
# ---------------------------------------------------------------------------

def find_phenix_docs_dir():
    """Auto-detect the Phenix documentation directory."""
    try:
        import libtbx.load_env
        docs_dir = libtbx.env.under_root("doc")
        if docs_dir and os.path.isdir(docs_dir):
            return docs_dir
        if getattr(libtbx.env, "installed", False):
            alt = os.path.join(
                libtbx.env.under_root("phenix"), "doc")
            if os.path.isdir(alt):
                return alt
    except Exception:
        pass

    phenix = os.environ.get("PHENIX")
    if phenix:
        for sub in ["doc", "share/doc", "phenix/doc"]:
            candidate = os.path.join(phenix, sub)
            if os.path.isdir(candidate):
                return candidate

    return None


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def build_docs(docs_dir, output_dir,
               max_pages=20, min_pages=3):
    """Full pipeline: load -> categorize -> rebalance -> generate PDFs."""
    os.makedirs(output_dir, exist_ok=True)

    # Load
    print("=" * 60)
    print("  Loading from %s" % docs_dir)
    print("=" * 60)
    pages = load_docs_structured(docs_dir)
    if not pages:
        print("ERROR: No documents found")
        return []

    # Categorize
    print("\n" + "=" * 60)
    print("  Categorizing %d documents" % len(pages))
    print("=" * 60)
    groups = defaultdict(list)
    for source, title, blocks in pages:
        cat = categorize_by_path(source)
        groups[cat].append((source, title, blocks))

    print("\n  %-28s %5s" % ("Category", "Pages"))
    print("  " + "-" * 38)
    for cat in sorted(groups.keys()):
        print("  %-28s %5d" % (cat, len(groups[cat])))
    print("  " + "-" * 38)
    print("  %-28s %5d" % ("TOTAL", len(pages)))

    # Rebalance: split large, merge small
    groups = rebalance_groups(groups, max_pages, min_pages)

    print("\n  After rebalancing:")
    print("  %-28s %5s" % ("PDF", "Pages"))
    print("  " + "-" * 38)
    for cat in sorted(groups.keys()):
        print("  %-28s %5d" % (cat, len(groups[cat])))
    print("  " + "-" * 38)
    print("  %-28s %5d  (%d PDFs)" % (
        "TOTAL", sum(len(v) for v in groups.values()),
        len(groups)))

    # Generate PDFs
    print("\n" + "=" * 60)
    print("  Generating PDFs in %s" % output_dir)
    print("=" * 60)
    generated = []
    for cat in sorted(groups.keys()):
        pdf = generate_pdf(cat, groups[cat], output_dir)
        if pdf:
            generated.append(pdf)

    total_mb = sum(
        os.path.getsize(p) / 1024 / 1024
        for p in generated)
    print("\n" + "=" * 60)
    print("  %d PDFs, %.1f MB total" % (
        len(generated), total_mb))
    print("=" * 60)
    for p in generated:
        print("  %s" % os.path.basename(p))

    return generated


def main():
    parser = argparse.ArgumentParser(
        description="Build Phenix doc PDFs for "
                    "NotebookLM Chat")
    parser.add_argument(
        "--docs-dir", default=None,
        help="Phenix docs directory (auto-detected)")
    parser.add_argument(
        "--output-dir", default="./documentation/",
        help="Output dir (default: ./documentation/)")
    parser.add_argument(
        "--max-pages", type=int, default=20,
        help="Max docs per PDF; larger groups are "
             "split (default: 20)")
    parser.add_argument(
        "--min-pages", type=int, default=3,
        help="Min docs per PDF; smaller groups are "
             "merged (default: 3)")
    args = parser.parse_args()

    docs_dir = args.docs_dir or find_phenix_docs_dir()
    if not docs_dir or not os.path.isdir(docs_dir):
        print("ERROR: Cannot find Phenix docs.\n"
              "Use --docs-dir or set $PHENIX.")
        sys.exit(1)

    build_docs(docs_dir, args.output_dir,
               max_pages=args.max_pages,
               min_pages=args.min_pages)


if __name__ == "__main__":
    main()
