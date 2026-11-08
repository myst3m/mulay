%dw 2.0
output application/json
var period = (|2010-12-10T12:10:12| - |2010-12-10T10:02:10|)
---
{
   hours:  period.hours,
   minutes:  period.minutes,
   secs:  period.secs,
}