import tkinter as tk
from tkinter import filedialog, ttk, simpledialog
from PIL import Image, ImageTk
import os
import json

class LevelEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tkinter Level Editor")
        self.geometry("1400x800")

        self.configure(bg='#1e1e1e')
        self.grid_size = 32
        self.offgrid = tk.BooleanVar(value=False)

        self.level_data = {
            "layers": []
        }
        self.current_layer = None
        self.layer_tile_images = {}

        self.setup_ui()

    def setup_ui(self):
        # Style for dark mode
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TButton", background="#2e2e2e", foreground="white")
        style.configure("TLabel", background="#1e1e1e", foreground="white")
        style.configure("TCheckbutton", background="#1e1e1e", foreground="white")

        # Left: Layer Panel
        self.layer_frame = tk.Frame(self, bg="#1e1e1e", width=200)
        self.layer_frame.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(self.layer_frame, text="Layers").pack(pady=5)
        self.layer_listbox = tk.Listbox(self.layer_frame, bg="#2e2e2e", fg="white")
        self.layer_listbox.pack(fill=tk.BOTH, expand=True)
        self.layer_listbox.bind("<<ListboxSelect>>", self.on_layer_select)

        ttk.Button(self.layer_frame, text="Add Layer", command=self.add_layer).pack(fill=tk.X)
        ttk.Button(self.layer_frame, text="Rename Layer", command=self.rename_layer).pack(fill=tk.X)
        ttk.Button(self.layer_frame, text="Load Layer Tiles", command=self.load_layer_tiles).pack(fill=tk.X)

        ttk.Checkbutton(self.layer_frame, text="Place off-grid", variable=self.offgrid).pack(pady=5)

        # Center: Grid Canvas
        self.canvas = tk.Canvas(self, bg="#121212", scrollregion=(0, 0, 3000, 3000))
        self.canvas.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        self.canvas.bind("<Button-1>", self.place_tile)

        # Right: Tile Palette
        self.palette_frame = tk.Frame(self, bg="#1e1e1e", width=200)
        self.palette_frame.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Label(self.palette_frame, text="Tiles").pack(pady=5)

        self.tile_canvas = tk.Canvas(self.palette_frame, bg="#1e1e1e", width=180)
        self.tile_scrollbar = tk.Scrollbar(self.palette_frame, command=self.tile_canvas.yview)
        self.tile_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tile_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tile_canvas.configure(yscrollcommand=self.tile_scrollbar.set)

        self.tile_frame = tk.Frame(self.tile_canvas, bg="#1e1e1e")
        self.tile_canvas.create_window((0, 0), window=self.tile_frame, anchor='nw')

        self.tile_images = []
        self.current_tile = None
        self.load_tiles("./data/tiles")

        self.tile_frame.update_idletasks()
        self.tile_canvas.config(scrollregion=self.tile_canvas.bbox("all"))

        # Menu for saving and loading
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Save", command=self.save_level)
        file_menu.add_command(label="Load", command=self.load_level)
        menubar.add_cascade(label="File", menu=file_menu)
        self.config(menu=menubar)

    def add_layer(self):
        name = f"Layer {len(self.level_data['layers'])}"
        self.level_data['layers'].append({"name": name, "tiles": []})
        self.layer_listbox.insert(tk.END, name)

    def rename_layer(self):
        index = self.layer_listbox.curselection()
        if index:
            new_name = simpledialog.askstring("Rename Layer", "Enter new layer name:")
            if new_name:
                self.level_data['layers'][index[0]]['name'] = new_name
                self.layer_listbox.delete(index)
                self.layer_listbox.insert(index[0], new_name)

    def load_layer_tiles(self):
        index = self.layer_listbox.curselection()
        if index:
            folder = filedialog.askdirectory(title="Select tile folder for this layer")
            if folder:
                self.layer_tile_images[index[0]] = folder

    def on_layer_select(self, event):
        index = self.layer_listbox.curselection()
        if index:
            self.current_layer = index[0]

    def load_tiles(self, folder):
        for filename in os.listdir(folder):
            if filename.endswith(".png"):
                img_path = os.path.join(folder, filename)
                img = Image.open(img_path).resize((32, 32))
                tk_img = ImageTk.PhotoImage(img)
                self.tile_images.append((filename, tk_img))
                btn = tk.Button(self.tile_frame, image=tk_img, command=lambda f=filename: self.select_tile(f), bg="#1e1e1e", bd=0)
                btn.pack(padx=2, pady=2)

    def select_tile(self, filename):
        self.current_tile = filename

    def place_tile(self, event):
        if self.current_tile is None or self.current_layer is None:
            return

        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        if not self.offgrid.get():
            x -= x % self.grid_size
            y -= y % self.grid_size

        tile_folder = self.layer_tile_images.get(self.current_layer, "./data/tiles")
        img_path = os.path.join(tile_folder, self.current_tile)
        img = Image.open(img_path).resize((32, 32))
        tk_img = ImageTk.PhotoImage(img)
        self.canvas.create_image(x, y, image=tk_img, anchor=tk.NW)
        self.canvas.image = tk_img  # Prevent garbage collection

        self.level_data['layers'][self.current_layer]['tiles'].append({
            "tile": self.current_tile,
            "x": x,
            "y": y
        })

    def save_level(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if path:
            with open(path, 'w') as f:
                json.dump(self.level_data, f, indent=4)

    def load_level(self):
        path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if path:
            with open(path, 'r') as f:
                self.level_data = json.load(f)
            self.layer_listbox.delete(0, tk.END)
            for layer in self.level_data['layers']:
                self.layer_listbox.insert(tk.END, layer['name'])
            self.redraw()

    def redraw(self):
        self.canvas.delete("all")
        for idx, layer in enumerate(self.level_data['layers']):
            tile_folder = self.layer_tile_images.get(idx, "./data/tiles")
            for tile in layer['tiles']:
                img_path = os.path.join(tile_folder, tile['tile'])
                img = Image.open(img_path).resize((32, 32))
                tk_img = ImageTk.PhotoImage(img)
                self.canvas.create_image(tile['x'], tile['y'], image=tk_img, anchor=tk.NW)
                self.canvas.image = tk_img  # Prevent GC

if __name__ == "__main__":
    app = LevelEditor()
    app.mainloop()
