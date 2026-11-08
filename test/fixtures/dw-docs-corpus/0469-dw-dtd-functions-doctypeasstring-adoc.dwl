%dw 2.0
import * from dw::xml::Dtd
output application/json
---
docTypeAsString({rootName: "cXML", systemId: "http://xml.cxml.org/schemas/cXML/1.2.014/cXML.dtd"})