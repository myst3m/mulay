%dw 2.0
import * from dw::core::URL
var uriDataTypeEx = "https://en.wikipedia.org/wiki/Uniform_Resource_Identifier#footer"
var queryStringsEx = 'http://my.company.com:1234/hello/?field=value'
output application/json
---
{
    'myUriDataTypeEx': parseURI(uriDataTypeEx),
    // queryStringsEx has a query string:
    'myQueryStringsEx': parseURI(queryStringsEx).query,
    // uriDataTypeEx lacks a query string:
    'myQueryStringNullEx': parseURI(uriDataTypeEx).query,
    // The URI includes the port number:
    'myAuthorityEx': parseURI('http://localhost:8080/test').authority
}