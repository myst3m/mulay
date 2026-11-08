%dw 2.0
---
[{"type": "a"}, {"type": "b"}, {"type": "a"}] groupBy ((item) -> item."type")