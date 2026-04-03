import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageOps
import os
import pygame
from random import randint
from jeu import JeuSolitaire
from cartes_pile import Carte

 

class InterfaceSolitaire:
    "Gère l'affichage, la souris et drag and drop."

 

    def __init__(self, racine: tk.Tk, dossier_cartes: str):
        # Fenêtre Tkinter
        self.racine = racine
        self.racine.title("Tokyo Solitaire Ghoul")

 

        
        self.largeur = self.racine.winfo_screenwidth()
        self.hauteur = self.racine.winfo_screenheight()

 

        self.jeu = JeuSolitaire()
        self.jeu.nouvelle_partie()
        self.jeu.plateau.assigner_images_dossier(dossier_cartes)

 

        # Dossier avc les images des cartes
        self.dossier_cartes = dossier_cartes

 

        # C'est un cache d'images pour éviter de recharger les mêmes fichiers tt le tmps
        self.images: dict[str, tk.PhotoImage] = {}

 

        # Données liées au drag and drop
        self.drag_data: dict[str, object] = {
            "x0": 0,
            "y0": 0,
            "source_type": None,
            "source_data": None,
            "cartes_draggees": []
        }

 

        # Barre de boutons en HAUT
        self.cadre_boutons = tk.Frame(self.racine, bg="darkgreen", height=60)
        self.cadre_boutons.pack_propagate(False)
        self.cadre_boutons.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        self.bouton_nouvelle = tk.Button(self.cadre_boutons, text="Nouvelle Partie", command=self.nouvelle_partie, 
                                         font=("Arial", 12), bg="lightblue", fg="black", padx=15, pady=8)
        self.bouton_nouvelle.pack(side=tk.LEFT, padx=10, pady=5)
        
        self.bouton_annuler = tk.Button(self.cadre_boutons, text="Arrière", command=self.annuler_coup,
                                        font=("Arial", 12), bg="lightyellow", fg="black", padx=15, pady=8)
        self.bouton_annuler.pack(side=tk.LEFT, padx=10, pady=5)
        
        self.bouton_quitter = tk.Button(self.cadre_boutons, text="Quitter", command=self.quitter_jeu,
                                        font=("Arial", 12), bg="lightcoral", fg="black", padx=15, pady=8)
        self.bouton_quitter.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Canvas pr afficher les cartes
        self.canvas = tk.Canvas(self.racine, bg="darkgreen")

 

        # evenements souris
        self.canvas.bind("<Button-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Button-3>", self.on_right_click)
        
    def quitter_jeu(self) -> None:
        "Ferme l'application complètement."
        if messagebox.askokcancel("Quitter", "Êtes-vous sûr de vouloir quitter ?"):
            self.racine.destroy()
        
    def afficher_interface(self):
        # Pack le canvas
        self.canvas.config(width=self.largeur, height=self.hauteur - 100, bg="darkgreen")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Pack les boutons EN DERNIER et FIXÉ en bas
        self.cadre_boutons.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        # Rafraîchir le plateau
        self.afficher_plateau()

 

    def charger_image(self, nom_fichier: str) -> tk.PhotoImage:
        "Charge une image de carte. Utilise le cache mis en place au dessus"
        # Gestion des chemins
        if os.path.isabs(nom_fichier) and os.path.exists(nom_fichier):
            chemin = nom_fichier
        else:
            chemin = os.path.join(self.dossier_cartes, nom_fichier)

 

        if chemin in self.images:
            return self.images[chemin]

 

        try:
            # Chargement + redimensionnement 
            img = Image.open(chemin)
            img = img.resize((80, 110))
            tkimg = ImageTk.PhotoImage(img)
            self.images[chemin] = tkimg
            return tkimg
        except Exception:
            # Si on a une erreur, on affiche une image vide
            if 'placeholder' not in self.images:
                self.images['placeholder'] = tk.PhotoImage(width=80, height=110)
            return self.images['placeholder']

 

    def nouvelle_partie(self) -> None:
        "Relance une nouvelle partie et réinitialise l'état du drag."
        self.jeu.nouvelle_partie()
        self.drag_data = {"x0": 0, "y0": 0, "source_type": None, "source_data": None, "cartes_draggees": []}
        self.afficher_plateau()

 

    def annuler_coup(self) -> None:
        "Annule le dernier coup si possible."
        if self.jeu.annuler_coup():
            self.afficher_plateau()
        else:
            messagebox.showinfo("Annuler", "Aucun coup à annuler.")

 

    def trouver_zone_clic(self, x: int, y: int) -> tuple:
        "Détermine sur quelle zone du plateau l'utilisateur a cliqué"
        # Talon
        if 50 <= x <= 130 and 30 <= y <= 140:
            return ("talon", None)

 

        # Défausse
        if 200 <= x <= 280 and 30 <= y <= 140:
            return ("defausse", None)

 

        # Fondations
        for i in range(4):
            xf = 400 + i * 110
            if xf <= x <= xf + 80 and 30 <= y <= 140:
                return ("fondation", i)

 

        # Colonnes
        for i in range(7):
            x_col = 80 + i * 110
            if x_col <= x <= x_col + 80 and 200 <= y <= self.hauteur:
                y_relative = y - 220
                card_index = max(0, y_relative // 25)
                
                col = self.jeu.plateau.colonnes[i]
                if card_index >= col.taille():
                    card_index = col.taille() - 1
                if card_index < 0:
                    card_index = 0
                
                return ("colonne", (i, card_index))

 

        return (None, None)

 

    def on_right_click(self, event: tk.Event) -> None:
        "Clic droit, essaie d'envoyer la carte visible vers sa fondation."
        zone_type, zone_data = self.trouver_zone_clic(event.x, event.y)
        succes = False

 

        if zone_type == "colonne":
            col_idx, _ = zone_data
            col = self.jeu.plateau.colonnes[col_idx]
            if col.taille() > 0 and col.regarder().est_visible():
                succes = self.jeu.jouer_deplacer_colonne_vers_fondation(col_idx)

 

        elif zone_type == "defausse":
            if self.jeu.plateau.defausse.taille() > 0:
                carte = self.jeu.plateau.defausse.regarder()
                couleur_idx = ["coeur", "carreau", "trefle", "pique"].index(carte.couleur)
                fond = self.jeu.plateau.fondations[couleur_idx]

 

                # Conditions pour empiler la carte sur sa fondation
                if (fond.taille() == 0 and carte.valeur == 1) or \
                   (fond.taille() > 0 and carte.valeur == fond.regarder().valeur + 1):
                    succes = True
                    self.jeu._sauvegarder_etat()
                    self.jeu.plateau.defausse.depiler()
                    fond.empiler(carte)
                    self.jeu.file_actions.append(('def->fond', couleur_idx))

 

        if succes:
            self.afficher_plateau()

 

    def on_press(self, event: tk.Event) -> None:
        "Détecte le clic initial et prépare peut etre un drag."
        self.drag_data["x0"], self.drag_data["y0"] = event.x, event.y

 

        zone_type, zone_data = self.trouver_zone_clic(event.x, event.y)

 

        # Pioche ou (talon)
        if zone_type == "talon":
            self.jeu.jouer_piocher()
            self.afficher_plateau()
            return

 

        # Rien de cliquable
        if zone_type is None:
            self.drag_data.update({"source_type": None, "cartes_draggees": []})
            return

 

        # Clic sur une colonne
        if zone_type == "colonne":
            col_idx, card_idx = zone_data
            col = self.jeu.plateau.colonnes[col_idx]
            if card_idx >= col.taille():
                return
            carte = col.carte_a_position(card_idx)
            if not carte.est_visible():
                return
            self.drag_data["cartes_draggees"] = col.toutes_les_cartes()[card_idx:]

 

        # Clic sur la défausse
        elif zone_type == "defausse":
            if self.jeu.plateau.defausse.taille() > 0:
                self.drag_data["cartes_draggees"] = [self.jeu.plateau.defausse.regarder()]
            else:
                return

 

        self.drag_data["source_type"] = zone_type
        self.drag_data["source_data"] = zone_data

 

    def on_drag(self, event: tk.Event) -> None:
        "Affiche les cartes pendant qu'elles sont déplacées avec la souris."
        self.afficher_plateau()
        if self.drag_data["cartes_draggees"]:
            dx = event.x - self.drag_data["x0"]
            dy = event.y - self.drag_data["y0"]
            for i, carte in enumerate(self.drag_data["cartes_draggees"]):
                img = self._image_pour_carte(carte)
                y_offset = 220 + i * 25 + dy
                self.canvas.create_image(event.x, y_offset, image=img)

 

    def on_release(self, event: tk.Event) -> None:
        "Quand le bouton de la souris est relâché, on pose les cartes déplacées."
        if not self.drag_data["source_type"] or not self.drag_data["cartes_draggees"]:
            self.afficher_plateau()
            return

 

        zone_dest_type, zone_dest_data = self.trouver_zone_clic(event.x, event.y)
        source_type, source_data = self.drag_data["source_type"], self.drag_data["source_data"]
        succes = False

 

        if source_type == "colonne" and zone_dest_type == "colonne":
            col_orig, pos_orig = source_data
            col_dest, _ = zone_dest_data
            if col_orig != col_dest:
                succes = self.jeu.jouer_deplacer_colonne_vers_colonne(col_orig, pos_orig, col_dest)

 

        elif source_type == "colonne" and zone_dest_type == "fondation":
            col_orig, _ = source_data
            succes = self.jeu.jouer_deplacer_colonne_vers_fondation(col_orig)

 

        elif source_type == "defausse" and zone_dest_type == "colonne":
            col_dest, _ = zone_dest_data
            succes = self.jeu.jouer_deplacer_defausse_vers_colonne(col_dest)

 

        elif source_type == "defausse" and zone_dest_type == "fondation":
            if self.jeu.plateau.defausse.taille() > 0:
                carte = self.jeu.plateau.defausse.regarder()
                fondation_idx = zone_dest_data
                couleur_idx = ["coeur", "carreau", "trefle", "pique"].index(carte.couleur)
                if fondation_idx == couleur_idx:
                    succes = self.jeu.jouer_deplacer_defausse_vers_colonne(fondation_idx)

 

        self.afficher_plateau()

 

    def _image_pour_carte(self, carte: Carte) -> tk.PhotoImage:
        "Renvoie l'image correspondante à une carte donnée."
        if getattr(carte, 'image', None):
            if os.path.exists(carte.image):
                return self.charger_image(carte.image)
            nom = os.path.basename(carte.image)
            if os.path.exists(os.path.join(self.dossier_cartes, nom)):
                return self.charger_image(nom)

 

        # Conversion valeur numérique en nom d'image
        noms = {1: "as", 11: "valet", 12: "dame", 13: "roi"}
        nom_valeur = noms.get(carte.valeur, str(carte.valeur))

 

        essais = [
            f"{nom_valeur}_{carte.couleur}.gif",
            f"{carte.valeur}_{carte.couleur}.gif",
        ]
        for nom in essais:
            if os.path.exists(os.path.join(self.dossier_cartes, nom)):
                return self.charger_image(nom)

 

        return self.charger_image('dos.gif')

 

    def afficher_plateau(self) -> None:
        "Redessine tout le plateau de jeu sur le canva."
        self.canvas.delete("all")
        if self.jeu.plateau is None:
            return

 

        # Carte dos (pour talon et les cartes cachées)
        dos_path = getattr(self.jeu.plateau, 'chemin_dos', None)
        dos_img = self.charger_image(dos_path) if dos_path else self.charger_image('dos.gif')

 

        # Talon
        if self.jeu.plateau.paquet and self.jeu.plateau.paquet.taille() > 0:
            self.canvas.create_image(90, 80, image=dos_img)
        else:
            self.canvas.create_rectangle(50, 30, 130, 140, outline="white")

 

        # Défausse
        if self.jeu.plateau.defausse.taille() > 0:
            carte = self.jeu.plateau.defausse.regarder()
            if carte.face_visible:
                img = self._image_pour_carte(carte)
                self.canvas.create_image(240, 80, image=img)

 

        # Fondations
        for i, fondation in enumerate(self.jeu.plateau.fondations):
            x = 400 + i * 110
            if fondation.taille() == 0:
                self.canvas.create_rectangle(x, 30, x + 80, 140, outline="white")
            else:
                carte = fondation.regarder()
                img = self._image_pour_carte(carte)
                self.canvas.create_image(x + 40, 80, image=img)

 

        # Colonnes principales
        for i, col in enumerate(self.jeu.plateau.colonnes):
            x = 80 + i * 110
            for j, carte in enumerate(col.toutes_les_cartes()):
                y = 220 + j * 25
                img = self._image_pour_carte(carte) if carte.face_visible else dos_img
                self.canvas.create_image(x + 40, y, image=img)

 

        # Vérifie si la partie est gagnée
        if self.jeu.plateau.verifier_victoire():
            messagebox.showinfo("Victoire!", "Bravo! Vous avez gagné!")
            self.nouvelle_partie()

 

    # Petite méthode utilitaire pour afficher le canvas + boutons quand Application le demande
    # (nom choisi pour être explicite mais n'altère pas les fonctions principales)
    def afficher_interface(self):
        # ajuste la taille du canvas à l'écran (au cas où)
        self.canvas.config(width=self.largeur, height=self.hauteur)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.cadre_boutons.pack(pady=5)
        # Rafraîchir l'affichage initial
        self.afficher_plateau()



 

class Application:
    def __init__(self, root):
        # Fenêtre en plein écran
        self.root = root
        self.root.attributes("-fullscreen", True)

 

        # Dimensions de l'écran
        self.largeur = self.root.winfo_screenwidth()
        self.hauteur = self.root.winfo_screenheight()

 

        # Zone de dessin principale
        self.zone_dessin = tk.Canvas(root, width=self.largeur, height=self.hauteur)
        self.zone_dessin.pack()

 

        # Initialisation audio(les musiques du chef)
        pygame.mixer.init()
        self.images_sons_dir = "images_sons"
        self.musique_intro = os.path.join(self.images_sons_dir, "tokyo_ghoul_instr.mp3")
        self.musique_jeu = os.path.join(self.images_sons_dir, "sol.mp3")
        self.son_demarrage = pygame.mixer.Sound(os.path.join(self.images_sons_dir, "gong.mp3"))

 

        # Chargement du menu principal
        self.charger_menu()

 

        # Initialisation des effets visuels
        self.cometes = []
        self.trainees = []
        self.images_cartes = []
        self.cometes_visibles = True

 

        # Lancement des animations
        self.demarrer_cometes()
        self.animer_cometes()

 

        # Bouton pour démarrer une nouvelle partie(donc où il est placer, l'esthetique , etc)
        self.bouton_jouer = tk.Button(self.root, text="NOUVELLE PARTIE", font=("Arial", 20),
                                      command=self.demarrer_partie, bg="grey", fg="black")
        self.zone_dessin.create_window(self.largeur // 2, self.hauteur // 2, window=self.bouton_jouer)

 

        # Interface du jeu de Tokyo Solitaire Ghoul
        # on crée l'instance mais on n'affiche pas encore son canvas (pack_forget dans sa __init__)
        self.interface_solitaire = InterfaceSolitaire(root, os.path.join(os.getcwd(), 'cartes'))

 

    # Affiche le menu principal avec fond et logo
    def charger_menu(self):
        fond_menu = ImageOps.fit(Image.open(os.path.join(self.images_sons_dir, "to.jpg")), (self.largeur, self.hauteur), method=Image.Resampling.LANCZOS)
        self.fond_menu_tk = ImageTk.PhotoImage(fond_menu)
        self.zone_dessin.create_image(0, 0, image=self.fond_menu_tk, anchor="nw")

 

        logo = Image.open(os.path.join(self.images_sons_dir, "logisol.png")).resize((300, 150), Image.Resampling.LANCZOS)
        self.logo_tk = ImageTk.PhotoImage(logo)
        self.zone_dessin.create_image(self.largeur // 2, self.hauteur // 3, image=self.logo_tk, anchor="center")

 

        pygame.mixer.music.load(self.musique_intro)
        pygame.mixer.music.play(-1)

 

    # Transition vers le jeu après clic sur "Nouvelle Partie"
    def demarrer_partie(self):
        self.son_demarrage.play()
        self.bouton_jouer.destroy()
        self.zone_dessin.delete("all")

 

        fond_chargement = ImageOps.fit(Image.open(os.path.join(self.images_sons_dir, "sai.jpg")), (self.largeur, self.hauteur), method=Image.Resampling.LANCZOS)
        self.fond_chargement_tk = ImageTk.PhotoImage(fond_chargement)
        self.zone_dessin.create_image(0, 0, image=self.fond_chargement_tk, anchor="nw")

 

        self.zone_dessin.create_text(self.largeur // 2, self.hauteur // 2,
                                     text="Chargement du jeu...(patientez un peu gros neuille de geek)",
                                     font=("Arial", 30), fill="red")

 

        # après le délai on lance le jeu
        self.root.after(4000, self.lancer_solitaire) # le nombre de temps que le chargement dois durer avant que le jeu ne se lance

 

    # Supprime les comètes et traînées de l'écran
    def degagez_cometes(self):
        for comete in self.cometes:
            self.zone_dessin.delete(comete['id'])
        for ligne in self.trainees:
            self.zone_dessin.delete(ligne)
        self.cometes.clear()
        self.trainees.clear()

 

    # Lance le jeu de solitaire après le chargement
    def lancer_solitaire(self):
        pygame.mixer.music.stop()
        pygame.mixer.music.load(self.musique_jeu)
        pygame.mixer.music.play(-1)

 

        fond_jeu = Image.open(os.path.join(self.images_sons_dir, "ni.jpg")).resize((self.largeur, self.hauteur), Image.Resampling.LANCZOS)
        self.fond_jeu_tk = ImageTk.PhotoImage(fond_jeu)
        self.zone_dessin.delete("all")
        self.cometes_visibles = False
        self.degagez_cometes()
        self.zone_dessin.create_image(0, 0, image=self.fond_jeu_tk, anchor="nw")

 

        self.zone_dessin.create_text(self.largeur // 2, 50, text="C'est parti mon kiki !", font=("Arial", 40), fill="white")

 

        

 

        # Ici on quitte le plein écran ---
        self.root.attributes("-fullscreen", False)
        self.root.geometry("1600x900")
        self.root.resizable(True, True)
        # --------------------------------------

 

        # On masque le canvas du menu
        self.zone_dessin.pack_forget()

 

        #  Et on affiche le vrai jeu Solitaire ---
        self.interface_solitaire.afficher_interface()
        
    # Crée une comète animée avec une image de carte
    def creer_comete(self):
        try:
            img = Image.open(os.path.join(self.images_sons_dir, "king_of_spades.png")).resize((70, 50), Image.Resampling.LANCZOS)
            tk_img = ImageTk.PhotoImage(img)
            self.images_cartes.append(tk_img)
            x = randint(0, self.largeur - 40)
            y = -60
            v = randint(5, 10)
            comete = {'id': self.zone_dessin.create_image(x, y, image=tk_img, anchor="nw"), 'x': x, 'y': y, 'v': v}
            self.cometes.append(comete)
        except Exception as e:
            print("Erreur comète :", e)

 

    # Anime les comètes en les déplaçant et en ajoutant une traînée
    def animer_cometes(self):
        for comete in list(self.cometes):
            comete['y'] += comete['v']  # Mise à jour de la position verticale
            self.zone_dessin.coords(comete['id'], comete['x'], comete['y'])  # Déplacement de l'image

 

            # Création d'une traînée lumineuse derrière la comète
            ligne = self.zone_dessin.create_line(
                comete['x'] + 20, comete['y'],
                comete['x'] + 20, comete['y'] - 30,
                fill="white", width=2
            )
            self.trainees.append(ligne)

 

            # Suppression des traînées les plus anciennes pour éviter la surcharge graphique
            if len(self.trainees) > 100:
                self.zone_dessin.delete(self.trainees.pop(0))

 

            # Suppression des comètes qui sortent de l'écran
            if comete['y'] > self.hauteur:
                self.zone_dessin.delete(comete['id'])
                self.cometes.remove(comete)

 

        # Relance l'animation toutes les 50 ms(millisecondes)
        self.root.after(50, self.animer_cometes)

 

    # Lance la création de comètes à intervalles réguliers
    def demarrer_cometes(self):
        if self.cometes_visibles:
            self.creer_comete()
            self.root.after(500, self.demarrer_cometes)



 

if __name__ == '__main__':
    root = tk.Tk()
    app = Application(root)
    root.mainloop()