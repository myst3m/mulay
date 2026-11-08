%dw 2.0
output application/json
var parseDate = (dateStr) -> (
  if (dateStr contains /^[A-z][A-z][A-z],/)
    dateStr as Localdatetime {format: "E, d LLL u H:m:s O"}
  else if (dateStr contains /^[A-z][A-z][A-z]\s/)
      (dateStr as Localdatetime {format: "E LLL d H:m:s u"})
    else dateStr as Localdatetime {format: "cccc, d-LLL-u H:m:s O"})
---
date: parseDate(payload.dateString)