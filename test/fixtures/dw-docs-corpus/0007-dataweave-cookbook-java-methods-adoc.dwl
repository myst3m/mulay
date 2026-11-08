%dw 2.0
output application/json
---
{
	a: java!org::mycompany::utils::MyUtils::appendRandom(vars.myString)
}