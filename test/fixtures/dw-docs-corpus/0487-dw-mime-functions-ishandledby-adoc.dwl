%dw 2.0
import * from dw::module::Mime
output application/json

var JSON = {'type': "application", subtype: "json", parameters: {}}
var MULTIPART = {'type': "multipart", subtype: "form-data", parameters: {boundary: "my-boundary"}}
var ALL = {'type': "*", subtype: "*", parameters: {}}
---
{
  a: isHandledBy(JSON, JSON),
  b: isHandledBy({'type': "*", subtype: "json", parameters: {}}, JSON),
  c: isHandledBy({'type': "application", subtype: "*", parameters: {}}, JSON),
  d: isHandledBy(ALL, MULTIPART),
  e: isHandledBy(MULTIPART, ALL),
  f: isHandledBy(JSON, MULTIPART),
  g: isHandledBy(
    {'type': "application", subtype: "*+xml", parameters: {}},
    {'type': "application", subtype: "soap+xml", parameters: {}})
}