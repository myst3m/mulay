%dw 2.0
// 偽の Salesforce の応答。vars.mode (呼ぶ側が Object Store に置く) と要求の path で決める
output application/java
var p = attributes.requestPath
var m = vars.mode default 'ok'
fun j(status, body) = {status: status, body: body, ct: 'application/json'}
var okBody =
  if (p endsWith '/composite/batch/')
    '{"hasErrors":false,"results":[{"statusCode":201,"result":{"id":"001A","success":true,"errors":[]}},{"statusCode":204,"result":null},{"statusCode":400,"result":[{"errorCode":"NOT_FOUND","message":"The requested resource does not exist"}]},{"statusCode":200,"result":{"attributes":{"type":"Account"},"Id":"001A","Name":"Acme"}},{"statusCode":200,"result":{"totalSize":1,"done":true,"records":[{"Id":"001A"}]}}]}'
  else if (p contains '/composite/tree/')
    '{"hasErrors":false,"results":[{"referenceId":"ref1","id":"001T"},{"referenceId":"ref2","id":"003T"}]}'
  else if (p endsWith '/composite/graph/')
    '{"graphs":[{"graphId":"g1","graphResponse":{"compositeResponse":[{"body":{"id":"001G","success":true,"errors":[]},"httpHeaders":{"Location":"/services/data/v67.0/sobjects/Account/001G"},"httpStatusCode":201,"referenceId":"newAcc"}]},"isSuccessful":true}]}'
  else if (p endsWith '/composite')
    '{"compositeResponse":[{"body":{"id":"001C","success":true,"errors":[]},"httpHeaders":{"Location":"/services/data/v67.0/sobjects/Account/001C"},"httpStatusCode":201,"referenceId":"r1"},{"body":[{"errorCode":"PROCESSING_HALTED","message":"The transaction was rolled back since another operation in the same transaction failed."}],"httpHeaders":{},"httpStatusCode":400,"referenceId":"r2"}]}'
  else if (p endsWith '/composite/sobjects/Account')
    '[{"attributes":{"type":"Account","url":"/services/data/v67.0/sobjects/Account/001A"},"Id":"001A","Name":"Acme"},null]'
  else if (p endsWith '/composite/sobjects/Account/ExtId__c')
    '[{"id":"001A","success":true,"errors":[],"created":false}]'
  else if (p endsWith '/composite/sobjects')
    '[{"id":"001A","success":true,"errors":[]},{"success":false,"errors":[{"statusCode":"REQUIRED_FIELD_MISSING","message":"Required fields are missing: [Name]","fields":["Name"]}]}]'
  else if (p contains '/query/01gNEXT')
    '{"totalSize":3,"done":true,"records":[{"attributes":{"type":"Account"},"Id":"001C","Name":"C"}]}'
  else if (p endsWith '/limits')
    '{"DailyApiRequests":{"Max":15000,"Remaining":14999}}'
  else '{}'
---
m match {
  case 'nums' -> j(200, '{"hasErrors":false,"results":[{"i":1,"l":2147483648,"b":9223372036854775808,"d":1.5,"e":1e2,"z":-0,"t":true,"n":null,"s":"x","a":[1,2.0],"o":{"y":1,"x":2}}],"zz":0}')
  case 's400' -> j(400, '[{"message":"The request body is either invalid or incomplete.","errorCode":"JSON_PARSER_ERROR"}]')
  case 's401' -> j(401, '[{"message":"Session expired or invalid","errorCode":"INVALID_SESSION_ID"}]')
  case 's401other' -> j(401, '[{"message":"nope","errorCode":"OTHER"}]')
  case 's401obj' -> j(401, '{"error":"nope"}')
  case 's401text' -> j(401, 'nope')
  case 's500phrase' -> j(500, 'Session timed out, please log in again')
  case 's404empty' -> j(404, '')
  case 'empty' -> j(200, '')
  case 'badjson' -> j(200, 'not json')
  case 'array' -> j(200, '[1,2]')
  case 'object' -> j(200, '{"a":1}')
  case 'null' -> j(200, 'null')
  case 'trailing' -> j(200, '{"a":1} trailing')
  case 'dupkey' -> j(200, '{"a":1,"b":2,"a":3}')
  case 'slow' -> j(200, okBody)
  else -> j(200, okBody)
}
