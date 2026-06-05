from collections import Counter
from datetime import datetime
import html
from statistics import mean, pstdev


def _normalize_range_values(values):
    if values is None:
        return []
    if not isinstance(values, tuple):
        return [(values,)]
    if not values:
        return []
    first_item = values[0]
    if isinstance(first_item, tuple):
        return [tuple(row) if isinstance(row, tuple) else (row,) for row in values]
    return [tuple(values)]


def _safe_text(value, fallback=""):
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def _format_number(value):
    if value is None:
        return "n/a"
    if isinstance(value, float):
        if value.is_integer():
            return f"{value:,.0f}"
        return f"{value:,.2f}"
    return f"{value:,}"


def _truncate_label(label, limit=18):
    label = _safe_text(label, "Untitled")
    if len(label) <= limit:
        return label
    return label[: limit - 1].rstrip() + "…"


def _column_values(rows, column_index):
    values = []
    for row in rows:
        values.append(row[column_index] if column_index < len(row) else None)
    return values


def _non_empty_count(values):
    count = 0
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        count += 1
    return count


def _as_number(value):
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _sheet_rows(worksheet):
    used_range = worksheet.UsedRange
    values = _normalize_range_values(used_range.Value)
    if not values:
        return [], []

    headers = []
    for index, value in enumerate(values[0]):
        header_text = _safe_text(value, f"Column {index + 1}")
        headers.append(header_text)

    data_rows = values[1:] if len(values) > 1 else []
    return headers, data_rows


def _vertical_bar_chart(title, labels, values, color="#c81d1d"):
    if not labels or not values:
        return ""

    width = 760
    height = 340
    margin_top = 58
    margin_bottom = 86
    margin_left = 48
    margin_right = 22
    chart_width = width - margin_left - margin_right
    chart_height = height - margin_top - margin_bottom
    max_value = max(values) if max(values) > 0 else 1
    group_width = chart_width / len(labels)
    bar_width = max(22, group_width * 0.58)

    bars = []
    for index, value in enumerate(values):
        bar_height = 0 if max_value == 0 else (value / max_value) * chart_height
        x = margin_left + index * group_width + (group_width - bar_width) / 2
        y = margin_top + chart_height - bar_height
        label_x = margin_left + index * group_width + group_width / 2
        bars.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_width:.2f}" height="{bar_height:.2f}" rx="8" fill="{color}" />'
        )
        bars.append(
            f'<text x="{label_x:.2f}" y="{max(margin_top + chart_height + 18, y - 8):.2f}" text-anchor="middle" font-size="13" fill="#4c433d">{html.escape(_format_number(value))}</text>'
        )
        bars.append(
            f'<text x="{label_x:.2f}" y="{height - 24}" text-anchor="middle" font-size="12" fill="#64584f">{html.escape(_truncate_label(labels[index], 16))}</text>'
        )

    axis_line = f'<line x1="{margin_left}" y1="{margin_top + chart_height:.2f}" x2="{margin_left + chart_width}" y2="{margin_top + chart_height:.2f}" stroke="rgba(17, 17, 17, 0.22)" stroke-width="1" />'
    return (
        f'<svg viewBox="0 0 {width} {height}" class="chart-graphic" role="img" aria-label="{html.escape(title)}">'
        f'<rect width="100%" height="100%" fill="white" rx="18" />'
        f'<text x="24" y="28" font-size="18" font-weight="700" fill="#1f1a17">{html.escape(title)}</text>'
        f'{axis_line}'
        f"{''.join(bars)}"
        f'</svg>'
    )


def _horizontal_bar_chart(title, labels, values, color="#c81d1d"):
    if not labels or not values:
        return ""

    width = 760
    row_height = 30
    gap = 12
    margin_top = 58
    margin_left = 210
    margin_right = 28
    bar_area_width = width - margin_left - margin_right
    height = margin_top + len(labels) * (row_height + gap) + 24
    max_value = max(values) if max(values) > 0 else 1

    bars = []
    for index, value in enumerate(values):
        y = margin_top + index * (row_height + gap)
        bar_width = 0 if max_value == 0 else (value / max_value) * bar_area_width
        bars.append(
            f'<text x="{margin_left - 12}" y="{y + row_height / 2 + 5:.2f}" text-anchor="end" font-size="13" fill="#4c433d">{html.escape(_truncate_label(labels[index], 28))}</text>'
        )
        bars.append(
            f'<rect x="{margin_left}" y="{y:.2f}" width="{bar_width:.2f}" height="{row_height}" rx="8" fill="{color}" />'
        )
        bars.append(
            f'<text x="{min(width - 18, margin_left + bar_width + 10):.2f}" y="{y + row_height / 2 + 5:.2f}" font-size="12" fill="#64584f">{html.escape(_format_number(value))}</text>'
        )

    return (
        f'<svg viewBox="0 0 {width} {height}" class="chart-graphic" role="img" aria-label="{html.escape(title)}">'
        f'<rect width="100%" height="100%" fill="white" rx="18" />'
        f'<text x="24" y="28" font-size="18" font-weight="700" fill="#1f1a17">{html.escape(title)}</text>'
        f"{''.join(bars)}"
        f'</svg>'
    )


def _analyze_numeric_columns(headers, data_rows):
    max_columns = max([len(headers)] + [len(row) for row in data_rows]) if data_rows else len(headers)
    profiles = []
    for column_index in range(max_columns):
        column_name = headers[column_index] if column_index < len(headers) else f"Column {column_index + 1}"
        values = _column_values(data_rows, column_index)
        numeric_values = []
        for value in values:
            number = _as_number(value)
            if number is not None:
                numeric_values.append(number)
        if len(numeric_values) < 2:
            continue
        profiles.append(
            {
                "name": column_name,
                "count": len(numeric_values),
                "mean": mean(numeric_values),
                "minimum": min(numeric_values),
                "maximum": max(numeric_values),
                "stdev": pstdev(numeric_values) if len(numeric_values) > 1 else 0,
            }
        )
    return profiles


def _best_category_profile(headers, data_rows):
    max_columns = max([len(headers)] + [len(row) for row in data_rows]) if data_rows else len(headers)
    for column_index in range(max_columns):
        values = _column_values(data_rows, column_index)
        text_values = []
        for value in values:
            if isinstance(value, str):
                cleaned = value.strip()
                if cleaned:
                    text_values.append(cleaned)
        if not text_values:
            continue
        unique_values = set(text_values)
        if len(unique_values) < 2 or len(unique_values) > 25:
            continue
        counts = Counter(text_values)
        total = sum(counts.values())
        top_categories = counts.most_common(8)
        return {
            "name": headers[column_index] if column_index < len(headers) else f"Column {column_index + 1}",
            "counts": counts,
            "top_categories": top_categories,
            "total": total,
        }
    return None


def _build_sheet_report(sheet_name, headers, data_rows):
    row_count = len(data_rows)
    column_count = max([len(headers)] + [len(row) for row in data_rows]) if data_rows else len(headers)
    non_empty_counts = []
    missing_counts = []
    for column_index in range(column_count):
        values = _column_values(data_rows, column_index)
        non_empty = _non_empty_count(values)
        non_empty_counts.append(non_empty)
        missing_counts.append(row_count - non_empty)

    numeric_profiles = _analyze_numeric_columns(headers, data_rows)
    category_profile = _best_category_profile(headers, data_rows)

    chart_columns = [headers[index] if index < len(headers) else f"Column {index + 1}" for index in range(min(column_count, 10))]
    coverage_chart = _vertical_bar_chart(
        f"{sheet_name}: non-empty cells by column",
        chart_columns,
        non_empty_counts[: len(chart_columns)],
    )

    charts = [
        {
            "title": "Data coverage",
            "svg": coverage_chart,
        }
    ]

    insights = []
    insights.append(f"{row_count} data rows across {column_count} columns.")

    if non_empty_counts:
        densest_index = max(range(len(non_empty_counts)), key=lambda idx: non_empty_counts[idx])
        sparsest_index = min(range(len(non_empty_counts)), key=lambda idx: missing_counts[idx])
        densest_label = headers[densest_index] if densest_index < len(headers) else f"Column {densest_index + 1}"
        sparsest_label = headers[sparsest_index] if sparsest_index < len(headers) else f"Column {sparsest_index + 1}"
        insights.append(f"Most complete column: {densest_label} with {_format_number(non_empty_counts[densest_index])} populated cells.")
        insights.append(f"Least missing column: {sparsest_label} with {_format_number(missing_counts[sparsest_index])} blanks.")

    if numeric_profiles:
        numeric_profiles = sorted(numeric_profiles, key=lambda profile: profile["count"], reverse=True)
        numeric_labels = [profile["name"] for profile in numeric_profiles[:6]]
        numeric_means = [profile["mean"] for profile in numeric_profiles[:6]]
        charts.append(
            {
                "title": "Numeric averages",
                "svg": _vertical_bar_chart(f"{sheet_name}: average by numeric column", numeric_labels, numeric_means),
            }
        )
        top_numeric = numeric_profiles[0]
        insights.append(
            f"Highest-volume numeric column: {top_numeric['name']} with {_format_number(top_numeric['count'])} values, average {_format_number(top_numeric['mean'])}."
        )

    if category_profile:
        top_categories = category_profile["top_categories"]
        charts.append(
            {
                "title": f"Top values in {category_profile['name']}",
                "svg": _horizontal_bar_chart(
                    f"{sheet_name}: top values in {category_profile['name']}",
                    [category for category, _ in top_categories],
                    [count for _, count in top_categories],
                ),
            }
        )
        dominant_category, dominant_count = top_categories[0]
        share = (dominant_count / category_profile["total"]) * 100 if category_profile["total"] else 0
        insights.append(
            f"Dominant category in {category_profile['name']}: {dominant_category} ({share:.1f}% of non-empty values)."
        )

    if len(data_rows) > 1:
        seen_rows = set()
        for row in data_rows:
            seen_rows.add(tuple(_safe_text(value, "") for value in row))
        duplicate_rows = len(data_rows) - len(seen_rows)
        insights.append(f"Potential duplicate rows: {_format_number(duplicate_rows)}.")

    return {
        "name": sheet_name,
        "row_count": row_count,
        "column_count": column_count,
        "non_empty_cells": sum(non_empty_counts),
        "missing_cells": sum(missing_counts),
        "numeric_profile_count": len(numeric_profiles),
        "category_profile": category_profile,
        "charts": charts,
        "insights": insights,
    }


def build_workbook_report(workbook, source_filename=None):
    sheet_reports = []
    total_rows = 0
    total_columns = 0
    total_missing_cells = 0
    empty_sheets = []

    for worksheet in workbook.Worksheets:
        sheet_name = _safe_text(worksheet.Name, "Sheet")
        headers, data_rows = _sheet_rows(worksheet)
        if not headers and not data_rows:
            empty_sheets.append(sheet_name)
            continue

        sheet_report = _build_sheet_report(sheet_name, headers, data_rows)
        sheet_reports.append(sheet_report)
        total_rows += sheet_report["row_count"]
        total_columns += sheet_report["column_count"]
        total_missing_cells += sheet_report["missing_cells"]

    overall_insights = []
    if sheet_reports:
        biggest_sheet = max(sheet_reports, key=lambda report: report["row_count"])
        overall_insights.append(
            f"Largest sheet: {biggest_sheet['name']} with {_format_number(biggest_sheet['row_count'])} data rows."
        )
        overall_insights.append(
            f"Workbook coverage: {_format_number(total_rows)} total data rows across {_format_number(len(sheet_reports))} analyzed sheets."
        )
        overall_insights.append(
            f"Empty cells detected across analyzed sheets: {_format_number(total_missing_cells)}."
        )
    else:
        overall_insights.append("No tabular data was found to analyze.")

    if empty_sheets:
        overall_insights.append(f"Sheets skipped because they were empty: {', '.join(empty_sheets)}.")

    return {
        "generated_at": datetime.now(),
        "source_filename": source_filename or "Workbook",
        "sheet_count": len(sheet_reports),
        "sheet_reports": sheet_reports,
        "overall_insights": overall_insights,
        "total_rows": total_rows,
        "total_columns": total_columns,
        "total_missing_cells": total_missing_cells,
    }