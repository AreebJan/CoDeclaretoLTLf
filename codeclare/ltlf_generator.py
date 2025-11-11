from typing import List, Dict, Any
from Declare4Py.ProcessModels.LTLModel import LTLTemplate

# Try different parser imports depending on pylogics version
try:
    from pylogics.parsers.ltl import parse_ltlf
except Exception:
    try:
        from pylogics.parsers.ltl import parse_ltl as parse_ltlf
    except Exception:
        try:
            from pylogics.parsers import ltlf
            parse_ltlf = ltlf.parse
        except Exception:
            print("Warning: pylogics.parse_ltlf not found; using raw string parser.")
            parse_ltlf = lambda s: s


def _clean(formula_str: str) -> str:
    #Remove Declare4Py's 'con_' prefix (added internally by templates)
    return formula_str.replace("con_", "")


class LTLfGenerator:
    #Converts declarative constraints into LTLf formulas and their corresponding pylogics object representation.

    def __init__(self, constraints: List[Dict[str, Any]]):
        self.constraints = constraints
        # Supported constraint templates
        self.supported = {
            # Built-in Declare4Py templates
            "next_a", "eventually_a", "eventually_a_then_b", "eventually_a_or_b",
            "eventually_a_next_b", "eventually_a_then_b_then_c",
            "eventually_a_next_b_next_c", "is_first_state_a", "is_second_state_a",
            "is_third_state_a", "last", "second_last", "third_last",
            "is_last_state_a", "is_second_last_state_a", "is_third_last_state_a",
            "precedence", "chain_precedence", "responded_existence",
            "chain_response", "not_chain_precedence", "not_chain_response",
            "response", "not_precedence", "not_response",
            "not_responded_existence", "alternate_response", "alternate_precedence",
            # Custom manually-defined ones
            "absence2", "neg_succession", "not_coexistence", "succession"
        }

    # Handle manual (non-Declare4Py) templates
    def _manual(self, name: str, acts: List[str]) -> str:
        if name == "absence2":
            a, = acts
            return f"!F({a} && X(F({a})))"
        if name == "neg_succession":
            a, b = acts
            return f"G({a} -> !F({b}))"
        if name == "not_coexistence":
            a, b = acts
            return f"!((F({a})) && (F({b})))"
        if name == "succession":
            a, b = acts
            # 'a' must be followed by 'b', and 'b' must not occur before 'a'
            return f"G({a} -> F({b})) && (!{b}) U {a}"
        raise KeyError(name)

    # Handle normal Declare4Py templates
    def _declare4py(self, template_name: str, acts: List[str]) -> str:
        t = LTLTemplate(template_name)

        # Handle argument number
        if len(acts) == 0:
            model = t.fill_template([])
        elif len(acts) == 1:
            model = t.fill_template(acts)
        elif len(acts) == 2:
            model = t.fill_template([acts[0]], [acts[1]])
        elif len(acts) >= 3 and template_name.lower() == "response":
            # Allow multiple targets in one response
            src = acts[0]
            targets = " || ".join(acts[1:])
            return f"G({src} -> F({targets}))"
        else:
            raise ValueError(f"Unsupported number {len(acts)} for {template_name}")

        return _clean(model.formula)

    def generate(self) -> List[Dict[str, Any]]:
        # Generates list of constraints with both string and object forms
        results = []
        for c in self.constraints:
            name = c["template"].lower()
            acts = c["activities"]
            if name not in self.supported:
                print(f"Skipping unknown template '{name}'")
                continue

            try:
                # Build formula string using manual or DECLARE template
                s = self._manual(name, acts) if name in {
                    "absence2", "neg_succession", "not_coexistence", "succession"
                } else self._declare4py(name, acts)

                # Parse LTLf string into a pylogics AST object
                obj = parse_ltlf(s)

                # Store both string and object form
                results.append({
                    "template": name,
                    "activities": acts,
                    "obj": obj,
                    "ltlf": s,
                })
            except Exception as e:
                print(f"Error in template '{name}' ({acts}): {e}")
        return results