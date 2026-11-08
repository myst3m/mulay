%dw 2.0
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
output application/json
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
   "grant" : eval("main.dwl", {"main.dwl": "{a: readUrl(`http://google.com`)}"}, {"payload": jsonValue }, {},{ securityManager: (grant, args) -> false }),
   "library" : eval("main.dwl", {"main.dwl": "Utils::sum(1,2)", "/Utils.dwl": Utils }, {"payload": jsonValue }),
   "timeout" : eval("main.dwl", {"main.dwl": "(1 to 1000000000000) map \$ + 1" }, {"payload": jsonValue }, {},{timeOut: 2}).success,
   "execFail" : eval("main.dwl", {"main.dwl": "dw::Runtime::fail('My Bad')" }, {"payload": jsonValue }),
   "parseFail" : eval("main.dwl", {"main.dwl": "(1 + " }, {"payload": jsonValue }),
   "writerFail" : eval("main.dwl", {"main.dwl": "output application/xml --- 2" }, {"payload": jsonValue }),
   "defaultOutput" : eval("main.dwl", {"main.dwl": "payload" }, {"payload": jsonValue2}, {},{outputMimeType: "application/csv", writerProperties: {"separator": "|"}}),
   "onExceptionFail": do  {
     dw::Runtime::try( () ->
         eval("main.dwl", {"main.dwl": "dw::Runtime::fail('Failing Test')" }, {"payload": jsonValue2}, {},{onException: "FAIL"})
     ).success
   },
   "customLogger":
        eval(
  "main.dwl",
           {"main.dwl": "log(1234)" },
   {"payload": jsonValue2},
    {},
   {
                  loggerService: {
                     initialize: () -> {token: "123"},
                     log: (level, msg, context) -> log("$(level) $(msg)", context)
                  }
                }
           )
}