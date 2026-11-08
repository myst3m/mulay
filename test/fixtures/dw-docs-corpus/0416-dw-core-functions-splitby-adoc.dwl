%dw 2.0
output application/json
---
{ "splitters" : {
    "split1" : "a-b-c" splitBy("-"),
    "split2" : "hello world" splitBy(""),
    "split3" : "first,middle,last" splitBy(","),
    "split4" : "no split" splitBy("NO")
   }
}