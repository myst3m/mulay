%dw 2.0
---
if (1 + 1 == 2 and (not 1 == 2)) {answer: "andNot - Condition met"} else {answer: "nope"}