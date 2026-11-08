%dw 2.0
input payload application/xml
output multipart/form-data boundary="----myboundary----"
---
{
  parts: {
    filePart: {
      headers: {
        "Content-Disposition": {
          "name": "<NAME>",
          "filename": "<FILE_NAME>.<FILE_EXTENSION>"
        },
        "Content-Type": "<FILE_CONTENT-TYPE>"
      },
      content: payload
    },
    otherJsonPart: {
      content: '{"name": "sampleFile.xml", "sampleFile": {"type": "sample"} }'
    }
  }
}