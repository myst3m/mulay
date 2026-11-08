%dw 2.0
// 偽の注文システム (SOAP)。payload は受け取った SOAP の要求 (XML)。X999 は障害 (Fault)
output application/java
var id = (payload..id)[0] default ''
var orders = {A100: {status: 'shipped', eta: '2026-10-12'}, B200: {status: 'packing'}}
var o = orders[id] default {status: 'not found'}
fun env(body) = '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body>' ++ body ++ '</soap:Body></soap:Envelope>'
---
if (id == 'X999') {status: 500, body: env('<soap:Fault><faultcode>soap:Server</faultcode><faultstring>the order system is down</faultstring></soap:Fault>')}
else {status: 200, body: env('<o:getOrderResponse xmlns:o="urn:example:orders"><status>' ++ o.status ++ '</status>'
    ++ (if (o.eta != null) '<eta>' ++ o.eta ++ '</eta>' else '') ++ '</o:getOrderResponse>')}
