%dw 2.0
output application/json
---
{
  "prepend-append" : [
  	 // Array on right side when prepending.
     { "prepend" : 1 >> [2] },
     { "prepend-number" : 1 >> [1] },
     { "prepend-string" : "a" >> [1] },
     { "prepend-object" : { "a" : "b"} >> [1] },
     { "prepend-array" : [1] >> [2, 3] },
     { "prepend-binary" : (1 as Binary) >> [1] },
     { "prepend-date-time" : |23:57:59Z| >> [ |2017-10-01| ] },
  	 // Array is on left side when appending.
     { "append-number" : [1] << 2 },
     { "append-string" : [1] << "a" },
     { "append-object" : [1] << { "a" : "b"} },
     { "append-array" : [1,2] << [1, 2, 3] },
     { "append-binary" : [1] << (1 as Binary) },
     { "append-date-time" : [ |2017-10-01| ] << |23:57:59Z| },
     { "append-object-to-array" : [1,2] << {"a" : "b"} },
     { "append-array-to-array1" : ["a","b"] << ["c","d"] },
     { "append-array-to-array2" : [["a","b"],["c","d"]] << ["e","f"] },
     // + always appends within the array
     { "append-with-+" : [1] + 2 },
     { "append-with-+" : [2] + 1 },
     { "removeNumberFromArray" : ( [1,2,3] - 2 ) },
     { "removeObjectFromArray" : ( [ {a : "b"}, {c : "d"} , { e : "f"} ] - { c : "d"} ) }
  ]
}