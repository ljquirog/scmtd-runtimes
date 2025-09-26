import csv
import runtime_suggestions_by_percentile

if __name__ == "__main__":
    route, start_date, end_date, days_of_week, percentiles = '20', '06-19-2025', '09-09-2025', '1,2,3,4,5', [30,30,40,50,50,60]
    data = runtime_suggestions_by_percentile.suggested_runtimes(route, percentiles, start_date, end_date, days_of_week)

# collect all unique timepoints from the dicts
timepoints = list(data[0][1].keys())  # assumes all dicts have the same keys

# build header
header = ["timepoint"] + [str(tb[0]) + "–" + str(tb[1]) for tb, _ in data]

# write to CSV
with open(f"{route}_suggested_runtimes.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(header)
    for tp in timepoints:
        row = [tp]
        for _, runtimes in data:
            row.append(runtimes.get(tp, ""))  # leave blank if missing
        writer.writerow(row)