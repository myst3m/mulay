%dw 2.0
---
{(a: payload.a) if payload.a?, (b: payload.b) if payload.b?}