import cProfile
import pstats
import io
from scripts.game import Game
import pygame

def profile_run():
    game = Game()
    # Mock some basic events or just run for N frames
    # We override the main loop to run for a specific duration
    game.ctx.scene_manager.play_scene()
    
    frame_limit = 300 # Run for 300 frames (approx 5 seconds at 60fps)
    frames = 0
    
    print(f"Starting profile run for {frame_limit} frames...")
    
    try:
        while frames < frame_limit:
            game.calculate_dt()
            game.update()
            game.render()
            frames += 1
            
            # Allow quit event to work so we can stop early if needed
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    frames = frame_limit
    except Exception as e:
        print(f"Error during profile: {e}")
    finally:
        pygame.quit()

if __name__ == '__main__':
    pr = cProfile.Profile()
    pr.enable()
    profile_run()
    pr.disable()
    
    s = io.StringIO()
    sortby = pstats.SortKey.CUMULATIVE
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats(20) # Top 20 functions
    
    print("\n" + "="*50)
    print("TOP 20 MOST EXPENSIVE FUNCTIONS (CUMULATIVE TIME)")
    print("="*50)
    print(s.getvalue())
    
    # Also sort by internal time
    s_t = io.StringIO()
    ps_t = pstats.Stats(pr, stream=s_t).sort_stats(pstats.SortKey.TIME)
    ps_t.print_stats(10)
    print("\n" + "="*50)
    print("TOP 10 MOST EXPENSIVE FUNCTIONS (INTERNAL TIME)")
    print("="*50)
    print(s_t.getvalue())
