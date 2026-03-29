VoltStudio Pro - Simulateur RLC Interactif

VoltStudio Pro est une application de simulation de circuits électriques développée en Python avec Tkinter. Elle permet de concevoir des circuits complexes, d'analyser leur topologie et de visualiser les phénomènes physiques comme la charge et la décharge d'un condensateur en temps réel.

Fonctionnalités principales

- Éditeur Graphique intuitif : Placez des composants (résistances, bobines, condensateurs, sources) sur une grille magnétique et reliez-les par un système de câblage intelligent qui suit les bornes (+/-) lors des déplacements.
- Analyseur de Topologie Avancé : Utilise un algorithme de parcours de graphe orienté pour détecter automatiquement les branches en série et en parallèle.
- Moteur Physique Temps Réel :
  * Calcul des impédances complexes ($Z$), de l'intensité ($I$) et de la puissance ($P$).
  * Simulation dynamique de la charge et de la décharge du condensateur.
  * Gestion du courant continu (DC) et alternatif (AC - 50Hz).

- Oscilloscope Digital : Un écran intégré affiche en permanence la tension, le courant et l'impédance totale du circuit.

- Mode Mesure Interactive : Utilisez l'outil "Mesure" pour cliquer sur un composant et obtenir ses détails électriques précis dans une fenêtre dédiée.

Architecture du Projet

- Le projet est divisé en trois modules pour une meilleure maintenance :

 * main.py : Point d'entrée qui initialise l'interface utilisateur.
 * interface.py : Gère toute la couche graphique (Canvas, Drag & Drop, menus, oscilloscope).
 * physics.py : Le cœur scientifique qui traite l'analyse du graphe et les calculs électriques.

Installation et Lancement

 1. Cloner le projet :
  git clone https://github.com/TON_PSEUDO/RLC_Simulator.git
 2. Lancer l'application :
  Assurez-vous d'avoir Python installé, puis lancez: python main.py

Exemple de Test : Circuit RC simple

 1. Posez une Pile (12V) et un Switch.
 2. Ajoutez une Résistance (100 Ω) et un Condensateur (0.001 F) en série.
 3. Activez le mode Interagir et fermez le Switch.
 4. Observez : La tension sur l'oscilloscope monte progressivement jusqu'à 12V (Phase de charge).
 5. Ouvrez le Switch : Si une résistance est en parallèle du condensateur, vous verrez la tension chuter lentement (Phase de décharge).
 
