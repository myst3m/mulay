{hello: "world", test: true} match {
    case {headKey: headValue ~ tail} -> headValue
    case {} -> null
}