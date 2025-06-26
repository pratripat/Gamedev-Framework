from tkinter import *
from tkinter import ttk, filedialog, simpledialog
import pygame
import json
import os
import time
import ast

# loads an image from a file and applies a colorkey for transparency
def load_image(path, colorkey=(0, 0, 0), scale=1):
    """
    Load an image from a file and apply a colorkey for transparency.
    
    :param path: Path to the image file.
    :param colorkey: Color to be treated as transparent.
    :param scale: Scale factor for the image.
    :return: Scaled image with colorkey applied.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"[UTILS] Image file '{path}' does not exist. (DEBUG)")
    
    image = pygame.image.load(path).convert()
    image.set_colorkey(colorkey)
    
    if scale != 1:
        width, height = image.get_size()
        image = pygame.transform.scale(image, (width * scale, height * scale))
    
    return image

# Init dummy Pygame display
pygame.init()
pygame.display.set_mode((1, 1))

# Constants
DISPLAY_WIDTH, DISPLAY_HEIGHT = 400, 400
DEFAULT_COLORKEY = (255, 0, 255)
COMPONENT_ORDER = [
    "PlayerTagComponent",
    "EnemyTagComponent",
    "Position",
    "Velocity",
    "AnimationComponent",
    "RenderComponent",
    "HurtBoxComponent",
    "HealthComponent",
    "CollisionComponent",
    "AnimationStateMachine",
    "WeaponComponent"
]

# Dummy schemas
COMPONENT_SCHEMAS = {
    "PlayerTagComponent": {},
    "EnemyTagComponent": {},
    "Position": {"x": {"type": float, "default": 0.0}, "y": {"type": float, "default": 0.0}},
    "Velocity": {"x": {"type": float, "default": 0.0}, "y": {"type": float, "default": 0.0}, "speed": {"type": float, "default": 4.0}},
    "AnimationComponent": {"entity": {"type": str, "default": "black_pawn"}, "animation_id": {"type": str, "default": "idle"}, "center": {"type": bool, "default": True}, "entity_type": {"type": str, "default": "chess_piece"}},
    "RenderComponent": {"image_file": {"type": str, "default": ""}, "offset_x": {"type": float, "default": 0.0}, "offset_y": {"type": float, "default": 0.0}, "center": {"type": bool, "default": True}},
    "HurtBoxComponent": {"offset_x": {"type": float, "default": 0.0}, "offset_y": {"type": float, "default": 0.0}, "width": {"type": float, "default": 16.0}, "height": {"type": float, "default": 64.0}, "center": {"type": bool, "default": True}},
    "HealthComponent": {"max_health": {"type": int, "default": 100}},
    "CollisionComponent": {"offset_x": {"type": float, "default": 0.0}, "offset_y": {"type": float, "default": 0.0}, "width": {"type": float, "default": 16.0}, "height": {"type": float, "default": 16.0}, "solid": {"type": bool, "default": False}, "center": {"type": bool, "default": True}},
    "AnimationStateMachine": {
        "animation_priority_list": {
            "type": list,
            "default": ["idle", "shoot", "moving", "damage", "death"]
        },
        "transitions": {
            "type": dict,
            "default": {
                "moving": {
                    "to_animation": "idle",
                    "cond": "vel_zero_check",  # Represented as string for editing
                    "self_dest": False
                }
            }
        }
    },
    "WeaponComponent": {
        "cooldown": {"type": float, "default": 1/6},
        "shoot_fn": {"type": str, "default": "shoot_spread"},  # Represented by function name
        "projectile_data": {
            "type": dict,
            "default": {
                "damage": 10,
                "speed": 5,
                "range": 100,
                "effects": [],
                "size": 1,
                "image_file": "data/graphics/images/projectile.png",
                "towards_player": True,
                "angle": 3
            }
        }
    }
}

class EntityEditor:
    def __init__(self, root, animation_handler):
        self.root = root
        self.animation_handler = animation_handler
        self.entities = {}
        self.selected_entity = None
        self.component_widgets = {}
        self.preview_animation = None
        self.preview_image = None
        self.preview_surface = pygame.Surface((DISPLAY_WIDTH, DISPLAY_HEIGHT))
        self.prev_time = time.time()
        self.root.title("Entity Editor")
        self.setup_ui()
        self.update_preview_loop()

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", background="#2e2e2e", foreground="white")
        style.configure("TButton", background="#444", foreground="white")

        self.root.configure(bg="#2e2e2e")
        self.root.geometry("1200x700")

        left = Frame(self.root, bg="#2e2e2e")
        left.pack(side=LEFT, fill=Y, padx=10, pady=10)

        Label(left, text="Entities", bg="#2e2e2e", fg="white", font=("Arial", 12, "bold")).pack()
        self.entity_listbox = Listbox(left, bg="#1e1e1e", fg="white", width=25)
        self.entity_listbox.pack(fill=Y, expand=True)
        self.entity_listbox.bind("<<ListboxSelect>>", self.select_entity)

        Button(left, text="Add Entity", command=self.add_entity).pack(fill=X, pady=2)
        Button(left, text="Rename Entity", command=self.rename_entity).pack(fill=X, pady=2)
        Button(left, text="Delete Entity", command=self.delete_entity).pack(fill=X, pady=2)

        center = Frame(self.root, bg="#2e2e2e")
        center.pack(side=LEFT, fill=BOTH, expand=True)

        top = Frame(center, bg="#2e2e2e")
        top.pack(fill=X)

        Label(top, text="Add Component:", bg="#2e2e2e", fg="white").pack(side=LEFT)
        self.component_selector = ttk.Combobox(top, values=COMPONENT_ORDER)
        self.component_selector.pack(side=LEFT, padx=5)
        Button(top, text="Add", command=self.add_component_to_entity).pack(side=LEFT)

        # self.fields_frame = Frame(center, bg="#2e2e2e")
        # self.fields_frame.pack(fill=BOTH, expand=True)
        right = Frame(self.root, bg="#1e1e1e", width=300)
        right.pack(side=RIGHT, fill=Y)
        Label(right, text="Preview", bg="#1e1e1e", fg="white", font=("Arial", 12, "bold")).pack()
        self.preview_canvas = Canvas(right, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, bg="black")
        self.preview_canvas.pack(padx=10, pady=10)

        # Component Fields (Scrollable)
        component_label = Label(center, text="Component Fields", fg="white", bg="#2e2e2e")
        component_label.pack(anchor=W, padx=10)

        # Canvas + scrollbar wrapper
        component_canvas = Canvas(center, bg="#2e2e2e", highlightthickness=0)
        component_canvas.pack(side=LEFT, fill=BOTH, expand=True)

        scrollbar = Scrollbar(center, orient=VERTICAL, command=component_canvas.yview)
        scrollbar.pack(side=RIGHT, fill=Y, expand=True)

        component_canvas.configure(yscrollcommand=scrollbar.set)

        # Inner frame where actual component widgets go
        self.fields_frame = Frame(component_canvas, bg="#2e2e2e")
        self.fields_frame.bind("<Configure>", lambda e: component_canvas.configure(scrollregion=component_canvas.bbox("all")))
        component_canvas.create_window((0, 0), window=self.fields_frame, anchor="nw")


        menu = Menu(self.root)
        self.root.config(menu=menu)
        file_menu = Menu(menu)
        menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save", command=self.save_data)
        file_menu.add_command(label="Load", command=self.load_data)

        def _on_mousewheel(event):
            component_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        component_canvas.bind_all("<MouseWheel>", _on_mousewheel)  # Windows/macOS
        component_canvas.bind_all("<Button-4>", lambda e: component_canvas.yview_scroll(-1, "units"))  # Linux scroll up
        component_canvas.bind_all("<Button-5>", lambda e: component_canvas.yview_scroll(1, "units"))   # Linux scroll down

        self.zoom_factor = 1.0  # Zoom in 2x by default

        zoom_label = Label(right, text="Zoom", fg="white", bg="#1e1e1e")
        zoom_label.pack()

        self.zoom_slider = Scale(right, from_=0.5, to=5.0, resolution=0.1, orient=HORIZONTAL,
                                bg="#1e1e1e", fg="white", troughcolor="#444", highlightthickness=0,
                                command=self.set_zoom)
        self.zoom_slider.set(self.zoom_factor)
        self.zoom_slider.pack()

    def add_entity(self):
        name = f"Entity_{len(self.entities)}"
        self.entities[name] = {}
        self.entity_listbox.insert(END, name)

    def rename_entity(self):
        sel = self.entity_listbox.curselection()
        if sel:
            old = self.entity_listbox.get(sel)
            new = simpledialog.askstring("Rename", "Enter new name:", initialvalue=old)
            if new and new not in self.entities:
                self.entities[new] = self.entities.pop(old)
                self.entity_listbox.delete(sel)
                self.entity_listbox.insert(sel, new)
                self.selected_entity = new
                self.update_component_ui()

    def delete_entity(self):
        sel = self.entity_listbox.curselection()
        if sel:
            name = self.entity_listbox.get(sel)
            del self.entities[name]
            self.entity_listbox.delete(sel)
            self.selected_entity = None
            self.clear_component_ui()

    def select_entity(self, e):
        sel = self.entity_listbox.curselection()
        if sel:
            self.selected_entity = self.entity_listbox.get(sel)
            self.update_component_ui()

    def add_component_to_entity(self):
        cname = self.component_selector.get()
        if not self.selected_entity or not cname:
            return
        entity = self.entities[self.selected_entity]
        if cname not in entity:
            entity[cname] = {k: v["default"] for k, v in COMPONENT_SCHEMAS[cname].items()}
            self.update_component_ui()

    def update_component_ui(self):
        self.clear_component_ui()
        if not self.selected_entity:
            return

        for comp_name, fields in self.entities[self.selected_entity].items():
            outer_frame = Frame(self.fields_frame, bg="#2e2e2e")
            outer_frame.pack(fill="x", padx=5, pady=5)  

            frame = LabelFrame(self.fields_frame, text=comp_name, fg="white", bg="#3a3a3a", padx=5, pady=5)
            frame.pack(fill="x", padx=5, pady=5)
            self.component_widgets[comp_name] = {}

            delete_btn = Button(
                outer_frame,
                text="x",
                command=lambda cname=comp_name: self.delete_component(cname),
                fg="white",
                bg="#ff5555",
                relief="groove"
            )
            delete_btn.pack(side=RIGHT, padx=5)

            schema = COMPONENT_SCHEMAS.get(comp_name, {})
            if not schema:
                # Show frame even if there are no fields
                Label(frame, text="(No editable fields)", bg="#3a3a3a", fg="#aaa").pack()
                continue    

            for key, value in fields.items():
                row = Frame(frame, bg="#3a3a3a")
                row.pack(fill="x", pady=2)
                Label(row, text=key, width=15, bg="#3a3a3a", fg="white").pack(side=LEFT)

                var_type = COMPONENT_SCHEMAS[comp_name][key]["type"]

                def make_callback(cname=comp_name, k=key):
                    def callback(*args, vtype=var_type):
                        var = self.component_widgets[cname][k]
                        val = var.get() if not isinstance(var, BooleanVar) else var.get()
                        try:
                            val = vtype(val)
                        except:
                            pass
                        self.entities[self.selected_entity][cname][k] = val
                        if cname == "AnimationComponent" and k in ("entity", "animation_id"):
                            self.update_preview_animation()
                        elif cname == "RenderComponent" and k == "image_file":
                            self.update_preview_animation()
                    return callback

                # Inside your loop where you create input fields per component field
                if var_type in [list, dict]:
                    text = Text(row, height=4, width=40, bg="#3a3a3a", fg="white", insertbackground="white")
                    text.insert("1.0", json.dumps(value, indent=2))  # Prettified
                    text.pack(side=LEFT, fill=X, expand=True)

                    def make_text_callback(cname=comp_name, k=key, t=text):
                        def callback(event=None):
                            try:
                                content = t.get("1.0", END).strip()
                                self.entities[self.selected_entity][cname][k] = ast.literal_eval(content)
                                if cname == "AnimationComponent" and k in ("entity", "animation_id"):
                                    self.update_preview_animation()
                            except Exception as e:
                                print(f"Error parsing {cname}.{k}: {e}")
                        return callback

                    text.bind("<FocusOut>", make_text_callback())
                    self.component_widgets[comp_name][key] = text

                elif var_type == bool:
                    var = BooleanVar(value=value)
                    chk = Checkbutton(row, variable=var, bg="#3a3a3a", selectcolor="black", activeforeground="white")
                    chk.pack(side=LEFT)
                    var.trace_add("write", make_callback())
                elif comp_name == "RenderComponent" and key == "image_file":
                    var = StringVar(value=value)

                    def open_dialog(v=var):
                        file_path = filedialog.askopenfilename()
                        if file_path:
                            v.set(file_path)

                    entry = Entry(row, textvariable=var)
                    entry.pack(side=LEFT, fill=X, expand=True)
                    Button(row, text="Browse", command=open_dialog).pack(side=LEFT)
                    entry.bind("<FocusOut>", make_callback())
                    entry.bind("<Return>", make_callback())
                else:
                    var = StringVar(value=str(value))
                    entry = Entry(row, textvariable=var)
                    entry.pack(side=LEFT, fill=X, expand=True)
                    entry.bind("<FocusOut>", make_callback())
                    entry.bind("<Return>", make_callback())

                self.component_widgets[comp_name][key] = var

    def update_preview_animation(self):
        comp = self.entities.get(self.selected_entity, {}).get("AnimationComponent")
        if comp:
            entity_id = comp.get("entity", "black_pawn")
            anim = comp.get("animation_id", "idle")
            self.preview_animation = self.animation_handler.get_animation(f"{entity_id}_{anim}")
            self.preview_image = None
            if self.preview_animation:
                self.preview_animation.frame = 0
            
        comp = self.entities.get(self.selected_entity, {}).get("RenderComponent")
        if comp and comp.get("image_file"):
            image_file = comp.get("image_file")
            if os.path.exists(image_file):
                self.preview_image = load_image(image_file)
                self.preview_animation = None
            else:
                print(f"[EntityEditor] Image file '{image_file}' does not exist. (DEBUG)")

    def clear_component_ui(self):
        for w in self.fields_frame.winfo_children():
            w.destroy()
        self.component_widgets.clear()

    def update_preview_loop(self):
        now = time.time()
        dt = now - self.prev_time
        self.prev_time = now

        self.preview_surface.fill((0, 0, 0))

        if self.preview_animation:
            comp = self.entities.get(self.selected_entity, {}).get("AnimationComponent", {})
            center = comp.get("center", True)
            width, height = self.preview_animation.image.get_size()
            pos = ((DISPLAY_WIDTH - width * self.zoom_factor) / 2, (DISPLAY_HEIGHT - height * self.zoom_factor) / 2) if center else (DISPLAY_WIDTH/2, DISPLAY_HEIGHT/2)
            self.preview_animation.run(None, None, 2)
            self.preview_animation.render(self.preview_surface, pos, scale=self.zoom_factor)
        
        if self.preview_image:
            comp = self.entities.get(self.selected_entity, {}).get("RenderComponent", {})
            center = comp.get("center", True)
            width, height = self.preview_image.get_size()
            pos = ((DISPLAY_WIDTH - width * self.zoom_factor) / 2, (DISPLAY_HEIGHT - height * self.zoom_factor) / 2) if center else (DISPLAY_WIDTH/2, DISPLAY_HEIGHT/2)
            self.preview_surface.blit(self.preview_image, pos)

        # Draw HurtBoxComponent
        hurt = self.entities.get(self.selected_entity, {}).get("HurtBoxComponent")
        if hurt:
            ox, oy = float(hurt.get("offset_x", 0))*self.zoom_factor, float(hurt.get("offset_y", 0))*self.zoom_factor
            w, h = float(hurt.get("width", 16)) * self.zoom_factor, float(hurt.get("height", 16)) * self.zoom_factor
            rect = pygame.Rect(DISPLAY_WIDTH / 2 + ox, DISPLAY_HEIGHT / 2 + oy, w, h)
            pygame.draw.rect(self.preview_surface, (255, 0, 0), rect, 1)
        
        # Draw CollisionBoxComponent
        collision = self.entities.get(self.selected_entity, {}).get("CollisionComponent")
        if collision:
            ox, oy = float(collision.get("offset_x", 0))*self.zoom_factor, float(collision.get("offset_y", 0))*self.zoom_factor
            w, h = float(collision.get("width", 16)) * self.zoom_factor, float(collision.get("height", 16)) * self.zoom_factor
            center = collision.get("center", False)
            if center:
                ox -= w / 2
                oy -= h / 2
            rect = pygame.Rect(DISPLAY_WIDTH / 2 + ox, DISPLAY_HEIGHT / 2 + oy, w, h)
            pygame.draw.rect(self.preview_surface, (0, 255, 0), rect, 1)

        # Crosshair
        pygame.draw.line(self.preview_surface, (255, 255, 255), (DISPLAY_WIDTH // 2 - 5, DISPLAY_HEIGHT // 2), (DISPLAY_WIDTH // 2 + 5, DISPLAY_HEIGHT // 2))
        pygame.draw.line(self.preview_surface, (255, 255, 255), (DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2 - 5), (DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2 + 5))

        pygame.image.save(self.preview_surface, "preview_temp.png")
        try:
            img = PhotoImage(file="preview_temp.png")
            self.preview_canvas.create_image(DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2, image=img)
            self.preview_canvas.image = img
        except:
            pass
        self.root.after(100, self.update_preview_loop)
    
    def set_zoom(self, val):
        try:
            self.zoom_factor = float(val)
            # print(f"[EntityEditor] Zoom factor set to {self.zoom_factor}. (DEBUG)")
        except ValueError:
            self.zoom_factor = 1.0
    
    def delete_component(self, comp_name):
        if self.selected_entity and comp_name in self.entities[self.selected_entity]:
            del self.entities[self.selected_entity][comp_name]
            self.update_component_ui()

    def save_data(self):
        if self.selected_entity:
            for comp, fields in self.component_widgets.items():
                for key, var in fields.items():
                    val = var.get()
                    schema_type = COMPONENT_SCHEMAS[comp][key]["type"]
                    try:
                        # Safely evaluate list/dict/string representations
                        if schema_type in [list, dict]:
                            val = ast.literal_eval(val)
                        else:
                            val = schema_type(val)
                    except Exception:
                        val = COMPONENT_SCHEMAS[comp][key]["default"]
                    self.entities[self.selected_entity][comp][key] = val

        file = filedialog.asksaveasfilename(defaultextension=".json")
        if file:
            with open(file, "w") as f:
                json.dump(self.entities, f, indent=4)

    def load_data(self):
        file = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file:
            with open(file, "r") as f:
                self.entities = json.load(f)
            self.entity_listbox.delete(0, END)
            for name in self.entities:
                self.entity_listbox.insert(END, name)    

# Example usage
if __name__ == "__main__":
    from scripts.systems.animation.animation_handler import AnimationHandler
    handler = AnimationHandler()
    root = Tk()
    EntityEditor(root, handler)
    root.mainloop()
