%dw 2.0
var myVar = 1234
var myDo =  do {
    var fn = "Annie"
    var ln = "Point"
    var fromDoScope = "Platform"
    ---
    {
      id : myVar,
      firstname : fn,
      lastname : ln
    }
}
output application/xml
---
{
    person : myDo ++ { "outsideDoScope" : fromDoScope }
}