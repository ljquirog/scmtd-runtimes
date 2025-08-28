import sys
import pandas as pd
from datetime import datetime, time, timedelta

def parse_time(value):
    if isinstance(value, time):
        return value
    elif isinstance(value, datetime):
        return value.time()
    elif isinstance(value, timedelta):
        full_datetime = (datetime.min + value)
        return full_datetime.time()
    elif isinstance(value, str):
        return datetime.strptime(value.strip(), "%H:%M:%S").time()
    else:
        raise ValueError(f"Unrecognized time format: {value} ({type(value)})")

def time_to_str(t):
    return t.strftime("%H:%M")

def add_one_minute(t):
    dt = datetime.combine(datetime.min, t) + timedelta(minutes=1)
    return dt.time()

def group_trips(df, threshold=180):
    df = df.copy()
    df['parsed_time'] = df['scheduled_trip_start_time'].apply(parse_time)
    df = df.sort_values('parsed_time')

    grouped = []
    current_group = []

    for i, row in df.iterrows():
        current_time = row['scheduled_trip_start_time']
        current_metric = float(row['metric'])

        if not current_group:
            current_group.append((current_time, current_metric))
            continue

        prev_metric = current_group[-1][1]
        if abs(current_metric - prev_metric) <= threshold:
            current_group.append((current_time, current_metric))
        else:
            grouped.append(current_group)
            current_group = [(current_time, current_metric)]

    if current_group:
        grouped.append(current_group)

    return grouped

def format_groups_to_columns(grouped):
    """
    Returns a dict: {column_header: [list_of_trip_times or trip_minutes]}
    Timeband headers are always [prev group's last time + 1] to [this group's last time].
    """
    columns = {}
    prev_end_time = None

    for i, group in enumerate(grouped):
        times = [parse_time(t) if not isinstance(t, time) else t for t, m in group]
        metrics = [float(m) for t, m in group]

        # Always use last time in the current group as the end
        end_time = times[-1]

        # Timeband starts at 1 minute after previous group's end, or first trip time if first group
        if prev_end_time:
            start_time = add_one_minute(prev_end_time)
        else:
            start_time = times[0]

        header = f"{time_to_str(start_time)} - {time_to_str(end_time)}"

        columns[header] = {
            'times': times,
            'metrics': metrics
        }

        prev_end_time = end_time  # update for next loop

    return columns

def main():
    if len(sys.argv) < 4:
        print("❌ Usage: python3 group_trips_by_metric_gap.py [file.xlsx] [sheet_name] [route_name]")
        sys.exit(1)

    file_path = sys.argv[1]
    sheet_name = sys.argv[2]
    route_name = sys.argv[3]

    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
    except Exception as e:
        print(f"❌ Error reading Excel file or sheet: {e}")
        sys.exit(1)

    grouped_trips = group_trips(df)
    columns = format_groups_to_columns(grouped_trips)
    max_len = max(len(v['times']) for v in columns.values())

    data_with_time = {}
    data_minutes_only = {}

    for header, content in columns.items():
        times = content['times']
        metrics = content['metrics']
        mins_rounded = [round(m / 60) for m in metrics]

        col_with_time = [f"[{time_to_str(t)} ; {m}]" for t, m in zip(times, mins_rounded)]
        col_mins_only = mins_rounded

        col_with_time.extend([""] * (max_len - len(col_with_time)))
        col_mins_only.extend([""] * (max_len - len(col_mins_only)))

        data_with_time[header] = col_with_time
        data_minutes_only[header] = col_mins_only

    df_with_time = pd.DataFrame(data_with_time)
    df_minutes_only = pd.DataFrame(data_minutes_only)

    output_file_1 = f"{route_name}_timeband_groups_with_time.xlsx"
    output_file_2 = f"{route_name}_timeband_groups_minutes_only.xlsx"

    df_with_time.to_excel(output_file_1, index=False)
    df_minutes_only.to_excel(output_file_2, index=False)

    print(f"\n✅ Excel files written:\n - {output_file_1}\n - {output_file_2}")

if __name__ == "__main__":
    main()
