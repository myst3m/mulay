%dw 2.0
output application/json
type WithParameters<A, B> = {first: A, second: B, nestedObject: {message: A}}
---
{
 a: true is WithParameters<Boolean, Number>.first,
 b: 4592 is WithParameters<String, Number>.second,
 c: "sdf" is WithParameters<String, Number>.nestedObject.message,
}