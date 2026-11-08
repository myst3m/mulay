%dw 2.0
output application/json
---
{
  processed: payload,
  metadata: {
    inputSize: vars.inputSize,
    outputSize: sizeOf(payload),
    highValueCount: vars.highValueCount
  }
}