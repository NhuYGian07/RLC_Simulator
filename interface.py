import tkinter as tk
from physics import PhysiqueElectrique, SimulateurCalcul, AnalyseurTopologie

class SimulateurCircuit:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulateur de Circuit Électrique")
        self.root.geometry("1300x850")
        self.root.configure(bg="#FFF5F7")

        self.composants_presents = []
        self.outil_selectionne = None
        self.point_depart = None
        self.point_depart_comp = None
        self.grid_size = 20
        self.temps_ecoule = 0
        self.simulation_active = False
        self.u_condensateur = 0
        self.selected_component = None
        self.drag_data = {"x": 0, "y": 0}
        self.derniers_resultats = {"i": 0, "z": 0, "u": 0, "circuit_ferme": False, "composants_actifs": []}
        self.labels_mesures = {}  # Pour afficher I/U sur chaque composant
        self.mode_interaction = "move"  # "move" ou "interact"
        
        self.colors = {
            "sidebar": "#FFE4E9", "accent": "#FFB7C5", "text": "#5D4E60",
            "canvas": "#FFFFFF", "wire": "#5D4E60", "grid": "#F8E1E7",
            "battery": "#B2E2F2", "gen_ac": "#B2F2BB", "resistor": "#FFD1DC",
            "inductor": "#E0BBE4", "capacitor": "#BBD6E4", "bulb_off": "#D3D3D3", 
            "bulb_on": "#FFF3A0", "screen_bg": "#1A1A1A", "screen_fg": "#00FF41",
            "actif": "#90EE90"  # Vert pour composants actifs dans le circuit
        }

        self.units = {
            "battery": "V", "gen_ac": "V", "resistor": "Ω", 
            "inductor": "H", "capacitor": "F", "bulb": "Ω", "wire": "Ω"
        }

        self._setup_ui()
        self.lancer_horloge()

    def _setup_ui(self):
        # Top Bar
        self.top_bar = tk.Frame(self.root, bg=self.colors["accent"], height=40)
        self.top_bar.pack(side="top", fill="x")
        self.status_label = tk.Label(self.top_bar, text="Prêt pour l'expérience", bg=self.colors["accent"], fg="white", font=("Arial", 10, "bold"))
        self.status_label.pack(pady=5)

        # Sidebar
        self.sidebar = tk.Frame(self.root, bg=self.colors["sidebar"], width=180)
        self.sidebar.pack(side="left", fill="y", padx=5, pady=5)

        # Oscilloscope
        self.screen_frame = tk.Frame(self.sidebar, bg=self.colors["screen_bg"], relief="sunken", bd=4)
        self.screen_frame.pack(fill="x", padx=10, pady=10)
        tk.Label(self.screen_frame, text="OSCILLOSCOPE", bg=self.colors["screen_bg"], fg=self.colors["screen_fg"], font=("Courier", 8, "bold")).pack()
        self.lbl_volt_screen = tk.Label(self.screen_frame, text="U: 00.00 V", bg=self.colors["screen_bg"], fg=self.colors["screen_fg"], font=("Courier", 16, "bold"))
        self.lbl_volt_screen.pack()
        self.lbl_current_screen = tk.Label(self.screen_frame, text="I: 0.0000 A", bg=self.colors["screen_bg"], fg="#FF6B6B", font=("Courier", 14, "bold"))
        self.lbl_current_screen.pack()
        self.lbl_impedance_screen = tk.Label(self.screen_frame, text="Z: 0.00 Ω", bg=self.colors["screen_bg"], fg="#87CEEB", font=("Courier", 12))
        self.lbl_impedance_screen.pack()
        self.lbl_time_screen = tk.Label(self.screen_frame, text="T: 0.00s", bg=self.colors["screen_bg"], fg=self.colors["screen_fg"], font=("Courier", 10))
        self.lbl_time_screen.pack(pady=2)
        self.lbl_circuit_status = tk.Label(self.screen_frame, text="Circuit ouvert", bg=self.colors["screen_bg"], fg="#FF4444", font=("Courier", 9))
        self.lbl_circuit_status.pack(pady=2)
        
        # Affichage condensateur
        self.cond_frame = tk.Frame(self.sidebar, bg="#2A2A2A", relief="sunken", bd=2)
        self.cond_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(self.cond_frame, text="CONDENSATEUR", bg="#2A2A2A", fg="#FFD700", font=("Courier", 8, "bold")).pack()
        self.lbl_u_cond = tk.Label(self.cond_frame, text="Uc: 0.00 V", bg="#2A2A2A", fg="#00FFFF", font=("Courier", 12, "bold"))
        self.lbl_u_cond.pack()
        self.lbl_charge_cond = tk.Label(self.cond_frame, text="Q: 0.00 µC", bg="#2A2A2A", fg="#AAFFAA", font=("Courier", 10))
        self.lbl_charge_cond.pack()

        self.btn_play = tk.Button(self.sidebar, text="START", bg="#98FB98", command=self.toggle_sim, font=("Arial", 10, "bold"))
        self.btn_play.pack(fill="x", padx=10, pady=5)

        # Mode d'interaction
        self.mode_frame = tk.Frame(self.sidebar, bg=self.colors["sidebar"])
        self.mode_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(self.mode_frame, text="Mode:", bg=self.colors["sidebar"], font=("Arial", 9, "bold")).pack(side="left")
        self.btn_mode_move = tk.Button(self.mode_frame, text="Deplacer", bg="#90EE90", font=("Arial", 8), command=lambda: self.set_mode("move"))
        self.btn_mode_move.pack(side="left", padx=2)
        self.btn_mode_interact = tk.Button(self.mode_frame, text="Interagir", bg="white", font=("Arial", 8), command=lambda: self.set_mode("interact"))
        self.btn_mode_interact.pack(side="left", padx=2)

        # Outils
        outils = [("Curseur", None), ("Mesure", "measure"), ("Gomme", "eraser"), ("Pile", "battery"), ("Gene AC", "gen_ac"),
                  ("Resistance", "resistor"), ("Bobine", "inductor"), ("Condensateur", "capacitor"), 
                  ("Ampoule", "bulb"), ("Cable", "wire"), ("Switch", "switch")]
        for txt, code in outils:
            tk.Button(self.sidebar, text=txt, bg="white", relief="flat", command=lambda c=code: self.changer_outil(c)).pack(fill="x", padx=10, pady=1)

        # Panel Mesures
        self.right_panel = tk.Frame(self.root, bg=self.colors["sidebar"], width=200)
        self.right_panel.pack(side="right", fill="y", padx=5, pady=5)
        self.scroll_frame = tk.Frame(self.right_panel, bg=self.colors["sidebar"])
        self.scroll_frame.pack(fill="both", expand=True)
        self.lbl_res = tk.Label(self.right_panel, text="I: 0A | Z: 0Ω", bg="white")
        self.lbl_res.pack(side="bottom", fill="x", pady=10)

        # Canvas
        self.canvas = tk.Canvas(self.root, bg="white")
        self.canvas.pack(side="right", expand=True, fill="both", padx=5, pady=5)
        self.canvas.bind("<Button-1>", self.clic_sur_canvas)
        self.canvas.bind("<B1-Motion>", self.drag_composant)
        self.canvas.bind("<ButtonRelease-1>", self.drop_composant)
        self._draw_grid()

    def verifier_chemin(self, debut_type, fin_type):
        fils = [c for c in self.composants_presents if c["type"] == "wire"]
        composants = [c for c in self.composants_presents if c["type"] not in ["wire"]]
        
        start_nodes = [c for c in composants if c["type"] == debut_type]
        target_nodes = [c for c in composants if c["type"] == fin_type]

        for start in start_nodes:
            chemins = [start["coords"]]
            visites = set()
            
            while chemins:
                actuel = chemins.pop()
                if actuel in visites: continue
                visites.add(actuel)

                for target in target_nodes:
                    if PhysiqueElectrique.calculer_distance(actuel, target["coords"]) < 40:
                        return True
                
                for f in fils:
                    f1, f2 = (f["coords"][0], f["coords"][1]), (f["coords"][2], f["coords"][3])
                    if PhysiqueElectrique.calculer_distance(actuel, f1) < 20: chemins.append(f2)
                    if PhysiqueElectrique.calculer_distance(actuel, f2) < 20: chemins.append(f1)
        return False

    def calculer_dynamique(self):
        """Simule la dynamique du circuit avec charge/decharge du condensateur."""
        condensateurs = [c for c in self.composants_presents if c["type"] == "capacitor"]
        batteries = [c for c in self.composants_presents if c["type"] in ["battery", "gen_ac"]]
        resistances = [c for c in self.composants_presents if c["type"] in ["resistor", "bulb"]]
        
        if not condensateurs:
            self.lbl_u_cond.config(text=f"Uc: {self.u_condensateur:.2f} V")
            self.lbl_time_screen.config(text=f"T: {self.temps_ecoule:.2f}s")
            return
        
        capacite = float(condensateurs[0].get("valeur", 1e-6))
        
        # Utiliser l'analyseur de circuit pour obtenir les composants actifs
        z_eq, u_source, composants_actifs = AnalyseurTopologie.analyser_circuit_complet(
            self.composants_presents, freq=50
        )
        
        # Verifier si le circuit de decharge est ferme (condensateur + resistance sans source)
        circuit_decharge = SimulateurCalcul.trouver_circuit_decharge(self.composants_presents)
        
        if z_eq is not None and composants_actifs:
            # Circuit avec source ferme - CHARGE du condensateur
            # Calculer la resistance totale des composants actifs
            r_totale = sum(
                float(r.get("valeur", 0)) 
                for r in resistances 
                if r["id"] in composants_actifs
            )
            if r_totale < 0.1:
                r_totale = 0.1
            
            if u_source > 0:
                is_charging = u_source > self.u_condensateur
                self.u_condensateur = SimulateurCalcul.simuler_condensateur(
                    u_source, self.u_condensateur, r_totale, capacite, 0.05, is_charging
                )
        elif circuit_decharge:
            # Circuit de decharge ferme (sans source) - DECHARGE du condensateur
            circuit_ids = [c["id"] for c in circuit_decharge]
            r_totale = sum(
                float(r.get("valeur", 0)) 
                for r in resistances 
                if r["id"] in circuit_ids
            )
            if r_totale < 0.1:
                r_totale = 0.1
            
            # Decharger le condensateur
            self.u_condensateur = SimulateurCalcul.simuler_condensateur(
                0, self.u_condensateur, r_totale, capacite, 0.05, False
            )
        # Si aucun circuit ferme, le condensateur garde sa charge
        
        # Calculer et afficher la charge
        charge = SimulateurCalcul.calculer_charge_condensateur(self.u_condensateur, capacite)
        self.lbl_charge_cond.config(text=f"Q: {charge*1e6:.2f} uC")
        
        # Mettre a jour l'affichage du condensateur
        self.lbl_u_cond.config(text=f"Uc: {self.u_condensateur:.2f} V")
        self.lbl_time_screen.config(text=f"T: {self.temps_ecoule:.2f}s")

    def analyser_circuit(self):
        """Analyse le circuit et calcule les grandeurs électriques avec détection série/parallèle."""
        # Utiliser l'analyseur de topologie pour détecter série/parallèle
        z_eq, u_source, composants_actifs = AnalyseurTopologie.analyser_circuit_complet(
            self.composants_presents, freq=50
        )
        
        # Vérifier également le circuit de décharge
        circuit_decharge = SimulateurCalcul.trouver_circuit_decharge(self.composants_presents)
        circuit_source = z_eq is not None
        
        if z_eq is not None:
            # Circuit avec source fermé - utiliser l'impédance calculée
            z_module = abs(z_eq)
            if z_module < 0.001:
                z_module = 0.001
            
            # Partie résistive pour calcul de puissance
            r_totale = z_eq.real if z_eq.real > 0 else 0.001
            
            # Vérifier présence condensateur
            has_capacitor = any(c["type"] == "capacitor" for c in self.composants_presents 
                               if c["id"] in composants_actifs)
            
            u_effective = u_source
            if has_capacitor:
                u_effective = u_source - self.u_condensateur
            
            intensite = u_effective / z_module if z_module > 0 else 0
            puissance = intensite ** 2 * r_totale
            
            res = {
                "u": round(u_source, 2),
                "z": round(z_module, 2),
                "i": round(intensite, 4),
                "p": round(puissance, 4),
                "circuit_ferme": True,
                "composants_actifs": composants_actifs
            }
        elif circuit_decharge:
            # Circuit de décharge du condensateur
            composants_actifs = [c["id"] for c in circuit_decharge]
            r_totale = sum(float(c.get("valeur", 0)) for c in circuit_decharge 
                          if c["type"] in ["resistor", "bulb"])
            if r_totale < 0.1:
                r_totale = 0.1
            
            intensite = self.u_condensateur / r_totale if r_totale > 0 else 0
            puissance = intensite ** 2 * r_totale
            
            res = {
                "u": round(self.u_condensateur, 2),
                "z": round(r_totale, 2),
                "i": round(intensite, 4),
                "p": round(puissance, 4),
                "circuit_ferme": True,
                "composants_actifs": composants_actifs
            }
        else:
            res = {
                "u": 0, "z": float('inf'), "i": 0, "p": 0,
                "circuit_ferme": False, "composants_actifs": []
            }
        
        self.derniers_resultats = res
        
        # Mettre à jour l'oscilloscope
        self.lbl_volt_screen.config(text=f"U: {res['u']:.2f} V")
        self.lbl_current_screen.config(text=f"I: {res['i']:.4f} A")
        self.lbl_impedance_screen.config(text=f"Z: {res['z']:.2f} Ω")
        self.lbl_res.config(text=f"I: {res['i']:.4f} A | Z: {res['z']:.1f} Ω | P: {res.get('p', 0):.4f} W")
        
        # Indicateur circuit ferme
        if res["circuit_ferme"]:
            if circuit_decharge and not circuit_source:
                self.lbl_circuit_status.config(text="Decharge condensateur", fg="#FFA500")
            else:
                self.lbl_circuit_status.config(text="Circuit ferme", fg="#00FF00")
        else:
            self.lbl_circuit_status.config(text="Circuit ouvert", fg="#FF4444")
        
        # Gérer les ampoules - elles s'allument SEULEMENT si:
        # 1. Le circuit est fermé
        # 2. L'ampoule fait partie du circuit actif
        # 3. Il y a un courant suffisant (I > 0.001 A)
        for b in [c for c in self.composants_presents if c["type"] == "bulb"]:
            est_dans_circuit = b["id"] in res.get("composants_actifs", [])
            courant_suffisant = res["i"] > 0.001
            brille = res["circuit_ferme"] and est_dans_circuit and courant_suffisant
            
            self.canvas.itemconfig(b["id"], fill=self.colors["bulb_on"] if brille else self.colors["bulb_off"])
        
        # Mettre à jour les labels de mesure sur les composants
        self.mettre_a_jour_labels_mesures(res)

    def lancer_horloge(self):
        if self.simulation_active:
            self.temps_ecoule += 0.05
            self.calculer_dynamique()
            self.analyser_circuit()
        self.root.after(50, self.lancer_horloge)
    
    def mettre_a_jour_labels_mesures(self, res):
        """Affiche/met à jour les mesures (I, U) sur chaque composant."""
        # Supprimer les anciens labels
        for label_id in list(self.labels_mesures.values()):
            self.canvas.delete(label_id)
        self.labels_mesures.clear()
        
        if not res["circuit_ferme"]:
            return
        
        intensite = res["i"]
        
        for comp in self.composants_presents:
            if comp["type"] in ["wire", "switch"]:
                continue
            
            if comp["id"] not in res.get("composants_actifs", []):
                continue
            
            cx, cy = comp["coords"]
            
            # Calculer la tension aux bornes (loi d'Ohm: U = R*I)
            tension = SimulateurCalcul.calculer_tension_composant(comp, intensite)
            
            # Afficher sous le composant
            if comp["type"] == "capacitor":
                texte = f"Uc={self.u_condensateur:.2f}V"
            elif comp["type"] in ["battery", "gen_ac"]:
                texte = f"E={tension:.1f}V"
            else:
                texte = f"U={tension:.2f}V I={intensite*1000:.1f}mA"
            
            label_id = self.canvas.create_text(
                cx, cy + 25, 
                text=texte, 
                font=("Arial", 7), 
                fill="#333333",
                tags=f"label_{comp['id']}"
            )
            self.labels_mesures[comp["id"]] = label_id
    
    def afficher_details_composant(self, composant):
        """Affiche une popup avec les details du composant."""
        res = self.derniers_resultats
        intensite = res.get("i", 0)
        
        # Creer une fenetre popup
        popup = tk.Toplevel(self.root)
        popup.title(f"Mesures - {composant['name']}")
        popup.geometry("250x200")
        popup.configure(bg="#2A2A2A")
        popup.resizable(False, False)
        
        # Titre
        tk.Label(popup, text=f"Mesures: {composant['name']}", bg="#2A2A2A", fg="white", 
                font=("Arial", 14, "bold")).pack(pady=10)
        
        # Verifier si dans le circuit
        dans_circuit = composant["id"] in res.get("composants_actifs", [])
        
        if not res.get("circuit_ferme", False):
            tk.Label(popup, text="Circuit ouvert", bg="#2A2A2A", fg="#FF6B6B", 
                    font=("Arial", 11)).pack(pady=5)
        elif not dans_circuit:
            tk.Label(popup, text="Non connecte au circuit", bg="#2A2A2A", fg="#FFD700", 
                    font=("Arial", 11)).pack(pady=5)
        else:
            # Calculer les valeurs
            tension = SimulateurCalcul.calculer_tension_composant(composant, intensite)
            valeur = float(composant.get("valeur", 0))
            
            frame = tk.Frame(popup, bg="#2A2A2A")
            frame.pack(pady=10)
            
            tk.Label(frame, text=f"Intensité: {intensite*1000:.2f} mA", bg="#2A2A2A", 
                    fg="#00FF00", font=("Courier", 11)).pack(anchor="w")
            tk.Label(frame, text=f"Tension: {tension:.3f} V", bg="#2A2A2A", 
                    fg="#00FFFF", font=("Courier", 11)).pack(anchor="w")
            
            if composant["type"] in ["resistor", "bulb"]:
                puissance = intensite ** 2 * valeur
                tk.Label(frame, text=f"Puissance: {puissance*1000:.2f} mW", bg="#2A2A2A", 
                        fg="#FFD700", font=("Courier", 11)).pack(anchor="w")
                tk.Label(frame, text=f"Résistance: {valeur:.1f} Ω", bg="#2A2A2A", 
                        fg="#AAAAAA", font=("Courier", 11)).pack(anchor="w")
            
            if composant["type"] == "capacitor":
                charge = SimulateurCalcul.calculer_charge_condensateur(self.u_condensateur, valeur)
                tk.Label(frame, text=f"Charge: {charge*1e6:.4f} µC", bg="#2A2A2A", 
                        fg="#FF69B4", font=("Courier", 11)).pack(anchor="w")
        
        # Bouton fermer
        tk.Button(popup, text="Fermer", command=popup.destroy, bg="#555555", fg="white").pack(pady=10)

    def toggle_sim(self):
        self.simulation_active = not self.simulation_active
        self.btn_play.config(text="PAUSE" if self.simulation_active else "START", bg="#FFD700" if self.simulation_active else "#98FB98")
    
    def set_mode(self, mode):
        """Change le mode d'interaction (move ou interact)."""
        self.mode_interaction = mode
        if mode == "move":
            self.btn_mode_move.config(bg="#90EE90")
            self.btn_mode_interact.config(bg="white")
            self.status_label.config(text="Mode Deplacer - Glissez les composants")
        else:
            self.btn_mode_move.config(bg="white")
            self.btn_mode_interact.config(bg="#90EE90")
            self.status_label.config(text="Mode Interagir - Cliquez sur les switches")

    def _draw_grid(self):
        for i in range(0, 1200, 20): self.canvas.create_line(i, 0, i, 900, fill=self.colors["grid"], dash=(1,1))
        for j in range(0, 900, 20): self.canvas.create_line(0, j, 1200, j, fill=self.colors["grid"], dash=(1,1))

    def changer_outil(self, outil): 
        self.outil_selectionne = outil
        curseur = ""
        if outil == "eraser":
            curseur = "X_cursor"
        elif outil == "wire":
            curseur = "cross"
        elif outil == "measure":
            curseur = "target"
        self.canvas.config(cursor=curseur)

    def clic_sur_canvas(self, event):
        x, y = round(event.x/20)*20, round(event.y/20)*20
        
        if self.outil_selectionne == "eraser":
            self.effacer_element(event.x, event.y)
        elif self.outil_selectionne == "measure":
            # Trouver le composant cliqué et afficher ses détails
            comp = self._trouver_composant_at(event.x, event.y)
            if comp:
                self.afficher_details_composant(comp)
            else:
                self.status_label.config(text="Cliquez sur un composant pour mesurer")
        elif self.outil_selectionne == "wire":
            self.poser_fil(x, y)
        elif self.outil_selectionne == "switch":
            self.placer_switch(x, y)
        elif self.outil_selectionne:
            self.placer_composant(x, y, self.outil_selectionne)
        else:
            # Mode curseur - comportement selon le mode d'interaction
            comp = self._trouver_composant_at(event.x, event.y)
            
            if self.mode_interaction == "move":
                # Mode déplacer : sélectionner pour drag
                if comp and comp["type"] != "wire":
                    self.selected_component = comp
                    self.drag_data["x"] = event.x
                    self.drag_data["y"] = event.y
            elif self.mode_interaction == "interact":
                # Mode interagir : activer les switches
                if comp and comp["type"] == "switch":
                    self._toggle_switch_by_comp(comp)
    
    def _trouver_composant_at(self, x, y):
        """Trouve et retourne le composant aux coordonnées données."""
        for c in self.composants_presents:
            if c["type"] != "wire":
                cx, cy = c["coords"]
                if abs(cx - x) < 40 and abs(cy - y) < 40:
                    return c
        return None

    def drag_composant(self, event):
        if self.selected_component is None:
            return
        
        dx = event.x - self.drag_data["x"]
        dy = event.y - self.drag_data["y"]
        
        x, y = self.selected_component["coords"]
        self.selected_component["coords"] = (x + dx, y + dy)
        
        self.canvas.move(self.selected_component["id"], dx, dy)
        self._update_connected_wires(self.selected_component)
        
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def drop_composant(self, event):
        if self.selected_component:
            x, y = self.selected_component["coords"]
            self.selected_component["coords"] = (round(x/20)*20, round(y/20)*20)
            self.canvas.coords(self.selected_component["id"], 
                             self.selected_component["coords"][0]-20, self.selected_component["coords"][1]-15,
                             self.selected_component["coords"][0]+20, self.selected_component["coords"][1]+15)
            self._update_connected_wires(self.selected_component)
            self.selected_component = None

    def placer_composant(self, x, y, c_type):
        tag = f"tag_{len(self.composants_presents)}"
        
        # Valeurs par défaut réalistes selon le type
        valeurs_defaut = {
            "battery": 12.0,      # 12V
            "gen_ac": 230.0,      # 230V AC
            "resistor": 100.0,    # 100Ω
            "inductor": 0.01,     # 10mH
            "capacitor": 0.001,   # 1000µF = 0.001F
            "bulb": 50.0          # 50Ω
        }
        valeur = valeurs_defaut.get(c_type, 10.0)
        
        comp = {"type": c_type, "coords": (x, y), "id": tag, "valeur": valeur, "name": f"{c_type[:2]}{len(self.composants_presents)+1}"}
        
        # Pour les sources, définir les bornes + (droite) et - (gauche)
        if c_type in ["battery", "gen_ac"]:
            comp["borne_plus"] = (x + 20, y)   # Borne + à droite
            comp["borne_moins"] = (x - 20, y)  # Borne - à gauche
        
        self.canvas.create_rectangle(x-20, y-15, x+20, y+15, fill=self.colors.get(c_type, "gray"), tags=tag)
        self.canvas.create_text(x, y, text=comp["name"], font=("Arial", 8, "bold"), tags=tag)
        
        # Afficher + et - sur les générateurs
        if c_type in ["battery", "gen_ac"]:
            self.canvas.create_text(x + 15, y, text="+", font=("Arial", 10, "bold"), fill="red", tags=tag)
            self.canvas.create_text(x - 15, y, text="−", font=("Arial", 10, "bold"), fill="blue", tags=tag)
        
        self.composants_presents.append(comp)
        self.update_ui_elements()

    def placer_switch(self, x, y):
        tag = f"sw_{len(self.composants_presents)}"
        comp = {"type": "switch", "coords": (x, y), "id": tag, "state": False, "name": f"SW{len(self.composants_presents)+1}"}
        self.canvas.create_rectangle(x-15, y-10, x+15, y+10, fill="white", outline="black", tags=tag)
        self.canvas.create_text(x, y, text="OFF", tags=(tag, f"txt_{tag}"), font=("Arial", 8))
        self.composants_presents.append(comp)
        self.update_ui_elements()
    
    def _toggle_switch_by_comp(self, comp):
        """Toggle un switch par son composant."""
        if comp["type"] != "switch":
            return
        comp["state"] = not comp["state"]
        # Mettre à jour le texte du switch
        txt_tag = f"txt_{comp['id']}"
        items = self.canvas.find_withtag(txt_tag)
        for item in items:
            self.canvas.itemconfig(item, text="ON" if comp["state"] else "OFF")
        # Mettre à jour la couleur
        self.canvas.itemconfig(comp["id"], fill="#90EE90" if comp["state"] else "white")
        self.analyser_circuit()

    def toggle_switch(self, c, t):
        # Ancienne méthode gardée pour compatibilité
        c["state"] = not c["state"]
        self.canvas.itemconfig(t, text="ON" if c["state"] else "OFF")
        self.canvas.itemconfig(c["id"], fill="#90EE90" if c["state"] else "white")
        self.analyser_circuit()

    def _detecter_borne(self, comp, x, y):
        """Détecte si le clic est sur la borne + ou - d'une source."""
        if comp["type"] not in ["battery", "gen_ac"]:
            return None  # Pas une source
        
        cx, cy = comp["coords"]
        # Si clic à droite du centre -> borne +
        # Si clic à gauche du centre -> borne -
        if x > cx:
            return "+"
        else:
            return "-"
    
    def poser_fil(self, x, y):
        if self.point_depart is None:
            # Trouver le composant de départ et utiliser son centre
            comp_depart = self._trouver_composant_at(x, y)
            if comp_depart:
                # Détecter la borne pour les sources
                borne = self._detecter_borne(comp_depart, x, y)
                cx, cy = comp_depart["coords"]
                
                # Ajuster le point de départ vers la borne si c'est une source
                if borne == "+":
                    self.point_depart = (cx + 20, cy)
                elif borne == "-":
                    self.point_depart = (cx - 20, cy)
                else:
                    self.point_depart = (cx, cy)
                
                self.point_depart_comp = comp_depart
                self.point_depart_borne = borne
                
                borne_txt = f" (borne {borne})" if borne else ""
                self.status_label.config(text=f"Depart: {comp_depart['name']}{borne_txt} - Cliquez sur le composant d'arrivee")
            else:
                self.status_label.config(text="Cable doit partir d'un composant")
        else:
            # Trouver le composant d'arrivée
            comp_arrivee = self._trouver_composant_at(x, y)
            if not comp_arrivee:
                self.point_depart = None
                self.point_depart_comp = None
                self.point_depart_borne = None
                self.status_label.config(text="Cable doit se connecter a un composant")
                return
            
            # Verifier qu'on ne connecte pas un composant a lui-meme
            if self.point_depart_comp and comp_arrivee["id"] == self.point_depart_comp["id"]:
                self.status_label.config(text="Impossible de connecter un composant a lui-meme")
                return
            
            # Détecter la borne d'arrivée
            borne_arrivee = self._detecter_borne(comp_arrivee, x, y)
            
            # Utiliser les centres/bornes des composants
            x1, y1 = self.point_depart
            cx2, cy2 = comp_arrivee["coords"]
            
            # Ajuster le point d'arrivée vers la borne si c'est une source
            if borne_arrivee == "+":
                x2, y2 = cx2 + 20, cy2
            elif borne_arrivee == "-":
                x2, y2 = cx2 - 20, cy2
            else:
                x2, y2 = cx2, cy2
            
            nom_depart = self.point_depart_comp["name"] if self.point_depart_comp else "?"
            borne_dep_txt = f"({self.point_depart_borne})" if self.point_depart_borne else ""
            borne_arr_txt = f"({borne_arrivee})" if borne_arrivee else ""
            
            tag = f"wire_{len(self.composants_presents)}"
            self.canvas.create_line(x1, y1, x2, y2, fill=self.colors["wire"], width=3, tags=tag)
            self.canvas.tag_lower(tag)  # Place le câble derrière les composants
            
            # Construire la connexion avec info de borne
            connexion_data = {
                "type": "wire", 
                "connexion": (self.point_depart_comp["id"], comp_arrivee["id"]),
                "coords": (x1, y1, x2, y2),
                "id": tag,
                "valeur": 0.0,
                "name": f"W{len(self.composants_presents)+1}"
            }
            
            # Ajouter info des bornes si présentes
            if self.point_depart_borne:
                connexion_data["borne_depart"] = self.point_depart_borne
            if borne_arrivee:
                connexion_data["borne_arrivee"] = borne_arrivee
            
            self.composants_presents.append(connexion_data)
            self.point_depart = None
            self.point_depart_comp = None
            self.point_depart_borne = None
            self.status_label.config(text=f"Cable: {nom_depart}{borne_dep_txt} -> {comp_arrivee['name']}{borne_arr_txt}")
            self.analyser_circuit()
            self.update_ui_elements()

    def _composant_at(self, x, y):
        """Check if there's a component at the given coordinates"""
        return self._trouver_composant_at(x, y) is not None

    def update_ui_elements(self):
        for w in self.scroll_frame.winfo_children(): 
            w.destroy()
        
        for c in self.composants_presents:
            if c["type"] not in ["wire", "switch"]:
                f = tk.Frame(self.scroll_frame, bg="white", relief="ridge", bd=1)
                f.pack(fill="x", padx=2, pady=2)
                
                tk.Label(f, text=c["name"], bg="white", font=("Arial", 9, "bold")).pack(side="left", padx=5)
                
                v = tk.StringVar(value=str(c.get("valeur", 10)))
                e = tk.Entry(f, textvariable=v, width=4, font=("Arial", 8))
                e.pack(side="right", padx=2)
                e.bind("<Return>", lambda _, co=c, va=v: self.set_val(co, va))
                
                unit = self.units.get(c["type"], "")
                tk.Label(f, text=unit, bg="white", font=("Arial", 8)).pack(side="right", padx=2)

    def set_val(self, c, v):
        try:
            c["valeur"] = float(v.get())
            self.analyser_circuit()
        except:
            pass

    def effacer_element(self, x, y):
        item = self.canvas.find_closest(x, y)
        tags = self.canvas.gettags(item)
        for t in tags:
            if t.startswith("tag_") or t.startswith("sw_") or t.startswith("wire_"):
                # Trouver le composant a supprimer
                comp_a_supprimer = next((c for c in self.composants_presents if c.get("id") == t), None)
                
                if comp_a_supprimer and comp_a_supprimer["type"] != "wire":
                    # Supprimer aussi tous les cables connectes a ce composant
                    cables_a_supprimer = [
                        w for w in self.composants_presents 
                        if w["type"] == "wire" and "connexion" in w 
                        and (w["connexion"][0] == t or w["connexion"][1] == t)
                    ]
                    for cable in cables_a_supprimer:
                        self.canvas.delete(cable["id"])
                        self.composants_presents = [c for c in self.composants_presents if c.get("id") != cable["id"]]
                
                self.canvas.delete(t)
                self.composants_presents = [c for c in self.composants_presents if c.get("id") != t]
        self.update_ui_elements()
        self.analyser_circuit()

    def _update_connected_wires(self, component):
        """Met a jour les cables connectes a un composant apres deplacement.
        
        Utilise la connexion statique (champ 'connexion') au lieu de la proximite.
        """
        comp_id = component["id"]
        cx, cy = component["coords"]
        
        for wire in [c for c in self.composants_presents if c["type"] == "wire"]:
            if "connexion" not in wire:
                continue
            
            id_source, id_dest = wire["connexion"]
            x1, y1, x2, y2 = wire["coords"]
            
            # Determiner les nouveaux points de connexion
            if id_source == comp_id:
                # Ce composant est le depart du cable
                borne = wire.get("borne_depart")
                if borne == "+":
                    new_x1, new_y1 = cx + 20, cy
                elif borne == "-":
                    new_x1, new_y1 = cx - 20, cy
                else:
                    new_x1, new_y1 = cx, cy
                wire["coords"] = (new_x1, new_y1, x2, y2)
                self.canvas.coords(wire["id"], new_x1, new_y1, x2, y2)
            
            if id_dest == comp_id:
                # Ce composant est l'arrivee du cable
                borne = wire.get("borne_arrivee")
                if borne == "+":
                    new_x2, new_y2 = cx + 20, cy
                elif borne == "-":
                    new_x2, new_y2 = cx - 20, cy
                else:
                    new_x2, new_y2 = cx, cy
                wire["coords"] = (x1, y1, new_x2, new_y2)
                self.canvas.coords(wire["id"], x1, y1, new_x2, new_y2)

if __name__ == "__main__":
    root = tk.Tk()
    app = SimulateurCircuit(root)
    root.mainloop()