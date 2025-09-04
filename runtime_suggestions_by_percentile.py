import json
import math
import api_request
import json_to_file
import percentiles_test


def get_route_stats(route, percentile, start_date, end_date, days_of_week):
    """Fetch route stats JSON for a given percentile"""
    route_stats_json = api_request.call(route, percentile, start_date, end_date, days_of_week)
    json_to_file.txt_convert('routeStats.json', route_stats_json)  
    
    with open('routeStats.json', "r") as file:
        return json.load(file)


def suggested_runtimes(route, percentiles, start, end, dow):
    """
    Build suggested runtimes by averaging per-timepoint values 
    for all trips within each new timeband.
    """
    print("\n=== STEP 1: Build skeleton timebands with default (60th) percentile ===")
    base_route_stats = get_route_stats(route, 60, start, end, dow)
    percentile_runtimes, schedule_runtimes = percentiles_test.runtime_per_trip(base_route_stats)

    grouped_timebands = percentiles_test.group_timebands(percentile_runtimes)
    new_timebands = percentiles_test.make_timebands(grouped_timebands)

    print("\nGrouped timebands:")
    for tb in grouped_timebands:
        print("   ", tb)

    print("\nNew (suggested) timebands:")
    for tb in new_timebands:
        print("   ", tb)

    print("\n=== STEP 2: Extract timepoint names ===")
    timepoints = []
    for trip_time, stops in percentile_runtimes.items():
        # print("# stops: ", len(stops), "# percentiles: ", len(percentiles))
        # print("stops: ", stops, "percentiles: ", percentiles)
        if len(stops)-1 != len(percentiles):
            raise ValueError("Number of timepoints != number of percentiles provided")
        timepoints = [tp for tp in stops if tp != "total"]
        break
    print("Timepoints:", timepoints)
    print("Percentiles:", percentiles)

    print("\n=== STEP 3: Re-run stats for each timepoint at its assigned percentile ===")
    per_timepoint_runtimes = {tp: {} for tp in timepoints}

    for i, p in enumerate(percentiles):
        tp = timepoints[i]
        print(f"\n-- Fetching runtimes for timepoint '{tp}' at percentile {p} --")
        route_stats = get_route_stats(route, p, start, end, dow)
        percentile_runtimes, _ = percentiles_test.runtime_per_trip(route_stats)

        for trip_time, stops in percentile_runtimes.items():
            per_timepoint_runtimes[tp][trip_time] = stops[tp]
            print(f"Trip {trip_time}: {tp} runtime = {stops[tp]}")

    print("\n=== STEP 4: Aggregate runtimes per timeband ===")
    suggested = []
    for j, (timeband_range, _) in enumerate(new_timebands):
        tb_start, tb_end = timeband_range
        agg = {}
        print(f"\nTimeband {tb_start} - {tb_end}")

        for tp in timepoints:
            runtimes = []
            print(f"  Timepoint {tp}:")
            for trip_time, _ in grouped_timebands[j]:
                if trip_time in per_timepoint_runtimes[tp]:
                    runtime_val = per_timepoint_runtimes[tp][trip_time]
                    runtimes.append(runtime_val)
                    print(f"    Trip {trip_time} → {runtime_val}")

            if runtimes:
                avg_val = math.ceil(sum(runtimes) / len(runtimes))
                agg[tp] = avg_val
                print(f"  → Average (rounded up) for {tp}: {avg_val}")

        agg["total"] = sum(agg.values())
        print(f"  → Total runtime for timeband: {agg['total']}")

        suggested.append(((tb_start, tb_end), agg))

    print("\n=== FINAL SUGGESTED RUNTIMES ===")
    for tb in suggested:
        print(tb)

    return suggested

if __name__ == "__main__":
    suggested_runtimes(11, [30, 40, 50], '03-16-2025', '06-18-2025', '1,2,3,4,5')