from typing import List

def _exactly_one(props: List[str]) -> str:
    #Return an LTLf formula that enforces 'exactly one' proposition is true.
    if not props:
        return "true"
    # Build OR of mutually exclusive propositions
    terms = []
    for i, p in enumerate(props):
        negs = [f"!{q}" for j, q in enumerate(props) if j != i]
        terms.append("(" + p + (" && " + " && ".join(negs) if negs else "") + ")")
    return "(" + " || ".join(terms) + ")"


def simple_trace_semantics(props: List[str]) -> str:
    #Each trace position has exactly one active proposition from the set
    return f"G({_exactly_one(props)})"


def strict_alternation(env: List[str], sys: List[str]) -> str:
    # Model strict alternation between environment and system:
    #Environment acts, then system responds.
    # Each step alternates deterministically.
    
    env_any = "(" + " || ".join(env) + ")" if env else "false"
    sys_any = "(" + " || ".join(sys) + ")" if sys else "false"
    return f"G(({env_any}) -> X({sys_any})) && G(({sys_any}) -> X({env_any}))"