%dw 2.0
output application/csv
---
[{
 "age": 14 ,
 "name": "Claire"
}, {
 "age": 56,
 "name": "Max"
}, {
 "age": 89,
 "name": "John"
}] map {
   age: $.age,
   name: $.name
}