%dw 2.0
output application/json
---
{
    enNumber: 12.3 as String {format: "##.##", locale: "en"},
    esNumber: 12.3 as String {format: "##.##", locale: "es"},
    esDate: "2020-12-31" as Date as String {format: "dd-MMM-yy", locale: "es"},
    enDate: "2020-12-31" as Date as String {format: "dd-MMM-yy", locale: "en"}
}
