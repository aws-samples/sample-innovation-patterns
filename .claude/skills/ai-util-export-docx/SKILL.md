---
name: ai-util-export-docx
description: "Export a markdown file to Microsoft Word (.docx) format. Use when the user says 'export to word', 'export to docx', 'convert to word', 'make a word doc', 'markdown to docx', 'aidoc docx', 'export aidoc to word', or wants to produce a .docx file from a markdown document. Supports both aidoc drafts and general markdown files. If a .dotx template is available, applies the template's styles."
model: opus
effort: medium
---

# Agent Docs: Export to DOCX

You convert an aidoc draft.md into a Microsoft Word .docx file using a zero-dependency Python converter embedded below. If a .dotx template is available, it applies the template's styles, theme, fonts, and page layout.

## User Input

```text
$ARGUMENTS
```

Expected: `[document-name]` — which document folder to export.

## Step 1: Read the Brief

Read `.context/README.md` from the project root.

- If not found: warn and suggest `/ai-init`. Continue if the user insists, but note that the export won't have project context.
- If found: parse `output_path.ai-doc` from frontmatter.

## Step 2: Resolve the Document Folder

1. If `$ARGUMENTS` specifies a document name → use `<output_path.ai-doc>/<name>/`
2. If one folder in `<output_path.ai-doc>/` → use it
3. If multiple folders → list and ask
4. If no folders → suggest `/ai-doc-create`

## Step 3: Read draft.md

Read `<doc-folder>/draft.md` as the conversion input.

- If not found: stop and tell the user to run `/ai-doc-draft <name>` first.

## Step 3.5: Locate Template

Check for a `.dotx` template in precedence order:

1. `<doc-folder>/template.dotx` (per-document template)
2. `<output_path.ai-doc>/template.dotx` (project-wide template)
3. `.context/template.dotx` (repo-level default)

- If found: note the template path — pass it as the third argument to the converter.
- If not found: proceed without a template (converter uses hardcoded defaults).

**ultrathink** — DOCX template application requires matching heading levels to style names, resolving conflicts between markdown structure and template hierarchy, and validating that custom styles exist in the .dotx before referencing them. Silent failures produce corrupt formatting that only surfaces when the user opens the file.

## Step 4: Convert to DOCX

Determine the output path: `<doc-folder>/<name>.docx` where `<name>` is the document folder name.

Run the converter by copying the script below **verbatim** into a Bash heredoc. Replace `INPUT_PATH`, `OUTPUT_PATH`, and optionally `TEMPLATE_PATH` with actual paths:

```bash
# Without template:
python3 - "INPUT_PATH" "OUTPUT_PATH" <<'PYEOF'
# [copy the entire converter script below]
PYEOF

# With template:
python3 - "INPUT_PATH" "OUTPUT_PATH" "TEMPLATE_PATH" <<'PYEOF'
# [copy the entire converter script below]
PYEOF
```

If the command exits with non-zero status, read the error output and consult the Troubleshooting Reference below.

### Converter Script

```python
#!/usr/bin/env python3
"""Markdown to .docx converter — zero external dependencies, best-effort .dotx template support.

Supported: headings (H1-H6), paragraphs, bold, italic, bold+italic, strikethrough,
inline code, bullet lists, numbered lists (with restart), nested lists (3 levels),
fenced code blocks, blockquotes, tables, hyperlinks, horizontal rules.

Template: extracts styles.xml, theme/theme1.xml, fontTable.xml, and sectPr from .dotx.
Does NOT extract headers/footers, media, custom numbering, or document settings.

Usage: python3 - INPUT.md OUTPUT.docx [TEMPLATE.dotx]
"""
import re
import sys
import zipfile
from io import BytesIO
import xml.etree.ElementTree as ET


# ═══════════════════════════════════════════════════════════════════
# XML SCAFFOLDING
# ═══════════════════════════════════════════════════════════════════

RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1"'
    ' Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"'
    ' Target="word/document.xml"/>'
    '</Relationships>'
)

DEFAULT_STYLES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
    # Document defaults: Times New Roman 10pt, single spacing, 6pt after
    '<w:docDefaults>'
    '<w:rPrDefault><w:rPr>'
    '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>'
    '<w:sz w:val="20"/><w:szCs w:val="20"/>'
    '</w:rPr></w:rPrDefault>'
    '<w:pPrDefault><w:pPr>'
    '<w:spacing w:after="120" w:line="240" w:lineRule="auto"/>'
    '</w:pPr></w:pPrDefault>'
    '</w:docDefaults>'
    # Normal
    '<w:style w:type="paragraph" w:default="1" w:styleId="Normal">'
    '<w:name w:val="Normal"/><w:qFormat/></w:style>'
    # Heading 1 — 20pt bold
    '<w:style w:type="paragraph" w:styleId="Heading1">'
    '<w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>'
    '<w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="240" w:after="120"/>'
    '<w:outlineLvl w:val="0"/></w:pPr>'
    '<w:rPr><w:b/><w:bCs/><w:sz w:val="40"/><w:szCs w:val="40"/></w:rPr></w:style>'
    # Heading 2 — 16pt bold
    '<w:style w:type="paragraph" w:styleId="Heading2">'
    '<w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>'
    '<w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="200" w:after="80"/>'
    '<w:outlineLvl w:val="1"/></w:pPr>'
    '<w:rPr><w:b/><w:bCs/><w:sz w:val="32"/><w:szCs w:val="32"/></w:rPr></w:style>'
    # Heading 3 — 13pt bold
    '<w:style w:type="paragraph" w:styleId="Heading3">'
    '<w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>'
    '<w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="160" w:after="80"/>'
    '<w:outlineLvl w:val="2"/></w:pPr>'
    '<w:rPr><w:b/><w:bCs/><w:sz w:val="26"/><w:szCs w:val="26"/></w:rPr></w:style>'
    # Heading 4 — 10pt bold
    '<w:style w:type="paragraph" w:styleId="Heading4">'
    '<w:name w:val="heading 4"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>'
    '<w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="120" w:after="80"/>'
    '<w:outlineLvl w:val="3"/></w:pPr>'
    '<w:rPr><w:b/><w:bCs/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr></w:style>'
    # Heading 5 — 10pt bold italic
    '<w:style w:type="paragraph" w:styleId="Heading5">'
    '<w:name w:val="heading 5"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>'
    '<w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="80" w:after="40"/>'
    '<w:outlineLvl w:val="4"/></w:pPr>'
    '<w:rPr><w:b/><w:bCs/><w:i/><w:iCs/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr></w:style>'
    # Heading 6 — 10pt italic
    '<w:style w:type="paragraph" w:styleId="Heading6">'
    '<w:name w:val="heading 6"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>'
    '<w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="80" w:after="40"/>'
    '<w:outlineLvl w:val="5"/></w:pPr>'
    '<w:rPr><w:i/><w:iCs/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr></w:style>'
    # List Paragraph
    '<w:style w:type="paragraph" w:styleId="ListParagraph">'
    '<w:name w:val="List Paragraph"/><w:basedOn w:val="Normal"/><w:qFormat/>'
    '<w:pPr><w:ind w:left="720"/></w:pPr></w:style>'
    '</w:styles>'
)

ABSTRACT_NUMBERING = (
    # Bullets: bullet, hollow circle, dash (3 levels)
    '<w:abstractNum w:abstractNumId="0">'
    '<w:multiLevelType w:val="hybridMultilevel"/>'
    '<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/>'
    '<w:lvlText w:val="&#x2022;"/><w:lvlJc w:val="left"/>'
    '<w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr>'
    '<w:rPr><w:rFonts w:ascii="Symbol" w:hAnsi="Symbol" w:hint="default"/></w:rPr></w:lvl>'
    '<w:lvl w:ilvl="1"><w:start w:val="1"/><w:numFmt w:val="bullet"/>'
    '<w:lvlText w:val="&#x25CB;"/><w:lvlJc w:val="left"/>'
    '<w:pPr><w:ind w:left="1440" w:hanging="360"/></w:pPr>'
    '<w:rPr><w:rFonts w:ascii="Courier New" w:hAnsi="Courier New" w:hint="default"/></w:rPr></w:lvl>'
    '<w:lvl w:ilvl="2"><w:start w:val="1"/><w:numFmt w:val="bullet"/>'
    '<w:lvlText w:val="&#x2013;"/><w:lvlJc w:val="left"/>'
    '<w:pPr><w:ind w:left="2160" w:hanging="360"/></w:pPr>'
    '<w:rPr><w:rFonts w:ascii="Courier New" w:hAnsi="Courier New" w:hint="default"/></w:rPr></w:lvl>'
    '</w:abstractNum>'
    # Decimal numbered: 1., a., i. (3 levels)
    '<w:abstractNum w:abstractNumId="1">'
    '<w:multiLevelType w:val="hybridMultilevel"/>'
    '<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="decimal"/>'
    '<w:lvlText w:val="%1."/><w:lvlJc w:val="left"/>'
    '<w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr></w:lvl>'
    '<w:lvl w:ilvl="1"><w:start w:val="1"/><w:numFmt w:val="lowerLetter"/>'
    '<w:lvlText w:val="%2."/><w:lvlJc w:val="left"/>'
    '<w:pPr><w:ind w:left="1440" w:hanging="360"/></w:pPr></w:lvl>'
    '<w:lvl w:ilvl="2"><w:start w:val="1"/><w:numFmt w:val="lowerRoman"/>'
    '<w:lvlText w:val="%3."/><w:lvlJc w:val="left"/>'
    '<w:pPr><w:ind w:left="2160" w:hanging="360"/></w:pPr></w:lvl>'
    '</w:abstractNum>'
)

DEFAULT_SECT_PR = (
    '<w:sectPr>'
    '<w:pgSz w:w="12240" w:h="15840"/>'
    '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"'
    ' w:header="720" w:footer="720" w:gutter="0"/>'
    '</w:sectPr>'
)


# ═══════════════════════════════════════════════════════════════════
# XML HELPERS
# ═══════════════════════════════════════════════════════════════════

def esc(text):
    """Escape XML entities. & must be replaced first."""
    return (text.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def wt(text):
    """Wrap text in <w:t>, adding xml:space='preserve' when needed."""
    escaped = esc(text)
    if text and (text[0] == " " or text[-1] == " "):
        return f'<w:t xml:space="preserve">{escaped}</w:t>'
    return f"<w:t>{escaped}</w:t>"


def make_run(text, bold=False, italic=False, code=False, strike=False):
    """Build a single <w:r> element with optional formatting."""
    rpr = []
    if code:
        rpr.append(
            '<w:rFonts w:ascii="Courier New" w:hAnsi="Courier New" w:cs="Courier New"/>'
            '<w:shd w:val="clear" w:color="auto" w:fill="E8E8E8"/>'
        )
    if bold:
        rpr.append("<w:b/><w:bCs/>")
    if italic:
        rpr.append("<w:i/><w:iCs/>")
    if strike:
        rpr.append("<w:strike/>")
    rpr_xml = f'<w:rPr>{"".join(rpr)}</w:rPr>' if rpr else ""
    return f"<w:r>{rpr_xml}{wt(text)}</w:r>"


# ═══════════════════════════════════════════════════════════════════
# INLINE PARSER
# ═══════════════════════════════════════════════════════════════════

class InlineParser:
    """Parses inline markdown into <w:r> XML, tracking hyperlink relationships."""

    def __init__(self):
        self.hyperlinks = []  # list of (rId, url)
        self.next_rel_id = 100  # start high to avoid collision with template rIds

    def parse_inline(self, text):
        """Parse inline markdown into concatenated XML runs."""
        runs = []
        pat = re.compile(
            r'\[([^\]]+)\]\(([^)]+)\)'   # 1,2: hyperlink [text](url)
            r'|`([^`]+)`'                # 3: inline code
            r'|~~(.+?)~~'                # 4: strikethrough
            r'|\*\*\*(.+?)\*\*\*'        # 5: bold+italic
            r'|\*\*(.+?)\*\*'            # 6: bold
            r'|\*(.+?)\*'               # 7: italic
            r'|([^`*~\[]+)'             # 8: plain text
        )
        for m in pat.finditer(text):
            if m.group(1) is not None:
                rid = f"rId{self.next_rel_id}"
                self.next_rel_id += 1
                self.hyperlinks.append((rid, m.group(2)))
                runs.append(
                    f'<w:hyperlink r:id="{rid}">'
                    f'<w:r><w:rPr>'
                    f'<w:color w:val="0563C1"/><w:u w:val="single"/>'
                    f'</w:rPr>{wt(m.group(1))}</w:r>'
                    f'</w:hyperlink>'
                )
            elif m.group(3) is not None:
                runs.append(make_run(m.group(3), code=True))
            elif m.group(4) is not None:
                runs.append(make_run(m.group(4), strike=True))
            elif m.group(5) is not None:
                runs.append(make_run(m.group(5), bold=True, italic=True))
            elif m.group(6) is not None:
                runs.append(make_run(m.group(6), bold=True))
            elif m.group(7) is not None:
                runs.append(make_run(m.group(7), italic=True))
            elif m.group(8) is not None:
                runs.append(make_run(m.group(8)))
        return "".join(runs)


# ═══════════════════════════════════════════════════════════════════
# TABLE PARSER
# ═══════════════════════════════════════════════════════════════════

def parse_table(lines, start, ip):
    """Parse a markdown table. Returns (xml_string, next_index) or (None, start)."""
    rows = []
    i = start
    while i < len(lines) and '|' in lines[i]:
        cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
        rows.append(cells)
        i += 1

    if len(rows) < 2:
        return None, start

    # Validate separator row (row index 1 must contain dashes/colons)
    if not all(re.match(r'^[-:]+$', c) for c in rows[1] if c):
        return None, start

    header, data = rows[0], rows[2:]
    nc = len(header)
    cw = 9360 // nc
    lw = 9360 - cw * (nc - 1)  # last column absorbs rounding remainder

    grid = ''.join(
        f'<w:gridCol w:w="{lw if j == nc - 1 else cw}"/>' for j in range(nc)
    )

    def mk_row(cells, hdr=False):
        tcs = []
        for j in range(nc):
            txt = cells[j] if j < len(cells) else ""
            w = lw if j == nc - 1 else cw
            r = ip.parse_inline(txt) if txt else ""
            shd = '<w:shd w:val="clear" w:color="auto" w:fill="D9E2F3"/>' if hdr else ''
            tcs.append(
                f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>{shd}</w:tcPr>'
                f'<w:p>{r}</w:p></w:tc>'
            )
        return f'<w:tr>{"".join(tcs)}</w:tr>'

    hdr_row = mk_row(header, hdr=True)
    data_xml = ''.join(mk_row(r) for r in data)

    return (
        '<w:tbl><w:tblPr>'
        '<w:tblW w:w="9360" w:type="dxa"/>'
        '<w:tblBorders>'
        '<w:top w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
        '<w:left w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
        '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
        '<w:right w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
        '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
        '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
        '</w:tblBorders>'
        '<w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0"'
        ' w:firstColumn="1" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/>'
        '</w:tblPr>'
        f'<w:tblGrid>{grid}</w:tblGrid>'
        f'{hdr_row}{data_xml}</w:tbl>'
    ), i


# ═══════════════════════════════════════════════════════════════════
# BLOCK PARSER
# ═══════════════════════════════════════════════════════════════════

def md_to_body(md_text, ip):
    """Convert Markdown text to XML body elements.
    Returns (list_of_xml_strings, max_num_id_used)."""
    paras = []
    lines = md_text.split("\n")
    i = 0
    next_num_id = 2   # 1 = bullets, 2 = first numbered list, 3+ = restart
    in_num = False
    cur_num_id = 2

    while i < len(lines):
        line = lines[i]

        # ── Blank line ──
        if not line.strip():
            if in_num:
                in_num = False
            i += 1
            continue

        # ── Fenced code block ──
        if line.strip().startswith("```"):
            i += 1
            code = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1  # skip closing fence
            for cl in code:
                e = esc(cl) if cl.strip() else ""
                if cl and (cl[0] in " \t" or cl[-1] == " "):
                    t = f'<w:t xml:space="preserve">{e}</w:t>'
                elif not cl.strip():
                    t = '<w:t/>'
                else:
                    t = f'<w:t>{e}</w:t>'
                paras.append(
                    '<w:p><w:pPr>'
                    '<w:shd w:val="clear" w:color="auto" w:fill="F5F5F5"/>'
                    '<w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/>'
                    '<w:ind w:left="240" w:right="240"/>'
                    '</w:pPr><w:r><w:rPr>'
                    '<w:rFonts w:ascii="Courier New" w:hAnsi="Courier New" w:cs="Courier New"/>'
                    f'<w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr>{t}</w:r></w:p>'
                )
            in_num = False
            continue

        # ── Horizontal rule ──
        if re.match(r'^(\s*)(---+|___+|\*\*\*+)\s*$', line):
            paras.append(
                '<w:p><w:pPr><w:pBdr>'
                '<w:bottom w:val="single" w:sz="6" w:space="1" w:color="999999"/>'
                '</w:pBdr></w:pPr></w:p>'
            )
            in_num = False
            i += 1
            continue

        # ── Heading ──
        hm = re.match(r'^(#{1,6})\s+(.+)$', line)
        if hm:
            lvl = len(hm.group(1))
            runs = ip.parse_inline(hm.group(2).strip())
            paras.append(
                f'<w:p><w:pPr><w:pStyle w:val="Heading{lvl}"/></w:pPr>{runs}</w:p>'
            )
            in_num = False
            i += 1
            continue

        # ── Blockquote ──
        if line.startswith("> ") or line == ">":
            txt = line[2:] if line.startswith("> ") else ""
            runs = ip.parse_inline(txt) if txt else ""
            paras.append(
                '<w:p><w:pPr>'
                '<w:pBdr><w:left w:val="single" w:sz="12" w:space="8" w:color="AAAAAA"/></w:pBdr>'
                '<w:spacing w:before="120" w:after="120"/>'
                '<w:ind w:left="480"/>'
                f'</w:pPr>{runs}</w:p>'
            )
            in_num = False
            i += 1
            continue

        # ── Bullet list item ──
        bm = re.match(r'^(\s*)[-*+]\s+(.+)$', line)
        if bm:
            lvl = min(len(bm.group(1)) // 2, 2)
            runs = ip.parse_inline(bm.group(2))
            paras.append(
                f'<w:p><w:pPr><w:pStyle w:val="ListParagraph"/>'
                f'<w:numPr><w:ilvl w:val="{lvl}"/><w:numId w:val="1"/></w:numPr>'
                f'</w:pPr>{runs}</w:p>'
            )
            in_num = False
            i += 1
            continue

        # ── Numbered list item ──
        nm = re.match(r'^(\s*)\d+\.\s+(.+)$', line)
        if nm:
            if not in_num:
                cur_num_id = next_num_id
                next_num_id += 1
                in_num = True
            lvl = min(len(nm.group(1)) // 3, 2)
            runs = ip.parse_inline(nm.group(2))
            paras.append(
                f'<w:p><w:pPr><w:pStyle w:val="ListParagraph"/>'
                f'<w:numPr><w:ilvl w:val="{lvl}"/><w:numId w:val="{cur_num_id}"/></w:numPr>'
                f'</w:pPr>{runs}</w:p>'
            )
            i += 1
            continue

        # ── Table ──
        if '|' in line and line.strip().startswith('|'):
            tbl, ni = parse_table(lines, i, ip)
            if tbl:
                paras.append(tbl)
                i = ni
                in_num = False
                continue

        # ── Normal paragraph (may span multiple lines) ──
        pl = []
        while (i < len(lines) and lines[i].strip()
               and not re.match(
                   r'^(#{1,6}\s|[-*+]\s|\d+\.\s|```|---+\s*$'
                   r'|\*\*\*+\s*$|___+\s*$|>|\|)', lines[i])):
            pl.append(lines[i].strip())
            i += 1
        if pl:
            runs = ip.parse_inline(" ".join(pl))
            paras.append(f"<w:p>{runs}</w:p>")
        else:
            i += 1  # skip unrecognized line to prevent infinite loop
        in_num = False

    return paras, next_num_id - 1


# ═══════════════════════════════════════════════════════════════════
# NUMBERING BUILDER
# ═══════════════════════════════════════════════════════════════════

def build_numbering_xml(max_num_id):
    """Build numbering.xml with bullet + numbered list definitions and restart entries."""
    max_num_id = max(max_num_id, 2)  # always include bullet and first number
    nums = [
        '<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>',
        '<w:num w:numId="2"><w:abstractNumId w:val="1"/></w:num>',
    ]
    for nid in range(3, max_num_id + 1):
        nums.append(
            f'<w:num w:numId="{nid}"><w:abstractNumId w:val="1"/>'
            f'<w:lvlOverride w:ilvl="0"><w:startOverride w:val="1"/></w:lvlOverride>'
            f'</w:num>'
        )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:numbering xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        + ABSTRACT_NUMBERING + ''.join(nums) + '</w:numbering>'
    )


# ═══════════════════════════════════════════════════════════════════
# CONTENT TYPES BUILDER
# ═══════════════════════════════════════════════════════════════════

def build_content_types(has_theme=False, has_font_table=False):
    """Build [Content_Types].xml dynamically based on included parts."""
    parts = [
        '<Override PartName="/word/document.xml"'
        ' ContentType="application/vnd.openxmlformats-officedocument'
        '.wordprocessingml.document.main+xml"/>',
        '<Override PartName="/word/styles.xml"'
        ' ContentType="application/vnd.openxmlformats-officedocument'
        '.wordprocessingml.styles+xml"/>',
        '<Override PartName="/word/numbering.xml"'
        ' ContentType="application/vnd.openxmlformats-officedocument'
        '.wordprocessingml.numbering+xml"/>',
    ]
    if has_theme:
        parts.append(
            '<Override PartName="/word/theme/theme1.xml"'
            ' ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>'
        )
    if has_font_table:
        parts.append(
            '<Override PartName="/word/fontTable.xml"'
            ' ContentType="application/vnd.openxmlformats-officedocument'
            '.wordprocessingml.fontTable+xml"/>'
        )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels"'
        ' ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        + ''.join(parts) + '</Types>'
    )


# ═══════════════════════════════════════════════════════════════════
# RELATIONSHIP BUILDER
# ═══════════════════════════════════════════════════════════════════

def build_doc_rels(hyperlinks, has_theme=False, has_font_table=False):
    """Build word/_rels/document.xml.rels with base rels + optional template rels + hyperlinks."""
    rels = [
        '<Relationship Id="rId1"'
        ' Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles"'
        ' Target="styles.xml"/>',
        '<Relationship Id="rId2"'
        ' Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering"'
        ' Target="numbering.xml"/>',
    ]
    if has_theme:
        rels.append(
            '<Relationship Id="rId3"'
            ' Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme"'
            ' Target="theme/theme1.xml"/>'
        )
    if has_font_table:
        rels.append(
            '<Relationship Id="rId4"'
            ' Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/fontTable"'
            ' Target="fontTable.xml"/>'
        )
    for rid, url in hyperlinks:
        rels.append(
            f'<Relationship Id="{rid}"'
            f' Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"'
            f' Target="{esc(url)}" TargetMode="External"/>'
        )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + ''.join(rels) + '</Relationships>'
    )


# ═══════════════════════════════════════════════════════════════════
# TEMPLATE EXTRACTOR
# ═══════════════════════════════════════════════════════════════════

def extract_template(template_path):
    """Extract style-related parts from a .dotx template. Best-effort — takes
    what's available, ignores headers/footers/media/numbering."""
    ET.register_namespace('w', 'http://schemas.openxmlformats.org/wordprocessingml/2006/main')
    ET.register_namespace('r', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships')
    parts = {}
    try:
        with zipfile.ZipFile(template_path, 'r') as tz:
            names = tz.namelist()
            if 'word/styles.xml' in names:
                parts['styles'] = tz.read('word/styles.xml')
            if 'word/theme/theme1.xml' in names:
                parts['theme'] = tz.read('word/theme/theme1.xml')
            if 'word/fontTable.xml' in names:
                parts['font_table'] = tz.read('word/fontTable.xml')
            if 'word/document.xml' in names:
                doc_xml = tz.read('word/document.xml')
                ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                root = ET.fromstring(doc_xml)
                sect = root.find('.//w:sectPr', ns)
                if sect is not None:
                    parts['sect_pr'] = ET.tostring(sect, encoding='unicode')
    except (zipfile.BadZipFile, KeyError, ET.ParseError) as e:
        print(f"Warning: Could not read template {template_path}: {e}", file=sys.stderr)
    return parts


# ═══════════════════════════════════════════════════════════════════
# DOCX ASSEMBLER
# ═══════════════════════════════════════════════════════════════════

def build_docx(md_text, template_path=None):
    """Convert Markdown string to .docx bytes. Optionally apply .dotx template."""
    tmpl = extract_template(template_path) if template_path else {}
    has_theme = 'theme' in tmpl
    has_ft = 'font_table' in tmpl

    ip = InlineParser()
    paras, max_num_id = md_to_body(md_text, ip)

    sect_pr = tmpl.get('sect_pr', DEFAULT_SECT_PR)
    body = "\n".join(paras)
    doc_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
        ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<w:body>{body}{sect_pr}</w:body></w:document>'
    )

    styles = tmpl.get('styles', DEFAULT_STYLES)
    if isinstance(styles, bytes):
        styles = styles.decode('utf-8')

    buf = BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('[Content_Types].xml', build_content_types(has_theme, has_ft))
        zf.writestr('_rels/.rels', RELS)
        zf.writestr('word/_rels/document.xml.rels',
                     build_doc_rels(ip.hyperlinks, has_theme, has_ft))
        zf.writestr('word/document.xml', doc_xml)
        zf.writestr('word/styles.xml', styles)
        zf.writestr('word/numbering.xml', build_numbering_xml(max_num_id))
        if has_theme:
            th = tmpl['theme']
            zf.writestr('word/theme/theme1.xml',
                         th.decode('utf-8') if isinstance(th, bytes) else th)
        if has_ft:
            ft = tmpl['font_table']
            zf.writestr('word/fontTable.xml',
                         ft.decode('utf-8') if isinstance(ft, bytes) else ft)
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════════
# CLI ENTRYPOINT
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 - INPUT.md OUTPUT.docx [TEMPLATE.dotx]", file=sys.stderr)
        sys.exit(1)
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        md = f.read()
    tmpl_path = sys.argv[3] if len(sys.argv) > 3 else None
    docx_bytes = build_docx(md, tmpl_path)
    with open(sys.argv[2], "wb") as f:
        f.write(docx_bytes)
    msg = f"Created {sys.argv[2]} ({len(docx_bytes):,} bytes)"
    if tmpl_path:
        msg += f" using template {tmpl_path}"
    print(msg)
```

## Step 5: Validate and Confirm

After the converter runs:

1. Check the `.docx` file exists and has non-zero size (use `ls -la`)
2. Report success: "Exported to `<doc-folder>/<name>.docx` (X bytes)"
3. If a template was used: note which template was applied
4. Suggest: "Open in Word, LibreOffice, or Google Docs to verify formatting"
5. Suggest: "To re-export after editing the draft: `/ai-util-export-docx <name>`"

Do NOT update `README.md` status — export is orthogonal to the research/outline/draft workflow.

## Troubleshooting Reference

### Common Errors

| Symptom | Cause | Fix |
|---------|-------|-----|
| "Unreadable content" on open | Malformed XML | Check entity escaping (`&` → `&amp;` must be first) |
| Words merge together | Missing `xml:space="preserve"` | Add to any `<w:t>` with leading/trailing space |
| Black background on shading | `w:val="solid"` in `<w:shd>` | Must use `w:val="clear"` |
| List numbering doesn't restart | Same `w:numId` across lists | Each separate list needs unique `w:numId` |
| Table renders wrong width | Mismatched widths | `tblW` must equal sum of `gridCol` = sum of `tcW` |
| Empty cell error | Missing paragraph | Every `<w:tc>` must contain at least one `<w:p>` |
| Content after sectPr | `<w:sectPr>` not last | Must be final child of `<w:body>` |
| pPr validation error | Wrong element order | pStyle, keepNext, keepLines, numPr, pBdr, shd, spacing, ind, jc, rPr |

### Inspecting a .docx

To debug a generated document:

```bash
mkdir debug_docx && cd debug_docx && unzip ../output.docx
python3 -c "
import xml.etree.ElementTree as ET, zipfile
errors = []
with zipfile.ZipFile('../output.docx', 'r') as zf:
    for name in zf.namelist():
        if name.endswith('.xml') or name.endswith('.rels'):
            try: ET.fromstring(zf.read(name))
            except ET.ParseError as e: errors.append(f'{name}: {e}')
print('Valid' if not errors else '\n'.join(errors))
"
```

### Critical Rules

**MUST DO:**
1. Escape XML entities: `&` first, then `<`, `>`, `"`
2. `xml:space="preserve"` on `<w:t>` with leading/trailing whitespace
3. Half-points for font sizes (pt * 2)
4. Twips for page dimensions/margins/spacing (inches * 1440)
5. `<w:pPr>` first in `<w:p>`, `<w:rPr>` first in `<w:r>`
6. `<w:sectPr>` last in `<w:body>`
7. Every `<w:tc>` must contain at least one `<w:p>`
8. Table widths must be consistent across tblW, gridCol, and tcW
9. `ZIP_DEFLATED` compression, UTF-8 encoding

**MUST NOT:**
1. No `\n` inside `<w:t>` — use separate `<w:p>` elements
2. No `w:val="solid"` for `<w:shd>` — use `"clear"`
3. No `w:type="pct"` for table widths — use `"dxa"`
4. No content after `<w:sectPr>` in `<w:body>`
5. No reusing `numId` across separate numbered lists

### Template Limitations

When a `.dotx` template is used, the converter extracts styles, theme, font table, and page layout. The following are **not** carried over — the user can add these in Word after export:

| Not Supported | Rationale |
|---------------|-----------|
| Headers and footers | Common post-export edit — user adds in Word |
| Embedded media (logos, watermarks) | Not a converter's job — user adds in Word |
| Custom list numbering definitions | Converter uses standard bullet/decimal |
| Document settings (tab stops, compat) | Defaults work fine |
| Attached template reference | Only matters in enterprise shared-template environments |

### Extending the Converter

To add features not in the current converter, consult the OOXML patterns:

- **Images**: Requires media relationship management + DrawingML — complex, skip for now
- **Footnotes**: Requires footnotes.xml + separator entries + relationship
- **TOC**: Field code `TOC \o "1-3" \h \z \u` — requires user to "Update" in Word
- **Headers/footers**: Requires header1.xml/footer1.xml + content types + relationships + sectPr references

For any extension, follow the critical rules above and validate all XML files parse correctly after assembly.
