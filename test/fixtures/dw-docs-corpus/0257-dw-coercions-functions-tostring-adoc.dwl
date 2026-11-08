%dw 2.0
import * from dw::util::Coercions
output application/json
---
{
   aDate: toString(|2003-10-01|, "uuuu/MM/dd"),
   aDateTime: toString(|2018-09-17T22:13:00-03:00|),
   aLocalTime: toString(|23:57:59|, "HH-mm-ss"),
   aLocalDateTime : toString(|2015-10-01T23:57:59|),
   aLocalDateTimeFormatted: toString(|2003-10-01T23:57:59|, "uuuu-MM-dd HH:mm:ss a"),
   aLocalDateTimeFormattedAndLocalizedSpain: toString(|2003-01-01T23:57:59|, "eeee, dd MMMM, uuuu HH:mm:ss a", "ES"),
   aTime: typeOf(|22:10:18Z|),
   aTimeZone: toString(|-03:00|)
}