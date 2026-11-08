%dw 2.0
output application/x-protobuf messageType='examples.oneof.ThisOrThat',descriptorUrl="descriptors/examples.dsc"
---
{
  this: true,
  that: false,
}