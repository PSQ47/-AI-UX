---
name: xlsx-to-markdown
description: "Convert layout-style Excel files (.xlsx) to clean Markdown. Use when xlsx files are documents (game design docs, planning sheets, specs) rather than data tables. Handles smart column/row trimming, heading detection, table extraction, image export, and NaN elimination. Trigger phrases: 'convert xlsx to markdown', 'read this excel as document', 'extract excel content', 'xlsx转markdown', '读取策划文档', '读取Excel文档'."
---

# xlsx-to-markdown

## When to Use

This skill is for **layout-style Excel files** — spreadsheets used as documents rather than data tables.

Common characteristics:
- Very wide column ranges (e.g., 16384 cols) with actual content in only a few columns
- Mixed content: section headers, paragraphs, data tables, and embedded images
- Merged cells used for layout/formatting
- Low cell fill rate (mostly empty cells)
- No formulas or very few formulas
- Chinese or multilingual text content

**Do NOT use** for data-centric spreadsheets with formulas, financial models, or structured datasets — use the `xlsx` skill for those.

## Quick Start

```bash
# Detect file type first (fast, read-only, no output files)
python xlsx2md.py input.xlsx --detect

# Basic conversion
python xlsx2md.py input.xlsx

# Specify output path
python xlsx2md.py input.xlsx output.md

# Skip image extraction
python xlsx2md.py input.xlsx --no-images
```

### Decision Flow for AI Assistants

When a user asks to read/analyze an xlsx file, run `--detect` first:

```bash
python xlsx2md.py file.xlsx --detect
```

This outputs JSON with per-sheet classification:
```json
{
  "type": "document",        // overall: "document" | "data" | "mixed"
  "sheets": [
    { "sheet": "设计概述", "type": "document", "confidence": 0.95, "reason": "sparse rows 90%, long texts 15%" },
    { "sheet": "配置表", "type": "data", "confidence": 0.7, "reason": "avg 5.2 cells/row, long texts 1%" }
  ]
}
```

**Routing rules:**
- `"type": "document"` → Use this skill: `python xlsx2md.py file.xlsx` then read the .md
- `"type": "data"` → Use the `xlsx` skill (pandas/openpyxl direct read)
- `"type": "mixed"` → Use this skill — it handles both document and table regions, and the markdown output is still cleaner than raw xlsx for mixed files

**Detection dimensions** (sampled from first 30 rows per sheet):
- **Row content distribution**: Document-style sheets have mostly sparse rows (≤2 non-empty cells); data tables have 3+ cells per row consistently
- **Text length distribution**: Document-style sheets have cells with long text (>50 chars); data tables have short values

The script outputs:
- A `.md` file with clean, structured Markdown
- An `./images/` directory with extracted images (unless `--no-images`)

## How It Works

### Core Pipeline

1. **Smart range detection**: Scans all cells to find actual used column/row range, ignoring empty padding
2. **Merged cell handling**: Treats merged cells correctly — value belongs to top-left cell only
3. **Row-by-row classification**: Each row is classified as one of:
   - **Heading** → `## ` / `### ` / `#### ` (detected by position, font, numbering pattern)
   - **Key-value pair** → `- **Key**: Value` (detected by `：` or `:` patterns)
   - **Table region** → proper Markdown table with `| col | col |` format
   - **Paragraph** → flowing text (long single-cell content)
   - **Mixed content** → joined with ` | ` separator
4. **Image extraction**: Embedded images are saved to `./images/` with descriptive filenames derived from nearby cell text, and `![context](./images/filename)` references are inserted at the anchor position
5. **NaN/Unnamed elimination**: Never outputs "NaN" or "Unnamed" — these are artifacts of pandas that this script avoids entirely

### Dependencies

- `openpyxl` — the only Python dependency (no pandas needed)
- Python 3.10+

**First-time setup:**
```bash
pip install openpyxl
```

### Relationship with the `xlsx` Skill

This skill is a **complement** to the `xlsx` skill, NOT a replacement.

| Scenario | Use this skill (`xlsx-to-markdown`) | Use `xlsx` skill |
|---|---|---|
| Read a layout-style document (game design, specs, planning) | ✅ | ❌ Produces NaN-heavy noise |
| Read a data table / financial model | ❌ | ✅ |
| Create or write xlsx files | ❌ | ✅ |
| Recalculate formulas | ❌ | ✅ |
| Detect file type (data vs document) | ✅ `--detect` | ❌ |

**If a user's xlsx is detected as `"type": "data"`**, suggest using the `xlsx` skill instead. If the user doesn't have the `xlsx` skill installed, briefly explain:

> The `xlsx` skill provides spreadsheet creation, editing, and analysis capabilities with formula support, formatting, and LibreOffice-based recalculation. It's designed for data-centric Excel files. You can install it from the skills marketplace.

## Workflow for AI Assistants

When a user provides an xlsx file:

1. **Detect**: Run `python xlsx2md.py file.xlsx --detect` to classify
2. **Route**: Follow routing rules from Decision Flow above
3. **Convert** (if document/mixed): Run `python xlsx2md.py file.xlsx`
4. **Read**: Read the generated `.md` file for analysis
5. **If images matter**: They're in `./images/` — use vision tools to inspect specific images when needed

## Output Quality

Compared to `markitdown` (Microsoft's generic converter):

| Aspect | markitdown | xlsx-to-markdown |
|---|---|---|
| NaN noise | ❌ Outputs "NaN" for every empty cell | ✅ Zero NaN |
| Column headers | ❌ "Unnamed: 1" ~ "Unnamed: N" | ✅ No unnamed headers |
| Structure | ❌ One giant markdown table per sheet | ✅ Headings, paragraphs, tables properly separated |
| Images | ❌ Ignored | ✅ Extracted with context-aware filenames |
| Token efficiency | ~166 KB for test file | ~60 KB for same file (64% smaller) |

## ⚠️ IMPORTANT LIMITATIONS

**This skill is designed for TEXT PROCESSING. The following Excel elements are NOT supported:**

| Element | Status | Notes |
|---------|--------|-------|
| **Geometric shapes** | ❌ NOT extracted | Lines, rectangles, circles, arrows, connectors |
| **Floating text boxes** | ❌ NOT extracted | Text boxes floating above cells |
| **Overlapping images** | ⚠️ Partial | Extracted as separate images, not combined |
| **Charts & Graphs** | ❌ NOT extracted | Excel charts, pivot tables |
| **Embedded objects** | ❌ NOT extracted | OLE objects, external files |

### What This Means for You

If your Excel document contains **diagrams made of geometric shapes** or **screenshots with overlaid annotations**, these will NOT appear in the converted Markdown. For such content, please **refer to the original Excel file**.

### Other Limitations

- Does not handle `.xls` (old Excel format) — only `.xlsx`
- Image position is approximate (based on anchor cell, not pixel coordinates)
- Heading detection heuristics may misclassify some rows in unusual layouts
- Cell formatting (background colors, borders) is preserved as text tags like `[bg:#RRGGBB]`, not actual visual styling
