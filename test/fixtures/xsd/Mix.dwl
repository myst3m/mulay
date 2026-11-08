%dw 2.0

type MixedThingDefinition = { mixedThing: { "__text"*?: String, x: String, y?: String } }

type CodeTypeDefinition = { CodeType: String }

type PriceTypeDefinition = { PriceType @(currency: String): String }

type BaseDefinition = { Base @(ba?: String): {- b: String -} }

type EmployeeDefinition = { Employee @(ba?: String): {- b?: String, e?: Number -} }

type NumListDefinition = { NumList: String }

type UnionTypeDefinition = { UnionType: String }

type PickDefinition = { pick: {| p: String |} | {| q: Number |} }

type personElementDefinition = {| person @(id?: Number): {- name: String, age?: Number, tag*?: String, phone*: String, addr @(zip: String, kind?: String): Object, note: String, price @(currency: String): PriceTypeDefinition.PriceType, born: LocalDateTime, at: DateTime, ok: Boolean, code: CodeTypeDefinition.CodeType, nums: NumListDefinition.NumList, u: UnionTypeDefinition.UnionType, any: {-  -}, emp @(ba?: String): EmployeeDefinition.Employee -} |}

type noteElementDefinition = {| note: String |}

type Root = personElementDefinition | noteElementDefinition


