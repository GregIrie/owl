from typing import Dict, Type, Any, Set
from pydantic import ValidationError

class NodeInputType:
    """
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
            raise ValueError(f"Clés dupliquées entre requis et optionnels : {duplicates}")

    def keys(self, include_required: bool = True, include_optional: bool = True) -> Set[str]:
        """
        Retourne l'ensemble des clés selon les catégories demandées.
        """
        keys: Set[str] = set()
        if include_required:
            keys |= set(self.required.keys())
        if include_optional:
            keys |= set(self.optional.keys())
        return keys

    def add_input(self, name: str, type_: Type, required: bool = True) -> None:
        """
        Ajoute une nouvelle définition d'input.
        Lève KeyError si déjà existant, TypeError si le type n'est pas correct.
        """
        if name in self.keys():
            raise KeyError(f"Input '{name}' existe déjà.")
        if not isinstance(name, str) or not isinstance(type_, type):
            raise TypeError("Nom d'input ou type invalide.")
        target = self.required if required else self.optional
        target[name] = type_

    def remove_input(self, name: str) -> None:
        """
        Supprime une définition d'input, qu'elle soit requise ou optionnelle.
        """
        if name in self.required:
            del self.required[name]
        elif name in self.optional:
            del self.optional[name]
        else:
            raise KeyError(f"Input '{name}' n'existe pas.")

    def validate(self, data: Dict[str, Any]) -> None:
        """
        Valide un dictionnaire d'inputs contre les définitions de types.
        Lève ValidationError en cas de manquant ou de type incorrect.
        """
        # Vérifier les requis
        for key, typ in self.required.items():
            if key not in data:
                raise ValidationError(f"Input requis manquant : '{key}'")
            if not isinstance(data[key], typ):
                raise ValidationError(
                    f"Input '{key}' attendu de type {typ.__name__}, reçu {type(data[key]).__name__}."
                )
        # Vérifier les optionnels fournis
        for key, value in data.items():
            if key in self.optional and not isinstance(value, self.optional[key]):
                raise ValidationError(
                    f"Input optionnel '{key}' attendu de type {self.optional[key].__name__}, reçu {type(value).__name__}."
                )
