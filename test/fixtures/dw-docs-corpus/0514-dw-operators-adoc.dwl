%dw 2.0
output application/dw
---
{ "equality" :
  [
    (1 == 1),
    (1 == 2),
    ("true" == true),
    ("true" ~= true),
    (['true'] ~= [true]),
    ('1' ~= 1)
  ]
}