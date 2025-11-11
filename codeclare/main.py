import argparse
import json
import os
import subprocess
from pathlib import Path
from .parser import load_spec
from .contract_builder import build_contract
from .tlsf_exporter import export_tlsf
from .utils.strategy_utils import dot_to_pdf, display_pdf_in_colab


def run_lydia_synthesis(tlsf_path: Path, output_dir: Path) -> Path:
    """
    Run LydiaSyft (or LydiaSyftEL) depending on which binary exists.
    Automatically detects the environment (Mac / Colab / Docker).
    """
    print("\n Running LydiaSyft synthesis...\n")

    tlsf_abs = tlsf_path.resolve()
    out_abs = output_dir.resolve()
    strategy_path = out_abs / "strategy.dot"

    # Try local or Docker-based execution
    lydiasyft_paths = [
        "/content/LydiaSyftPlus/build/bin/LydiaSyft",
        "/content/LydiaSyftPlus/build/bin/LydiaSyftEL",
        "/LydiaSyft/build/bin/LydiaSyft",
        "/LydiaSyft/build/bin/LydiaSyftEL",
    ]
    lydiasyft_bin = next((p for p in lydiasyft_paths if Path(p).exists()), None)

    if not lydiasyft_bin:
        raise FileNotFoundError(" No LydiaSyft or LydiaSyftEL binary found.")

    # --- Construct the appropriate command ---
    if lydiasyft_bin.endswith("LydiaSyft"):
        cmd = [lydiasyft_bin, "synthesis", "-f", str(tlsf_abs)]
    else:
        # LydiaSyftEL expects --input-file, --partition-file, etc.
        dummy_partition = out_abs / "dummy_partition.txt"
        dummy_partition.write_text("i a\no b")  # minimal placeholder partition
        cmd = [
            lydiasyft_bin,
            "-i", str(tlsf_abs),
            "-p", str(dummy_partition),
            "-s", "1",  # starting player: agent
            "-g", "0",  # game solver: Emerson-Lei
        ]

    print(f"▶️ Running: {' '.join(cmd)}\n")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        print(result.stderr)
    except subprocess.CalledProcessError as e:
        print(f" LydiaSyft synthesis failed (exit code {e.returncode}).")
        print(e.stderr)
        raise

    # If strategy.dot was generated, copy to outputs
    strategy_dot = Path("strategy.dot")
    if strategy_dot.exists():
        subprocess.run(["cp", str(strategy_dot), str(strategy_path)], check=False)
        print(f" Copied strategy.dot → {strategy_path}")
    else:
        print(" No strategy.dot file found (possibly unrealizable).")

    return strategy_path if strategy_path.exists() else None


def main():
    ap = argparse.ArgumentParser(description="coDECLARE → LTLf → TLSF → LydiaSyft")
    ap.add_argument("--in", dest="input_path", required=True, help="Input coDECLARE JSON file")
    args = ap.parse_args()

    input_path = Path(args.input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    print(f"Loading coDECLARE model from {input_path}")
    spec = load_spec(input_path)

    # Step 1: Build assume–guarantee contract
    print("Building assume–guarantee LTLf contract...")
    result = build_contract(spec)

    outputs_dir = Path("outputs")
    outputs_dir.mkdir(exist_ok=True)
    base = input_path.stem

    ltlf_out = outputs_dir / f"{base}.ltlf"
    tlsf_out = outputs_dir / f"{base}.tlsf"

    # Step 2: Save only the .ltlf and .tlsf outputs
    ltlf_out.write_text(result["contract_ltlf"])
    export_tlsf(result, tlsf_out, title=f"coDECLARE contract ({base})")

    print(f"\n Contract files generated:")
    print(f"  LTLf:  {ltlf_out}")
    print(f"  TLSF:  {tlsf_out}")

    # Step 3: Run LydiaSyft synthesis
    try:
        strategy_dot = run_lydia_synthesis(tlsf_out, outputs_dir)
        if strategy_dot:
            pdf_path = dot_to_pdf(strategy_dot)
            if "COLAB_RELEASE_TAG" in os.environ:
                display_pdf_in_colab(str(pdf_path))
            else:
                print(f" Strategy PDF ready at: {pdf_path}")
        else:
            print(" No strategy file produced.")

    except Exception as e:
        print(f" Synthesis pipeline failed: {e}")

    print("\n Pipeline completed.")


if __name__ == "__main__":
    main()
