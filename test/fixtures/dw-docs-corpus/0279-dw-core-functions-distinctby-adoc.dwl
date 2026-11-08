%dw 2.0
output application/json
var record =  {
  "title": "XQuery Kick Start",
  "author": [
    "James McGovern",
    "Per Bothner",
    "Kurt Cagle",
    "James Linn",
    "Kurt Cagle",
    "Kurt Cagle",
    "Kurt Cagle",
    "Vaidyanathan Nagarajan"
  ],
  "year":"2000"
}
---
{
    "book" : {
      "title" : record.title,
      "year" : record.year,
      "authors" : record.author distinctBy $
    }
}