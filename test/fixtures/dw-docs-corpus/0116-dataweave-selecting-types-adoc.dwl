%dw 2.0
output application/json
type User = {
 birthDate: Date {format: "dd-MMM-yy"},
 userName : String {schema: "value"}
}
type FormattedDate = User.birthDate
type UserName = User.userName
var formattedDate: FormattedDate = "10-SEP-15" as Date {format: "dd-MMM-yy"}
var otherFormatDate = "23-10-2022" as Date {format: "dd-MM-yyyy"}
var userName = "Messi" as String {schema: "value"}
var otherUserName = "Di María" as String {schema: "otherValue"}
---
{
formattedDate: formattedDate is FormattedDate,
userName: userName is UserName,
otherFormatDate: otherFormatDate is FormattedDate,
otherUserName: otherUserName is UserName
}