%dw 2.0
output application/json
input payload application/x-protobuf messageType='examples.descriptor.MyMessage',descriptorUrl="descriptors/examples.dsc"
---
payload