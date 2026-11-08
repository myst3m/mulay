%dw 2.0
import * from dw::Runtime
output application/json

var jsonDF = findDataFormatDescriptorByMime({'type': "*", subtype: "json", parameters: {}})
var unknownDF = findDataFormatDescriptorByMime({'type': "*", subtype: "*", parameters: {}})

fun simplify(df: DataFormatDescriptor | Null) = df  match {
  case d is DataFormatDescriptor -> { name: d.name, defaultMimeType: d.defaultMimeType }
  case is Null -> { name: "unknown", defaultMimeType: "unknown" }
}
---
{
  json: simplify(jsonDF),
  unknown: simplify(unknownDF)
}