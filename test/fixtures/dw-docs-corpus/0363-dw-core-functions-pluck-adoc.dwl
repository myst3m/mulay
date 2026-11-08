%dw 2.0
output application/json
---
{"a":"b","c":"d"} pluck (value,key,index) -> { (index) : { (value):key} }