%dw 2.0
output application/json
fun myFunction() = dw::Runtime::wait("My result",100)
---
dw::util::Timer::duration(() -> myFunction())