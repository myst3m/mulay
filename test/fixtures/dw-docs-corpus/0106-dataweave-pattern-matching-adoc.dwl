[1,2,3,4] match {
	case [head ~ tail] -> head
	case [] -> null
}