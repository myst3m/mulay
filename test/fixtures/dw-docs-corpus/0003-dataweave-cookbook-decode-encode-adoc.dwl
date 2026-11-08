%dw 2.0
import * from dw::core::Binaries
var myPDF = readUrl("classpath://pdf-test.pdf", "application/octet-stream")
var myPDFasBinary = toBase64(myPDF as Binary)
output application/PDF with binary
---
fromBase64(myPDFasBinary as String) as Binary