%dw 2.0
import * from dw::Runtime
var jsonValue = {
  value: '{"name": "Mariano"}' as Binary {encoding: "UTF-8"},
  encoding: "UTF-8",
  properties: {},
  mimeType: "application/json"
}

var Utils = "fun sum(a,b) = a +b"
output application/json
---
{
  "execute_ok" : evalUrl("classpath://org/mule/weave/v2/engine/runtime_evalUrl/example.dwl", {"payload": jsonValue }),
  "execute_ok_withValue" : evalUrl("classpath://org/mule/weave/v2/engine/runtime_evalUrl/example.dwl", {}, {"payload": {name: "Mariano"}})
}