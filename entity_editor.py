from tkinter import *
from tkinter import ttk, filedialog, simpledialog
import pygame
import json
import os
import time

# Init dummy Pygame display
pygame.init()
pygame.display.set_mode((1, 1))

# Constants
DISPLAY_WIDTH, DISPLAY_HEIGHT = 200, 200
DEFAULT_COLORKEY = (255, 0, 255)
COMPONENT_ORDER = ["Position", "Velocity", "HurtBox", "AnimationComponent", "RenderComponent"]

# Dummy schemas
COMPONENT_SCHEMAS = {
    "Position": {"x": {"type": float, "default": 0.0}, "y": {"type": float, "default": 0.0}},
    "Velocity": {"vx": {"type": float, "default": 0.0}, "vy": {"type": float, "default": 0.0}, "speed": {"type": float, "default": 4.0}},
    "HurtBox": {"offset_x": {"type": float, "default": 0.0}, "offset_y": {"type": float, "default": 0.0}, "width": {"type": float, "default": 16.0}, "height": {"type": float, "default": 64.0}},
    "AnimationComponent": {"entity": {"type": str, "default": "black_pawn"}, "animation_id": {"type": str, "default": "idle"}, "center": {"type": bool, "default": True}},
    "RenderComponent": {"image_file": {"type": str, "default": ""}}
}

class EntityEditor:
    def __init__(self, root, animation_handler):
        self.root = root
        self.animation_handler = animation_handler
        self.entities = {}
        self.selected_entity = None
        self.component_widgets = {}
        self.preview_animation = None
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

        self.fields_frame = Frame(center, bg="#2e2e2e")
        self.fields_frame.pack(fill=BOTH, expand=True)

        right = Frame(self.root, bg="#1e1e1e", width=300)
        right.pack(side=RIGHT, fill=Y)
        Label(right, text="Preview", bg="#1e1e1e", fg="white", font=("Arial", 12, "bold")).pack()
        self.preview_canvas = Canvas(right, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, bg="black")
        self.preview_canvas.pack(padx=10, pady=10)

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

    # def update_component_ui(self):
    #     self.clear_component_ui()
    #     if not self.selected_entity:
    #         return

    #     for comp_name, fields in self.entities[self.selected_entity].items():
    #         frame = LabelFrame(self.fields_frame, text=comp_name, fg="white", bg="#3a3a3a", padx=5, pady=5)
    #         frame.pack(fill="x", padx=5, pady=5)
    #         self.component_widgets[comp_name] = {}

    #         for key, value in fields.items():
    #             row = Frame(frame, bg="#3a3a3a")
    #             row.pack(fill="x", pady=2)
    #             Label(row, text=key, width=15, bg="#3a3a3a", fg="white").pack(side=LEFT)

    #             var_type = COMPONENT_SCHEMAS[comp_name][key]["type"]
    #             # Save every change live to self.entities[selected_entity]
    #             def make_callback(cname=comp_name, k=key):
    #                 def callback(varname, index, mode, vtype=var_type):
    #                     var = self.component_widgets[cname][k]
    #                     val = var.get() if not isinstance(var, BooleanVar) else var.get()
    #                     try:
    #                         val = vtype(val)
    #                     except:
    #                         pass
    #                     self.entities[self.selected_entity][cname][k] = val
    #                     if cname == "AnimationComponent" and k in ("entity", "animation_id"):
    #                         self.update_preview_animation()
    #                 return callback

    #             if var_type == bool:
    #                 var = BooleanVar(value=value)
    #                 chk = Checkbutton(row, variable=var, bg="#3a3a3a", selectcolor="black", activeforeground="white")
    #                 chk.pack(side=LEFT)
    #                 var.trace_add("write", make_callback())
    #             elif comp_name == "RenderComponent" and key == "image_file":
    #                 var = StringVar(value=value)

    #                 def open_dialog(v=var):
    #                     file_path = filedialog.askopenfilename()
    #                     if file_path:
    #                         v.set(file_path)

    #                 Entry(row, textvariable=var).pack(side=LEFT, fill=X, expand=True)
    #                 Button(row, text="Browse", command=open_dialog).pack(side=LEFT)
    #                 var.trace_add("write", make_callback())
    #             else:
    #                 var = StringVar(value=str(value))
    #                 Entry(row, textvariable=var).pack(side=LEFT, fill=X, expand=True)
    #                 var.trace_add("write", make_callback())

    #             self.component_widgets[comp_name][key] = var

    #     # Refresh animation based on current values
    #     self.update_preview_animation()

    def update_component_ui(self):
        self.clear_component_ui()
        if not self.selected_entity:
            return

        for comp_name, fields in self.entities[self.selected_entity].items():
            frame = LabelFrame(self.fields_frame, text=comp_name, fg="white", bg="#3a3a3a", padx=5, pady=5)
            frame.pack(fill="x", padx=5, pady=5)
            self.component_widgets[comp_name] = {}

            for key, value in fields.items():
                row = Frame(frame, bg="#3a3a3a")
                row.pack(fill="x", pady=2)
                Label(row, text=key, width=15, bg="#3a3a3a", fg="white").pack(side=LEFT)

                var_type = COMPONENT_SCHEMAS[comp_name][key]["type"]

                def make_callback(cname=comp_name, k=key):
                    def callback(event=None, vtype=var_type):
                        var = self.component_widgets[cname][k]
                        val = var.get() if not isinstance(var, BooleanVar) else var.get()
                        try:
                            val = vtype(val)
                        except:
                            pass
                        self.entities[self.selected_entity][cname][k] = val
                        if cname == "AnimationComponent" and k in ("entity", "animation_id"):
                            self.update_preview_animation()
                    return callback

                if var_type == bool:
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
            if self.preview_animation:
                self.preview_animation.frame = 0

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
            pos = ((DISPLAY_WIDTH - width) / 2, (DISPLAY_HEIGHT - height) / 2) if center else (DISPLAY_WIDTH/2, DISPLAY_HEIGHT/2)
            self.preview_animation.run(None, None, 2)
            self.preview_animation.render(self.preview_surface, pos)

        # Draw HurtBox
        hurt = self.entities.get(self.selected_entity, {}).get("HurtBox")
        if hurt:
            ox, oy = float(hurt["offset_x"]), float(hurt["offset_y"])
            w, h = float(hurt["width"]), float(hurt["height"])
            rect = pygame.Rect(DISPLAY_WIDTH // 2 + ox, DISPLAY_HEIGHT // 2 + oy, w, h)
            pygame.draw.rect(self.preview_surface, (255, 0, 0), rect, 1)

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

# Example usage
if __name__ == "__main__":
    from scripts.systems.animation.animation_handler import AnimationHandler
    handler = AnimationHandler()
    root = Tk()
    EntityEditor(root, handler)
    root.mainloop()
