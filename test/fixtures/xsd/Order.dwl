%dw 2.0

ns ns0 http://example.com/order

type ItemTypeDefinition = { ns0#ItemType: {- ns0#name: String, ns0#qty: Number -} }

type OrderTypeDefinition = { ns0#OrderType @(status: "NEW" | "DONE"): {- ns0#id: Number, ns0#item*: ItemTypeDefinition.ns0#ItemType, ns0#note?: String -} }

type StatusTypeDefinition = { ns0#StatusType: "NEW" | "DONE" }

type orderElementDefinition = {| ns0#order @(status: "NEW" | "DONE"): OrderTypeDefinition.ns0#OrderType |}

type Root = orderElementDefinition


