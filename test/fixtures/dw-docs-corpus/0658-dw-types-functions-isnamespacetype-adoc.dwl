%dw 2.0
import * from dw::core::Types
type ANamespace = Namespace
output application/json
---
{
   a: isNamespaceType(ANamespace),
   b: isNamespaceType(Namespace),
   c: isNamespaceType(String),
}