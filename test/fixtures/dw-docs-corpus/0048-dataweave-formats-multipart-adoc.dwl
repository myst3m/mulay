%dw 2.0
input payload multipart boundary='boundary1'
output multipart boundary='test2'
---
{
  parts : {
    orderAck : {
      headers : {
        "Content-Type": "text/plain"
      },
      content : "Order payload of type " ++ payload.parts.order.content.^mimeType ++ " and id " ++ (payload.parts.order.content.id as String) ++ " received. Receipt available."
    },
    partner: {
      headers : {
        "Content-Type": payload.parts.partner.content.^mediaType
      },
      content : payload.parts.partner.content
    }
  }
}