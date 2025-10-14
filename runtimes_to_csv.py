import runtime_suggestions_by_percentile
from openpyxl import Workbook, load_workbook
from openpyxl.utils import get_column_letter
import os

def runtimes_to_excel(data, route, filename, label=None, percentiles=None, write_header=True, add_blank_row=False):
    # Check if workbook exists; otherwise create new
    # if os.path.exists(filename):
    wb = load_workbook(filename)
    ws = wb.active
    # else:
    #     wb = Workbook()
    #     ws = wb.active

    # Add a blank row if needed
    if add_blank_row:
        ws.append([])

    # Section label (e.g. "Suggested Runtimes")
    if label:
        ws.append([label])
    
    if percentiles:
        header = ["Percentile/Timepoint", "Timepoint"] + [f"{tb[0]} – {tb[1]}" for tb, _ in data]
    else:
        header = ["", "Timepoint"] + [f"{tb[0]} – {tb[1]}" for tb, _ in data]
    ws.append(header)


    # assume all dicts share same keys
    timepoints = list(data[0][1].keys())

    if percentiles:
        all_percentiles = percentiles + ["total"]

        for i, p in enumerate(all_percentiles):
            # Safely match percentile to its corresponding timepoint
            tp = timepoints[i] if i < len(timepoints) else "total"

            # Build the row: [percentile, timepoint, <runtime values across timebands>]
            row = [str(p), tp]
            for _, runtimes in data:
                row.append(runtimes.get(tp, ""))

            ws.append(row)
    else:
        # ---- NORMAL MODE ----
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