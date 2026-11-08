%dw 2.0
import * from dw::util::Coercions
output application/json
---
{
  toUriExample: toUri("https://www.google.com/")
}