import json
import math
import api_request
import json_to_file
import percentiles_test
from datetime import datetime, timedelta

def daterange(start_date, end_date):
    """Yield each date in the range [start_date, end_date]."""
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

def get_route_stats(route, percentile, start_date, end_date, days_of_week):
    """
    Fetch route stats JSON for a given percentile and write to file.
    Returns the parsed JSON as a dict.
    """
    route_stats_json = api_request.call(route, percentile, start_date, end_date, days_of_week)
    json_to_file.txt_convert('routeStats.json', route_stats_json)  
    
    with open('routeStats.json', "r") as file:
        return json.load(file)
    
def get_num_timepoints(route, start, end, dow):
    length, timepoints = 0, []
    fixed_route_stats = get_route_stats(route, 60, start, end, dow)
    percentile_runtimes, schedule_runtimes = percentiles_test.runtime_per_trip(fixed_route_stats)
    for trip_time, stops in percentile_runtimes.items():
        
        # Make sure user provided the right number of percentiles
        length = len(stops)-1
        # Grab all stop names except 'total'
        timepoints = [tp for tp in stops if tp != "total"]
        break  # only need to do this once
    return length, timepoints

def end_to_end_runtimes(route, start, end, dow):
    print("END TO END RUNTIMES")
    # === STEP 1: Build "skeleton" timebands using default (60th percentile) ===
    print("\n=== STEP 1: Build skeleton timebands with default (60th) percentile ===")
    base_route_stats = get_route_stats(route, 60, start, end, dow)
    percentile_runtimes, schedule_runtimes = percentiles_test.runtime_per_trip(base_route_stats)

    grouped_timebands = percentiles_test.group_timebands(percentile_runtimes) # groups trips if runtimes are within threshold
    new_timebands = percentiles_test.make_timebands(grouped_timebands) # consolidate grouped trips into new timebands

    base_route_stats = get_route_stats(route, 90, start, end, dow)
    percentile_runtimes, schedule_runtimes = percentiles_test.runtime_per_trip(base_route_stats)
    

    # === STEP 2: Run end-to-end percentile runtimes per trip ===
    print("\n=== STEP 2: Run end-to-end percentile runtimes per trip ===")
    runtimes_90 = {"total": {}}
    for trip_time, stops in percentile_runtimes.items():
        runtimes_90["total"][trip_time] = stops["total"]
    # print(runtimes_90)

    # === STEP 3: Aggregate runtimes per timeband ===
    print("\n=== STEP 4: Aggregate runtimes per timeband ===")

    suggested = []
    for j, (timeband_range, _) in enumerate(new_timebands):
        tb_start, tb_end = timeband_range
        agg = {}
        print(f"\nTimeband {tb_start} - {tb_end}")

        # For each timepoint, look at all trips inside this timeband group
        for total in runtimes_90:
            new_runtimes = []

            for trip_time, _ in grouped_timebands[j]:
                if trip_time in runtimes_90[total]:
                    new_runtimes.append(runtimes_90[total][trip_time])  # append all days

            if new_runtimes:
                avg_val = math.ceil(sum(new_runtimes) / len(new_runtimes))
                agg[total] = avg_val
                print(f"  → Avg across {len(new_runtimes)} values for {total}: {avg_val}")

        agg["total"] = sum(agg.values())
        print(f"  → Total runtime for timeband: {agg['total']}")
        suggested.append(((tb_start, tb_end), agg))   
    
    print(suggested)
    return suggested
    


# t=0 for percentile, t=1 for scheduled
def suggested_runtimes(route, percentiles, start, end, dow, t=0):
    """
    Build suggested runtimes for each timeband, using custom percentiles per timepoint.

    Args:
        route (int): The route ID
        percentiles (list[int]): List of percentiles, one per timepoint
        start, end (str): Date range
        dow (list): Days of week to filter
        t (int): Type of runtime; t=0 for percentile, 1 for scheduled

    Returns:
        list: Suggested runtimes per new timeband in the form:
              [((start_time, end_time), {timepoint: avg_runtime, ..., "total": total})]
    """
    # Parse input dates (MM-DD-YYYY)
    start_dt = datetime.strptime(start, "%m-%d-%Y")
    end_dt = datetime.strptime(end, "%m-%d-%Y")

    # === STEP 1: Build "skeleton" timebands using default (60th percentile) ===
    print("\n=== STEP 1: Build skeleton timebands with default (60th) percentile ===")
    base_route_stats = get_route_stats(route, 60, start, end, dow)
    percentile_runtimes, schedule_runtimes = percentiles_test.runtime_per_trip(base_route_stats)
    grouped_timebands = percentiles_test.group_timebands(percentile_runtimes) # groups trips if runtimes are within threshold
    new_timebands = percentiles_test.make_timebands(grouped_timebands) # consolidate grouped trips into new timebands

    # checking what it would look like if you ran this w/ scheduled runtimes
    # percentile_runtimes = schedule_runtimes # be careful
    runtimes = percentile_runtimes if t==0 else schedule_runtimes
    
    # print("\nGrouped timebands (raw trips grouped):")
    # for tb in grouped_timebands:
    #     print("   ", tb)

    # print("\nNew (suggested) timebands (rolled up from groups):")
    # for tb in new_timebands:
    #     print("   ", tb)

    # === STEP 2: Extract timepoint names from the first trip ===
    print("\n=== STEP 2: Extract timepoint names ===")
    timepoints = []
    for trip_time, stops in runtimes.items():
        if len(stops)-1 != len(percentiles):
            raise ValueError("Number of timepoints != number of percentiles provided")
        timepoints = [tp for tp in stops if tp != "total"] # Grab all stop names except 'total'
        break  # only need to do this once
    print("Timepoints:", timepoints)
    print("Percentiles:", percentiles)

    # === STEP 3: Re-run stats for each timepoint at its assigned percentile ===
    print("\n=== STEP 3: Re-run stats for each timepoint at its assigned percentile ===")
    # Nested dict: {tp: {trip_time: [list of runtimes across days]}}
    per_timepoint_runtimes = {tp: {} for tp in timepoints}

    for i, p in enumerate(percentiles):
        tp = timepoints[i]
        print(f"\n-- Collecting runtimes for timepoint '{tp}' at percentile {p} --")

        route_stats = get_route_stats(route, p, start, end, dow)
        
        if t==0:
            runtimes, _ = percentiles_test.runtime_per_trip(route_stats)
        else: 
            _, runtimes = percentiles_test.runtime_per_trip(route_stats)

        # Fill per_timepoint_runtimes with runtimes for this stop at this percentile
        for trip_time, stops in runtimes.items():
            value = stops.get(tp)
            if value is None:
                value = 0  # default, or continue
            per_timepoint_runtimes[tp][trip_time] = value
            # print(f"Trip {trip_time}: {tp} runtime = {stops[tp]}")

    # === STEP 4: Aggregate runtimes per timeband ===
    print("\n=== STEP 4: Aggregate runtimes per timeband ===")
    suggested = []
    for j, (timeband_range, _) in enumerate(new_timebands):
        tb_start, tb_end = timeband_range
        agg = {}
        print(f"\nTimeband {tb_start} - {tb_end}")

        # For each timepoint, look at all trips inside this timeband group
        for tp in timepoints:
            new_runtimes = []
            print(f"  Timepoint {tp}:")
            for trip_time, _ in grouped_timebands[j]:
                if trip_time in per_timepoint_runtimes[tp]:
                    new_runtimes.append(per_timepoint_runtimes[tp][trip_time])  # append all days

            if new_runtimes:
                avg_val = math.ceil(sum(new_runtimes) / len(new_runtimes))
                agg[tp] = avg_val
                print(f"  → Avg across {len(new_runtimes)} values for {tp}: {avg_val}")

        agg["total"] = sum(agg.values())
        print(f"  → Total runtime for timeband: {agg['total']}")
        suggested.append(((tb_start, tb_end), agg))   
    
    # print(per_timepoint_runtimes)
    # === FINAL OUTPUT ===
    print("\n=== FINAL SUGGESTED RUNTIMES ===")
    for tb in suggested:
        print(tb)

    return suggested

def test_diff():
    base_route_stats = get_route_stats(11, 60, "06-19-2025", "09-10-2025", "1,2,3,4,5")
    percentile_runtimes, schedule_runtimes = percentiles_test.runtime_per_trip(base_route_stats)
    with open("percentile_test.txt", "w") as file:
        file.write(str(percentile_runtimes))
    
    with open("schedule_test.txt", "w") as file:
        file.write(str(schedule_runtimes))
    
if __name__ == "__main__":
    
    # def_start, def_end = "09-11-2025", "09-24-2025"
    # default_wd, default_we = "1,2,3,4,5", "6,7"

    # date_presets = {
    #     "default_s": def_start,
    #     "default_e": def_end,
    # }

    # dow_presets = {
    #     "default_wd": default_wd,
    #     "default_we": default_we,
    # }

    # # Ask for start & end date
    # raw_dates = input(
    #     f"* Start date and end date\n"
    #     f"** Format: 'MM-DD-YY' 'MM-DD-YY'\n"
    #     f"Press Enter for default ({def_start} to {def_end}), "
    #     f"or use 'default_s' / 'default_e': "
    # ).strip()

    # if raw_dates:
    #     start_date, end_date = raw_dates.split()
    #     # Replace presets if typed
    #     start_date = date_presets.get(start_date, start_date)
    #     end_date   = date_presets.get(end_date, end_date)
    # else:
    #     # Blank input → full defaults
    #     start_date, end_date = def_start, def_end

    # # Ask for days of week
    # days_of_week = input(
    #     f"* Day of week\n"
    #     f"** Format: '1,2,3,4,5,6,7'\n"
    #     f"Press Enter for default (weekday={default_wd}), "
    #     f"or type 'default_wd' / 'default_we': "
    # ).strip()

    # if days_of_week:
    #     days_of_week = dow_presets.get(days_of_week, days_of_week)
    # else:
    #     # Blank input → default weekdays
    #     days_of_week = default_wd

    # route = input("* Route: ")
    # length, timepoints = get_num_timepoints(route, start_date, end_date, days_of_week)
    # print(f"\n> Route {route} has {length} timepoints:")
    # for tp in timepoints:
    #     print(">> ", tp)
    
    # if length == 0:
    #     raise ValueError("Timepoint calculation failed; route has 0 timepoints")
    
    # percentiles = input(f"\n* List the percentiles you'd like each timepoint to be ran at.\n** Format: 30,40,50\n")

    # percentiles = [int(x.strip()) for x in percentiles.split(",")]

    # suggested = suggested_runtimes(route, percentiles, start_date, end_date, days_of_week)
    # # print(suggested)
    
    # -- Left off here --
        # TODO: Add variables to suggested_runtimes
        
        # Other ideas:
        # - Compare runtime suggestions total to avg timeband total
        #     - E.g. do the 90th and take the difference to get layover
        # - Write a function to convert suggested runtimes to csv in json_to_csv and call it in main
        # - Combine timebands_by_percentile and runtime_suggestions_by_percentile together??

    # 09/29: left off debugging why route stats is empty for route 16 @ a single day level
    # in step 3, get_route_stats returns an empty path_stats. so debug at this level first then revisit
    # the point: aggregate all the days in the date range instead of just one (last commit)
    # rs = get_route_stats('16', 60, '09-11-2025', '09-14-2025', '1,2,3,4,5')
    # print(rs)

    # route, start_date, end_date, days_of_week, percentiles = '11', '09-11-2025', '10-01-2025', '1,2,3,4,5', [30,40,50]
    # # print(get_num_timepoints(route, start_date, end_date, days_of_week))
    # suggested = suggested_runtimes(route, percentiles, start_date, end_date, days_of_week, 1)
    # # print(suggested)
    
    route, start_date, end_date, days_of_week, percentiles = (
        "11", "06-19-2025", "09-09-2025", "1,2,3,4,5", [30,40,60]
    )
    # data = suggested_runtimes(
    #     route, percentiles, start_date, end_date, days_of_week, 1
    # )
    end_to_end_runtimes(route, start_date, end_date, days_of_week)

    