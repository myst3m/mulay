%dw 2.0
var aRecord =
 [
    "bookId":"101",
    "title":"world history",
    "price":"19.99"
 ]
output application/xml
---
{ examples:
	{
	   ex1 : if (1 + 1 == 55) true
	         else false,
	   ex2 : if ([1,2,3,4][1] == 1) 1
	         else "value of index 1 is not 1",
	   ex3 : if (isEmpty(aRecord.bookId)) "ID is empty"
	  	 else "ID is not empty",
	   ex4 : aRecord.bookId map (idValue) ->
	   	 if (idValue as Number == 101) idValue as Number
		 else "not 101"
	}
}