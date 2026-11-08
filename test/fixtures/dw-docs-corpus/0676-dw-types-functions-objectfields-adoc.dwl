import * from dw::core::Types
ns ns0 http://acme.com
type ADictionary = {_ : String}
type ASchema = {ns0#name @(ns0#foo: String): {}}
type AUser = {name @(foo?: String,l: Number)?: String, lastName*: Number}
---
{
    a: objectFields(ADictionary),
    b: objectFields(ASchema),
    c: objectFields(Object),
    d: objectFields(AUser)
}