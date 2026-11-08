%dw 2.0

type FileData<Content> = {
    data: Content,
    name: String
}

fun read(file: FileData<String>) =  "This is a text file with data " ++ file.data
fun read(file: FileData<Binary>) =  "This is a binary file with data " ++ (file.data as String {base: "64"})

---
{
  binary: read({data: "Hello World" as Binary, name: "myFile.bin"}),
  text: read({data: "Hello World", name: "myFile.txt"})
}