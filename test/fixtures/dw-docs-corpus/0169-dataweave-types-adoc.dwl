%dw 2.0
output application/json
var myDate = |2003-10-01T23:57:59.700-03:00|
---
{
  year: myDate.year,
  month: myDate.month,
  day: myDate.day,
  hour: myDate.hour,
  minutes: myDate.minutes,
  seconds: myDate.seconds,
  milliseconds: myDate.milliseconds,
  nanoseconds: myDate.nanoseconds,
  quarter: myDate.quarter,
  dayOfWeek: myDate.dayOfWeek,
  dayOfYear: myDate.dayOfYear,
  offsetSeconds: myDate.offsetSeconds
}