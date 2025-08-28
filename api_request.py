import http.client
import csv
import json

# args: route (str), percentile (int), start date ("MM-DD-YYYY"), end date ("MM-DD-YYYY"), days of week (comma delimited, no spaces)
def call(route=11, percentile=60, start_date ="03-13-2025", end_date="06-18-2025", days_of_week="1,2,3,4,5"):
    conn = http.client.HTTPSConnection("api.goswift.ly")

    headers = {
        'Accept': "application/json, text/csv; charset=utf-8, */*",
        'Authorization': "52d1916b5d1221ed54267b01e6a47de5"
    }

    conn.request("GET", f"/run-times/santa-cruz/path-stats?routes={route}&additionalGroupBy=SCHEDULED_TRIP_START_TIME,SCHEDULED_RUN_TIME&aggregationTypes=PERCENTILE&aggregationFields=RUN_TIME&listAggregations=SCHEDULED_RUN_TIME&percentiles={percentile}&groupByTimepoint=true&startDate={start_date}&endDate={end_date}&daysOfWeek={days_of_week}", headers=headers)

    res = conn.getresponse()
    data = res.read()
    
    # parse string
    percentiles = json.loads(data)
    
    return percentiles

if __name__ == "__main__":
    print(call())

