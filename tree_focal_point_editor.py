import pygame
import json
import os
from scripts.utils import load_images_from_spritesheet, SCALE

class TreeEditor:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Tree Focal Point Editor - [Left/Right: Switch Tree] [1/2/3: Select Point] [Mouse: Move Point] [Scroll: Resize Radius] [S: Save]")
        
        self.clock = pygame.time.get_ticks()
        self.font = pygame.font.SysFont("Arial", 16)
        
        # Load images
        self.images = load_images_from_spritesheet("data/graphics/spritesheets/foliage.png")
        self.current_tree_idx = 0
        
        # Config structure: { "tree_idx": [ {"pos": [x, y], "radius": r}, ... ] }
        self.config_path = "data/config/foliage_wind_custom.json"
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                self.config = json.load(f)
        else:
            self.config = {}

        self.selected_point_idx = 0
        self.running = True

    def get_current_data(self):
        idx_str = str(self.current_tree_idx)
        if idx_str not in self.config:
            w, h = self.images[self.current_tree_idx].get_size()
            self.config[idx_str] = [
                {"pos": [w*0.2, h*0.4], "radius": 15},
                {"pos": [w*0.8, h*0.4], "radius": 15},
                {"pos": [w*0.5, h*0.2], "radius": 15}
            ]
        return self.config[idx_str]

    def run(self):
        while self.running:
            self.screen.fill((50, 50, 50))
            dt = pygame.time.get_ticks() - self.clock
            
            tree_img = self.images[self.current_tree_idx]
            tree_data = self.get_current_data()
            
            # Draw Tree (Scaled up for easier editing)
            scale = 4
            view_surf = pygame.transform.scale(tree_img, (tree_img.get_width() * scale, tree_img.get_height() * scale))
            tree_rect = view_surf.get_rect(center=(400, 300))
            self.screen.blit(view_surf, tree_rect)
            
            # Draw Circles
            for i, point in enumerate(tree_data):
                px, py = point["pos"]
                pr = point["radius"]
                
                # Convert tree local to screen
                screen_px = tree_rect.left + px * scale
                screen_py = tree_rect.top + py * scale
                screen_pr = pr * scale
                
                color = (255, 255, 0) if i == self.selected_point_idx else (200, 200, 200)
                # Center
                pygame.draw.circle(self.screen, color, (int(screen_px), int(screen_py)), 4)
                # Boundary
                pygame.draw.circle(self.screen, color, (int(screen_px), int(screen_py)), int(screen_pr), 1)
                
                # Label
                label = self.font.render(f"P{i+1}: R={pr:.1f}", True, color)
                self.screen.blit(label, (screen_px + 10, screen_py - 10))

            # UI Info
            info_lines = [
                f"Tree: {self.current_tree_idx + 1} / {len(self.images)}",
                f"Selected Point: {self.selected_point_idx + 1}",
                "",
                "CONTROLS:",
                "LEFT / RIGHT ARROWS: Switch Tree",
                "1, 2, 3: Select Point",
                "MOUSE CLICK: Place Selected Point",
                "MOUSE SCROLL: Adjust Radius",
                "S: Save Config",
                "ESC: Exit"
            ]
            for i, line in enumerate(info_lines):
                text = self.font.render(line, True, (255, 255, 255))
                self.screen.blit(text, (10, 10 + i * 20))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_RIGHT:
                        self.current_tree_idx = (self.current_tree_idx + 1) % len(self.images)
                    elif event.key == pygame.K_LEFT:
                        self.current_tree_idx = (self.current_tree_idx - 1) % len(self.images)
                    elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3]:
                        self.selected_point_idx = event.key - pygame.K_1
                    elif event.key == pygame.K_s:
                        with open(self.config_path, "w") as f:
                            json.dump(self.config, f, indent=4)
                        print(f"Saved config to {self.config_path}")

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1: # Left click
                        mx, my = event.pos
                        if tree_rect.collidepoint(mx, my):
                            # Convert screen to tree local
                            lx = (mx - tree_rect.left) / scale
                            ly = (my - tree_rect.top) / scale
                            tree_data[self.selected_point_idx]["pos"] = [lx, ly]
                    
                    elif event.button == 4: # Scroll up
                        tree_data[self.selected_point_idx]["radius"] += 1
                    elif event.button == 5: # Scroll down
                        tree_data[self.selected_point_idx]["radius"] = max(1, tree_data[self.selected_point_idx]["radius"] - 1)

            pygame.display.flip()
        
        pygame.quit()

if __name__ == "__main__":
    TreeEditor().run()
