%dw 2.0
output application/json
---
{
   nowCalled: now(),
   nowCalledSpecificTimeZone: now() >> "America/New_York"
}