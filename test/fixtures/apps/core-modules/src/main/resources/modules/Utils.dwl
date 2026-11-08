%dw 2.0
import upper from dw::core::Strings
import modules::sub::Helpers

var greeting = "Hello"

fun greet(name: String) = greeting ++ ", " ++ capitalize(name)

fun capitalize(s: String) = upper(s[0]) ++ s[1 to -1]

fun twice(x) = Helpers::double(x)

fun boom(x) = x.missing!
