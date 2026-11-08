%dw 2.0
var myData =
{ user : [
   {
     group : "dev",
     myarray : [
       { name : "Shoki", id : 5678 },
       { name : "Mariano", id : 9123 }
     ]
   },
   {
     group : "test",
     myarray : [
       { name : "Sai", id : 2001 },
       { name : "Peter", id : 2002 }
     ]
   }
 ]
}
output application/json
---
flatten(myData.user.myarray)