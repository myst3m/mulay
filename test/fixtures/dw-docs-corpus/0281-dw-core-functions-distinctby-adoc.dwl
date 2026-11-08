%dw 2.0
output application/xml
---
{
   book : {
     title : payload.book.title,
     authors: payload.book.&author distinctBy $
   }
}