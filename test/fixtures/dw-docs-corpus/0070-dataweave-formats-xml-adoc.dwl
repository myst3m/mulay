%dw 2.0
output application/json
import * from dw::xml::Dtd
---
docTypeAsString(payload.^docType)