%dw 2.0
input payload application/x-protobuf messageType='examples.repeated.People',descriptorUrl="descriptors/examples.dsc"
output application/json
---
names: payload.people.*names