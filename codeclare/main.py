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
    Run LydiaSyftPlus natively inside Colab (no Docker).
    Assumes LydiaSyft was compiled in ./LydiaSyftPlus/build/bin/LydiaSyft.
    """
    print("\n Running LydiaSyft synthesis locally \n")

    binary = Path("LydiaSyft/build/bin/LydiaSyft")
    if not binary.exists():
        raise FileNotFoundError("❌ LydiaSyft binary not found at LydiaSyft/build/bin/LydiaSyft")

    cmd = [str(binary), "synthesis", "-f", str(tlsf_path)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(result.stdout)
        if "UNREALIZABLE" in result.stdout.upper():
            print("❌ Specification is UNREALIZABLE")
        elif "REALIZABLE" in result.stdout.upper():
            print(" Specification is REALIZABLE")
        else:
            print(" Could not determine realizability status from output.")
    except subprocess.CalledProcessError as e:
        print(f" LydiaSyft synthesis failed (exit code {e.returncode})")
        print(e.stderr)
        raise

    # Locate strategy.dot
    strategy_path = Path("LydiaSyft/build/strategy.dot")
    if not strategy_path.exists():
        raise FileNotFoundError(" No strategy .dot file produced by LydiaSyft.")
    print(f" Strategy DOT file generated: {strategy_path}")
    return strategy_path

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

        # Step 4: Convert to PDF
        pdf_path = dot_to_pdf(strategy_dot)

        # Step 5: Display in Colab (optional)
        if "COLAB_RELEASE_TAG" in os.environ:
            display_pdf_in_colab(str(pdf_path))
        else:
            print(f"Strategy PDF ready at: {pdf_path}")

    except subprocess.CalledProcessError as e:
        print(f" LydiaSyft synthesis failed with error code {e.returncode}")
    except Exception as e:
        print(f" {e}")

    print("\n Pipeline completed.")


if __name__ == "__main__":
    main()