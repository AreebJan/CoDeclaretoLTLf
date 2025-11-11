import subprocess
from pathlib import Path

def dot_to_pdf(dot_path: str) -> Path:
    """
    Convert a .dot file produced by LydiaSyft into a .pdf strategy graph.
    Requires Graphviz installed (apt-get install graphviz).
    """
    dot_file = Path(dot_path)
    if not dot_file.exists():
        raise FileNotFoundError(f".dot file not found: {dot_path}")

    pdf_file = dot_file.with_suffix(".pdf")
    cmd = ["dot", "-Tpdf", str(dot_file), "-o", str(pdf_file)]
    subprocess.run(cmd, check=True)
    print(f" Strategy PDF generated: {pdf_file}")
    return pdf_file


def display_pdf_in_colab(pdf_path: str):
    """Show the strategy PDF directly in Google Colab."""
    from IPython.display import IFrame, display
    display(IFrame(pdf_path, width=800, height=600))

