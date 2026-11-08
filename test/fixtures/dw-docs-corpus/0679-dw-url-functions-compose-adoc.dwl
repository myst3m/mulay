%dw 2.0
output application/json
var urlPath = "content folder"
import * from dw::core::URL
---
{ "encodedURL" : compose `http://examplewebsite.com/$(urlPath)/page.html`}