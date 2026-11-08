%dw 2.0
import * from dw::module::Mime
output application/json
---
toString({'type': "application", subtype: "json", parameters: {}})