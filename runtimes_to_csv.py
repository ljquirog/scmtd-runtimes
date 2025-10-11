# import csv
import runtime_suggestions_by_percentile

# def runtimes_to_csv(data, route, filename, label=None, percentiles=None, write_header=True, add_blank_row=False):
#     # collect all unique timepoints from the dicts
#     timepoints = list(data[0][1].keys())  # assumes all dicts have the same keys

#     # build header
#     header = ["timepoint"] + [str(tb[0]) + "–" + str(tb[1]) for tb, _ in data]

#     # open in append or write mode
#     mode = "a" if not write_header else "w"
#     with open(filename, mode, newline="", encoding="utf-8") as f:
#         writer = csv.writer(f)

#         if add_blank_row:
#             writer.writerow([])  # separate datasets by one row

#         # section label (e.g. "Suggested Runtimes")
#         if label:
#             writer.writerow([label])

#         # header row
#         writer.writerow(header)

#         # timepoint rows
#         for tp in timepoints:
#             row = [tp]
#             for _, runtimes in data:
#                 row.append(runtimes.get(tp, ""))  # leave blank if missing
#             writer.writerow(row)

#         # add percentile rows if provided
#         if percentiles:
#             for p in percentiles:
#                 row = [f"{p}th percentile"] + [""] * len(data)
#                 writer.writerow(row)



# if __name__ == "__main__":
#     filename = "route_1_suggested_runtimes.csv"

#     route, start_date, end_date, days_of_week, percentiles, direction = (
#         "1", "09-11-2025", "10-09-2025", "1,2,3,4,5", [30, 40, 40, 60], 0
#     )

#     # Suggested
#     data = runtime_suggestions_by_percentile.suggested_runtimes(
#         route, percentiles, start_date, end_date, days_of_week, direction, 0
#     )
#     runtimes_to_csv(
#         data, route, filename,
#         label="Suggested Runtimes",
#         percentiles=percentiles,
#         write_header=True
#     )

#     # Scheduled
#     data = runtime_suggestions_by_percentile.suggested_runtimes(
#         route, percentiles, start_date, end_date, days_of_week, direction, 1
#     )
#     runtimes_to_csv(
#         data, route, filename,
#         label="Scheduled Runtimes",
#         write_header=False,
#         add_blank_row=True
#     )

#     # End to End
#     data = runtime_suggestions_by_percentile.end_to_end_runtimes(
#         route, start_date, end_date, days_of_week, direction
#     )
#     runtimes_to_csv(
#         data, route, filename,
#         label="End to End 90th percentile",
#         write_header=False,
#         add_blank_row=True
#     )
# import csv

# def _to_number(x):
#     """safe numeric conversion for summing."""
#     if x is None or x == "":
#         return 0.0
#     try:
#         return float(x)
#     except Exception:
#         try:
#             return float(str(x).replace(",", ""))
#         except Exception:
#             return 0.0

# def runtimes_to_csv(data, route, filename, label=None, percentiles=None, write_header=True, add_blank_row=False):
#     """
#     data: list of ((start,end), runtimes_dict) as before
#     label: section label string (e.g. "Suggested Runtimes")
#     percentiles: list of percentile numbers (used only for 'Suggested Runtimes')
#     write_header: if True, opens file in 'w' else 'a'
#     add_blank_row: if True, write a blank row before the label (for separation)
#     """
#     if not data:
#         raise ValueError("data is empty")

#     # build timeband headers and ordered timepoints (assumes consistent keys)
#     timebands = [f"{tb[0]}–{tb[1]}" for tb, _ in data]
#     timepoints = list(data[0][1].keys())

#     mode = "w" if write_header else "a"
#     with open(filename, mode, newline="", encoding="utf-8-sig") as f:
#         writer = csv.writer(f)

#         if add_blank_row:
#             writer.writerow([])

#         if label:
#             writer.writerow([label])  # label on its own row

#         # header: 'percentile,timepoint,...' for Suggested, otherwise ',timepoint,...'
#         first_col = "percentile" if label and label.lower().startswith("suggested") else ""
#         header = [first_col, "timepoint"] + timebands
#         writer.writerow(header)

#         # --- Suggested Runtimes: write percentile rows (mapped by index to timepoints) + total ---
#         if label and label.lower().startswith("suggested") and percentiles:
#             # percentiles -> mapped to first N timepoints by index
#             for i, p in enumerate(percentiles):
#                 if i >= len(timepoints):
#                     break
#                 tp = timepoints[i]
#                 row = [f"{p}", tp]
#                 for _, runtimes in data:
#                     row.append(runtimes.get(tp, ""))
#                 writer.writerow(row)

#             # totals row (sums across all timepoints per timeband)
#             totals = []
#             for _, runtimes in data:
#                 s = 0.0
#                 for tp in timepoints:
#                     s += _to_number(runtimes.get(tp, 0))
#                 totals.append(s)
#             # format totals as integers where possible
#             formatted_totals = [int(t) if float(t).is_integer() else round(t, 2) for t in totals]
#             writer.writerow(["", "total"] + formatted_totals)
#             return

#         # --- End to End label: only write total row (matches example) ---
#         if label and "end to end" in label.lower():
#             totals = []
#             for _, runtimes in data:
#                 s = 0.0
#                 for tp in timepoints:
#                     s += _to_number(runtimes.get(tp, 0))
#                 totals.append(s)
#             formatted_totals = [int(t) if float(t).is_integer() else round(t, 2) for t in totals]
#             writer.writerow(["", "total"] + formatted_totals)
#             return

#         # --- Scheduled or general: write each timepoint row (leftmost blank) + total ---
#         for tp in timepoints:
#             row = ["", tp]
#             for _, runtimes in data:
#                 row.append(runtimes.get(tp, ""))
#             writer.writerow(row)

#         totals = []
#         for _, runtimes in data:
#             s = 0.0
#             for tp in timepoints:
#                 s += _to_number(runtimes.get(tp, 0))
#             totals.append(s)
#         formatted_totals = [int(t) if float(t).is_integer() else round(t, 2) for t in totals]
#         writer.writerow(["", "total"] + formatted_totals)
# if __name__ == "__main__":
    

#     route = "2"
#     start_date = "09-11-2025"
#     end_date = "10-09-2025"
#     days_of_week = "1,2,3,4,5"
#     percentiles = [30, 40, 50,50,60]
#     direction = 0
#     filename = f"route_{route}_suggested_runtimes.csv"

#     # Suggested
#     data = runtime_suggestions_by_percentile.suggested_runtimes(
#         route, percentiles, start_date, end_date, days_of_week, direction, 0
#     )
#     runtimes_to_csv(
#         data, route, filename,
#         label="Suggested Runtimes",
#         percentiles=percentiles,
#         write_header=True
#     )

#     # Scheduled
#     data = runtime_suggestions_by_percentile.suggested_runtimes(
#         route, percentiles, start_date, end_date, days_of_week, direction, 1
#     )
#     runtimes_to_csv(
#         data, route, filename,
#         label="Scheduled Runtimes",
#         write_header=False,
#         add_blank_row=True
#     )

#     # End to End
#     data = runtime_suggestions_by_percentile.end_to_end_runtimes(
#         route, start_date, end_date, days_of_week, direction
#     )
#     runtimes_to_csv(
#         data, route, filename,
#         label="End to End 90th percentile",
#         write_header=False,
#         add_blank_row=True
#     )
from openpyxl import Workbook, load_workbook
from openpyxl.utils import get_column_letter
import os

def runtimes_to_excel(data, route, filename, label=None, percentiles=None, write_header=True, add_blank_row=False):
    # Check if workbook exists; otherwise create new
    if os.path.exists(filename):
        wb = load_workbook(filename)
        ws = wb.active
    else:
        wb = Workbook()
        ws = wb.active

    # Add a blank row if needed
    if add_blank_row:
        ws.append([])

    # Section label (e.g. "Suggested Runtimes")
    if label:
        ws.append([label])

    if percentiles:
        # Build header row
        header = ["percentile/timepoint"] + [f"{tb[0]}–{tb[1]}" for tb, _ in data]
        ws.append(header)

    # Add percentile/timepoint rows
    timepoints = list(data[0][1].keys())  # assumes same keys in each dict
    if percentiles:
    # +1 to include the total row
        for i in range(len(percentiles) + 1):
            # label the row (percentile or total)
            if i < len(percentiles):
                label = f"{percentiles[i]}"
            else:
                label = "total"

            row = [label]
            for _, runtimes in data:
                tp = timepoints[i] if i < len(timepoints) else ""
                val = runtimes.get(tp, "")
                row.append(val)

            ws.append(row)
    else:
        for tp in timepoints:
            row = ["", tp]
            for _, runtimes in data:
                row.append(runtimes.get(tp, ""))
            ws.append(row)

    wb.save(filename)

if __name__ == "__main__":
    route, start_date, end_date, days_of_week, percentiles, direction = (
        "1", "09-11-2025", "10-09-2025", "1,2,3,4,5", [30, 40, 50, 60], 0
    )
    filename = f"route_{route}_suggested_runtimes.xlsx"
    
    # Suggested
    data = runtime_suggestions_by_percentile.suggested_runtimes(
        route, percentiles, start_date, end_date, days_of_week, direction, 0
    )
    runtimes_to_excel(
        data, route, filename,
        label="Suggested Runtimes",
        percentiles=percentiles,
        write_header=True
    )

    # Scheduled
    data = runtime_suggestions_by_percentile.suggested_runtimes(
        route, percentiles, start_date, end_date, days_of_week, direction, 1
    )
    runtimes_to_excel(
        data, route, filename,
        label="Scheduled Runtimes",
        write_header=False,
        add_blank_row=True
    )

    # End to End
    data = runtime_suggestions_by_percentile.end_to_end_runtimes(
        route, start_date, end_date, days_of_week, direction
    )
    runtimes_to_excel(
        data, route, filename,
        label="End to End 90th percentile",
        write_header=False,
        add_blank_row=True
    )
