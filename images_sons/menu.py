from tkinter import Tk, Canvas, Button
from PIL import Image, ImageTk, ImageOps
import pygame
from random import randint, shuffle

 

pygame.mixer.init()
pygame.mixer.music.load("tokyo_ghoul_instr.mp3")
pygame.mixer.music.play(-1)
son_demarrage = pygame.mixer.Sound("gong.mp3")

 

fenetre = Tk()
fenetre.attributes("-fullscreen", True)

 

cartes_fond = []
images_cartes = []
cometes = []
trainees = []
cometes_visibles = True

 

largeur = fenetre.winfo_screenwidth()
hauteur = fenetre.winfo_screenheight()

 

zone_dessin = Canvas(fenetre, width=largeur, height=hauteur)
zone_dessin.pack()

 

fond_menu = Image.open("to.jpg")
fond_menu = ImageOps.fit(fond_menu, (largeur, hauteur), method=Image.Resampling.LANCZOS)
fond_menu_tk = ImageTk.PhotoImage(fond_menu)
zone_dessin.create_image(0, 0, image=fond_menu_tk, anchor="nw")
zone_dessin.image = fond_menu_tk

 

logo = Image.open("logisol.png").resize((300, 150), Image.Resampling.LANCZOS)
logo_tk = ImageTk.PhotoImage(logo)
zone_dessin.create_image(largeur // 2, hauteur // 4, image=logo_tk, anchor="center")
zone_dessin.logo = logo_tk

 

def demarrer_partie():
    son_demarrage.play()
    zone_dessin.delete("all")

 

    fond_chargement = Image.open("sai.jpg")
    fond_chargement = ImageOps.fit(fond_chargement, (largeur, hauteur), method=Image.Resampling.LANCZOS)
    fond_chargement_tk = ImageTk.PhotoImage(fond_chargement)
    zone_dessin.create_image(0, 0, image=fond_chargement_tk, anchor="nw")
    zone_dessin.image = fond_chargement_tk

 

    zone_dessin.create_text(
        largeur // 2, hauteur // 2,
        text="Chargement du jeu...(patientez un peu bon sang)",
        font=("Arial", 30),
        fill="red"
    )

 

    fenetre.after(4000, lancer_solitaire)

 

bouton_jouer = Button(
    fenetre,
    text="NOUVELLE PARTIE",
    font=("Arial", 20),
    command=demarrer_partie,
    bg="grey",
    fg="black"
)
zone_dessin.create_window(largeur // 2, hauteur // 2, window=bouton_jouer)

 

class Carte:
    def __init__(self, valeur, couleur, visible=False):
        self.valeur = valeur
        self.couleur = couleur
        self.visible = visible

 

    def est_rouge(self):
        return self.couleur in ['coeur', 'carreau']

 

    def __str__(self):
        return f"{self.valeur} de {self.couleur}" if self.visible else "Carte cachée"

 

class PileCartes:
    def __init__(self):
        self.cartes = []

 

    def ajouter(self, carte):
        self.cartes.append(carte)

 

    def retirer(self):
        return self.cartes.pop() if self.cartes else None

 

    def sommet(self):
        return self.cartes[-1] if self.cartes else None

 

    def est_vide(self):
        return len(self.cartes) == 0

 

    def retourner_derniere(self):
        if self.cartes and not self.cartes[-1].visible:
            self.cartes[-1].visible = True

 

def preparer_cartes():
    couleurs = ['coeur', 'carreau', 'pique', 'trefle']
    valeurs = list(range(1, 14))
    paquet = [Carte(v, c) for c in couleurs for v in valeurs]
    shuffle(paquet)

 

    colonnes = [PileCartes() for _ in range(7)]
    for i in range(7):
        for j in range(i + 1):
            carte = paquet.pop()
            carte.visible = (j == i)
            colonnes[i].ajouter(carte)

 

    pioche = paquet
    fondations = [PileCartes() for _ in range(4)]
    return colonnes, pioche, fondations

 

def afficher_plateau():
    valeur_map = {1: 'A', 11: 'J', 12: 'Q', 13: 'K'}
    couleur_map = {'coeur': 'H', 'carreau': 'D', 'pique': 'S', 'trefle': 'C'}

 

    for i, pile in enumerate(colonnes):
        x = 100 + i * 120
        y = 150
        for j, carte in enumerate(pile.cartes):
            if carte.visible:
                val = valeur_map.get(carte.valeur, str(carte.valeur))
                coul = couleur_map[carte.couleur]
                nom_fichier = f"cartes/{val}{coul}.png"
            else:
                nom_fichier = "cartes/back.png"

 

            try:
                cadre_largeur = 80
                cadre_hauteur = 120
                img_largeur = 70
                img_hauteur = 110
                x0 = x
                y0 = y + j * 30
                x1 = x0 + cadre_largeur
                y1 = y0 + cadre_hauteur

 

                zone_dessin.create_rectangle(x0, y0, x1, y1, fill="white", outline="black", width=2)

 

                img = Image.open(nom_fichier).resize((img_largeur, img_hauteur), Image.Resampling.LANCZOS)
                tk_img = ImageTk.PhotoImage(img)
                images_cartes.append(tk_img)

 

                img_x = x0 + (cadre_largeur - img_largeur) // 2
                img_y = y0 + (cadre_hauteur - img_hauteur) // 2
                zone_dessin.create_image(img_x, img_y, image=tk_img, anchor="nw")

 

            except Exception as e:
                zone_dessin.create_text(x, y + j * 30, text=str(carte), fill="white", font=("Arial", 10))

 

def nettoyer_cometes():
    for comete in cometes:
        zone_dessin.delete(comete['id'])
    for ligne in trainees:
        zone_dessin.delete(ligne)
    cometes.clear()
    trainees.clear()

 

def lancer_solitaire():
    pygame.mixer.music.stop()
    pygame.mixer.music.load("sol.mp3")
    pygame.mixer.music.play(-1)

 

    fond_jeu = ImageOps.fit(Image.open("ni.jpg"), (largeur, hauteur), method=Image.Resampling.LANCZOS)
    fond_jeu_tk = ImageTk.PhotoImage(fond_jeu)
    zone_dessin.delete("all")
    global cometes_visibles
    cometes_visibles = False
    nettoyer_cometes()
    zone_dessin.create_image(0, 0, image=fond_jeu_tk, anchor="nw")
    zone_dessin.image = fond_jeu_tk

 

    zone_dessin.create_text(largeur // 2, 50, text="C'est parti mon kiki !", font=("Arial", 40), fill="white")

 

    global colonnes, pioche, fondations
    colonnes, pioche, fondations = preparer_cartes()
    afficher_plateau()

 

def creer_comete():
    try:
        img = Image.open("king_of_spades.png").resize((70, 50), Image.Resampling.LANCZOS)
        tk_img = ImageTk.PhotoImage(img)
        images_cartes.append(tk_img)
        x = randint(0, largeur - 40)
        y = -60
        vitesse = randint(5, 10)
        comete = {'id': zone_dessin.create_image(x, y, image=tk_img, anchor="nw"), 'x': x, 'y': y, 'v': vitesse}
        cometes.append(comete)
    except Exception as e:
        print("Erreur comète :", e)

 

def animer_cometes():
    for comete in cometes:
        x, y, v = comete['x'], comete['y'], comete['v']
        y += v
        comete['y'] = y
        zone_dessin.coords(comete['id'], x, y)

 

        ligne = zone_dessin.create_line(x + 20, y, x + 20, y - 30, fill="white", width=2)
        trainees.append(ligne)

 

        if len(trainees) > 100:
            zone_dessin.delete(trainees.pop(0))

 

        if y > hauteur:
            zone_dessin.delete(comete['id'])
            cometes.remove(comete)

 

    fenetre.after(50, animer_cometes)

 

def demarrer_cometes():
    if cometes_visibles:
        creer_comete()
        fenetre.after(500, demarrer_cometes)

 

demarrer_cometes()
animer_cometes()
fenetre.mainloop()