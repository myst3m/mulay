%dw 2.0
output application/xml
ns xml http://www.w3.org/XML/1998/namespace

var cXmlObj = {
  cXML @(payloadID: "9949494", xml#lang: "en-US", timestamp: "2002-02-04T18:39:09-08:00"): {
      Header: {
        From: {
          Credential @(domain: "NetworkId"): {
            Identity: "Identity"
          }
        }
    }
  }
} as Object {
    docType: { rootName: "cXML", systemId: "http://xml.cXML.org/schemas/cXML/1.2.014/cXML.dtd" }
}
---
cXmlObj