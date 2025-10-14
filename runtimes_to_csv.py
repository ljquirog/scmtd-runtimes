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

    # if percentiles:
    #     # Build header row
    #     header = ["Percentile per Timepoint", "Timepoint"] + [f"{tb[0]} – {tb[1]}" for tb, _ in data]
    #     ws.append(header)
    # else:
    #     header = ["","Timepoint"] + [f"{tb[0]} - {tb[1]}" for tb,_ in data]
    #     ws.append(header)
    
    # # assume all dicts share same keys
    timepoints = list(data[0][1].keys())

    # if percentiles:
    #     # loop through percentiles + total
    #     for i in range(len(percentiles) + 1):
    #         percentile_label = f"{percentiles[i]}" if i < len(percentiles) else "total"
    #         for tp_label, runtimes in data:
    #             # Convert tuple like ('07:15:00', '11:14:00') into a readable string
    #             if isinstance(tp_label, tuple):
    #                 tp_label = f"{tp_label[0]} – {tp_label[1]}"

    #             row = [percentile_label, tp_label]
    #             for tp in timepoints:
    #                 row.append(runtimes.get(tp, ""))
    #             ws.append(row)

            

    #         # ws.append(row)
    # else:
    #     # no percentiles — just write stops as rows
    #     for tp in timepoints:
    #         row = ["", tp]
    #         for _, runtimes in data:
    #             row.append(runtimes.get(tp, ""))
    #         ws.append(row)
        # assume all dicts share same keys (including 'total' as last key)
    # header
    if percentiles:
        header = ["Percentile/Timepoint", "Timepoint"] + [f"{tb[0]} – {tb[1]}" for tb, _ in data]
    else:
        header = ["", "Timepoint"] + [f"{tb[0]} – {tb[1]}" for tb, _ in data]
    ws.append(header)

    # # ---- PERCENTILE MODE ----
    # if percentiles:
    #     # include total after the percentiles
    #     all_percentiles = percentiles + ["total"]

    #     for p in all_percentiles:
    #         percentile_label = str(p)
    #         ws.append([percentile_label])
    #         # for tp in timepoints:
    #         #     # first two columns: percentile + timepoint
    #         #     row = []
    #         #     # fill rest with runtimes across all timebands
    #         #     for _, runtimes in data:
    #         #         row.append(runtimes.get(tp, ""))
    #         #     ws.append(row)

    # # ---- NORMAL MODE ----
    # else:
    #     for tp in timepoints:
    #         row = ["", tp]
    #         for _, runtimes in data:
    #             row.append(runtimes.get(tp, ""))
    #         ws.append(row)

    # wb.save(filename)

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