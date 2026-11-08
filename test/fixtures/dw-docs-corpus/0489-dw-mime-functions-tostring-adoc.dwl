%dw 2.0
import * from dw::module::Mime
output application/json
---
toString({'type': "multipart", subtype: "form-data", parameters: {boundary: "my-boundary"}})