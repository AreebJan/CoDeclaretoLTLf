from typing import Dict, Any, List, Tuple, Set
from .ltlf_generator import LTLfGenerator
from .semantics import simple_trace_semantics, strict_alternation
import re

def _conj(parts: List[str]) -> str:
    #Join multiple formulas with logical AND (&&)
    parts = [p for p in parts if p and p.strip()]
    if not parts:
        return "true"
    return "(" + ") && (".join(parts) + ")"

#Small helper to extract atomic propositions from formulas
_OPS = {"G", "F", "X", "U", "W", "R", "true", "false", "&&", "||", "->", "<->", "!", "(", ")"}
def _atoms_in(formula: str) -> Set[str]:
    #Return all atomic propositions appearing in an LTLf formula
    toks = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", formula)
    return {t for t in toks if t not in _OPS}


def _auto_reclassify(A_gen, G_gen, env, sys):
    #Automatically determine which constraints belong to ASSUMPTIONS vs GUARANTEES.
    #This ensures correct assume–guarantee partitioning even if input JSON is rough.
    
    env_set, sys_set = set(env), set(sys)

    def classify(c):
        aps = _atoms_in(c["ltlf"])
        has_env = any(a in env_set for a in aps)
        has_sys = any(a in sys_set for a in aps)

        # Only environment variables → assumption
        if has_env and not has_sys:
            return "A"
        # Only system variables → guarantee
        if has_sys and not has_env:
            return "G"

        # Mixed → check if template direction implies env→sys
        name = c.get("template", "").lower()
        directed_to_sys = {
            "response", "chain_response", "alternate_response",
            "precedence", "chain_precedence", "alternate_precedence",
            "succession", "weak_link"
        }
        return "G" if name in directed_to_sys else "G"

    # Apply classification
    newA, newG = [], []
    for c in A_gen + G_gen:
        side = classify(c)
        (newA if side == "A" else newG).append(c)
    return newA, newG


def build_contract(spec: Dict[str, Any]) -> Dict[str, Any]:
    # Build a full assume–guarantee LTLf contract from a coDECLARE model:
    # Generates LTLf formulas from templates
    # Reclassifies constraints as assumptions/guarantees
    # Adds trace semantics + strict alternation constraints
    
    env = spec.get("environment", [])
    sys = spec.get("system", [])

    # Generate raw formulas from templates
    A_gen = LTLfGenerator(spec["assumptions"]).generate()
    G_gen = LTLfGenerator(spec["guarantees"]).generate()

    # Automatically fix misclassified constraints
    A_gen, G_gen = _auto_reclassify(A_gen, G_gen, env, sys)

    # Build conjunctions for each side
    A_text = _conj([x["ltlf"] for x in A_gen])
    G_text = _conj([x["ltlf"] for x in G_gen])

    # Add formal semantics: simple trace + strict alternation
    env_sem = simple_trace_semantics(env)
    sys_sem = simple_trace_semantics(sys)
    alt = strict_alternation(env, sys)

    left = _conj([A_text, env_sem, alt])
    right = _conj([G_text, sys_sem, alt])
    contract_ltlf = f"({left}) -> ({right})"

    def _clean(constraints):
        cleaned = []
        for c in constraints:
            c2 = dict(c)
            c2.pop("obj", None)  # 🔹 remove pylogics object
            cleaned.append(c2)
        return cleaned

    return {
        "assumptions_list": _clean(A_gen),
        "guarantees_list": _clean(G_gen),
        "env_semantics": {"simple_trace": env_sem},
        "sys_semantics": {"simple_trace": sys_sem},
        "alternation": alt,
        "contract_ltlf": contract_ltlf,
        "environment": env,
        "system": sys,
    }