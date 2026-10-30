import argparse
import math
import os
import re
from pathlib import Path

try:
  from openpyxl import load_workbook
except ImportError:
  print('Error: openpyxl is required but not installed.')
  print('Install it with: pip install openpyxl')
  raise SystemExit(1)




def cell_text(value):
  if value is None:
    return ''
  if isinstance(value, str):
    return value.strip()
  if isinstance(value, bool):
    return 'TRUE' if value else 'FALSE'
  if isinstance(value, (int, float)):
    if isinstance(value, float) and math.isnan(value):
      return ''
    if isinstance(value, float) and value.is_integer():
      return str(int(value))
    return str(value)
  return str(value).strip()


def is_valid_hex_color(s):
  """Check if string is a valid hex color (6 or 8 hex digits)."""
  if not s or len(s) < 6:
    return False
  # Must be all hex digits
  hex_chars = set('0123456789ABCDEFabcdef')
  return all(c in hex_chars for c in s)


def get_font_color(font):
  """Extract font color from cell font, handling theme colors."""
  if not font or not font.color:
    return None
  
  # Direct RGB color - convert RGB object to string
  if font.color.rgb:
    rgb_str = str(font.color.rgb)
    # Handle both 'RRGGBBAA' and 'RRGGBB' formats
    if is_valid_hex_color(rgb_str) and rgb_str not in ('00000000', '000000'):
      # Take last 6 chars if it's 8 chars (with alpha), or all if 6 chars
      return f'#{rgb_str[-6:]}'
  
  # Theme color - Excel standard theme colors
  # These are standard Office theme colors, actual appearance depends on the specific theme
  if font.color.theme is not None:
    try:
      theme_idx = int(font.color.theme)
      theme_colors = {
        0: '#000000',   # Dark 1 (Text/Black)
        1: '#FFFFFF',   # Light 1 (Background/White)
        2: '#1F497D',   # Dark 2 (Dark Blue)
        3: '#EEECE1',   # Light 2 (Light Beige)
        4: '#4F81BD',   # Accent 1 (Blue)
        5: '#C0504D',   # Accent 2 (Red)
        6: '#9BBB59',   # Accent 3 (Green)
        7: '#8064A2',   # Accent 4 (Purple)
        8: '#4BACC6',   # Accent 5 (Teal)
        9: '#F79646',   # Accent 6 (Orange)
      }
      return theme_colors.get(theme_idx)
    except (ValueError, TypeError):
      pass
  
  return None


def get_fill_color(fill):
  """Extract background fill color from cell fill."""
  if not fill or not fill.fgColor:
    return None
  
  # Check if it's actually a solid fill (not pattern)
  if fill.patternType != 'solid':
    return None
  
  # Direct RGB color
  if fill.fgColor.rgb:
    rgb_str = str(fill.fgColor.rgb)
    if is_valid_hex_color(rgb_str) and rgb_str not in ('00000000', '000000'):
      return f'#{rgb_str[-6:]}'
  
  # Theme color - skip theme 0 (usually means no fill/default)
  if fill.fgColor.theme is not None:
    try:
      theme_idx = int(fill.fgColor.theme)
      # Theme 0 is typically default/no fill, skip it
      if theme_idx == 0:
        return None
      theme_colors = {
        1: '#FFFFFF',
        2: '#1F497D',
        3: '#EEECE1',
        4: '#4F81BD',
        5: '#C0504D',
        6: '#9BBB59',
        7: '#8064A2',
        8: '#4BACC6',
        9: '#F79646',
      }
      return theme_colors.get(theme_idx)
    except (ValueError, TypeError):
      pass
  
  return None


def format_cell_with_style(cell):
  """Extract text and formatting from a cell, returning styled text."""
  text = cell_text(cell.value)
  if not text:
    return ''
  
  font = cell.font if cell else None
  fill = cell.fill if cell else None
  
  # Apply font styles
  if font:
    # Bold
    if font.bold:
      text = f'**{text}**'
    # Italic (but not if already bold to avoid nesting issues)
    elif font.italic:
      text = f'*{text}*'
    
    # Underline
    if font.underline:
      text = f'<u>{text}</u>'
  
  # Apply color tags (prefix style)
  font_color = get_font_color(font)
  # Skip default colors: black (#000000) and white (#FFFFFF)
  if font_color and font_color not in ('#000000', '#FFFFFF'):
    text = f'[color:{font_color}]{text}'
  
  # Apply background color tags
  fill_color = get_fill_color(fill)
  # Skip default colors: white (#FFFFFF) and black (#000000) backgrounds
  if fill_color and fill_color not in ('#FFFFFF', '#000000'):
    text = f'[bg:{fill_color}]{text}'
  
  return text


def inline_text(text, for_table=False):
  cleaned = text.replace('\r\n', '\n').replace('\r', '\n')
  if for_table:
    return cleaned.replace('\n', '<br>')
  return cleaned.replace('\n', ' ')


def normalize_name(text, fallback):
  if not text:
    return fallback
  cleaned = re.sub(r'[^0-9a-zA-Z\u4e00-\u9fff_-]+', '_', text)
  cleaned = cleaned.strip('_')
  return cleaned[:40] or fallback


def get_merged_non_topleft(ws):
  merged_non_topleft = set()
  for merged in ws.merged_cells.ranges:
    for row in range(merged.min_row, merged.max_row + 1):
      for col in range(merged.min_col, merged.max_col + 1):
        if row == merged.min_row and col == merged.min_col:
          continue
        merged_non_topleft.add((row, col))
  return merged_non_topleft


def detect_used_range(ws, merged_non_topleft):
  used_cols = set()
  last_row = 0
  for row in ws.iter_rows(min_row=1, max_row=ws.max_row, max_col=ws.max_column):
    row_has_value = False
    for cell in row:
      if (cell.row, cell.column) in merged_non_topleft:
        continue
      text = cell_text(cell.value)
      if text:
        used_cols.add(cell.column)
        last_row = max(last_row, cell.row)
        row_has_value = True
    if row_has_value:
      last_row = max(last_row, row[0].row)
  return sorted(used_cols), last_row


def row_values(ws, row_idx, used_cols, merged_non_topleft, enable_formatting=True):
  values = []
  cells = []
  for col in used_cols:
    if (row_idx, col) in merged_non_topleft:
      values.append('')
      cells.append(None)
      continue
    cell = ws.cell(row=row_idx, column=col)
    if enable_formatting:
      values.append(format_cell_with_style(cell))
    else:
      values.append(cell_text(cell.value))
    cells.append(cell)
  return values, cells


def is_heading(text, row_values_list, row_cells, used_cols):
  if not text:
    return False
  first_col_index = None
  for idx, value in enumerate(row_values_list):
    if value:
      first_col_index = idx
      break
  if first_col_index is None or first_col_index > 1:
    return False
  non_empty = [value for value in row_values_list if value]
  if len(non_empty) > 2:
    return False
  font = row_cells[first_col_index].font if row_cells[first_col_index] else None
  bold = font.bold if font else False
  size = font.sz if font else None
  numbered = bool(re.match(r'^\s*\d', text))
  right_cells_empty = all(not value for value in row_values_list[first_col_index + 1:])
  return right_cells_empty and (bold or (size and size >= 12) or numbered)


def heading_level(text):
  match = re.match(r'^\s*(\d+(?:\.\d+)*)', text)
  if not match:
    return 3
  parts = match.group(1).split('.')
  if len(parts) <= 1:
    return 3
  if len(parts) == 2:
    return 4
  return 5


def is_key_value(values_list):
  non_empty = [(idx, value) for idx, value in enumerate(values_list) if value]
  if len(non_empty) == 2:
    key = non_empty[0][1]
    return key.endswith(':') or key.endswith('：') or '：' in key
  if len(non_empty) == 1:
    return '：' in non_empty[0][1]
  return False


def is_paragraph_row(values_list):
  non_empty = [value for value in values_list if value]
  if len(non_empty) != 1:
    return False
  return len(non_empty[0]) > 20


def is_table_header(values_list):
  return sum(1 for value in values_list if value) >= 3


def find_context_text(ws, start_row, used_cols, merged_non_topleft):
  for row_idx in range(start_row, 0, -1):
    values, _ = row_values(ws, row_idx, used_cols, merged_non_topleft, enable_formatting=False)
    for value in values:
      if value:
        # Strip formatting tags for context text
        clean_value = re.sub(r'\[\w+:[^\]]*\]', '', value)
        clean_value = clean_value.replace('**', '').replace('*', '').replace('<u>', '').replace('</u>', '')
        return clean_value
  return 'image'


def extract_images(ws, used_cols, merged_non_topleft, images_dir, sheet_name, enabled):
  """Extract images from worksheet."""
  images_by_row = {}
  if not enabled:
    return images_by_row, 0
  count = 0
  name_counts = {}
  for image in getattr(ws, '_images', []):
    anchor = getattr(image, 'anchor', None)
    if not anchor or not hasattr(anchor, '_from'):
      continue
    row = anchor._from.row + 1
    context = find_context_text(ws, row, used_cols, merged_non_topleft)
    context_name = normalize_name(context, 'image')
    sheet_safe = normalize_name(sheet_name, 'sheet')
    col = anchor._from.col + 1
    ext = 'png'
    if getattr(image, 'format', None):
      ext = image.format.lower()
      if ext == 'jpeg':
        ext = 'jpg'
    elif getattr(image, 'path', None):
      ext = os.path.splitext(image.path)[1].lstrip('.') or 'png'
    base_name = f'{sheet_safe}_row{row}_col{col}_{context_name}.{ext}'
    suffix = name_counts.get(base_name, 0)
    name_counts[base_name] = suffix + 1
    filename = base_name
    if suffix:
      stem, extension = os.path.splitext(base_name)
      filename = f'{stem}_{suffix + 1}{extension}'
    images_dir.mkdir(parents=True, exist_ok=True)
    with open(images_dir / filename, 'wb') as handle:
      handle.write(image._data())
    images_by_row.setdefault(row, []).append((context, filename))
    count += 1
  return images_by_row, count


def format_table(header_values, data_rows):
  columns = list(range(len(header_values)))
  for idx in range(len(header_values) - 1, -1, -1):
    if not header_values[idx] and all(not row[idx] for row in data_rows):
      columns.pop(columns.index(idx))
  if not columns:
    return []
  header = [inline_text(header_values[idx] or '', True) for idx in columns]
  rows = [
    [inline_text(row[idx] or '', True) for idx in columns]
    for row in data_rows
  ]
  lines = ['| ' + ' | '.join(header) + ' |']
  lines.append('| ' + ' | '.join(['---'] * len(header)) + ' |')
  for row in rows:
    lines.append('| ' + ' | '.join(row) + ' |')
  lines.append('')
  return lines


def sheet_to_markdown(ws, images_dir, enable_images, enable_formatting=True):
  merged_non_topleft = get_merged_non_topleft(ws)
  used_cols, last_row = detect_used_range(ws, merged_non_topleft)
  images_by_row, image_count = extract_images(
    ws, used_cols, merged_non_topleft, images_dir, ws.title, enable_images
  )
  if images_by_row:
    last_row = max(last_row, max(images_by_row))
  if not used_cols and not images_by_row:
    return ['_Empty sheet_', ''], 0
  lines = []
  row_idx = 1
  while row_idx <= last_row:
    if row_idx in images_by_row:
      for context, filename in images_by_row[row_idx]:
        lines.append(f'![{context}](./images/{filename})')
        lines.append('')
    values, cells = row_values(ws, row_idx, used_cols, merged_non_topleft, enable_formatting)
    if not any(values):
      row_idx += 1
      continue
    first_value = next((value for value in values if value), '')
    if is_heading(first_value, values, cells, used_cols):
      level = heading_level(first_value)
      lines.append(f'{"#" * level} {first_value}')
      lines.append('')
      row_idx += 1
      continue
    if is_key_value(values):
      non_empty = [value for value in values if value]
      if len(non_empty) == 1 and '：' in non_empty[0]:
        key, value = non_empty[0].split('：', 1)
        lines.append(f'- **{key.strip()}**: {value.strip()}')
      else:
        key = non_empty[0].rstrip(':：')
        value = non_empty[1] if len(non_empty) > 1 else ''
        lines.append(f'- **{key.strip()}**: {value.strip()}')
      lines.append('')
      row_idx += 1
      continue
    if is_table_header(values):
      header_values = [inline_text(value, True) if value else '' for value in values]
      table_cols = [idx for idx, value in enumerate(values) if value]
      data_rows = []
      empty_streak = 0
      scan_row = row_idx + 1
      while scan_row <= last_row:
        scan_values, _ = row_values(ws, scan_row, used_cols, merged_non_topleft, enable_formatting)
        if not any(scan_values):
          empty_streak += 1
          if empty_streak >= 2:
            break
          scan_row += 1
          continue
        empty_streak = 0
        outside = any(
          value for idx, value in enumerate(scan_values) if idx not in table_cols and value
        )
        if outside:
          break
        data_rows.append([inline_text(value, True) if value else '' for value in scan_values])
        scan_row += 1
      lines.extend(format_table(header_values, data_rows))
      row_idx = scan_row
      continue
    if is_paragraph_row(values):
      para_lines = []
      scan_row = row_idx
      while scan_row <= last_row:
        scan_values, _ = row_values(ws, scan_row, used_cols, merged_non_topleft, enable_formatting)
        if not is_paragraph_row(scan_values):
          break
        para_lines.append(next(value for value in scan_values if value))
        scan_row += 1
      lines.append(inline_text(' '.join(para_lines)))
      lines.append('')
      row_idx = scan_row
      continue
    line_text = ' | '.join(inline_text(value) for value in values if value)
    if line_text:
      lines.append(line_text)
      lines.append('')
    row_idx += 1
  return lines, image_count


def run(input_path, output_path, enable_images, enable_formatting=True):
  wb = load_workbook(input_path, data_only=False)
  output_lines = []
  images_dir = output_path.parent / 'images'
  total_images = 0
  
  # Add conversion notice at the top of the markdown file (Bilingual)
  output_lines.append('<!--')
  output_lines.append('================================================================================')
  output_lines.append('  CONVERSION NOTICE | 转换说明')
  output_lines.append('================================================================================')
  output_lines.append('This document was automatically converted from an Excel (.xlsx) file.')
  output_lines.append('本文档由 Excel (.xlsx) 文件自动转换而来。')
  output_lines.append('')
  output_lines.append('LIMITATIONS | 使用限制:')
  output_lines.append('  - Geometric shapes (lines, rectangles, circles, arrows) are NOT extracted')
  output_lines.append('    几何图形（线条、矩形、圆形、箭头）不会被提取')
  output_lines.append('  - Floating text boxes are NOT extracted')
  output_lines.append('    悬浮文本框不会被提取')
  output_lines.append('  - Multiple overlapping images are extracted as separate images, not combined')
  output_lines.append('    多张重叠的图片会被提取为单独的图片，不会合并')
  output_lines.append('')
  output_lines.append('For complex graphics, please refer to the original Excel file.')
  output_lines.append('如需查看复杂图形，请参考原始 Excel 文件。')
  output_lines.append('================================================================================')
  output_lines.append('-->')
  output_lines.append('')
  
  for ws in wb.worksheets:
    output_lines.append(f'## {ws.title}')
    output_lines.append('')
    sheet_lines, image_count = sheet_to_markdown(ws, images_dir, enable_images, enable_formatting)
    output_lines.extend(sheet_lines)
    total_images += image_count
  output_path.write_text('\n'.join(output_lines).strip() + '\n', encoding='utf-8')
  size = output_path.stat().st_size
  print(
    f'Processed {len(wb.worksheets)} sheets, extracted {total_images} images, '
    f'output size {size} bytes'
  )
  print()
  print('Note: This skill is designed for text processing. The following complex graphics are not supported:')
  print('  - Geometric shapes (lines, rectangles, circles, arrows)')
  print('  - Floating text boxes')
  print('  - Multiple overlapping images (they will be extracted as separate images)')


def detect_type(input_path, sample_rows=30):
  """Classify xlsx as 'document', 'data', or 'mixed' by sampling first N rows."""
  import json as _json
  wb = load_workbook(input_path, read_only=True, data_only=True)
  sheet_results = []
  for ws in wb.worksheets:
    max_row = ws.max_row or 0
    rows_checked = 0
    fill_counts = []  # non-empty cells per row
    long_texts = 0    # cells with >50 chars
    non_empty_total = 0
    for row in ws.iter_rows(max_row=min(sample_rows, max_row)):
      non_empty = 0
      for cell in row:
        text = cell_text(cell.value)
        if text:
          non_empty += 1
          if len(text) > 50:
            long_texts += 1
      fill_counts.append(non_empty)
      non_empty_total += non_empty
      rows_checked += 1
    if not rows_checked:
      sheet_results.append({
        'sheet': ws.title, 'type': 'empty', 'confidence': 1.0, 'reason': 'no rows'
      })
      continue
    avg_fill = sum(fill_counts) / len(fill_counts)
    sparse_rows = sum(1 for c in fill_counts if c <= 2) / len(fill_counts)
    long_text_ratio = long_texts / max(non_empty_total, 1)
    # Document signal: most rows have <=2 filled cells, some cells have long text
    doc_score = sparse_rows * 0.6 + min(long_text_ratio * 10, 0.4)
    # Data signal: rows consistently have 3+ filled cells, short values
    data_score = (1 - sparse_rows) * 0.7 + (1 - min(long_text_ratio * 10, 1)) * 0.3
    if doc_score > data_score + 0.15:
      stype, confidence = 'document', min(doc_score, 1.0)
      reason = f'sparse rows {sparse_rows:.0%}, long texts {long_text_ratio:.1%}'
    elif data_score > doc_score + 0.15:
      stype, confidence = 'data', min(data_score, 1.0)
      reason = f'avg {avg_fill:.1f} cells/row, long texts {long_text_ratio:.1%}'
    else:
      stype, confidence = 'mixed', 1 - abs(doc_score - data_score)
      reason = f'doc={doc_score:.2f} data={data_score:.2f}'
    sheet_results.append({
      'sheet': ws.title, 'type': stype, 'confidence': round(confidence, 2),
      'reason': reason, 'rows_sampled': rows_checked
    })
  wb.close()
  types = [s['type'] for s in sheet_results if s['type'] != 'empty']
  if not types:
    overall = 'empty'
  elif all(t == 'document' for t in types):
    overall = 'document'
  elif all(t == 'data' for t in types):
    overall = 'data'
  else:
    overall = 'mixed'
  result = {'file': str(input_path), 'type': overall, 'sheets': sheet_results}
  print(_json.dumps(result, ensure_ascii=False, indent=2))
  return result


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('input')
  parser.add_argument('output', nargs='?')
  parser.add_argument('--no-images', action='store_true')
  parser.add_argument('--no-formatting', action='store_true',
                      help='Disable cell formatting (bold, colors, etc.)')
  parser.add_argument('--detect', action='store_true',
                      help='Detect file type (document/data/mixed) and exit')
  args = parser.parse_args()
  input_path = Path(args.input)
  if args.detect:
    detect_type(input_path)
    return
  output_path = Path(args.output) if args.output else input_path.with_suffix('.md')
  run(input_path, output_path, not args.no_images, not args.no_formatting)


if __name__ == '__main__':
  main()
