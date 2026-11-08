%dw 2.0
output application/json
---
{
    header: {
        senderId: payload.cXML.Header.From.Credential.Identity,
        receiverId: payload.cXML.Header.To.Credential.Identity,
        docType: payload.^docType
    }
}