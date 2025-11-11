import json
from pathlib import Path

def load_spec(path: str):
    """
    Load and validate a coDECLARE JSON specification.
    This file defines the environment and system activities,
    and lists all declarative constraints (assumptions, guarantees).
    """
    # Read JSON file from path
    p = Path(path)
    data = json.loads(p.read_text())

    # Ensure mandatory fields are present
    required = ["environment", "system", "assumptions", "guarantees"]
    for k in required:
        if k not in data:
            raise ValueError(f"Missing key '{k}' in {path}")

    # Clean up and normalize activity names
    data["environment"] = [a.strip() for a in data["environment"]]
    data["system"] = [a.strip() for a in data["system"]]

    # Normalize constraint definitions
    for section in ("assumptions", "guarantees"):
        for c in data[section]:
            # normalize names like “Responded Existence” → “responded_existence”
            c["template"] = c["template"].strip().lower().replace(" ", "_")
            c["activities"] = [a.strip() for a in c["activities"]]

    # Ensure environment and system variables don’t overlap
    overlap = set(data["environment"]) & set(data["system"])
    if overlap:
        raise ValueError(f"Environment/System share variables: {', '.join(overlap)}")

    return data