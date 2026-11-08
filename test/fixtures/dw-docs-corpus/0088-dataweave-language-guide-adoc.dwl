%dw 2.0
output application/json
var collaborators =
{
    Max: {role: "admin", id: "01"},
    Einstein: {role: "dev", id: "02"},
    Astro: {role: "admin", id: "03"},
    Blaze: {role: "user", id: "04"}
}
---
filter(
   pluck(
       collaborators, (value,key,index)->
       {
           "Name": key,
           "Role": upper(value.role),
           "ID": value.id
       }),
   (item, index) -> item.Role == "ADMIN")