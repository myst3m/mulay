import json, random, sys
random.seed(7)
n = int(sys.argv[1]) if len(sys.argv) > 1 else 100000
cats = ["books", "music", "games", "tools", "food", "toys", "garden", "sports"]
rows = [{"id": i, "name": "item-%d" % i, "cat": cats[i % len(cats)], "price": round(random.uniform(1, 500), 2),
         "qty": random.randint(0, 20), "tags": ["t%d" % (i % 7), "u%d" % (i % 3)], "active": i % 4 != 0} for i in range(1, n + 1)]
json.dump(rows, sys.stdout, separators=(",", ": "))
