%dw 2.0
output application/json
var s1= 20201228 // (uuuuMMdd),
var s2= 1608 //(HHMM)
---
(s1 ++ s2)
as LocalDateTime {format:"uuuuMMddHHmm"}
as String {format:"MM-dd-uuuu HH:mm:ss"}