# import csv
# import runtime_suggestions_by_percentile


# def runtimes_to_csv():
#     # collect all unique timepoints from the dicts
#     timepoints = list(data[0][1].keys())  # assumes all dicts have the same keys

#     # build header
#     header = ["timepoint"] + [str(tb[0]) + "–" + str(tb[1]) for tb, _ in data]

#     # write to CSV
#     with open(f"{route}_suggested_runtimes.csv", "w", newline="", encoding="utf-8") as f:
#         writer = csv.writer(f)
#         writer.writerow(header)
#         for tp in timepoints:
#             row = [tp]
#             for _, runtimes in data:
#                 row.append(runtimes.get(tp, ""))  # leave blank if missing
#             writer.writerow(row)

# if __name__ == "__main__":
#     route, start_date, end_date, days_of_week, percentiles = '20', '06-19-2025', '09-09-2025', '1,2,3,4,5', [30,30,40,50,50,60]
#     data = runtime_suggestions_by_percentile.suggested_runtimes(route, percentiles, start_date, end_date, days_of_week)
import csv
import runtime_suggestions_by_percentile


def runtimes_to_csv(data, route, filename, write_header=True, add_blank_row=False):
    # collect all unique timepoints from the dicts
    timepoints = list(data[0][1].keys())  # assumes all dicts have the same keys

    # build header
    header = ["timepoint"] + [str(tb[0]) + "–" + str(tb[1]) for tb, _ in data]

    # open in append mode
    mode = "a" if not write_header else "w"
    with open(filename, mode, newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if add_blank_row:
            writer.writerow([])  # separate datasets by one row

        if write_header:
            writer.writerow(header)

        for tp in timepoints:
            row = [tp]
            for _, runtimes in data:
                row.append(runtimes.get(tp, ""))  # leave blank if missing
            writer.writerow(row)


if __name__ == "__main__":
    filename = "11_suggested_runtimes.csv"

    # Suggested (first run)
    route, start_date, end_date, days_of_week, percentiles, direction = (
        "11", "06-19-2025", "09-09-2025", "1,2,3,4,5", [30,40,60], 1
    )
    data = runtime_suggestions_by_percentile.suggested_runtimes(
        route, percentiles, start_date, end_date, days_of_week, direction, 0
    )
    runtimes_to_csv(data, route, filename, write_header=True)

    # Scheduled (second run)
    data = runtime_suggestions_by_percentile.suggested_runtimes(
        route, percentiles, start_date, end_date, days_of_week, direction, 1
    )
    runtimes_to_csv(data, route, filename, write_header=False, add_blank_row=True)

    data = runtime_suggestions_by_percentile.end_to_end_runtimes(route, start_date, end_date, days_of_week)
    runtimes_to_csv(data, route, filename, write_header=False, add_blank_row=True)


