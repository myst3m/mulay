import os, random, sys

d = sys.argv[1]
rows = int(sys.argv[2]) if len(sys.argv) > 2 else 1000000
copy_mb = int(sys.argv[3]) if len(sys.argv) > 3 else 1024
os.makedirs(d, exist_ok=True)
rnd = random.Random(42)
regions = ["north", "south", "east", "west", "kanto", "kansai", "kyushu", "hokkaido"]
recs = [(i, f"cust-{rnd.randrange(100000):05d}", regions[rnd.randrange(8)],
         f"{rnd.randrange(100000) / 100:.2f}", rnd.randrange(1, 20),
         f"2026-{rnd.randrange(1, 13):02d}-{rnd.randrange(1, 29):02d}") for i in range(1, rows + 1)]
with open(os.path.join(d, "orders.csv"), "w") as f:
    f.write("id,customer,region,amount,qty,date\n")
    for r in recs:
        f.write("%d,%s,%s,%s,%d,%s\n" % r)
with open(os.path.join(d, "orders.json"), "w") as f:
    f.write("[\n")
    for k, r in enumerate(recs):
        f.write('  {"id": %d, "customer": "%s", "region": "%s", "amount": %s, "qty": %d, "date": "%s"}' % r)
        f.write(",\n" if k + 1 < len(recs) else "\n")
    f.write("]\n")
with open(os.path.join(d, "orders.xml"), "w") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n<orders>\n')
    for r in recs:
        f.write('  <order id="%d"><customer>%s</customer><region>%s</region><amount>%s</amount><qty>%d</qty><date>%s</date></order>\n' % r)
    f.write("</orders>\n")
blk = os.urandom(1 << 20)
with open(os.path.join(d, "big.bin"), "wb") as f:
    for _ in range(copy_mb):
        f.write(blk)
