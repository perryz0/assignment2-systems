import json
import os
import torch
import torch.distributed as dist
import torch.multiprocessing as mp

def worker(rank, ws, sizes_mb):
    os.environ["MASTER_ADDR"] = "localhost"
    os.environ["MASTER_PORT"] = f"2950{ws}"
    dist.init_process_group("nccl", rank=rank, world_size=ws)
    torch.cuda.set_device(rank)
    
    results = {}
    for ms in sizes_mb:
        n = int(ms * 1024 * 1024 / 4)
        x = torch.randn(n, dtype=torch.float32, device=f"cuda:{rank}")
        
        for _ in range(5):
            dist.all_reduce(x, op=dist.ReduceOp.SUM)
        torch.cuda.synchronize()
        
        t0 = torch.cuda.Event(enable_timing=True)
        t1 = torch.cuda.Event(enable_timing=True)
        t0.record()
        for _ in range(20):
            dist.all_reduce(x, op=dist.ReduceOp.SUM)
        t1.record()
        torch.cuda.synchronize()
        
        dt = t0.elapsed_time(t1) / 1000.0
        msg_bytes = ms * 1024 * 1024
        eff = 2 * (ws - 1) / ws * msg_bytes
        gbps = (eff * 20) / (dt * 1e9)
        
        results[ms] = gbps
    
    out = [None] * ws
    dist.all_gather_object(out, results)
    
    if rank == 0:
        with open(f"results_ws_{ws}.json", "w") as f:
            json.dump(out, f, indent=2)
    
    dist.destroy_process_group()

def main():
    mp.set_start_method("spawn", force=True)
    sizes_mb = [1, 10, 100, 1000]
    
    for ws in [2, 4, 8]:
        mp.spawn(worker, args=(ws, sizes_mb), nprocs=ws, join=True)

if __name__ == "__main__":
    main()

