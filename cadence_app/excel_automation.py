import html
import os
import statistics
import time
from collections import Counter

import pythoncom
import win32com.client

def _wait_for_refresh(wb, timeout=120):
    start = time.time()
    while True:
        refreshing = False
        try:
            for ws in wb.Worksheets:
                try:
                    # QueryTables (legacy) attached to sheets
                    qts = ws.QueryTables
                    for i in range(1, qts.Count + 1):
                        qt = qts.Item(i)
                        if getattr(qt, 'Refreshing', False):
                            refreshing = True
                            break
                except Exception:
                    pass
                try:
                    # ListObjects loaded by Power Query have QueryTable
                    los = ws.ListObjects
                    for j in range(1, los.Count + 1):
                        lo = los.Item(j)
                        try:
                            qt = lo.QueryTable
                            if getattr(qt, 'Refreshing', False):
                                refreshing = True
                                break
                        except Exception:
                            pass
                except Exception:
                    pass
            if not refreshing:
                break
        except Exception:
            # If enumerating worksheets fails, break to avoid infinite loop
            break
        if time.time() - start > timeout:
            break
        time.sleep(1)


def _normalize_used_range(value):
    if value is None:
        return []
    if isinstance(value, tuple):
        if not value:
            return []
        if not isinstance(value[0], tuple):
            return [list(value)]
        return [list(row) if isinstance(row, tuple) else [row] for row in value]
    return [[value]]


def _is_blank(value):
    return value is None or value == ""


def _coerce_number(value):
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        if cleaned.startswith("$"):
            cleaned = cleaned[1:]
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def _truncate(text, max_length=28):
    text = str(text)
    if len(text) <= max_length:
        return text
    return text[: max_length - 1] + "…"


def _build_bar_chart(title, labels, values, color="#c81d1d"):
    if not labels or not values:
        return ""
    width = 760
    height = 320
    margin_left = 56
    margin_right = 24
    margin_top = 54
    margin_bottom = 62
    chart_width = width - margin_left - margin_right
    chart_height = height - margin_top - margin_bottom
    slot_width = chart_width / max(len(values), 1)
    max_value = max(values) or 1
    bars = []
    for index, (label, value) in enumerate(zip(labels, values)):
        bar_height = 0 if max_value == 0 else (value / max_value) * chart_height
        x = margin_left + index * slot_width + 8
        bar_width = max(18, slot_width - 16)
        y = margin_top + (chart_height - bar_height)
        bars.append(
            f'<g><rect x="{x:.2f}" y="{y:.2f}" width="{bar_width:.2f}" height="{bar_height:.2f}" rx="10" fill="{color}" opacity="0.9" />'
            f'<text x="{x + bar_width / 2:.2f}" y="{y - 8:.2f}" text-anchor="middle" class="chart-value">{value:.1f}</text>'
            f'<text x="{x + bar_width / 2:.2f}" y="{height - 26}" text-anchor="middle" class="chart-label">{html.escape(_truncate(label, 18))}</text></g>'
        )
    return f'''
    <section class="chart-card">
      <h3>{html.escape(title)}</h3>
      <svg viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(title)}">
        <line x1="{margin_left}" y1="{margin_top + chart_height}" x2="{width - margin_right}" y2="{margin_top + chart_height}" class="axis-line"></line>
        {''.join(bars)}
      </svg>
    </section>
    '''


def _extract_sheet_summary(worksheet):
    sheet_name = worksheet.Name
    used_range = worksheet.UsedRange
    values = _normalize_used_range(used_range.Value)
    if not values:
        return None

    if len(values) == 1:
        headers = [f"Column {index + 1}" for index in range(len(values[0]))]
        data_rows = []
    else:
        raw_headers = values[0]
        headers = []
        for index, header in enumerate(raw_headers):
            header_text = str(header).strip() if not _is_blank(header) else f"Column {index + 1}"
            headers.append(header_text)
        data_rows = values[1:]

    columns = {header: [] for header in headers}
    for row in data_rows:
        padded = list(row) + [None] * max(0, len(headers) - len(row))
        for index, header in enumerate(headers):
            columns[header].append(padded[index] if index < len(padded) else None)

    numeric_columns = []
    categorical_columns = []
    missing_cells = 0
    for header, column_values in columns.items():
        non_empty = [value for value in column_values if not _is_blank(value)]
        missing_cells += len(column_values) - len(non_empty)
        numeric_values = [number for number in (_coerce_number(value) for value in non_empty) if number is not None]
        if numeric_values:
            numeric_columns.append(
                {
                    "name": header,
                    "count": len(numeric_values),
                    "missing": len(column_values) - len(non_empty),
                    "mean": statistics.fmean(numeric_values),
                    "minimum": min(numeric_values),
                    "maximum": max(numeric_values),
                    "total": sum(numeric_values),
                }
            )
            continue

        text_values = [str(value).strip() for value in non_empty if str(value).strip()]
        if text_values:
            counts = Counter(text_values)
            if 2 <= len(counts) <= 12:
                categorical_columns.append(
                    {
                        "name": header,
                        "counts": counts,
                        "top_label": counts.most_common(1)[0][0],
                        "top_count": counts.most_common(1)[0][1],
                    }
                )

    primary_chart = ""
    if numeric_columns:
        top_numeric = sorted(numeric_columns, key=lambda item: item["mean"], reverse=True)[:5]
        primary_chart = _build_bar_chart(
            f"Average values in {sheet_name}",
            [item["name"] for item in top_numeric],
            [item["mean"] for item in top_numeric],
        )
    elif categorical_columns:
        top_categorical = max(categorical_columns, key=lambda item: item["top_count"])
        top_items = top_categorical["counts"].most_common(8)
        primary_chart = _build_bar_chart(
            f"Distribution for {top_categorical['name']}",
            [item[0] for item in top_items],
            [float(item[1]) for item in top_items],
        )

    insights = []
    if numeric_columns:
        strongest = max(numeric_columns, key=lambda item: item["mean"])
        insights.append(
            f"Highest average numeric field: {strongest['name']} at {strongest['mean']:.2f}."
        )
    if categorical_columns:
        most_common = max(categorical_columns, key=lambda item: item["top_count"])
        insights.append(
            f"Most common category: {most_common['top_label']} in {most_common['name']} ({most_common['top_count']} rows)."
        )
    if missing_cells:
        insights.append(f"Missing values detected: {missing_cells} cells across the analyzed data.")

    return {
        "name": sheet_name,
        "row_count": len(data_rows),
        "column_count": len(headers),
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "chart_html": primary_chart,
        "insights": insights,
    }


def _render_report_html(source_name, sheet_summaries):
    total_rows = sum(sheet["row_count"] for sheet in sheet_summaries)
    total_columns = sum(sheet["column_count"] for sheet in sheet_summaries)
    numeric_fields = sum(len(sheet["numeric_columns"]) for sheet in sheet_summaries)
    categorical_fields = sum(len(sheet["categorical_columns"]) for sheet in sheet_summaries)

    global_insights = []
    if sheet_summaries:
        largest_sheet = max(sheet_summaries, key=lambda item: item["row_count"])
        global_insights.append(
            f"Largest sheet: {largest_sheet['name']} with {largest_sheet['row_count']} data rows."
        )
        numeric_candidates = [column for sheet in sheet_summaries for column in sheet["numeric_columns"]]
        if numeric_candidates:
            strongest = max(numeric_candidates, key=lambda item: item["mean"])
            global_insights.append(
                f"Strongest average metric: {strongest['name']} at {strongest['mean']:.2f}."
            )
        categorical_candidates = [column for sheet in sheet_summaries for column in sheet["categorical_columns"]]
        if categorical_candidates:
            most_common = max(categorical_candidates, key=lambda item: item["top_count"])
            global_insights.append(
                f"Most common category observed: {most_common['top_label']} in {most_common['name']}."
            )

    chart_sections = []
    for sheet in sheet_summaries:
        if sheet["chart_html"]:
            chart_sections.append(sheet["chart_html"])

    sheet_sections = []
    for sheet in sheet_summaries:
        numeric_rows = []
        for column in sheet["numeric_columns"]:
            numeric_rows.append(
                f"<tr><td>{html.escape(column['name'])}</td><td>{column['count']}</td><td>{column['mean']:.2f}</td><td>{column['minimum']:.2f}</td><td>{column['maximum']:.2f}</td></tr>"
            )
        categorical_rows = []
        for column in sheet["categorical_columns"]:
            categorical_rows.append(
                f"<tr><td>{html.escape(column['name'])}</td><td>{len(column['counts'])}</td><td>{html.escape(str(column['top_label']))}</td><td>{column['top_count']}</td></tr>"
            )
        insights_html = "".join(f"<li>{html.escape(insight)}</li>" for insight in sheet["insights"])
        sheet_sections.append(
            f'''
            <section class="report-section">
              <div class="section-heading">
                <h2>{html.escape(sheet['name'])}</h2>
                <span>{sheet['row_count']} rows · {sheet['column_count']} columns</span>
              </div>
              <div class="sheet-grid">
                <div class="summary-panel">
                  <h3>Insights</h3>
                  <ul>{insights_html or '<li>No numeric or categorical pattern was detected.</li>'}</ul>
                </div>
                <div class="summary-panel">
                  <h3>Numeric columns</h3>
                  <table>
                    <thead><tr><th>Column</th><th>Count</th><th>Mean</th><th>Min</th><th>Max</th></tr></thead>
                    <tbody>{''.join(numeric_rows) or '<tr><td colspan="5">No numeric columns detected.</td></tr>'}</tbody>
                  </table>
                </div>
                <div class="summary-panel">
                  <h3>Categorical columns</h3>
                  <table>
                    <thead><tr><th>Column</th><th>Distinct</th><th>Top value</th><th>Count</th></tr></thead>
                    <tbody>{''.join(categorical_rows) or '<tr><td colspan="4">No categorical columns detected.</td></tr>'}</tbody>
                  </table>
                </div>
              </div>
            </section>
            '''
        )

    return f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Workbook Report - {html.escape(source_name)}</title>
    <style>
      :root {{
        color-scheme: light;
        --bg: #f6f6f6;
        --panel: #ffffff;
        --text: #111111;
        --muted: #5b5b5b;
        --accent: #c81d1d;
        --accent-soft: #fde8e8;
        --border: #d1d1d1;
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        font-family: "Segoe UI", "Trebuchet MS", Arial, sans-serif;
        color: var(--text);
        background: var(--bg);
      }}
      .wrap {{ max-width: 1200px; margin: 0 auto; padding: 32px 20px 48px; }}
      .hero {{
        background: #c81d1d;
        color: #fff;
        padding: 28px;
        border-radius: 24px;
      }}
      .hero h1 {{ margin: 0 0 10px; font-size: clamp(2rem, 4vw, 3.1rem); line-height: 1.05; }}
    .hero p {{ margin: 0; max-width: 72ch; line-height: 1.65; color: #ffffff; }}
    .stats {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin: 18px 0 0; }}
    .stat {{ background: #ffffff; border: 1px solid #111111; border-radius: 18px; padding: 16px; }}
    .stat span {{ display: block; color: #111111; font-size: 0.9rem; margin-bottom: 8px; }}
      .stat strong {{ font-size: 1.35rem; }}
            .insight-strip {{ margin: 18px 0; padding: 18px 20px; border-radius: 20px; background: var(--accent-soft); border: 1px solid var(--border); }}
      .insight-strip ul {{ margin: 0; padding-left: 18px; color: var(--muted); line-height: 1.6; }}
      .chart-grid {{ display: grid; gap: 16px; margin: 18px 0 0; }}
    .chart-card, .report-section, .summary-panel {{ background: var(--panel); border: 1px solid var(--border); border-radius: 20px; }}
      .chart-card {{ padding: 18px; }}
      .chart-card h3, .summary-panel h3 {{ margin: 0 0 12px; }}
      .chart-card svg {{ width: 100%; height: auto; display: block; }}
            .axis-line {{ stroke: #111111; stroke-width: 1; }}
      .chart-label {{ fill: var(--muted); font-size: 11px; }}
      .chart-value {{ fill: var(--accent); font-size: 11px; font-weight: 700; }}
      .report-section {{ padding: 20px; margin-top: 18px; }}
      .section-heading {{ display: flex; align-items: baseline; justify-content: space-between; gap: 12px; margin-bottom: 14px; }}
      .section-heading h2 {{ margin: 0; font-size: 1.25rem; }}
      .section-heading span {{ color: var(--muted); font-size: 0.95rem; }}
      .sheet-grid {{ display: grid; gap: 14px; grid-template-columns: repeat(3, minmax(0, 1fr)); }}
    .summary-panel {{ padding: 16px; }}
      .summary-panel ul {{ margin: 0; padding-left: 18px; color: var(--muted); line-height: 1.6; }}
      table {{ width: 100%; border-collapse: collapse; font-size: 0.92rem; }}
    th, td {{ text-align: left; padding: 8px 6px; border-bottom: 1px solid #d1d1d1; vertical-align: top; }}
      th {{ color: var(--muted); font-weight: 700; }}
      .charts, .insight-grid {{ display: grid; gap: 16px; }}
      .footer-note {{ margin-top: 18px; color: var(--muted); }}
      @media (max-width: 980px) {{
        .stats, .sheet-grid {{ grid-template-columns: 1fr 1fr; }}
      }}
      @media (max-width: 720px) {{
        .stats, .sheet-grid {{ grid-template-columns: 1fr; }}
        .section-heading {{ flex-direction: column; align-items: flex-start; }}
      }}
    </style>
  </head>
  <body>
    <main class="wrap">
      <section class="hero">
        <h1>Workbook report for {html.escape(source_name)}</h1>
        <p>This report summarizes the refreshed workbook, highlights the most meaningful numeric and categorical patterns, and embeds quick visual charts for the strongest signals found in your data.</p>
        <div class="stats">
          <div class="stat"><span>Sheets analyzed</span><strong>{len(sheet_summaries)}</strong></div>
          <div class="stat"><span>Total rows</span><strong>{total_rows}</strong></div>
          <div class="stat"><span>Numeric fields</span><strong>{numeric_fields}</strong></div>
          <div class="stat"><span>Categorical fields</span><strong>{categorical_fields}</strong></div>
        </div>
      </section>

      <section class="insight-strip">
        <ul>{''.join(f'<li>{html.escape(item)}</li>' for item in global_insights) or '<li>No strong cross-sheet insights were detected.</li>'}</ul>
      </section>

      <section class="chart-grid">
        {''.join(chart_sections) or '<div class="report-section"><p>No charts could be generated from the workbook data.</p></div>'}
      </section>

      {''.join(sheet_sections)}

      <p class="footer-note">This report was generated automatically from the refreshed workbook data.</p>
    </main>
  </body>
</html>'''

def refresh_power_query_workbook(src_path, out_path=None, report_path=None, timeout=120):
    if out_path is None:
        out_path = src_path
    # Ensure absolute paths
    src_path = os.path.abspath(src_path)
    out_path = os.path.abspath(out_path)
    if report_path is not None:
        report_path = os.path.abspath(report_path)

    # COM must be initialized on the current thread
    pythoncom.CoInitialize()
    excel = win32com.client.DispatchEx('Excel.Application')
    excel.Visible = False
    excel.DisplayAlerts = False
    report_summary = None
    report_error = None
    try:
        wb = excel.Workbooks.Open(src_path, UpdateLinks=0)
        # Refresh all Power Query / connections
        wb.RefreshAll()
        # Wait for refresh completion
        _wait_for_refresh(wb, timeout=timeout)
        # Save workbook as xlsx (preserve macro-enabled if needed)
        wb.SaveAs(out_path)
        if report_path is not None:
            sheet_summaries = []
            for worksheet in wb.Worksheets:
                try:
                    summary = _extract_sheet_summary(worksheet)
                    if summary is not None:
                        sheet_summaries.append(summary)
                except Exception:
                    continue
            report_html = _render_report_html(os.path.basename(out_path), sheet_summaries)
            with open(report_path, 'w', encoding='utf-8') as report_file:
                report_file.write(report_html)
            report_summary = {
                'sheet_count': len(sheet_summaries),
                'row_count': sum(sheet['row_count'] for sheet in sheet_summaries),
                'numeric_fields': sum(len(sheet['numeric_columns']) for sheet in sheet_summaries),
                'categorical_fields': sum(len(sheet['categorical_columns']) for sheet in sheet_summaries),
            }
        wb.Close(SaveChanges=False)
    finally:
        try:
            excel.Quit()
        except Exception:
            pass
        pythoncom.CoUninitialize()
    return {
        'output_path': out_path,
        'report_path': report_path,
        'report_summary': report_summary,
        'report_error': report_error,
    }
