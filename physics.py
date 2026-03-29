import math

class PhysiqueElectrique:
    @staticmethod
    def calculer_distance(p1, p2):
        return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)


class AnalyseurCircuit:
    """Analyse le circuit avec un graphe ORIENTÉ.
    
    Les fils sont des liens UNIDIRECTIONNELS entre deux composants.
    Le courant va du composant A vers le composant B comme câblé.
    Les switches ouverts bloquent le passage.
    """
    
    @staticmethod
    def construire_graphe(composants):
        """Construit un graphe ORIENTÉ de connexions à partir des fils.
        
        Un fil (A, B) crée une connexion A -> B (sens du courant).
        
        Retourne:
            - graphe: dict {comp_id: set(comp_ids successeurs)}
            - comp_map: dict {comp_id: composant}
            - source: le générateur (battery/gen_ac) ou None
        """
        fils = [c for c in composants if c["type"] == "wire"]
        autres = [c for c in composants if c["type"] != "wire"]
        
        # Map id -> composant
        comp_map = {c["id"]: c for c in autres}
        
        # Trouver la source
        source = None
        for c in autres:
            if c["type"] in ["battery", "gen_ac"]:
                source = c
                break
        
        # Identifier les switches ouverts
        switches_ouverts = {c["id"] for c in autres 
                          if c["type"] == "switch" and not c.get("state", False)}
        
        # Construire le graphe ORIENTÉ
        graphe = {c["id"]: set() for c in autres}
        
        for fil in fils:
            # Récupérer les IDs des composants connectés
            if "connexion" not in fil:
                continue
            
            id_source, id_dest = fil["connexion"]
            
            # Vérifier que les deux IDs existent
            if id_source not in comp_map or id_dest not in comp_map:
                continue
            
            # Si un des composants est un switch ouvert, pas de connexion
            if id_source in switches_ouverts or id_dest in switches_ouverts:
                continue
            
            # Ajouter la connexion UNIDIRECTIONNELLE (sens du courant)
            graphe[id_source].add(id_dest)
        
        return graphe, comp_map, source
    
    @staticmethod
    def trouver_chemins_fermes(graphe, source_id, max_depth=15):
        """Trouve tous les chemins ORIENTÉS qui partent de la source et y reviennent.
        
        Suit le sens des flèches dans le graphe orienté.
        """
        chemins = []
        
        def dfs(current, path, visited):
            if len(path) > max_depth:
                return
            
            for successeur in graphe.get(current, set()):
                if successeur == source_id and len(path) >= 1:
                    # Chemin fermé trouvé !
                    chemins.append(list(path))
                elif successeur not in visited:
                    visited.add(successeur)
                    dfs(successeur, path + [successeur], visited)
                    visited.remove(successeur)
        
        # Démarrer depuis les successeurs directs de la source
        for successeur in graphe.get(source_id, set()):
            dfs(successeur, [successeur], {successeur})
        
        return chemins
    
    @staticmethod
    def calculer_impedance_composant(comp, freq=50):
        """Calcule l'impédance complexe d'un composant."""
        val = float(comp.get("valeur", 0))
        c_type = comp["type"]
        
        if c_type in ["resistor", "bulb"]:
            return complex(max(val, 0.001), 0)
        elif c_type == "inductor":
            xl = 2 * math.pi * freq * val
            return complex(0.001, xl)
        elif c_type == "capacitor":
            if val > 0 and freq > 0:
                xc = 1 / (2 * math.pi * freq * val)
                return complex(0.001, -xc)
            return complex(0.001, 0)
        elif c_type == "switch":
            # Switch fermé = résistance quasi-nulle
            return complex(0.001, 0)
        else:
            # wire, battery, gen_ac
            return complex(0.001, 0)
    
    @staticmethod
    def chemin_valide(chemin, comp_map):
        """Vérifie qu'un chemin contient au moins une résistance."""
        for comp_id in chemin:
            comp = comp_map.get(comp_id)
            if comp and comp["type"] in ["resistor", "bulb", "inductor", "capacitor"]:
                return True
        return False
    
    @staticmethod
    def calculer_impedance_chemin(chemin, comp_map, freq=50):
        """Calcule l'impédance totale d'un chemin (série)."""
        z_total = complex(0, 0)
        for comp_id in chemin:
            comp = comp_map.get(comp_id)
            if comp:
                z_total += AnalyseurCircuit.calculer_impedance_composant(comp, freq)
        return z_total
    
    @staticmethod
    def analyser_circuit(composants, freq=50):
        """Analyse complète du circuit.
        
        Retourne: (impedance_eq, tension_source, composants_actifs)
        """
        graphe, comp_map, source = AnalyseurCircuit.construire_graphe(composants)
        
        if not source:
            return None, 0, []
        
        u_source = float(source.get("valeur", 0))
        
        # Trouver tous les chemins fermés
        chemins = AnalyseurCircuit.trouver_chemins_fermes(graphe, source["id"])
        
        if not chemins:
            return None, u_source, []
        
        # Filtrer les chemins valides (avec au moins une résistance)
        chemins_valides = [c for c in chemins if AnalyseurCircuit.chemin_valide(c, comp_map)]
        
        if not chemins_valides:
            # Que des court-circuits
            return complex(0.001, 0), u_source, list(comp_map.keys())
        
        # Éliminer les doublons (même ensemble de composants)
        chemins_uniques = []
        vus = set()
        for chemin in chemins_valides:
            key = frozenset(chemin)
            if key not in vus:
                vus.add(key)
                chemins_uniques.append(chemin)
        
        # Collecter tous les composants actifs
        actifs = set()
        actifs.add(source["id"])
        for chemin in chemins_uniques:
            actifs.update(chemin)
        
        if len(chemins_uniques) == 1:
            # Circuit série simple
            z_eq = AnalyseurCircuit.calculer_impedance_chemin(chemins_uniques[0], comp_map, freq)
        else:
            # Circuit avec branches parallèles
            # Trouver les composants communs à tous les chemins (en série)
            ensembles = [set(c) for c in chemins_uniques]
            composants_serie = ensembles[0].intersection(*ensembles[1:]) if ensembles else set()
            
            # Calculer Z série
            z_serie = complex(0, 0)
            for comp_id in composants_serie:
                comp = comp_map.get(comp_id)
                if comp:
                    z_serie += AnalyseurCircuit.calculer_impedance_composant(comp, freq)
            
            # Calculer les impédances des branches parallèles
            impedances_branches = []
            for chemin in chemins_uniques:
                z_branche = complex(0, 0)
                for comp_id in chemin:
                    if comp_id not in composants_serie:
                        comp = comp_map.get(comp_id)
                        if comp:
                            z_branche += AnalyseurCircuit.calculer_impedance_composant(comp, freq)
                if abs(z_branche) > 0.0001:
                    impedances_branches.append(z_branche)
            
            # Combiner les branches en parallèle
            if impedances_branches:
                somme_inv = sum(1/z for z in impedances_branches if abs(z) > 0.0001)
                z_parallele = 1/somme_inv if abs(somme_inv) > 0.0001 else complex(0, 0)
            else:
                z_parallele = complex(0, 0)
            
            z_eq = z_serie + z_parallele
        
        # Garantir une impédance minimale
        if abs(z_eq) < 0.001:
            z_eq = complex(0.001, 0)
        
        return z_eq, u_source, list(actifs)


# Garder la compatibilité avec l'ancien nom
class AnalyseurTopologie:
    """Wrapper pour compatibilité avec l'ancien code."""
    
    @staticmethod
    def analyser_circuit_complet(composants, freq=50):
        return AnalyseurCircuit.analyser_circuit(composants, freq)
    
    @staticmethod
    def calculer_impedance_composant(composant, freq=50):
        return AnalyseurCircuit.calculer_impedance_composant(composant, freq)


class SimulateurCalcul:
    """Calculs de simulation du circuit."""
    
    @staticmethod
    def trouver_circuit_ferme(composants):
        """Vérifie si le circuit est fermé avec une source."""
        graphe, comp_map, source = AnalyseurCircuit.construire_graphe(composants)
        if not source:
            return None
        chemins = AnalyseurCircuit.trouver_chemins_fermes(graphe, source["id"])
        if chemins:
            # Retourner les composants du premier chemin trouvé
            return [comp_map[cid] for cid in chemins[0] if cid in comp_map]
        return None
    
    @staticmethod
    def trouver_circuit_decharge(composants):
        """Trouve un circuit de décharge (condensateur + résistance, sans source)."""
        fils = [c for c in composants if c["type"] == "wire"]
        autres = [c for c in composants if c["type"] != "wire"]
        
        condensateurs = [c for c in autres if c["type"] == "capacitor"]
        if not condensateurs:
            return None
        
        # Construire graphe sans les sources
        comp_map = {c["id"]: c for c in autres if c["type"] not in ["battery", "gen_ac"]}
        switches_ouverts = {c["id"] for c in autres 
                          if c["type"] == "switch" and not c.get("state", False)}
        
        graphe = {cid: set() for cid in comp_map}
        
        for fil in fils:
            if "connexion" not in fil:
                continue
            id_a, id_b = fil["connexion"]
            
            # Ignorer si connecté à une source
            comp_a = next((c for c in autres if c["id"] == id_a), None)
            comp_b = next((c for c in autres if c["id"] == id_b), None)
            if comp_a and comp_a["type"] in ["battery", "gen_ac"]:
                continue
            if comp_b and comp_b["type"] in ["battery", "gen_ac"]:
                continue
            
            if id_a not in comp_map or id_b not in comp_map:
                continue
            if id_a in switches_ouverts or id_b in switches_ouverts:
                continue
            
            graphe[id_a].add(id_b)
            graphe[id_b].add(id_a)
        
        # Chercher un chemin fermé passant par le condensateur
        for cond in condensateurs:
            chemins = []
            
            def dfs(current, path, visited):
                if len(path) > 10:
                    return
                for voisin in graphe.get(current, set()):
                    if voisin == cond["id"] and len(path) >= 1:
                        chemins.append(list(path))
                    elif voisin not in visited:
                        visited.add(voisin)
                        dfs(voisin, path + [voisin], visited)
                        visited.remove(voisin)
            
            for voisin in graphe.get(cond["id"], set()):
                dfs(voisin, [voisin], {voisin})
            
            # Chercher un chemin avec résistance
            for chemin in chemins:
                has_resistance = any(
                    comp_map.get(cid, {}).get("type") in ["resistor", "bulb"]
                    for cid in chemin
                )
                if has_resistance:
                    return [comp_map[cid] for cid in chemin if cid in comp_map]
        
        return None
    
    @staticmethod
    def calculer_impedance(composants, freq=50, u_condensateur=0):
        """Calcule l'impédance et le courant du circuit."""
        z_eq, u_source, actifs = AnalyseurCircuit.analyser_circuit(composants, freq)
        
        if z_eq is None:
            return {
                "u": 0, "z": float('inf'), "i": 0, "p": 0,
                "circuit_ferme": False, "composants_actifs": []
            }
        
        z_module = abs(z_eq)
        if z_module < 0.001:
            z_module = 0.001
        
        r_totale = max(z_eq.real, 0.001)
        
        # Ajuster pour condensateur
        has_capa = any(
            c["type"] == "capacitor" 
            for c in composants if c.get("id") in actifs
        )
        u_eff = u_source - u_condensateur if has_capa and freq == 0 else u_source
        
        intensite = u_eff / z_module
        puissance = intensite ** 2 * r_totale
        
        return {
            "u": round(u_source, 2),
            "u_eff": round(u_eff, 2),
            "z": round(z_module, 2),
            "i": round(intensite, 4),
            "p": round(puissance, 4),
            "circuit_ferme": True,
            "composants_actifs": actifs
        }
    
    @staticmethod
    def calculer_tension_composant(composant, intensite):
        """Calcule U = R*I pour un composant."""
        val = float(composant.get("valeur", 0))
        c_type = composant["type"]
        
        if c_type in ["resistor", "bulb"]:
            return round(val * intensite, 4)
        elif c_type in ["battery", "gen_ac"]:
            return val
        return 0
    
    @staticmethod
    def simuler_condensateur(u_source, u_actuel, resistance, capacite, dt, en_charge):
        """Simule charge/décharge d'un condensateur."""
        if capacite <= 0 or resistance <= 0:
            return u_actuel
        
        tau = resistance * capacite
        
        if en_charge:
            delta = (u_source - u_actuel) * (1 - math.exp(-dt / tau))
            return u_actuel + delta
        else:
            return u_actuel * math.exp(-dt / tau)
    
    @staticmethod
    def calculer_charge_condensateur(u_condensateur, capacite):
        """Q = C * U (Coulombs)."""
        return capacite * u_condensateur
