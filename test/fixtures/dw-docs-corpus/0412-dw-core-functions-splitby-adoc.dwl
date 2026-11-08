%dw 2.0
output application/json
---
{ "splitters" : {
   "split1" : "a-b-c" splitBy(/.b./),
   "split2" : "hello world" splitBy(/\s/),
   "split3" : "no match" splitBy(/^s/),
   "split4" : "no match" splitBy(/^n../),
   "split5" : "a1b2c3d4A1B2C3D" splitBy(/[0-9A-Z]/)
  }
}