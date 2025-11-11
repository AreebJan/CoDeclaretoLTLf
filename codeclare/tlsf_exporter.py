from pathlib import Path
from typing import Dict, Any
import re

def _sanitize_formula(f: str) -> str:
    # Clean and normalize an LTLf formula for TLSF syntax (spaces, parentheses)
    f = f.strip().rstrip(";")
    f = re.sub(r'\s+', ' ', f)
    f = f.replace("&&", " && ").replace("||", " || ").replace("->", " -> ")
    f = re.sub(r'(?<! )U(?![A-Za-z])', ' U ', f)
    opens, closes = f.count("("), f.count(")")
    if opens > closes:
        f += ")" * (opens - closes)
    elif closes > opens:
        f = "(" * (closes - opens) + f
    return f.strip()


def export_tlsf(result: Dict[str, Any], out_path: str,
                title= "Assume-Guarantee contract", description="LTLf format"):
    # Export the LTLf assume–guarantee contract into TLSF format,
    # so that it can be checked/synthesized using LydiaSyft.
    
    env = result.get("environment", [])
    sys = result.get("system", [])

    assumptions = [x["ltlf"] for x in result.get("assumptions_list", [])]
    guarantees = [x["ltlf"] for x in result.get("guarantees_list", [])]

    env_sem = result.get("env_semantics", {}).get("simple_trace", "")
    sys_sem = result.get("sys_semantics", {}).get("simple_trace", "")
    alt = result.get("alternation", "")

    # Merge all assumptions and guarantees with semantics
    assumptions_full = [*assumptions, env_sem, alt]
    guarantees_full = [*guarantees, sys_sem, alt]

    def _block(lines: list[str]) -> str:
        #print a list of formulas as TLSF block content.
        cleaned = [_sanitize_formula(f) + ";" for f in lines if f.strip()]
        return "\n  ".join(cleaned) if cleaned else "true;"

    text = f"""INFO {{
  TITLE:       "{title}"
  DESCRIPTION: "{description}"
  SEMANTICS:   Finite,Mealy
  TARGET:      Moore
}}

MAIN {{

  INPUTS {{
    {'; '.join(env)}; 
  }}

  OUTPUTS {{
    {'; '.join(sys)}; 
  }}

  ASSUMPTIONS {{
    {_block(assumptions_full)}
  }}

  GUARANTEES {{
    {_block(guarantees_full)}
  }}

}}
"""
    Path(out_path).write_text(text)