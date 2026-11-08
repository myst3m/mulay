import * from dw::Runtime
var jsonValue = {
  value: '{"name": "Mariano"}' as Binary {encoding: "UTF-8"},
  encoding: "UTF-8",
  properties: {},
  mimeType: "application/json"
}

var jsonValue2 = {
  value: '{"name": "Mariano", "lastName": "achaval"}' as Binary {encoding: "UTF-8"},
  encoding: "UTF-8",
  properties: {},
  mimeType: "application/json"
}

var invalidJsonValue = {
  value: '{"name": "Mariano' as Binary {encoding: "UTF-8"},
  encoding: "UTF-8",
  properties: {},
  mimeType: "application/json"
}

var Utils = "fun sum(a,b) = a +b"
---
{
  "execute_ok" : run("main.dwl", {"main.dwl": "{a: 1}"}, {"payload": jsonValue }),
  "logs" : do {
    var execResult = run("main.dwl", {"main.dwl": "{a: log(1)}"}, {"payload": jsonValue })
    ---
    {
        m: execResult.logs.message,
        l: execResult.logs.level
    }
  },
  "grant" : run("main.dwl", {"main.dwl": "{a: readUrl(`http://google.com`)}"}, {"payload": jsonValue }, { securityManager: (grant, args) -> false }),
  "library" : run("main.dwl", {"main.dwl": "Utils::sum(1,2)", "/Utils.dwl": Utils }, {"payload": jsonValue }),
  "timeout" : run("main.dwl", {"main.dwl": "(1 to 1000000000000) map \$ + 1" }, {"payload": jsonValue }, {timeOut: 2}).success,
  "execFail" : run("main.dwl", {"main.dwl": "dw::Runtime::fail('My Bad')" }, {"payload": jsonValue }),
  "parseFail" : run("main.dwl", {"main.dwl": "(1 + " }, {"payload": jsonValue }),
  "writerFail" : run("main.dwl", {"main.dwl": "output application/xml --- 2" }, {"payload": jsonValue }),
  "readerFail" : run("main.dwl", {"main.dwl": "output application/xml --- payload" }, {"payload": invalidJsonValue }),
  "defaultOutput" : run("main.dwl", {"main.dwl": "payload" }, {"payload": jsonValue2}, {outputMimeType: "application/csv", writerProperties: {"separator": "|"}}),
}