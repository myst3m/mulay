%dw 2.0
output application/json

var myUser = {user: {friend: {name: "Shoki"}, id: 1, name: "Tomo"}, accountId: "leansh" }
---
log("User", myUser.user).friend.name