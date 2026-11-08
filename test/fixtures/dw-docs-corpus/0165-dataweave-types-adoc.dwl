output application/json
var period = (|2010-12-10T12:10:12| - |2010-09-09T10:02:10|)
---
{
 nanos: period as Number {unit: "nanos"},
 millis: period as Number {unit: "milliseconds"},
 seconds: period as Number {unit: "seconds"},
 hours: period as Number {unit: "hours"},
 days: period as Number {unit: "days"}
}