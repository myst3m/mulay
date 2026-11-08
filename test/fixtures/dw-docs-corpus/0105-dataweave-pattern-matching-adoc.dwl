%dw 2.0
var myInput = {
  "phones": [
    "+1 (415) 229-2009",
    "(647) 456-7008"
  ]
}
output application/json
---
{
  a: myInput.phones map ($ match {
     case phone matches /\+(\d+)\s\((\d+)\)\s(\d+\-\d+)/ -> { country: phone[1]}
     case phone matches /\((\d+)\)\s(\d+\-\d+)/ -> { area: phone[1], number: phone[2] }
   }),
 b: myInput.phones map ($ match {
   case phone matches /\+(\d+)\s\((\d+)\)\s(\d+\-\d+)/ -> { country: phone[1], area: phone[2], number: phone[3] }
   case phone matches /\((\d+)\)\s(\d+\-\d+)/ -> { area: phone[1], number: phone[2] }
 })
}