%dw 2.0
output application/x-protobuf messageType='examples.repeated.People',descriptorUrl="descriptors/examples.dsc"
---
reduce(payload.names, (item, acc = {}) ->  acc ++ {names: item})