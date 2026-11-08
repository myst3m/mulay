%dw 2.0
import * from dw::util::Coercions
output application/json
---
{
  transformTimeZone: toString(|Z|),
  transformBoolean: toString(true),
  transformPeriod: toString(|P1D|),
  transformRegex: toString(/a-Z/),
  transformPeriod: toString(|PT8M10S|),
  transformUri: toString("https://docs.mulesoft.com/" as Uri)
}  ++
{ transformKey : toString((keysOf({ "aKeyToString" : "aValue"})[0])) }