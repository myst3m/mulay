%dw 2.0
import * from dw::core::Arrays
var arr0 = [] as Array<Number>
output application/json
---
{ "results" : [
     "ok" : [
        [1,1,1] every ($ == 1),
        [1] every ($ == 1)
     ],
     "err" : [
        [1,2,3] every ((log('should stop at 2 ==', $) mod 2) == 1),
        [1,1,0] every ($ == 1),
        [0,1,1,0] every (log('should stop at 0 ==', $) == 1),
        [1,2,3] every ($ == 1),
        arr0 every true,
     ]
   ]
 }