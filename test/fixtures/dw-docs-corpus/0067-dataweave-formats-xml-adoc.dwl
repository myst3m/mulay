%dw 2.0
output application/json
---
payload.root.*employees map ((payload01 , indexOfPayload01) ->
  {
     Id: payload01.Id as String,
     Name: payload01.Name as String,
     Address: payload01.Address replace /([\-\,\/])/ with " "
  }
)