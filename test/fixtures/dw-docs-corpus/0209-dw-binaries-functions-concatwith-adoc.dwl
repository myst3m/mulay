%dw 2.0
import * from dw::core::Binaries
output application/dw
---
"CAFE" as Binary {base: "16"} concatWith "ABCD" as Binary {base: "16"}