%dw 2.0
import * from dw::core::Binaries
var myPDF = readUrl("classpath://pdf-test.pdf", "application/octet-stream")
output text/plain
---
toBase64(myPDF as Binary)