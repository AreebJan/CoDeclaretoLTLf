import json
from typing import List, Dict, Any

class CoDeclareModel:
    """
    A class representing a coDECLARE model.
    It defines the environment and system activities and their constraints.

    You can build the model programmatically in Python and then
    serialize it to JSON for use in the main pipeline.
    """

    def __init__(self):
        self.environment: List[str] = []
        self.system: List[str] = []
        self.assumptions: List[Dict[str, Any]] = []
        self.guarantees: List[Dict[str, Any]] = []

    # -----------------------------------------------------------
    # Add environment/system activities
    # -----------------------------------------------------------
    def add_environment_activity(self, name: str):
        if name not in self.environment:
            self.environment.append(name)

    def add_system_activity(self, name: str):
        if name not in self.system:
            self.system.append(name)

    # -----------------------------------------------------------
    #  Add constraints for assumptions (environment) or guarantees (system)
    # -----------------------------------------------------------
    def add_assumption(self, template: str, activities: List[str]):
        self.assumptions.append({
            "template": template,
            "activities": activities
        })

    def add_guarantee(self, template: str, activities: List[str]):
        self.guarantees.append({
            "template": template,
            "activities": activities
        })

    # -----------------------------------------------------------
    #  Convert the model to a dictionary
    # -----------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        return {
            "environment": self.environment,
            "system": self.system,
            "assumptions": self.assumptions,
            "guarantees": self.guarantees
        }

    # -----------------------------------------------------------
    #  Serialize to JSON
    # -----------------------------------------------------------
    def to_json(self, path: str):
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        print(f" Model saved to {path}")

    # -----------------------------------------------------------
    #  Load from JSON (alternative constructor)
    # -----------------------------------------------------------
    @classmethod
    def from_json(cls, path: str) -> "CoDeclareModel":
        with open(path) as f:
            data = json.load(f)

        model = cls()
        model.environment = data.get("environment", [])
        model.system = data.get("system", [])
        model.assumptions = data.get("assumptions", [])
        model.guarantees = data.get("guarantees", [])
        return model
