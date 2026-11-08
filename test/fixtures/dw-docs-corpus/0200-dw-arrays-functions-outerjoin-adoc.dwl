%dw 2.0
import * from dw::core::Arrays
var users = [{id: "1", name:"Mariano"},{id: "2", name:"Leandro"},{id: "3", name:"Julian"},{id: "5", name:"Julian"}]
var products = [{ownerId: "1", name:"DataWeave"},{ownerId: "1", name:"BAT"}, {ownerId: "3", name:"DataSense"}, {ownerId: "4", name:"SmartConnectors"}]
output application/json
---
outerJoin(users, products, (user) -> user.id, (product) -> product.ownerId)