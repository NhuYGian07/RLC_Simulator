import tkinter as tk
from interface import SimulateurCircuit

if __name__ == "__main__":
    root = tk.Tk()
    # On définit une police par défaut plus jolie
    root.option_add("*Font", "SegoeUI 9")
    app = SimulateurCircuit(root)
    root.mainloop()