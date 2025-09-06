import os
import sys, shlex
import subprocess
import argparse
import re
import pandas as pd
import matplotlib.pyplot as plt
plt.style.use('bmh')


def _split_argv_string(s: str):
    # Use Windows quoting rules on Windows, POSIX elsewhere
    return shlex.split(s, posix=(os.name != 'nt'))

def make_output_name(script_path, pass_args):
    """Return a human-readable identifier from script name + pass-args."""
    base = os.path.splitext(os.path.basename(script_path))[0]

    tokens = []
    for s in pass_args:
        for t in shlex.split(s, posix=(os.name != 'nt')):
            # Drop leading '--'
            t = t.lstrip('-')
            # Replace separators with safe chars
            t = t.replace('=', '-')
            t = re.sub(r'\W+', '_', t)  # non-alphanumeric → underscore
            if t:
                tokens.append(t)

    suffix = "_".join(tokens)
    if suffix:
        return f"{base}_{suffix}"
    return base or "benchmark_results"


def run_benchmark_subprocess(script_path, num_threads, repeat, script_args=None):
    """Run the script in a subprocess with OMP_NUM_THREADS set and return measured times."""
    if script_args is None:
        script_args = []

    times = []
    for _ in range(repeat):
        env = os.environ.copy()
        env["OMP_NUM_THREADS"] = str(num_threads)

        cmd = [sys.executable, script_path] + list(script_args)
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            check=True
        )

        # Try to parse the last line as a float; fall back to first float anywhere.
        stdout = result.stdout.strip()
        candidate = stdout.splitlines()[-1] if stdout else ""
        try:
            elapsed = float(candidate)
        except ValueError:
            m = re.search(r"([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)", stdout)
            if not m:
                print(f"Unexpected output (no float found):\n{stdout}")
                raise
            elapsed = float(m.group(1))
        times.append(elapsed)
    return times

def benchmark(script_path, thread_list, repeat=3,
              output_csv="benchmark_results", script_args=None):
    records = []

    for threads in thread_list:
        times = run_benchmark_subprocess(script_path, threads, repeat, script_args=script_args)
        avg_time = sum(times) / len(times)
        print(f"{threads} threads: {avg_time:.6f} s")

        records.append({
            "Threads": threads,
            "Avg Time (s)": avg_time,
        })

    df = pd.DataFrame(records)
    df.to_csv(output_csv + '.csv', index=False)
    print(f"\nSaved results to {output_csv}.csv")
    return df

def plot_results(df, output):
    plt.figure(figsize=(6, 5))
    plt.plot(df["Threads"], 1.0 / df["Avg Time (s)"],
             marker='o', linewidth=2, markersize=6)

    plt.xlabel("Number of Threads", fontsize=12)
    plt.ylabel("Average Execution Speed ($s^{-1}$)", fontsize=12)
    plt.title(f"OpenMP Performance vs Threads {output}", fontsize=14)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.axhline(y=0, ls='--', color='k')
    plt.tight_layout()
    plt.savefig(output + '.png', dpi=300)

def main():
    parser = argparse.ArgumentParser(
        description="Benchmark OpenMP-enabled Python code",
        epilog="""
        Note that options provided with " --pass-args " are passed to the target script. 

        Examples:
  openmp-benchmark myscript.py --min-threads 1 --max-threads 8 --repeat 5
  openmp-benchmark myscript.py --pass-args "--size 1000000 --mode fast"
  openmp-benchmark myscript.py --min-threads 2 --max-threads 16 --output results/run1 --pass-args "--method fast"
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        allow_abbrev=False,  # avoids accidental short-flag matches
    )
    parser.add_argument("script", help="Path to Python script that prints compute time")
    parser.add_argument("--thread-list", type=str, default=None, help="Comma separated list of threads to test. min-threads, max-threads and step-threads will be ignored if this is provided.")
    parser.add_argument("--min-threads", type=int, default=2, help="Minimum thread count to test")
    parser.add_argument("--max-threads", type=int, default=20, help="Maximum thread count to test")
    parser.add_argument("--step-threads", type=int, default=2, help="Thread counts to step by")
    parser.add_argument("--repeat", type=int, default=3,
                        help="Number of repetitions of calls to the script, to average down noise.")
    parser.add_argument("--output", default=None, help="Output CSV/PNG filename")
    parser.add_argument("--no-plot", action="store_true", help="Skip plotting results")
    parser.add_argument(
        "-A", "--pass-args", dest="pass_args", action="append", default=[],
        metavar='"ARGS"',
        help='Quoted string of args for the target script. May be used multiple times, e.g. -A "--size 1e6 --mode fast".'
    )



    if len(sys.argv)==1:
        parser.print_help(sys.stderr)
    args = parser.parse_args()

    # Build final argv for the target from all provided strings
    script_args = []
    for s in args.pass_args:
        script_args.extend(_split_argv_string(s))

    if not(args.output):
        args.output = make_output_name(args.script, args.pass_args)
    print(f"Benchmarking with output name {args.output}...")
        
    if args.thread_list:
        thread_list = [int(x) for x in args.thread_list.split(',')]
    else:
        print(args.thread_list)
        thread_list = range(min_threads, max_threads + step_threads, step_threads)

    df = benchmark(
        args.script,
        thread_list,
        args.repeat,
        args.output,
        script_args=script_args
    )
    if not args.no_plot:
        plot_results(df, args.output)

if __name__ == "__main__":
    main()

