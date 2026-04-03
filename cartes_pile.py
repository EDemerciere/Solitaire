from __future__ import annotations
from typing import List, Optional
import random

COULEURS = ("coeur", "carreau", "trefle", "pique")

VALEURS_NOM = {
    1: "As",
    11: "Valet",
    12: "Dame",
    13: "Roi",
}


class Carte:
    "Représente une carte à jouer avec une couleur, une valeur et état (face visible ou pass)."

    def __init__(self, couleur: str, valeur: int, face_visible: bool = False, image: Optional[str] = None):
        # Vérification de la validité des arguments
        if couleur not in COULEURS:
            raise ValueError(f"Couleur invalide : {couleur}")
        if not (1 <= valeur <= 13):
            raise ValueError("La valeur doit être entre 1 et 13")

        self.couleur: str = couleur
        self.valeur: int = valeur
        self.face_visible: bool = face_visible
        self.image: Optional[str] = image

    def __repr__(self) -> str:
        # Affiche une représentation de la carte,  ex:, "Dame de pique"
        return f"{self.nom_valeur()} de {self.couleur}"

    def nom_valeur(self) -> str:
        # Retourne le nom de la valeur
        return VALEURS_NOM.get(self.valeur, str(self.valeur))

    def est_rouge(self) -> bool:
        # Détermine si la carte est rouge
        return self.couleur in ("coeur", "carreau")

    def retourner(self) -> None:
        # Retourne la carte : face cachée,et face visible
        self.face_visible = not self.face_visible

    def est_visible(self) -> bool:
        # Indique si la carte est actuellement visible
        return self.face_visible

    def peut_empiler_sur_tableau(self, autre: Optional[Carte]) -> bool:
        "Vérifie si la carte peut être posée sur une autre carte dans le tableau ( en suivant la logique du solitaire)"
        if autre is None:
            return self.valeur == 13  # Un Roi peut aller sur une colonne vide
        return (self.valeur == autre.valeur - 1) and (self.est_rouge() != autre.est_rouge())


class Pile:
    "Représente une pile de cartes."

    def __init__(self, cartes: Optional[List[Carte]] = None):
        # On copie la liste pour éviter que l'initial soit modif
        self._cartes: List[Carte] = list(cartes) if cartes else []

    def __repr__(self) -> str:
        return f"Pile({len(self._cartes)} cartes)"

    def empiler(self, carte: Carte) -> None:
        # Ajoute une carte au sommet de la pile
        self._cartes.append(carte)

    def depiler(self) -> Carte:
        # Retire et renvoie la carte du dessus
        if not self._cartes:
            raise IndexError("depiler depuis une pile vide")
        return self._cartes.pop()

    def regarder(self) -> Optional[Carte]:
        # Regarde la carte du dessus sans la retirer
        return self._cartes[-1] if self._cartes else None

    def est_vide(self) -> bool:
        # Vérifie si la pile est vide
        return not self._cartes

    def taille(self) -> int:
        # Retourne le nombre de cartes dans la pile
        return len(self._cartes)

    def empiler_sequence(self, sequence: List[Carte]) -> None:
        # Ajoute plusieurs cartes à la pile (utilisé dans les déplacements de séquences)
        self._cartes.extend(sequence)

    def extraire_sequence(self, n: int) -> List[Carte]:
        "On enleve les n dernières cartes de la pile et les renvoie sous forme de liste."
        if n < 0:
            raise ValueError("n doit être positif")
        if n > len(self._cartes):
            raise IndexError("pas assez de cartes dans la pile pour extraire la séquence")
        sequence = self._cartes[-n:]
        del self._cartes[-n:]
        return sequence

    def depiler_n_recursif(self, n: int) -> List[Carte]:
        "Dépile récursivement n cartes."
        if n < 0:
            raise ValueError("n doit être positif")
        if n == 0:
            return []
        if self.est_vide():
            raise IndexError("pas assez de cartes dans la pile pour depiler recursif")
        carte = self.depiler()
        reste = self.depiler_n_recursif(n - 1)
        return reste + [carte]

    def toutes_les_cartes(self) -> List[Carte]:
        # Retourne une copie de la liste des cartes
        return list(self._cartes)


class Paquet:
    "Représente un paquet standard de 52 cartes."

    def __init__(self, melanger_au_depart: bool = True):
        # Création d’un jeu complet (4 couleurs foiis 13 valeurs)
        self._cartes: List[Carte] = [
            Carte(c, v, face_visible=False)
            for c in COULEURS
            for v in range(1, 14)
        ]
        if melanger_au_depart:
            self.melanger()

    def melanger(self) -> None:
        # Mélange les cartes aléatoirement
        random.shuffle(self._cartes)

    def piocher(self) -> Carte:
        # Retire et renvoie la carte du dessus du paquet
        if not self._cartes:
            raise IndexError("pioche vide")
        return self._cartes.pop()

    def taille(self) -> int:
        # Renvoie le nombre de cartes restantes
        return len(self._cartes)

    def est_vide(self) -> bool:
        # Indique si le paquet est vide
        return not self._cartes
