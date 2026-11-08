%dw 2.0
---
'file-' ++ today() as String {format: 'yyyyMMdd'} ++ '.dat'