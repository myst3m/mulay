%dw 2.0
var myInput = [
    {
        "AccountNumber": "987999321",
        "NameOnAccount": "QA",
        "Type": "AAAA",
        "CDetail": {
            "Status": "Open"
        }
    },
    {
        "AccountNumber": "12399978",
        "NameOnAccount": "QA",
        "Type": "BBBB",
        "CDetail": {}
    },
    {
        "AccountNumber": "32199974",
        "NameOnAccount": "QA",
        "Type": "CCCC",
        "CDetail": {}
    }
]
output application/json
---
(myInput orderBy $.Type)[-1 to 0]