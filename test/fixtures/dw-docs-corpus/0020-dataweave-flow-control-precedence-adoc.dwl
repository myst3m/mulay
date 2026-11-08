%dw 2.0
output application/json
var flights = [
  { "toAirport": "SFO", "price": 550, "airline": "American" },
  { "toAirport": "MUA", "price": 200, "airline": "American" },
  { "toAirport": "SFO", "price": 300, "airline": "American" },
  { "toAirport": "CLE", "price": 600, "airline": "American" },
  { "toAirport": "CLE", "price": 190, "airline": "American" },
  { "toAirport": "SFO", "price": 400, "airline": "American" }
]
---
( ( ( flights filter $.price < 500 ) orderBy $.price ) groupBy $.toAirport )