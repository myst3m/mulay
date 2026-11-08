%dw 2.0
output application/json
---
"hello world" match {
	case word matches  /(hello)\s\w+/ ->  word[1] ++ " was matched"
	case literalMatch: "hello world" -> upper(literalMatch)
	case last if(true) -> last
}