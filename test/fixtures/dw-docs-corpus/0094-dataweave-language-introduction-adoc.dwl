%dw 2.0
output application/xml

ns ns0 http://www.abc.com
ns ns1 http://www.123.com
---
{
    ns0#myroot: {
         ns1#secondroot: "hello world"
    }
}