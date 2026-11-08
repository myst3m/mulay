%dw 2.0
var myVar = read('<users xmlns="http://test.com">
                     <user name="Mariano" lastName="Achaval"/>
                     <user name="Stacey" lastName="Duke"/>
                  </users>', 'application/xml')
output application/json
---
{ keysOfExample: flatten([keysOf(myVar.users) map $.#,
                          keysOf(myVar.users) map $.@])
}
++
{ namesOfExample: flatten([namesOf(myVar.users) map $.#,
                    namesOf(myVar.users) map $.@])
}