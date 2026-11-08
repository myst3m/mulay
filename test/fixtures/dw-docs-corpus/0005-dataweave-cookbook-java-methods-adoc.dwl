%dw 2.0
import java!org::mycompany::utils::MyUtils
output application/json
---
{
	a: MyUtils::appendRandom("myString")
}