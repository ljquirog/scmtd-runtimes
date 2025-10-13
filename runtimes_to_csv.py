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
