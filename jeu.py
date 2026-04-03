from __future__ import annotations
from typing import Optional, List, Tuple, Any
from collections import deque
import copy

from plateau import Plateau
from cartes_pile import Paquet


class JeuSolitaire:
    "Classe principale représentant une partie complète."

    def __init__(self):
        # Le plateau de jeu actuel
        self.plateau: Optional[Plateau] = None

        # Historique des états du plateau pour permettre l’action d(annulation via le bouton
        self.historique: List[Plateau] = []

        # File d’actions effectuées pour pouvoir rejouer la partie depuis le début
        self.file_actions: deque[Tuple[str, Any]] = deque()

    def _sauvegarder_etat(self) -> None:
        "Crée une copie du plateau et la stocke dans l'historique."
        if self.plateau is None:
            return
        copie = copy.deepcopy(self.plateau)
        self.historique.append(copie)

    def nouvelle_partie(self, paquet: Optional[Paquet] = None) -> None:
        "Démarre une nouvelle partie de Solitaire."
        self.plateau = Plateau()
        self.plateau.initialiser_plateau(paquet)
        self.historique.clear()
        self.file_actions.clear()

    def jouer_piocher(self) -> bool:
        "Pioche une ou plusieurs cartes depuis le talon. Si le talon vide, il est remis dans le paquet. AUssi enregistre l'action et sauvegarde l'état avant la pioche."
        if self.plateau is None:
            raise RuntimeError("Partie non initialisée")

        try:
            # Si le paquet est vide, on remet le talon dedans
            if self.plateau.paquet is not None and self.plateau.paquet.est_vide():
                self._sauvegarder_etat()
                self.plateau.remettre_talon_dedans()
                self.file_actions.append(('remettre_talon', None))
                return True

            # Sinon, on pioche normalement
            self._sauvegarder_etat()
            cartes = self.plateau.piocher_du_talon()
            cartes_info: List[Tuple[str, int]] = [(c.couleur, c.valeur) for c in cartes]
            self.file_actions.append(('piocher', cartes_info))
            return True
        except IndexError:
            return False

    def jouer_deplacer_colonne_vers_colonne(self, origine: int, position: int, destination: int) -> bool:
        "Déplace une séquence de cartes d'une colonne vers une autre.(origine, position, destination)"
        if self.plateau is None:
            raise RuntimeError("Partie non initialisée")

        self._sauvegarder_etat()
        succes = self.plateau.deplacer_sequence_entre_colonnes(origine, position, destination)

        if succes:
            self.file_actions.append(('col->col', (origine, position, destination)))
            return True

        # Si l’action échoue, on retire la sauvegarde inutile
        self.historique.pop()
        return False

    def jouer_deplacer_colonne_vers_fondation(self, origine: int) -> bool:
        "Déplace la carte du haut d'une colonne vers la fondation."
        if self.plateau is None:
            raise RuntimeError("Partie non initialisée")

        self._sauvegarder_etat()
        succes = self.plateau.deplacer_vers_fondation(origine)

        if succes:
            self.file_actions.append(('col->fond', origine))
            return True

        # En cas d’échec, on retire la sauvegarde inutile
        self.historique.pop()
        return False

    def jouer_deplacer_defausse_vers_colonne(self, destination: int) -> bool:
        "Déplace la carte du dessus de la défausse vers une colonne."
        if self.plateau is None:
            raise RuntimeError("Partie non initialisée")

        if self.plateau.defausse.est_vide():
            return False

        self._sauvegarder_etat()
        carte = self.plateau.defausse.depiler()

        # Vérifie si la carte peut être placée sur la colonne
        if self.plateau.colonnes[destination].peut_empiler_sequence([carte]):
            self.plateau.colonnes[destination].empiler(carte)
            self.file_actions.append(('def->col', destination))
            return True
        else:
            # Si ce n’est pas possible, on restaure l’état d'avant
            self.plateau.defausse.empiler(carte)
            self.historique.pop()
            return False

    def obtenir_etat_simplifie(self) -> dict[str, Any]:
        "Retourne le plateau sous forme de dictionnaire.(pour afficher ou sauvegarder l'état du jeu.)"
        if self.plateau is None:
            return {}
        return self.plateau.get_etat()

    def annuler_coup(self) -> bool:
        "Annule le dernier coup joué.(si possible)"
        if not self.historique:
            return False

        dernier = self.historique.pop()
        self.plateau = dernier
        return True

    def rejouer_actions(self) -> None:
        "Rejoue toutes les actions enregistrées dans la file d'actions,en repartant d'une nouvelle partie vide."
        self.nouvelle_partie()

        # On rejoue toutes les actions une à une dans l’ordre
        while self.file_actions:
            nom, data = self.file_actions.popleft()

            if nom == 'piocher':
                try:
                    self.plateau.piocher_du_talon()
                except Exception:
                    pass

            elif nom == 'remettre_talon':
                try:
                    self.plateau.remettre_talon_dedans()
                except Exception:
                    pass

            elif nom == 'col->col':
                o, pos, d = data
                try:
                    self.plateau.deplacer_sequence_entre_colonnes(o, pos, d)
                except Exception:
                    pass

            elif nom == 'col->fond':
                try:
                    self.plateau.deplacer_vers_fondation(data)
                except Exception:
                    pass

            elif nom == 'def->col':
                try:
                    carte = self.plateau.defausse.regarder()
                    if carte:
                        self.plateau.colonnes[data].empiler(self.plateau.defausse.depiler())
                except Exception:
                    pass
