#!/usr/bin/env python3
"""csvview - Display CSV files in a formatted table."""

import csv
import sys
import argparse

def read_csv(filepath, delimiter=","):
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=delimiter)
        rows = list(reader)
    return rows[0] if rows else [], rows[1:] if len(rows) > 1 else []


def col_widths(headers, rows):
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(str(cell)))
    return widths


def fmt_row(cells, widths, alignments):
    parts = []
    for i, (cell, w) in enumerate(zip(cells, widths)):
        align = alignments[i] if i < len(alignments) else "<"
        parts.append(f"{str(cell):{align}{w}}")
    return "│ " + " │ ".join(parts) + " │"


def separator(widths, left, mid, right, dash="─"):
    return left + mid.join(dash * (w + 2) for w in widths) + right


def guess_alignments(headers, rows):
    """Right-align columns that look numeric."""
    alignments = ["<"] * len(headers)
    sample = rows[:20]
    for i, _ in enumerate(headers):
        numeric = 0
        total = 0
        for row in sample:
            if i < len(row) and row[i].strip():
                total += 1
                try:
                    float(row[i])
                    numeric += 1
                except ValueError:
                    pass
        if total > 0 and numeric / total >= 0.8:
            alignments[i] = ">"
    return alignments


DEFAULT_TAIL = 10


def numeric_averages(headers, rows):
    """Return a list of average strings for numeric columns, empty string otherwise."""
    result = []
    for i, _ in enumerate(headers):
        values = []
        has_non_numeric = False
        for row in rows:
            if i < len(row) and row[i].strip():
                try:
                    values.append(float(row[i]))
                except ValueError:
                    has_non_numeric = True
                    break
        if not has_non_numeric and values:
            avg = sum(values) / len(values)
            result.append(f"{avg:.2f}")
        else:
            result.append("")
    return result


def display(headers, rows, limit=None, no_color=False, average=False):
    total = len(rows)
    show_all = limit == 0

    if show_all:
        display_rows = rows
        skipped = 0
    elif limit is None:
        # Default: show last DEFAULT_TAIL rows
        display_rows = rows[-DEFAULT_TAIL:]
        skipped = max(0, total - DEFAULT_TAIL)
    else:
        display_rows = rows[-limit:]
        skipped = max(0, total - limit)

    widths = col_widths(headers, display_rows)
    alignments = guess_alignments(headers, display_rows)

    BOLD = "\033[1m" if not no_color else ""
    CYAN = "\033[96m" if not no_color else ""
    DIM = "\033[2m" if not no_color else ""
    YELLOW = "\033[93m" if not no_color else ""
    RESET = "\033[0m" if not no_color else ""

    if skipped:
        skip_msg = f"  ··· {skipped} row{'s' if skipped != 1 else ''} above ···"
        inner_width = sum(w + 3 for w in widths) - 1
        if len(skip_msg) > inner_width:
            widths[0] += len(skip_msg) - inner_width

    top = separator(widths, "┌", "┬", "┐")
    mid = separator(widths, "├", "┼", "┤")
    skip_sep = separator(widths, "╞", "╪", "╡", "═")
    bot = separator(widths, "└", "┴", "┘")

    print(CYAN + top + RESET)
    print(BOLD + CYAN + fmt_row(headers, widths, ["<"] * len(headers)) + RESET)
    print(CYAN + mid + RESET)

    if skipped:
        inner_width = sum(w + 3 for w in widths) - 1
        print(YELLOW + "│" + skip_msg.ljust(inner_width) + "│" + RESET)
        print(CYAN + skip_sep + RESET)

    for i, row in enumerate(display_rows):
        padded = row + [""] * (len(headers) - len(row))
        line = fmt_row(padded[:len(headers)], widths, alignments)
        print((DIM if i % 2 else "") + line + RESET)

    if average:
        avgs = numeric_averages(headers, display_rows)
        if any(avgs):
            avg_sep = separator(widths, "╞", "╪", "╡", "═")
            print(CYAN + avg_sep + RESET)
            label_row = []
            placed_label = False
            for j, v in enumerate(avgs):
                if v:
                    label_row.append(v)
                elif not placed_label:
                    label_row.append("AVG")
                    placed_label = True
                else:
                    label_row.append("")
            print(BOLD + fmt_row(label_row, widths, alignments) + RESET)

    print(CYAN + bot + RESET)

    shown = len(display_rows)
    if skipped:
        print(f"  Showing last {shown} of {total} rows  (use --limit 0 to show all)")
    else:
        print(f"  {total} row{'s' if total != 1 else ''}  ·  {len(headers)} column{'s' if len(headers) != 1 else ''}")

    return display_rows


def stats(headers, rows):
    """Print basic stats for numeric columns."""
    print("\n── Column Stats ──")
    for i, h in enumerate(headers):
        values = []
        for row in rows:
            if i < len(row):
                try:
                    values.append(float(row[i]))
                except ValueError:
                    pass
        if values:
            print(f"  {h}: min={min(values):.2f}  max={max(values):.2f}  avg={sum(values)/len(values):.2f}")


def main():
    parser = argparse.ArgumentParser(
        description="Display a CSV file as a formatted table.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  csvview data.csv\n"
               "  csvview data.csv --limit 20\n"
               "  csvview data.csv --cols timestamp,download_mbps\n"
               "  csvview data.csv --average\n"
               "  csvview data.csv --stats\n"
               "  csvview data.csv --delimiter ';'",
    )
    parser.add_argument("file", help="CSV file to display")
    parser.add_argument("--limit", "-n", type=int, default=None,
                        help="Last N rows to show; 0 = show all (default: last 10)")
    parser.add_argument("--delimiter", "-d", default=",", help="Field delimiter (default: ',')")
    parser.add_argument("--cols", "-c", default=None, help="Comma-separated column names to show")
    parser.add_argument("--average", "-a", action="store_true", help="Show average values for integer columns")
    parser.add_argument("--stats", "-s", action="store_true", help="Show basic stats for numeric columns")
    parser.add_argument("--no-color", action="store_true", help="Disable color output")
    args = parser.parse_args()

    try:
        headers, rows = read_csv(args.file, delimiter=args.delimiter)
    except FileNotFoundError:
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)

    if not headers:
        print("Empty or invalid CSV file.", file=sys.stderr)
        sys.exit(1)

    # Filter columns
    if args.cols:
        selected = [c.strip() for c in args.cols.split(",")]
        indices = []
        for col in selected:
            if col in headers:
                indices.append(headers.index(col))
            else:
                print(f"Warning: column '{col}' not found", file=sys.stderr)
        if indices:
            headers = [headers[i] for i in indices]
            rows = [[row[i] for i in indices if i < len(row)] for row in rows]

    visible_rows = display(headers, rows, limit=args.limit, no_color=args.no_color, average=args.average)

    if args.stats:
        stats(headers, visible_rows)


if __name__ == "__main__":
    main()
