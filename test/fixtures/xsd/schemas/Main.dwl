%dw 2.0

ns ns1 urn:common

ns ns0 urn:main

import xmlschema!schemas::Part

import xmlschema!schemas::common::Types

type LineDefinition = { ns0#Line: {- ns0#sku: String -} }

type invoiceElementDefinition = {| ns0#invoice: {- ns0#total: Types::MoneyDefinition.ns1#Money, ns1#header: String, ns0#line*: Part::LineDefinition.ns0#Line -} |}

type headerElementDefinition = {| ns1#header: String |}

type Root = invoiceElementDefinition | headerElementDefinition


