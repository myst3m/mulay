%dw 2.0
var myDateTime1 = |2017-10-01T22:57:59-03:00|
var myDateTime2 = |2018-10-01T23:57:59-03:00|
output application/json
---
{
  myMaxBy: {
    byDateTime: [ myDateTime1, myDateTime2 ] maxBy ((item) -> item),
    byDate: [ myDateTime1 as Date, myDateTime2 as Date ] maxBy ((item) -> item),
    byTime: [ myDateTime1 as Time, myDateTime2 as Time ] maxBy ((item) -> item),
    emptyArray: [] maxBy ((item) -> item)
  }
}