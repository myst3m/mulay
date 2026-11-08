%dw 2.0
output application/json
---
"hello world" match {
	case word matches /(hello)\s\w+/ ->  word[1] as String ++ " was matched"
	case literalMatch: "hello world" -> upper(literalMatch)
	case hasOne if( hasOne is Object and hasOne.three? ) -> hasOne.three
	else -> $
}