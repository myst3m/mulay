import * from dw::Runtime
var jsonValue = {
  value: '{"name": "Mariano"}' as Binary {encoding: "UTF-8"},
  encoding: "UTF-8",
  properties: {},
  mimeType: "application/json"
}

var Utils = "fun sum(a,b) = a +b"
---
{
  "execute_ok" : runUrl("classpath://org/mule/weave/v2/engine/runtime_runUrl/example.dwl", {"payload": jsonValue })
}