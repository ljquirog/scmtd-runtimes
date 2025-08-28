import http.client
import json

conn = http.client.HTTPSConnection("api.goswift.ly")

headers = {
    'Accept': "application/json, text/csv; charset=utf-8, */*",
    'Authorization': "52d1916b5d1221ed54267b01e6a47de5"
}

conn.request("GET", "/run-times/santa-cruz/route/18/suggested-schedule?daysOfWeek=1%2C2%2C3%2C4%2C5&direction=0&allowableEarly=0&allowableLate=5&startDate=03-13-2025&endDate=06-19-2025", headers=headers)

res = conn.getresponse()
data = res.read()

json_parse = json.loads(data)

print(data)

# print(f"Stop ID: {json_parse['data']['filterData']['timebandSplitSeconds']}")



# loop


# print(data.decode("utf-8"))