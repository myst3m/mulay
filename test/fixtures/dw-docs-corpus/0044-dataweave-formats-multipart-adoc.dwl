%dw 2.0
output multipart/form-data boundary='34b21'
---
{
  parts : {
    text : {
      headers : {
        "Content-Type": "text/plain"
      },
      content : "Book"
    },
    file1 : {
      headers : {
        "Content-Disposition" : {
            "name": "file1",
            "filename": "a.json"
        },
        "Content-Type" : "application/json"
      },
      content : {
        title: "Java 8 in Action",
        author: "Mario Fusco",
        year: 2014
      }
    },
    file2 : {
      headers : {
        "Content-Disposition" : {
            "filename": "a.html"
        },
        "Content-Type" : payload.^mimeType
      },
      content : payload
    }
  }
}