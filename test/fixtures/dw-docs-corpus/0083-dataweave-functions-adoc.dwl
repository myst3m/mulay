%dw 2.0
output application/json
fun optionalParamsLast(param1, param2 = 2, param3 = 3) =
    { "param1": param1, "param2": param2, "param3": param3}
fun optionalParamsFirst(param1 = 1, param2 = 2, param3) =
    { "param1": param1, "param2": param2, "param3": param3}
fun allParametersOptional(param1 = 1, param2 = 2, param3 = 3) =
    { "param1": param1, "param2": param2, "param3": param3}
---
{
  "optionalParamsLast(A)":optionalParamsLast('A'),
  "optionalParamsLast(A, B)":optionalParamsLast('A', 'B'),
  "optionalParamsLast(A, B, C)":optionalParamsLast('A', 'B', 'C'),
  "optionalParamsFirst(A)":optionalParamsFirst('A'),
  "optionalParamsFirst(A, B)":optionalParamsFirst('A', 'B'),
  "optionalParamsFirst(A, B, C)":optionalParamsFirst('A', 'B', 'C'),
  "allParametersOptional(A)":allParametersOptional('A'),
  "allParametersOptional(A, B)":allParametersOptional('A', 'B'),
  "allParametersOptional(A, B, C)":allParametersOptional('A', 'B', 'C')
}