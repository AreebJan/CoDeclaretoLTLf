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
    Run LydiaSyft inside Docker container `lydiasyft_dev`
    using the syntax: ./bin/LydiaSyft -p synthesis -f <file>.
    Captures realizability result and copies strategy.dot back to host.
    """
    print("\n🐳 Running LydiaSyft synthesis inside lydiasyft_dev container...\n")

    tlsf_abs = tlsf_path.resolve()
    out_abs = output_dir.resolve()
    strategy_path = out_abs / "strategy.dot"

    container_name = "lydiasyft_dev"
    container_outputs = "/LydiaSyft/outputs"
    container_tlsf = f"{container_outputs}/{tlsf_abs.name}"
    container_strategy = "/LydiaSyft/build/strategy.dot"  # LydiaSyft saves here by default

    # 1️⃣ Ensure container is running
    result = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", container_name],
        capture_output=True, text=True
    )
    if "true" not in result.stdout:
        print("▶️ Starting lydiasyft_dev container...")
        subprocess.run(["docker", "start", container_name], check=True)
        print("✅ Container started successfully.")

    # 2️⃣ Ensure /LydiaSyft/outputs exists
    subprocess.run(["docker", "exec", container_name, "mkdir", "-p", container_outputs], check=True)
    print("📁 Ensured /LydiaSyft/outputs exists inside container")

    # 3️⃣ Copy TLSF file to container
    subprocess.run([
        "docker", "cp",
        str(tlsf_abs),
        f"{container_name}:{container_tlsf}"
    ], check=True)
    print(f"📂 Copied TLSF to container: {container_tlsf}")

    # 4️⃣ Run LydiaSyft inside container
    cmd = [
        "docker", "exec", container_name,
        "bash", "-c",
        f"cd /LydiaSyft/build && ./bin/LydiaSyft -p synthesis -f {container_tlsf}"
    ]
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        if "UNREALIZABLE" in result.stdout.upper():
            print("❌ Specification is UNREALIZABLE")
        elif "REALIZABLE" in result.stdout.upper():
            print("✅ Specification is REALIZABLE")
        else:
            print("ℹ️ Could not determine realizability status from output.")
    except subprocess.CalledProcessError as e:
        print(f"❌ LydiaSyft synthesis failed (exit code {e.returncode}).")
        print(e.stderr)
        raise

    # 5️⃣ Copy strategy.dot back from container
    subprocess.run([
        "docker", "cp",
        f"{container_name}:{container_strategy}",
        str(strategy_path)
    ], check=True)
    print(f"📄 Copied strategy.dot back to host: {strategy_path}")

    if not strategy_path.exists():
        raise FileNotFoundError("❌ No strategy .dot file produced by LydiaSyft.")
    print(f"✅ Strategy DOT file generated: {strategy_path}")
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