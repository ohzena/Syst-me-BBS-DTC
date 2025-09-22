# utils.py

"""
utils.py - Fonctions utilitaires pour BBS avec py_ecc
"""

import hashlib
from typing import Tuple, Union, Optional
from py_ecc.optimized_bls12_381 import curve_order, normalize

def hash_to_scalar(data: bytes, dst: bytes = b"") -> int:
    """Hache des octets en un scalaire modulo l'ordre de la courbe."""
    h = hashlib.sha256(data + dst).digest()
    return int.from_bytes(h, "big") % curve_order

def points_equal(P: Optional[Tuple], Q: Optional[Tuple]) -> bool:
    """
    ompare deux points py_ecc de manière fiable.
    Cette approche s'appuie directement sur la fonction `normalize` de la bibliothèque,
    qui gère tous les cas (affine, projectif, infini) pour G1 et G2.
    """
    # Si les deux objets sont identiques en mémoire (ou les deux sont None), ils sont égaux.
    if P is Q:
        return True

    # Si l'un est None et pas l'autre, ils sont différents.
    if P is None or Q is None:
        return False
    
    try:
        # `normalize` convertit n'importe quel point en une représentation
        # canonique (un tuple de 3 éléments pour les coordonnées projectives).
        # La comparaison de ces tuples est fiable et gère tous les types.
        norm_P = normalize(P)
        norm_Q = normalize(Q)
        
        return norm_P == norm_Q
        
    except (TypeError, AssertionError, Exception):
        # Si la normalisation échoue pour l'un ou l'autre des points (parce que le
        # format est invalide), on considère qu'ils ne sont pas égaux.
        return False