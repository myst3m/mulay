%dw 2.0
import * from dw::util::Values
output application/xml
---
payload update ["users", "user", "language"] with (if ($ == "English") "Gibberish" else $)