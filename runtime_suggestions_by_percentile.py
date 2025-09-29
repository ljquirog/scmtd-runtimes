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


def suggested_runtimes(route, percentiles, start, end, dow):
    """
    Build suggested runtimes for each timeband, using custom percentiles per timepoint.

    Args:
        route (int): The route ID
        percentiles (list[int]): List of percentiles, one per timepoint
        start, end (str): Date range
        dow (list): Days of week to filter

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

    # print("\nGrouped timebands (raw trips grouped):")
    # for tb in grouped_timebands:
    #     print("   ", tb)

    # print("\nNew (suggested) timebands (rolled up from groups):")
    # for tb in new_timebands:
    #     print("   ", tb)

    # === STEP 2: Extract timepoint names from the first trip ===
    print("\n=== STEP 2: Extract timepoint names ===")
    timepoints = []
    for trip_time, stops in percentile_runtimes.items():
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
        
        for day in daterange(start_dt, end_dt):
            day_str = day.strftime("%m-%d-%Y")
            print(day_str)
            # Skip if this day’s DOW not in allowed list
            dow_cp = [int(x.strip()) for x in dow.split(",") if x.strip()] # make dow a list
            dow_cp = [(d % 7) for d in dow_cp] # shift: 1→0 (Mon), …, 7→6 (Sun)
            
            if day.weekday() not in dow_cp:
                continue
            print(dow_cp, dow)
            daily_stats = get_route_stats(route, p, day_str, day_str, dow)
            print(daily_stats)
            daily_percentiles, _ = percentiles_test.runtime_per_trip(daily_stats)

            print(len(daily_percentiles))

            for trip_time, stops in daily_percentiles.items():
                value = stops.get(tp, 0)
                per_timepoint_runtimes[tp].setdefault(trip_time, []).append(value)
                print(f"Trip {trip_time}: {tp} runtime = {stops[tp]}")
        # route_stats = get_route_stats(route, p, start, end, dow)
        # percentile_runtimes, _ = percentiles_test.runtime_per_trip(route_stats)

        # # Fill per_timepoint_runtimes with runtimes for this stop at this percentile
        # for trip_time, stops in percentile_runtimes.items():
        #     value = stops.get(tp)
        #     if value is None:
        #         value = 0  # default, or continue
        #     per_timepoint_runtimes[tp][trip_time] = value
        #     # print(f"Trip {trip_time}: {tp} runtime = {stops[tp]}")

    # === STEP 4: Aggregate runtimes per timeband ===
    print("\n=== STEP 4: Aggregate runtimes per timeband ===")
    suggested = []
    for j, (timeband_range, _) in enumerate(new_timebands):
        tb_start, tb_end = timeband_range
        agg = {}
        print(f"\nTimeband {tb_start} - {tb_end}")

        # For each timepoint, look at all trips inside this timeband group
        for tp in timepoints:
            runtimes = []
            print(f"  Timepoint {tp}:")
            for trip_time, _ in grouped_timebands[j]:
                if trip_time in per_timepoint_runtimes[tp]:
                    runtimes.extend(per_timepoint_runtimes[tp][trip_time])  # append all days

            if runtimes:
                avg_val = math.ceil(sum(runtimes) / len(runtimes))
                agg[tp] = avg_val
                print(f"  → Avg across {len(runtimes)} values for {tp}: {avg_val}")

        agg["total"] = sum(agg.values())
        print(f"  → Total runtime for timeband: {agg['total']}")
        suggested.append(((tb_start, tb_end), agg))   
            
    # === FINAL OUTPUT ===
    print("\n=== FINAL SUGGESTED RUNTIMES ===")
    for tb in suggested:
        print(tb)

    return suggested

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
    rs = get_route_stats('16', 60, '09-11-2025', '09-12-2025', '1,2,3,4,5')
    print(rs)
    route, start_date, end_date, days_of_week, percentiles = '16', '09-11-2025', '09-27-2025', '1,2,3,4,5', [30,40,50]
    # print(get_num_timepoints(route, start_date, end_date, days_of_week))
    suggested = suggested_runtimes(route, percentiles, start_date, end_date, days_of_week)
    print(suggested)
    