%dw 2.0
output application/json
---
{
  "DateTime1" : (|23:57:59| as Time) ++ |2017-10-01|,
  "DateTime2" : |23:57:59Z| ++ |2017-10-01|,
  "DateTime3" : |2017-10-01| ++ |23:57:59+02:00|
}