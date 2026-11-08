%dw 2.0
---
if (not (1 + 1 == 2 and (not 1 == 1))) {answer: "notWithAndNot - Condition met"} else {answer: "nope"}