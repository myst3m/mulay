%dw 2.0
output application/json
---
{
    id: payload.Id,
    markCode: payload.marketCode,
    languageCode: payload.languageCode,
    username: payload.profile.base.username,
    phoneNumber: (payload.profile.base.phone filter ($.activeInd == "Y" and $.primaryInd== "Y")).number default []
}