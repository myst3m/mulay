{
  a: {
    lastName: "Achaval",
    friends @(id: 123): [
      {
        test: true
      },
      {
        age: 123
      }
    ]
  },
  b: null,
  c: [
    {
      name: "Mariano"
    },
    {
      test: [
        1,
        2,
        3
      ]
    },
    {
      dw: ""
    }
  ]
}