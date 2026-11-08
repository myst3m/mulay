%dw 2.0
import java!org::mycompany::utils::MyUtils::appendRandom
output application/json
---
{
	a: appendRandom("myString")
}