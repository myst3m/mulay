%dw 2.0
import dw::module::Multipart
output multipart/form-data
var firstPart = "content for my first part"
var secondPart = "content for my second part"
---
{
  parts: {
    part1: Multipart::field({name:"myFirstPart",value: firstPart}),
    part2: Multipart::field("mySecondPart", secondPart)
  }
}