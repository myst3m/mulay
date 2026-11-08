%dw 2.0
output multipart/form-data  boundary="----myboundary----"
---
{
  parts: {
    filePart: {
      headers: {
        "Content-Disposition": {
          "name": "test",
          "filename": "sampleFile.xml"
        },
        "Content-Type": "application/xml"
      },
      content: payload
    },
    otherJsonPart: {
      content: '{"name": "sampleFile.xml", "sampleFile": {"type": "sample"} }'
    }
  }
}