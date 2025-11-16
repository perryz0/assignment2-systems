import json
import matplotlib.pyplot as plt

THEO = 50

sizes = [1, 10, 100, 1000]
ws_list = [2, 4, 8]

for ws in ws_list:
    with open(f"results_ws_{ws}.json", "r") as f:
        data = json.load(f)
    
    gbps = []
    for ms in sizes:
        vals = [d[ms] for d in data]
        gbps.append(sum(vals) / len(vals))
    
    plt.plot(sizes, gbps, marker="o", label=f"ws={ws}")

plt.axhline(y=THEO, color="r", linestyle="--", label="theoretical max")
plt.xscale("log")
plt.xlabel("Message Size (MB)")
plt.ylabel("Throughput (GB/s)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig("allreduce_benchmark.png", dpi=150)
plt.close()

