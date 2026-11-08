%dw 2.0
import * from dw::module::Mime
output application/json
---
fromString("multipart/form-data; boundary=the-boundary")