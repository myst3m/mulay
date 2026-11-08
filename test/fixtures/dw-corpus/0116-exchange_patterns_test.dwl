%dw 2.0
---
["a","b","c"] reduce (($$ default "") ++ (if ($$ == null) "" else "-") ++ $)