%dw 2.0
output application/xml
---
{
  name @(
    (company: "Acme") if false,
    (transform: "Anything") if true
  ): "DataWeave"
}