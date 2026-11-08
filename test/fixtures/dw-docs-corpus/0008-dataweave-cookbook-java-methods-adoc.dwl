%dw 2.0
import java!org::mycompany::utils::MyClass
output application/json
---
{
	a: MyClass::new("myString").foo
}