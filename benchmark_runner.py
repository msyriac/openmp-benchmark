import os
import time
import subprocess
import argparse
import pandas as pd
import matplotlib.pyplot as plt
plt.style.use('bmh') 

def run_benchmark_subprocess(script_path, num_threads, repeat):
    """Run the script in a subprocess with OMP_NUM_THREADS set and return measured times."""
    times = []
    for _ in range(repeat):
        env = os.environ.copy()
        env["OMP_NUM_THREADS"] = str(num_threads)

        result = subprocess.run(
            ["python", script_path],
            env=env,
            capture_output=True,
            text=True,
            check=True
        )

        try:
            elapsed = float(result.stdout.strip())
            times.append(elapsed)
        except ValueError:
            print(f"Unexpected output (not float):\n{result.stdout}")
            raise
    return times

def benchmark(script_path, min_threads=2, max_threads=20, step_threads=2, repeat=3, output_csv="benchmark_results"):
    records = []

    for threads in range(min_threads, max_threads + step_threads, step_threads):
        times = run_benchmark_subprocess(script_path, threads, repeat)
        avg_time = sum(times) / len(times)
        print(f"{threads} threads: {avg_time:.6f} s")

        records.append({
            "Threads": threads,
            "Avg Time (s)": avg_time,
        })

    df = pd.DataFrame(records)
    df.to_csv(output_csv+'.csv', index=False)
    print(f"\nSaved results to {output_csv}.csv")
    return df

def plot_results(df,output):
    plt.figure(figsize=(6, 5))
    plt.plot(df["Threads"], 1./df["Avg Time (s)"],
             marker='o', linewidth=2, markersize=6)

    plt.xlabel("Number of Threads", fontsize=12)
    plt.ylabel("Average Execution Speed ($s^{-1}$)", fontsize=12)
    plt.title(f"OpenMP Performance vs Threads {output}", fontsize=14)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.axhline(y=0,ls='--',color='k')
    plt.tight_layout()
    plt.savefig(output+'.png')

def main():
    parser = argparse.ArgumentParser(description="Benchmark OpenMP-enabled Python code")
    parser.add_argument("script", help="Path to Python script that prints compute time")
    parser.add_argument("--min-threads", type=int, default=2, help="Minimum thread count to test")
    parser.add_argument("--max-threads", type=int, default=20, help="Maximum thread count to test")
    parser.add_argument("--step-threads", type=int, default=2, help="Thread counts to step by")
    parser.add_argument("--repeat", type=int, default=3, help="Number of repetitions of calls to the script, to average down noise.")
    parser.add_argument("--output", default="benchmark_results", help="Output CSV/PNG filename")
    parser.add_argument("--no-plot", action="store_true", help="Skip plotting results")

    args = parser.parse_args()
    df = benchmark(args.script, args.min_threads, args.max_threads, args.step_threads, args.repeat, args.output)
    if not args.no_plot:
        plot_results(df,args.output)

if __name__ == "__main__":
    main()
