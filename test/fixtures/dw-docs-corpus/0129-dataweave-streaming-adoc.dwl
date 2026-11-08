%dw 2.0
output application/xml
---
{
  salesorder: {
    itemList: payload.order."order-items".*"order-item" map {
      ("i_" ++ $$) : {
        id: $.@id,
        productId: $.product,
        quantity: $.quantity,
        price: $.price
      }
    }
  }
}