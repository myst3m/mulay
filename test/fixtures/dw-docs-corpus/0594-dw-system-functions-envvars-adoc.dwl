%dw 2.0
import dw::System
output application/json
---
{ "envVars" : dw::System::envVars().SHELL }