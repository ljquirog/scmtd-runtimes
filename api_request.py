import http.client
import csv
import json
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("API_KEY")

# args: route (str), percentile (int), start date ("MM-DD-YYYY"), end date ("MM-DD-YYYY"), days of week (comma delimited, no spaces)
def call(route=11, percentile=60, start_date ="03-13-2025", end_date="06-18-2025", days_of_week="1,2,3,4,5", dir=1):
    conn = http.client.HTTPSConnection("api.goswift.ly")

    headers = {
        'Accept': "application/json, text/csv; charset=utf-8, */*",
        'Authorization': api_key
    }

    conn.request("GET", f"/run-times/santa-cruz/path-stats?routes={route}&additionalGroupBy=SCHEDULED_TRIP_START_TIME,SCHEDULED_RUN_TIME&aggregationTypes=PERCENTILE&aggregationFields=RUN_TIME&listAggregations=SCHEDULED_RUN_TIME&percentiles={percentile}&groupByTimepoint=true&startDate={start_date}&endDate={end_date}&daysOfWeek={days_of_week}&excludeDates=01-20-2025,02-17-2025,09-01-2025,05-26-2025,12-24-2025,12-24-2024,12-25-2025,12-25,2024&directionId={dir}", headers=headers)

    res = conn.getresponse()
    data = res.read()
    
    # parse string
    percentiles = json.loads(data)
    
    return percentiles

if __name__ == "__main__":
    print(call())

