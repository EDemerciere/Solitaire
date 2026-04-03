from __future__ import annotations
from typing import List, Optional
import os

from cartes_pile import Carte, Pile, Paquet

COULEURS = ("coeur", "carreau", "trefle", "pique")


class Colonne:
    def __init__(self, cartes: Optional[List[Carte]] = None):
        self._cartes: List[Carte] = list(cartes) if cartes else []

    def __repr__(self) -> str:
        return f"Colonne({len(self._cartes)} cartes)"

    def empiler(self, carte: Carte) -> None:
        self._cartes.append(carte)

    def empiler_sequence(self, sequence: List[Carte]) -> None:
        "Empile une séquence (liste ordonnée bas vers haut)."
        for carte in sequence:
            if not carte.est_visible():
                carte.retourner()
        self._cartes.extend(sequence)

    def depiler(self) -> Carte:
        if not self._cartes:
            raise IndexError("depiler d'une colonne vide")
        return self._cartes.pop()

    def regarder(self) -> Optional[Carte]:
        return self._cartes[-1] if self._cartes else None

    def taille(self) -> int:
        return len(self._cartes)

    def carte_a_position(self, index: int) -> Carte:
        return self._cartes[index]

    def extraire_sequence_depuis(self, index: int) -> List[Carte]:
        if index < 0 or index >= len(self._cartes):
            raise IndexError("index hors limites pour extraire la séquence")
        sequence = self._cartes[index:]
        del self._cartes[index:]
        return sequence

    def toutes_les_cartes(self) -> List[Carte]:
        return list(self._cartes)

    def peut_empiler_sequence(self, sequence: List[Carte]) -> bool:
        if not sequence:
            return False
        
        # Vérifier que la première carte peut s'empiler
        premiere = sequence[0]
        dessus = self.regarder()
        if not premiere.peut_empiler_sur_tableau(dessus):
            return False
        
        # Vérifier que toute la séquence est valide
        for i in range(len(sequence) - 1):
            carte_actuelle = sequence[i]
            carte_suivante = sequence[i + 1]
            # Les cartes doivent s'empiler correctement entre elles
            if not carte_suivante.peut_empiler_sur_tableau(carte_actuelle):
                return False
        
        return True


class Plateau:
    def __init__(self):
        self.colonnes: List[Colonne] = [Colonne() for _ in range(7)]
        self.fondations: List[Pile] = [Pile() for _ in range(4)]
        self.paquet: Optional[Paquet] = None
        self.defausse: Pile = Pile()
        self.nb_cartes_piochees = 0 

    def initialiser_plateau(self, paquet: Optional[Paquet] = None) -> None:
        "Distribue les cartes pour commencer une partie."
        self.colonnes = [Colonne() for _ in range(7)]
        self.fondations = [Pile() for _ in range(4)]
        self.defausse = Pile()
        self.paquet = paquet if paquet is not None else Paquet(melanger_au_depart=True)
        self.nb_cartes_piochees = 0

        # distribution
        for i in range(7):
            for j in range(i + 1):
                carte = self.paquet.piocher()
                # Toutes les cartes sauf la dernière de chaque colonne sont face cachée
                if j < i:
                    # Face cachée
                    carte.face_visible = False
                else:
                    # Dernière carte de la colonne, visible
                    carte.face_visible = True
                self.colonnes[i].empiler(carte)

    def piocher_du_talon(self) -> List[Carte]:
        "Pioche 1 à 3 cartes du talon et les ajoute à la défausse."
        if self.paquet is None:
            raise RuntimeError("paquet non initialisé")
        if self.paquet.est_vide():
            raise IndexError("paquet vide - appeler remettre_talon_dedans() si souhaité")
        
        cartes_piochees = []
        nb_a_piocher = min(3, self.paquet.taille())  # Piocher jusqu'à 3 cartes
        
        for _ in range(nb_a_piocher):
            carte = self.paquet.piocher()
            carte.face_visible = True  # Rendre visible
            self.defausse.empiler(carte)
            cartes_piochees.append(carte)
        
        return cartes_piochees

    def remettre_talon_dedans(self) -> None:
        "Remet toutes les cartes de la défausse dans le paquet."
        cartes = self.defausse.toutes_les_cartes()
        self.defausse = Pile()
        if self.paquet is None:
            self.paquet = Paquet(melanger_au_depart=False)
            self.paquet._cartes = []
        
        for carte in reversed(cartes):
            carte.face_visible = False  # Retourner la carte face cachée
            self.paquet._cartes.append(carte)

    def deplacer_sequence_entre_colonnes(self, origine: int, position: int, destination: int) -> bool:
        col_o = self.colonnes[origine]
        col_d = self.colonnes[destination]
        
        # Vérifier que la position est valide
        if position < 0 or position >= col_o.taille():
            return False
        
        # Vérifier que la carte est visible
        if not col_o.carte_a_position(position).est_visible():
            return False
        
        # extraire la séquence
        try:
            sequence = col_o.extraire_sequence_depuis(position)
        except IndexError:
            return False

        if col_d.peut_empiler_sequence(sequence):
            col_d.empiler_sequence(sequence)
            # si la colonne d'origine a maintenant un nouveau sommet face cachée, on le retourne
            sommet = col_o.regarder()
            if sommet and not sommet.est_visible():
                sommet.retourner()
            return True
        else:
            # restauration en cas d'échec
            col_o.empiler_sequence(sequence)
            return False

    def deplacer_vers_fondation(self, origine: int) -> bool:
        col = self.colonnes[origine]
        carte = col.regarder()
        if carte is None:
            return False
        
        # trouver index de la fondation selon la couleur
        try:
            idx = COULEURS.index(carte.couleur)
        except ValueError:
            return False
        
        fond = self.fondations[idx]
        if fond.est_vide():
            # on n'accepte qu'un As (1)
            if carte.valeur == 1:
                col.depiler()
                fond.empiler(carte)
                # retourner la nouvelle carte du sommet si nécessaire
                sommet = col.regarder()
                if sommet and not sommet.est_visible():
                    sommet.retourner()
                return True
            else:
                return False
        else:
            dessus = fond.regarder()
            if carte.valeur == dessus.valeur + 1:
                col.depiler()
                fond.empiler(carte)
                sommet = col.regarder()
                if sommet and not sommet.est_visible():
                    sommet.retourner()
                return True
            else:
                return False

    def cartes_visibles_recursif(self, colonne_idx: int, position: int) -> List[Carte]:
        col = self.colonnes[colonne_idx]
        if position >= col.taille():
            return []
        carte = col.carte_a_position(position)
        if not carte.est_visible():
            return []
        # si on est au sommet, on renvoie la carte
        if position == col.taille() - 1:
            return [carte]
        # sinon, concaténer récursivement
        return [carte] + self.cartes_visibles_recursif(colonne_idx, position + 1)

    def verifier_victoire(self) -> bool:
        return all(f.taille() == 13 for f in self.fondations)

    def get_etat(self) -> dict:
        return {
            "colonnes": [[(c.valeur, c.couleur, c.est_visible()) for c in col.toutes_les_cartes()] for col in self.colonnes],
            "fondations": [[(c.valeur, c.couleur) for c in fond.toutes_les_cartes()] for fond in self.fondations],
            "taille_paquet": self.paquet.taille() if self.paquet is not None else 0,
            "taille_defausse": self.defausse.taille(),
        }

    def assigner_images_dossier(self, dossier: str) -> None:
        if not os.path.isdir(dossier):
            return

        mapping = {}  # (couleur, valeur) vers chemin_image
        for couleur in COULEURS:
            for valeur in range(1, 14):
                # Déterminer le nom de la valeur
                if valeur == 1:
                    nom_valeur = "as"
                elif valeur == 11:
                    nom_valeur = "valet"
                elif valeur == 12:
                    nom_valeur = "dame"
                elif valeur == 13:
                    nom_valeur = "roi"
                else:
                    nom_valeur = str(valeur)
                
                # Chercher le fichier : d'abord nom_valeur_couleur, sinon valeur_couleur
                noms_possibles = [
                    f"{nom_valeur}_{couleur}.gif",
                    f"{valeur}_{couleur}.gif",
                ]
                trouve = None
                for nom in noms_possibles:
                    chemin = os.path.join(dossier, nom)
                    if os.path.exists(chemin):
                        trouve = chemin
                        break
                if trouve:
                    mapping[(couleur, valeur)] = trouve

        # chemin du dos
        self.chemin_dos = None
        chemin_dos = os.path.join(dossier, "dos.gif")
        if os.path.exists(chemin_dos):
            self.chemin_dos = chemin_dos

        def appliquer_sur_liste(cartes: List[Carte]):
            for c in cartes:
                key = (c.couleur, c.valeur)
                if key in mapping:
                    c.image = mapping[key]

        # appliquer partout
        for col in self.colonnes:
            appliquer_sur_liste(col.toutes_les_cartes())
        for fond in self.fondations:
            appliquer_sur_liste(fond.toutes_les_cartes())
        appliquer_sur_liste(self.defausse.toutes_les_cartes())
        if self.paquet is not None:
            appliquer_sur_liste(self.paquet._cartes)