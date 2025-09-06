# -*- coding: utf-8 -*-
"""
Map Management System

Handles all aspects of the game map including:
- Stage loading with hardcoded Stage 1 and procedural generation for others
- Tile-based collision detection and passability checking
- Destructible terrain system with delayed destruction animations
- Grid-pixel coordinate conversion utilities
- Visual rendering with sprite-based and programmatic fallback systems
- Base protection with automatic 3x3 brick wall placement

The map uses a 16x14 grid system where each cell represents a TILE_SIZE x TILE_SIZE
pixel area. Different tile types have different behaviors for movement, bullets,
and visual rendering.

Tile Types:
- TILE_EMPTY: Passable, no visual
- TILE_BRICK: Destructible by all bullets, blocks movement
- TILE_STEEL: Destructible only by POWER_SUPER bullets, blocks movement
- TILE_WATER: Bullets pass through, blocks tanks, visual water pattern
- TILE_FOREST: Everything passes through, provides visual cover
- TILE_ICE: Passable terrain (unused in current stages)
- TILE_BASE: Game over if destroyed, never actually removed from map
"""

import pyxel
from constants import *

class MapManager:
    """
    Manages the game map, collision detection, and tile-based terrain system.
    
    Responsibilities:
    - Load and generate stage layouts (hardcoded Stage 1, procedural others)
    - Provide tile-based collision detection for tanks and bullets
    - Handle destructible terrain with delayed destruction animations
    - Convert between pixel and grid coordinate systems
    - Render map tiles with sprites or programmatic fallback
    - Manage base protection and special tile behaviors
    
    Attributes:
        current_stage (int): Currently loaded stage number (1-based)
        map_data (list[list[int]]): 2D grid of tile type constants
        base_position (tuple[int, int]): Grid coordinates of player base
        spawn_positions (list[tuple[int, int]]): Enemy spawn points in grid coords
        delayed_destructions (list[dict]): Tiles scheduled for destruction with timers
        explosion_manager (ExplosionManager): Reference for explosion animations
        game_context (GameContext): Reference to global game context
    """
    def __init__(self) -> None:
        """
        Initialize the map manager with default Stage 1.
        
        Sets up the grid system, defines key positions, and loads the first stage.
        The base is positioned at the bottom center for optimal player defense,
        while enemy spawn points are distributed across the top edge.
        """
        # Stage management
        self.current_stage: int = 1  # Start with Stage 1
        
        # Map data storage - 2D grid of tile type constants
        # Grid dimensions: MAP_WIDTH x MAP_HEIGHT (16x14 tiles)
        self.map_data: list[list[int]] = []
        
        # Key positions in grid coordinates (not pixels)
        self.base_position: tuple[int, int] = (7, 13)  # Bottom center - player base location
        self.spawn_positions: list[tuple[int, int]] = [(0, 0), (6, 0), (12, 0)]  # Top edge enemy spawns
        
        # Delayed destruction system for explosion animations
        # Each entry: {'x': grid_x, 'y': grid_y, 'timer': frames_remaining}
        self.delayed_destructions: list[dict] = []
        
        # External system references (set by game_manager after initialization)
        self.explosion_manager = None  # For explosion animations
        self.game_context = None       # For global game state
        
        # Load initial stage
        self.load_stage(self.current_stage)
    
    
    
    
    
    def load_stage(self, stage_num: int) -> None:
        """
        Load and initialize a specific stage with its terrain layout.
        
        Stage system:
        - Stage 1: Hardcoded layout with specific obstacle placement for tutorial
        - Stages 2+: Procedurally generated with increasing difficulty
        - All stages: Automatic base placement with 3x3 protective brick wall
        
        Args:
            stage_num (int): Stage number to load (1-based)
        """
        # Update current stage tracking
        self.current_stage = stage_num
        
        # Initialize empty map grid filled with passable tiles
        self.map_data = [[TILE_EMPTY for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
        
        # Generate stage layout based on stage number
        if stage_num == 1:
            # Stage 1 uses carefully designed hardcoded layout for tutorial/introduction
            self.create_stage_1()
        else:
            # All other stages use procedural generation with stage-based difficulty scaling
            self.create_procedural_stage(stage_num)
        
        # Add player base with protective walls for all stages
        # This ensures base is always surrounded by destructible barriers
        self.place_base()
    
    def create_stage_1(self) -> None:
        """
        ユーザー修正版の正確なレイアウトでStage 1を作成。
        """
        # Row 2: " R R R WW R R R"
        for x in [1, 3, 5, 10, 12, 14]:
            self.map_data[1][x] = TILE_BRICK
        for x in [7, 8]:
            self.map_data[1][x] = TILE_WATER

        # Row 3: " R R RWWWWR R R"
        for x in [1, 3, 5, 10, 12, 14]:
            self.map_data[2][x] = TILE_BRICK
        for x in [6, 7, 8, 9]:
            self.map_data[2][x] = TILE_WATER

        # Row 4: " R R R WW R R R"
        for x in [1, 3, 5, 10, 12, 14]:
            self.map_data[3][x] = TILE_BRICK
        for x in [7, 8]:
            self.map_data[3][x] = TILE_WATER

        # Row 5: " R R        R R"
        for x in [1, 3, 12, 14]:
            self.map_data[4][x] = TILE_BRICK

        # Row 6: "    R II R"
        for x in [5]:
            self.map_data[5][x] = TILE_BRICK
        for x in [7, 8]:
            self.map_data[5][x] = TILE_STEEL
        for x in [10]:
            self.map_data[5][x] = TILE_BRICK

        # Row 7: "I RR I II I RR I"
        for x in [2, 3, 12, 13]:
            self.map_data[6][x] = TILE_BRICK
        for x in [0, 5, 7, 8, 10, 15]:
            self.map_data[6][x] = TILE_STEEL

        # Row 8: "    R    R"
        for x in [5, 10]:
            self.map_data[7][x] = TILE_BRICK

        # Row 9: " R R   TT   R R"
        for x in [1, 3, 12, 14]:
            self.map_data[8][x] = TILE_BRICK
        for x in [7, 8]:
            self.map_data[8][x] = TILE_FOREST

        # Row 10: " RRR RTTTTR RRR"
        for x in [1, 2, 3, 5, 10, 12, 13, 14]:
            self.map_data[9][x] = TILE_BRICK
        for x in [6, 7, 8, 9]:
            self.map_data[9][x] = TILE_FOREST

        # Row 11: " R R   TT   R R"
        for x in [1, 3, 12, 14]:
            self.map_data[10][x] = TILE_BRICK
        for x in [7, 8]:
            self.map_data[10][x] = TILE_FOREST

        # Row 12: " R R        R R"
        for x in [1, 3, 12, 14]:
            self.map_data[11][x] = TILE_BRICK

        # Row 13: " R R  RRR   R R"
        for x in [1, 3, 6, 7, 8, 12, 14]:
            self.map_data[12][x] = TILE_BRICK

        # Row 14: "     RBR" - 基地は place_base() で自動配置
        for x in [6, 8]:
            self.map_data[13][x] = TILE_BRICK
    
    
    def create_procedural_stage(self, stage_num: int) -> None:
        """
        Generate a procedural stage layout with difficulty scaling.
        
        Procedural generation features:
        - Deterministic: Same stage number always generates same layout
        - Difficulty scaling: Higher stages have more obstacles
        - Safe placement: Avoids blocking spawn points and base area
        - Varied terrain: Mix of destructible, indestructible, and special tiles
        
        Generation parameters by stage:
        - Brick walls: 15 + (stage * 2) - main destructible obstacles
        - Steel walls: 3 + stage - indestructible strategic barriers
        - Water patches: 2 fixed patches - tactical movement barriers
        
        Args:
            stage_num (int): Stage number for difficulty scaling and seed
        """
        import random
        # Use stage number as seed for deterministic generation
        # This ensures same stage always generates same layout
        random.seed(stage_num)
        
        # Generate brick walls - primary destructible obstacles
        # Count scales with stage number for increasing difficulty
        brick_count = 15 + stage_num * 2  # Stage 2: 19, Stage 3: 21, etc.
        for _ in range(brick_count):
            # Random placement within valid map area
            x = random.randint(0, MAP_WIDTH - 1)
            y = random.randint(2, MAP_HEIGHT - 4)  # Avoid top/bottom edges
            
            # Only place if location doesn't interfere with key areas
            if self.is_valid_placement(x, y):
                self.map_data[y][x] = TILE_BRICK
        
        # Generate steel walls - indestructible strategic barriers
        # Fewer than brick walls but scale with stage difficulty
        steel_count = 3 + stage_num  # Stage 2: 5, Stage 3: 6, etc.
        for _ in range(steel_count):
            x = random.randint(0, MAP_WIDTH - 1)
            y = random.randint(2, MAP_HEIGHT - 4)
            
            # Place steel only in valid locations
            if self.is_valid_placement(x, y):
                self.map_data[y][x] = TILE_STEEL
        
        # Generate water patches - tactical movement barriers
        # Fixed count of 2 patches regardless of stage (for balance)
        for _ in range(2):
            # Choose random location for 2x2 water patch
            start_x = random.randint(1, MAP_WIDTH - 3)   # Leave room for 2x2 patch
            start_y = random.randint(3, MAP_HEIGHT - 5)  # Avoid edges and base area
            
            # Create 2x2 water patch
            for dx in range(2):
                for dy in range(2):
                    x, y = start_x + dx, start_y + dy
                    
                    # Ensure patch stays within map bounds
                    if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT:
                        # Only place water in valid locations
                        if self.is_valid_placement(x, y):
                            self.map_data[y][x] = TILE_WATER
        
        # Generate forest patches - visual cover areas
        # Count scales with stage number for variety
        forest_patches = 1 + stage_num // 3  # Stage 2-4: 1, Stage 5-7: 2, etc.
        for _ in range(forest_patches):
            # Choose random location for 3x3 forest patch
            start_x = random.randint(1, MAP_WIDTH - 4)   # Leave room for 3x3 patch
            start_y = random.randint(3, MAP_HEIGHT - 5)  # Avoid edges and base area
            
            # Create 3x3 forest patch
            for dx in range(3):
                for dy in range(3):
                    x, y = start_x + dx, start_y + dy
                    
                    # Ensure patch stays within map bounds
                    if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT:
                        # Only place forest in valid locations
                        if self.is_valid_placement(x, y):
                            self.map_data[y][x] = TILE_FOREST
    
    def is_valid_placement(self, x: int, y: int) -> bool:
        """
        Check if a grid position is valid for procedural tile placement.
        
        Placement rules:
        - Must not interfere with enemy spawn points (3x3 area around each)
        - Must not interfere with player base area (5x5 area around base)
        - Must not overwrite existing non-empty tiles
        - Ensures gameplay remains fair and accessible
        
        Args:
            x (int): Grid X coordinate to test
            y (int): Grid Y coordinate to test
            
        Returns:
            bool: True if position is safe for tile placement, False otherwise
        """
        # Check proximity to enemy spawn points
        # Keep 3x3 area clear around each spawn point for enemy movement
        for spawn_x, spawn_y in self.spawn_positions:
            if abs(x - spawn_x) <= 1 and abs(y - spawn_y) <= 1:
                return False  # Too close to enemy spawn
        
        # Check proximity to player base
        # Keep 5x5 area clear around base for base protection and player movement
        base_x, base_y = self.base_position
        if abs(x - base_x) <= 2 and abs(y - base_y) <= 2:
            return False  # Too close to player base
        
        # Check if position is already occupied
        # Don't overwrite existing obstacles or special tiles
        if self.map_data[y][x] != TILE_EMPTY:
            return False  # Position already has a tile
        
        # Position is safe for placement
        return True
    
    
    def place_base(self) -> None:
        """
        Place the player base with automatic 3x3 protective brick wall.
        
        Base protection system:
        - Base tile placed at designated base_position
        - 3x3 brick wall surrounds base for initial protection
        - Only places protective blocks on empty tiles within map bounds
        - Pattern ensures base has destructible defense that can be strategically managed
        
        Protective wall pattern:
        BBB
        BKB  (where K = base, B = brick)
        BBB
        
        This gives players initial defense while allowing enemies to eventually
        break through if the player doesn't actively defend.
        """
        base_x, base_y = self.base_position
        
        # Place the base tile itself
        self.map_data[base_y][base_x] = TILE_BASE
        
        # Create 3x3 protective brick wall around base
        for dy in range(-1, 2):  # -1, 0, 1 (relative to base)
            for dx in range(-1, 2):  # -1, 0, 1 (relative to base)
                # Skip center position - that's where the base is located
                if dx == 0 and dy == 0:
                    continue
                    
                # Calculate absolute grid coordinates for protective block
                block_x = base_x + dx
                block_y = base_y + dy
                
                # Only place protective blocks within map bounds on empty tiles
                # This prevents overwriting existing terrain or going off-map
                if (0 <= block_x < MAP_WIDTH and 0 <= block_y < MAP_HEIGHT and 
                    self.map_data[block_y][block_x] == TILE_EMPTY):
                    self.map_data[block_y][block_x] = TILE_BRICK
    
    def get_tile(self, x: int, y: int) -> int:
        """
        Get the tile type at a specific grid coordinate.
        
        Boundary handling:
        - Returns actual tile type for valid coordinates
        - Returns TILE_STEEL for out-of-bounds coordinates (acts as map border)
        - This creates invisible steel walls around map edges for collision
        
        Args:
            x (int): Grid X coordinate
            y (int): Grid Y coordinate
            
        Returns:
            int: Tile type constant (TILE_EMPTY, TILE_BRICK, etc.)
        """
        # Return actual tile type if coordinates are within map bounds
        if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT:
            return self.map_data[y][x]
        
        # Return steel for out-of-bounds access - creates indestructible map border
        return TILE_STEEL
    
    def set_tile(self, x: int, y: int, tile_type: int) -> None:
        """
        Set the tile type at a specific grid coordinate.
        
        Only modifies tiles within valid map bounds. Out-of-bounds
        coordinates are silently ignored to prevent array access errors.
        
        Args:
            x (int): Grid X coordinate
            y (int): Grid Y coordinate  
            tile_type (int): Tile type constant to set
        """
        # Only modify tiles within valid map bounds
        if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT:
            self.map_data[y][x] = tile_type
    
    def is_passable(self, x: int, y: int) -> bool:
        """
        Check if a tile position allows tank movement.
        
        Passability rules:
        - TILE_EMPTY: Always passable (empty space)
        - TILE_FOREST: Always passable (provides visual cover only)
        - TILE_ICE: Always passable (unused in current stages)
        - TILE_WATER: Blocks tanks (but bullets can pass through)
        - TILE_BRICK/TILE_STEEL: Block tanks (solid obstacles)
        - TILE_BASE: Blocks tanks (base is solid)
        - Tiles scheduled for destruction: Blocked during explosion animation
        
        The delayed destruction system prevents movement through exploding
        tiles until the animation completes, maintaining gameplay consistency.
        
        Args:
            x (int): Grid X coordinate to check
            y (int): Grid Y coordinate to check
            
        Returns:
            bool: True if tanks can move through this position, False otherwise
        """
        # Get the tile type at this position
        tile = self.get_tile(x, y)
        
        # Check if this tile is currently exploding (scheduled for destruction)
        # During explosion animation, tile should block movement until destruction completes
        is_scheduled_for_destruction = any(
            d['x'] == x and d['y'] == y 
            for d in self.delayed_destructions
        )
        
        if is_scheduled_for_destruction:
            # Block movement during explosion animation for gameplay consistency
            return False
        
        # Check tile type for normal passability
        # Only empty space, forest (visual cover), and ice allow tank movement
        return tile in [TILE_EMPTY, TILE_FOREST, TILE_ICE]
    
    def can_destroy(self, x: int, y: int, power_level: int = POWER_NORMAL) -> bool:
        """
        Check if a tile can be destroyed by a bullet of given power level.
        
        Destruction rules by tile type:
        - TILE_BRICK: Always destructible by any bullet power
        - TILE_STEEL: Only destructible by POWER_SUPER bullets
        - TILE_BASE: Never destructible (triggers game over instead)
        - TILE_WATER/TILE_FOREST/TILE_EMPTY/TILE_ICE: Not destructible
        
        Power level affects steel wall destruction:
        - POWER_NORMAL/FAST_SHOT/DOUBLE_SHOT: Cannot destroy steel
        - POWER_SUPER: Can destroy both brick and steel
        
        Args:
            x (int): Grid X coordinate to check
            y (int): Grid Y coordinate to check
            power_level (int, optional): Bullet power level. Defaults to POWER_NORMAL.
            
        Returns:
            bool: True if tile can be destroyed by this power level, False otherwise
        """
        tile = self.get_tile(x, y)
        
        # Brick walls are always destructible by any bullet
        if tile == TILE_BRICK:
            return True
        
        # Steel walls require super bullets to destroy
        elif tile == TILE_STEEL and power_level >= POWER_SUPER:
            return True
        
        # Base tile triggers game over but is never "destroyed" in map data
        # This is handled separately in bullet collision detection
        elif tile == TILE_BASE:
            return False  # Base destruction handled by game over logic
        
        # All other tiles (water, forest, empty, ice) are indestructible
        return False
    
    def destroy_tile(self, x: int, y: int) -> bool:
        """
        Immediately destroy a tile if it can be destroyed.
        
        This is used for instant destruction effects where no animation delay
        is needed. For explosion animations, use schedule_tile_destruction() instead.
        
        Args:
            x (int): Grid X coordinate of tile to destroy
            y (int): Grid Y coordinate of tile to destroy
            
        Returns:
            bool: True if tile was destroyed, False if indestructible
        """
        # Check if tile can be destroyed by default power level
        if self.can_destroy(x, y):
            # Replace with empty tile (remove obstacle)
            self.set_tile(x, y, TILE_EMPTY)
            return True  # Destruction successful
        
        return False  # Tile could not be destroyed
    
    def schedule_tile_destruction(self, x: int, y: int, delay_frames: int) -> bool:
        """
        Schedule a tile for destruction after a specified delay.
        
        This system allows explosion animations to play before the tile
        actually disappears, creating better visual feedback. During the
        delay period, the tile remains visually present but blocks movement
        to prevent gameplay inconsistencies.
        
        Args:
            x (int): Grid X coordinate of tile to schedule
            y (int): Grid Y coordinate of tile to schedule
            delay_frames (int): Number of frames to wait before destruction
            
        Returns:
            bool: True if tile was scheduled for destruction, False if indestructible
        """
        # Only schedule destructible tiles
        if self.can_destroy(x, y):
            # Add to delayed destruction queue
            self.delayed_destructions.append({
                'x': x,           # Grid X coordinate
                'y': y,           # Grid Y coordinate
                'timer': delay_frames  # Countdown timer in frames
            })
            return True  # Successfully scheduled
        
        return False  # Tile cannot be destroyed
    
    def update_delayed_destructions(self) -> None:
        """
        Update timers for all scheduled tile destructions.
        
        Called once per frame to countdown destruction timers. When a
        timer reaches zero, the tile is immediately destroyed (set to empty).
        This system coordinates with explosion animations to ensure proper
        visual-gameplay synchronization.
        
        Processing:
        1. Decrease timer for each scheduled destruction
        2. Remove tile from map when timer reaches zero
        3. Clean up completed destructions from the queue
        """
        # Process all scheduled destructions (use slice copy to allow modification during iteration)
        for destruction in self.delayed_destructions[:]:
            # Countdown timer
            destruction['timer'] -= 1
            
            # Check if destruction should occur this frame
            if destruction['timer'] <= 0:
                # Actually destroy the tile now
                self.set_tile(destruction['x'], destruction['y'], TILE_EMPTY)
                
                # Remove this destruction from the queue
                self.delayed_destructions.remove(destruction)
    
    def pixel_to_grid(self, pixel_x: float, pixel_y: float) -> tuple[int, int]:
        """
        Convert pixel coordinates to grid coordinates.
        
        Essential for collision detection and tile access. The game uses
        a grid system where each tile occupies TILE_SIZE x TILE_SIZE pixels.
        
        Args:
            pixel_x (float): X coordinate in pixels
            pixel_y (float): Y coordinate in pixels
            
        Returns:
            tuple[int, int]: Grid coordinates as (grid_x, grid_y)
        """
        return int(pixel_x // TILE_SIZE), int(pixel_y // TILE_SIZE)
    
    def grid_to_pixel(self, grid_x: int, grid_y: int) -> tuple[int, int]:
        """
        Convert grid coordinates to pixel coordinates.
        
        Used for positioning entities and visual elements based on grid
        positions. Returns the top-left pixel coordinate of the grid cell.
        
        Args:
            grid_x (int): Grid X coordinate
            grid_y (int): Grid Y coordinate
            
        Returns:
            tuple[int, int]: Pixel coordinates as (pixel_x, pixel_y)
        """
        return grid_x * TILE_SIZE, grid_y * TILE_SIZE
    
    def draw(self) -> None:
        """
        Render the entire map to the screen with tile-based graphics.
        
        Rendering system:
        - Dual-mode: Sprite-based rendering with programmatic fallback
        - Sprite mode: Uses tiles from my_resource.pyxres for visual consistency
        - Programmatic mode: Draws tiles with patterns when sprites unavailable
        - Only non-empty tiles are rendered for performance
        
        Sprite coordinates (from my_resource.pyxres):
        - TILE_BRICK: [0,48] - Destructible brown brick walls
        - TILE_STEEL: [16,48] - Indestructible grey steel walls  
        - TILE_WATER: [32,48] - Blue water areas (blocks tanks)
        - TILE_FOREST: [48,48] - Green forest areas (visual cover)
        - TILE_ICE: [64,48] - Ice terrain (unused in current stages)
        - TILE_BASE: [80,48] - Player base (yellow with eagle symbol)
        
        Performance: Renders only visible non-empty tiles in map grid.
        """
        # Detect sprite availability by checking image bank dimensions
        sprite_width = pyxel.images[0].width
        sprite_height = pyxel.images[0].height
        # Require minimum dimensions for sprite-based rendering
        use_sprites = sprite_width >= 80 and sprite_height >= 64
        
        # Render all tiles in the map grid
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                # Convert grid coordinates to screen pixel coordinates
                pixel_x, pixel_y = self.grid_to_pixel(x, y)
                tile_type = self.map_data[y][x]
                
                # Skip empty tiles for performance (no visual representation needed)
                if tile_type != TILE_EMPTY:
                    if use_sprites:
                        # Sprite-based rendering using my_resource.pyxres
                        if tile_type == TILE_BRICK:
                            # Brown destructible brick walls
                            pyxel.blt(pixel_x, pixel_y, 0, 0, 48, 16, 16)    # [0,48]
                        elif tile_type == TILE_STEEL:
                            # Grey indestructible steel walls
                            pyxel.blt(pixel_x, pixel_y, 0, 16, 48, 16, 16)   # [16,48]
                        elif tile_type == TILE_WATER:
                            # Animated water waves - alternate between 0° and 90° rotation
                            # Create wave effect by cycling rotation based on time and position
                            wave_cycle = (pyxel.frame_count // 12) % 2  # Switch every 0.2 seconds (12 frames at 60 FPS)
                            position_offset = (x + y) % 2  # Offset pattern based on tile position
                            
                            # Combine time cycle and position for natural wave pattern
                            if (wave_cycle + position_offset) % 2 == 0:
                                rotation_angle = 0    # 0° rotation
                            else:
                                rotation_angle = 180  # 180° rotation
                                
                            pyxel.blt(pixel_x, pixel_y, 0, 32, 48, 16, 16, 0, rotation_angle)   # [32,48] animated waves
                        elif tile_type == TILE_FOREST:
                            # Skip forest in main draw - rendered in overlay for cover effect
                            pass
                        elif tile_type == TILE_ICE:
                            # Ice terrain (passable, unused in current stages)
                            pyxel.blt(pixel_x, pixel_y, 0, 64, 48, 16, 16)   # [64,48]
                        elif tile_type == TILE_BASE:
                            # Player base with eagle symbol
                            pyxel.blt(pixel_x, pixel_y, 0, 80, 48, 16, 16)   # [80,48]
                        else:
                            # Debug output for unknown tile types
                            print(f"DEBUG: Unknown tile_type {tile_type} at ({x},{y})")
                    else:
                        # Programmatic fallback rendering when sprites not available
                        if tile_type == TILE_BRICK:
                            # Brown brick wall with brick pattern
                            pyxel.rect(pixel_x, pixel_y, TILE_SIZE, TILE_SIZE, COLOR_BROWN)
                            # Add realistic brick pattern with offset rows
                            for by in range(0, TILE_SIZE, 4):  # Horizontal brick rows
                                for bx in range(0, TILE_SIZE, 8):  # Brick width
                                    offset = 4 if by % 8 == 4 else 0  # Offset every other row
                                    pyxel.rect(pixel_x + bx + offset, pixel_y + by, 6, 2, COLOR_DARK_GREY)
                        
                        elif tile_type == TILE_STEEL:
                            # Grey steel wall with metallic grid pattern
                            pyxel.rect(pixel_x, pixel_y, TILE_SIZE, TILE_SIZE, COLOR_LIGHT_GREY)
                            # Add steel grid pattern
                            for i in range(0, TILE_SIZE, 4):
                                # Vertical lines
                                pyxel.line(pixel_x + i, pixel_y, pixel_x + i, pixel_y + TILE_SIZE - 1, COLOR_WHITE)
                                # Horizontal lines
                                pyxel.line(pixel_x, pixel_y + i, pixel_x + TILE_SIZE - 1, pixel_y + i, COLOR_WHITE)
                        
                        elif tile_type == TILE_WATER:
                            # Dark blue water with wave pattern
                            pyxel.rect(pixel_x, pixel_y, TILE_SIZE, TILE_SIZE, COLOR_DARK_BLUE)
                            # Add animated-looking wave pattern
                            for i in range(0, TILE_SIZE, 4):
                                # Upper wave line
                                pyxel.line(pixel_x + i, pixel_y + 2, pixel_x + i + 2, pixel_y + 4, COLOR_CYAN)
                                # Lower wave line
                                pyxel.line(pixel_x + i, pixel_y + 8, pixel_x + i + 2, pixel_y + 10, COLOR_CYAN)
                        
                        elif tile_type == TILE_FOREST:
                            # Dark green forest with tree pattern
                            pyxel.rect(pixel_x, pixel_y, TILE_SIZE, TILE_SIZE, COLOR_DARK_GREEN)
                            # Add tree canopy pattern
                            for tx in range(2, TILE_SIZE, 6):  # Tree spacing
                                for ty in range(2, TILE_SIZE, 6):
                                    pyxel.rect(pixel_x + tx, pixel_y + ty, 4, 4, COLOR_GREEN)
                        
                        elif tile_type == TILE_BASE:
                            # Yellow base with eagle symbol approximation
                            pyxel.rect(pixel_x, pixel_y, TILE_SIZE, TILE_SIZE, COLOR_YELLOW)
                            # Inner red square (eagle body)
                            pyxel.rect(pixel_x + 4, pixel_y + 4, 8, 8, COLOR_RED)
                            # Inner white square (eagle head)
                            pyxel.rect(pixel_x + 6, pixel_y + 6, 4, 4, COLOR_WHITE)
    
    def draw_forest_overlay(self) -> None:
        """
        Draw forest tiles above all other game elements for visual cover effect.
        
        This creates the illusion that tanks are moving through/under forest canopy,
        providing true visual cover. Forest tiles are rendered above tanks to create
        the effect that tanks are partially hidden when moving through forest areas.
        """
        # Detect sprite availability
        sprite_width = pyxel.images[0].width
        sprite_height = pyxel.images[0].height
        use_sprites = sprite_width >= 80 and sprite_height >= 64
        
        # Render only forest tiles as overlay
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                tile_type = self.map_data[y][x]
                
                if tile_type == TILE_FOREST:
                    pixel_x, pixel_y = self.grid_to_pixel(x, y)
                    
                    if use_sprites:
                        # Green forest providing visual cover (above tanks)
                        pyxel.blt(pixel_x, pixel_y, 0, 48, 48, 16, 16)   # [48,48]
                    else:
                        # Programmatic forest overlay with semi-transparency effect
                        # Dark green forest base with tree pattern
                        pyxel.rect(pixel_x, pixel_y, TILE_SIZE, TILE_SIZE, COLOR_DARK_GREEN)
                        # Add tree canopy pattern above tanks
                        for tx in range(2, TILE_SIZE, 6):  # Tree spacing
                            for ty in range(2, TILE_SIZE, 6):
                                pyxel.rect(pixel_x + tx, pixel_y + ty, 4, 4, COLOR_GREEN)