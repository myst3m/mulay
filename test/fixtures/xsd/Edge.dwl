%dw 2.0

ns ns0 urn:e

type InnerDefinition = { ns0#Inner: {- deep @(ns0#w?: String): {- v: String -} -} }

type LevelDefinition = { ns0#Level: Number }

type otherElementDefinition = {| ns0#other: Number |}

type rootElementDefinition = {| ns0#root @(ns0#"type"?: String, ns0#n: Number, ns0#lv?: Number): {- "first-name": String, "_x": String, class: String, "if": String, "default": String, match: String, untyped: {- "__text"*?: String -}, level: LevelDefinition.ns0#Level, inner: InnerDefinition.ns0#Inner, ns0#other: Number, f: Number, b64: Binary, t: Time, anyuri: String, dur: String, qn: String, tok: String, gy: String -} |}

type Root = otherElementDefinition | rootElementDefinition


