%dw 2.0
output application/json
---
{
  examples : {

    badDateWithLenient: '02/31/2020' as Date {mode: "LENIENT", format: 'MM/dd/uuuu'},
    badDateWithSmart: '02/31/2020' as Date {mode: "SMART", format: 'MM/dd/uuuu'}
  }
}