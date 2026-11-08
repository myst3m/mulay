%dw 2.0
import * from dw::System
output application/json
---
{
    "envVars" : [
       "real" : envVar("SHELL"),
       "fake" : envVar("FAKE_ENV_VAR")
    ]
}