%dw 2.0

ns ns0 urn:common

type MoneyDefinition = { ns0#Money: {- ns0#amount: Number, ns0#ccy: String -} }

type headerElementDefinition = {| ns0#header: String |}

type Root = headerElementDefinition


