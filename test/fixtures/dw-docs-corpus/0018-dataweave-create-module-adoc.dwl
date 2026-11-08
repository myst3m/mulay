%dw 2.0
import modules::MyModule as WeaveMod
output application/json
---
WeaveMod::myFunc("dataweave")