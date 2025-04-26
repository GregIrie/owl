from typing import Dict, Type, Any, Set
from .errors import NodeValidationError

class NodeInputType:
    """
    Define the input types (required and optionals) for a node
    Représente les types d'inputs d'un Node, séparés en requis et optionnels.
    """
    def __init__(
        self,
        required: Dict[str, Type] = None,
        optional: Dict[str, Type] = None
    ):
        self.required: Dict[str, Type] = required or {}
        self.optional: Dict[str, Type] = optional or {}

        # Vérifier l'unicité des clés entre requis et optionnels
        duplicates = set(self.required) & set(self.optional)
        if duplicates:
            raise ValueError(f"Duplicated key between required and optional: {duplicates}")

    def keys(self, include_required: bool = True, include_optional: bool = True) -> Set[str]:
        """
        Return all the key according the asked categories : optional or required
        """
        keys: Set[str] = set()
        if include_required:
            keys |= set(self.required.keys())
        if include_optional:
            keys |= set(self.optional.keys())
        return keys

    def add_input(self, name: str, type_: Type, required: bool = True) -> None:
        """
        Add a new input definition. 
        Raise a KeyError if the input already exists.
        Raise a TypeError if the type is not correct.
        """
        if name in self.keys():
            raise KeyError(f"Input '{name}' already exists.")
        if not isinstance(name, str) or not isinstance(type_, type):
            raise TypeError("Name or type is not valid.")
        target = self.required if required else self.optional
        target[name] = type_

    def remove_input(self, name: str) -> None:
        """
        Delete an input definition whenever it is required or optional.
        """
        if name in self.required:
            del self.required[name]
        elif name in self.optional:
            del self.optional[name]
        else:
            raise KeyError(f"Input '{name}' doesn't exist.")

    def validate(self, data: Dict[str, Any]) -> None:
        """
        Validate an input dictionary against its type definition.
        """
        # Vérifier les requis
        for key, typ in self.required.items():
            if key not in data:
                raise NodeValidationError(f"Missing Required input: '{key}'")
            if not isinstance(data[key], typ):
                raise NodeValidationError(
                    f"Input '{key}' expected type {typ.__name__}, got {type(data[key]).__name__}."
                )
        # Vérifier les optionnels fournis
        for key, value in data.items():
            if key in self.optional and not isinstance(value, self.optional[key]):
                raise NodeValidationError(
                    f"Optional Input '{key}' expected type {self.optional[key].__name__}, got {type(value).__name__}."
                )
