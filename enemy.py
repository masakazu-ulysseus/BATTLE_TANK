from typing import List, Tuple, Optional
import pyxel
import random
from constants import *

class Enemy:
    def __init__(self, x: int, y: int, enemy_type: int) -> None:
        self.x: int = int(x)
        self.y: int = int(y)
        self.enemy_type: int = enemy_type
        self.direction: int = random.choice([UP, DOWN, LEFT, RIGHT])
        self.health: int = self.get_max_health()
        self.active: bool = True
        
        # 移動状態
        self.move_timer: int = 0
        self.target_x: int = x
        self.target_y: int = y
        self.is_moving: bool = False
        
        # AI状態
        self.ai_timer: int = 0
        self.fire_timer: int = 0
        self.change_direction_timer: int = random.randint(60, 180)  # 1-3秒
        
        # 特殊属性
        self.carries_item: bool = False
        self.item_type: Optional[int] = None
        
        # ランダムアイテムキャリア設定（4分の1の確率）
        if random.random() < 0.25:
            self.carries_item = True
            self.item_type = random.choice([ITEM_STAR, ITEM_GRENADE, ITEM_TANK, 
                                         ITEM_SHOVEL, ITEM_CLOCK, ITEM_HELMET])
    
    def get_max_health(self) -> int:
        """敵タイプに基づく最大ヘルス取得"""
        if self.enemy_type == TANK_LIGHT:
            return 1
        elif self.enemy_type == TANK_ARMORED:
            return 1
        elif self.enemy_type == TANK_FAST_SHOT:
            return 1
        elif self.enemy_type == TANK_HEAVY:
            return 4
        return 1
    
    def get_speed(self) -> int:
        """敵タイプに基づく移動速度取得"""
        if self.enemy_type == TANK_ARMORED:
            return TANK_SPEED * 2
        else:
            return TANK_SPEED
    
    def get_fire_rate(self) -> int:
        """敵タイプに基づく発射レート取得"""
        if self.enemy_type == TANK_FAST_SHOT:
            return 30  # 0.5秒ごとに発射
        else:
            return 90  # 1.5秒ごとに発射
    
    def update(self, map_manager: 'MapManager', player: 'Player', bullet_manager: 'BulletManager') -> None:
        """敵タンクAIと移動の更新"""
        if not self.active:
            return
        
        # Safety check: ensure enemy is within valid bounds
        if (self.x < -TILE_SIZE or self.x >= SCREEN_WIDTH + TILE_SIZE or 
            self.y < -TILE_SIZE or self.y >= MAP_HEIGHT * TILE_SIZE + TILE_SIZE):
            self.active = False
            return
        
        # Update timers
        self.ai_timer += 1
        self.fire_timer += 1
        self.change_direction_timer -= 1
        
        # Handle movement
        if self.move_timer > 0:
            self.move_timer -= 1
            self.smooth_move()
        else:
            self.update_ai(map_manager, player, bullet_manager)
        
        # Try to fire
        self.try_fire(bullet_manager, player)
    
    def update_ai(self, map_manager: 'MapManager', player: 'Player', bullet_manager: 'BulletManager') -> None:
        """Update AI behavior"""
        # Change direction periodically or when blocked
        if self.change_direction_timer <= 0 or not self.can_move_forward(map_manager):
            self.choose_new_direction(map_manager, player)
            self.change_direction_timer = random.randint(60, 180)
        
        # Try to move forward
        if self.can_move_forward(map_manager):
            dx, dy = self.get_direction_vector()
            self.start_move(dx * TILE_SIZE, dy * TILE_SIZE)
    
    def choose_new_direction(self, map_manager: 'MapManager', player: 'Player') -> None:
        """Choose new direction based on AI logic"""
        possible_directions = []
        
        # Check all four directions
        for direction in [UP, DOWN, LEFT, RIGHT]:
            old_direction = self.direction
            self.direction = direction
            if self.can_move_forward(map_manager):
                possible_directions.append(direction)
            self.direction = old_direction
        
        if not possible_directions:
            return
        
        # Simple AI: Sometimes move toward player, sometimes random
        if random.random() < 0.3 and player.lives > 0:  # 30% chance to target player
            # Calculate direction toward player
            dx = player.x - self.x
            dy = player.y - self.y
            
            if abs(dx) > abs(dy):
                target_direction = RIGHT if dx > 0 else LEFT
            else:
                target_direction = DOWN if dy > 0 else UP
            
            if target_direction in possible_directions:
                self.direction = target_direction
                return
        
        # Random direction
        self.direction = random.choice(possible_directions)
    
    def can_move_forward(self, map_manager: 'MapManager') -> bool:
        """Check if tank can move forward in current direction"""
        dx, dy = self.get_direction_vector()
        return self.can_move(dx * TILE_SIZE, dy * TILE_SIZE, map_manager)
    
    def get_direction_vector(self) -> Tuple[int, int]:
        """Get direction vector (dx, dy) for current direction"""
        if self.direction == UP:
            return (0, -1)
        elif self.direction == DOWN:
            return (0, 1)
        elif self.direction == LEFT:
            return (-1, 0)
        elif self.direction == RIGHT:
            return (1, 0)
        return (0, 0)
    
    def start_move(self, dx: int, dy: int) -> None:
        """Start smooth movement to target position"""
        self.target_x = self.x + dx
        self.target_y = self.y + dy
        self.move_timer = 8  # Frames for smooth movement
        self.is_moving = True
    
    def smooth_move(self) -> None:
        """Perform smooth movement towards target"""
        if self.move_timer <= 0:
            # Ensure target position is valid before setting
            if (self.target_x >= 0 and self.target_x < SCREEN_WIDTH - TILE_SIZE and
                self.target_y >= 0 and self.target_y < MAP_HEIGHT * TILE_SIZE - TILE_SIZE):
                self.x = int(self.target_x)
                self.y = int(self.target_y)
            self.is_moving = False
            return
        
        # Simple movement
        move_x = (self.target_x - self.x) / (self.move_timer + 1)
        move_y = (self.target_y - self.y) / (self.move_timer + 1)
        
        self.x += move_x
        self.y += move_y
    
    def can_move(self, dx: int, dy: int, map_manager: 'MapManager') -> bool:
        """Check if tank can move to new position"""
        new_x = self.x + dx
        new_y = self.y + dy
        
        # Check screen boundaries
        if new_x < 0 or new_x >= SCREEN_WIDTH - TILE_SIZE:
            return False
        if new_y < 0 or new_y >= (MAP_HEIGHT * TILE_SIZE):
            return False
        
        # Check collision with map tiles
        return self.check_map_collision(new_x, new_y, map_manager)
    
    def check_map_collision(self, x: float, y: float, map_manager: 'MapManager') -> bool:
        """Check collision with map tiles"""
        # Check all four corners of the tank
        corners = [
            (x, y),
            (x + TILE_SIZE - 1, y),
            (x, y + TILE_SIZE - 1),
            (x + TILE_SIZE - 1, y + TILE_SIZE - 1)
        ]
        
        for corner_x, corner_y in corners:
            grid_x, grid_y = map_manager.pixel_to_grid(int(corner_x), int(corner_y))
            if not map_manager.is_passable(grid_x, grid_y):
                return False
        
        return True
    
    def try_fire(self, bullet_manager: 'BulletManager', player: 'Player') -> None:
        """Try to fire a bullet with intelligent targeting"""
        if self.fire_timer < self.get_fire_rate():
            return
        
        # Check if there's already a bullet from this enemy
        enemy_bullets = bullet_manager.get_bullets_by_owner(self.enemy_type)
        if len(enemy_bullets) >= 1:
            return
        
        # Check if we should aim at player or base
        target_direction = self.get_best_attack_direction(player)
        
        # Only fire if we have a good shot (70% chance when aligned, 20% chance otherwise)
        fire_chance = 0.7 if target_direction else 0.2
        
        if random.random() < fire_chance:
            # Turn to face target if we have one
            if target_direction:
                self.direction = target_direction
            
            # Reset fire timer
            self.fire_timer = 0
            
            # Create and add bullet
            bullet = self.create_bullet()
            bullet_manager.add_bullet(bullet)
    
    def get_best_attack_direction(self, player: 'Player') -> Optional[int]:
        """
        敵タンクの攻撃AI：プレイヤーまたは司令部への最適な攻撃方向を判定
        
        攻撃優先度:
        1. プレイヤーとの直線上 (水平/垂直) で射線が通る場合
        2. 司令部との直線上で射線が通る場合
        3. どちらにも狙いを定められない場合はNone
        
        Returns:
            int or None: 最適な攻撃方向 (UP/DOWN/LEFT/RIGHT) または None
        """
        # プレイヤー位置（ピクセル座標をグリッド座標に変換）
        player_grid_x = int(player.x // TILE_SIZE)
        player_grid_y = int(player.y // TILE_SIZE)
        
        # 自機のグリッド座標
        enemy_grid_x = int(self.x // TILE_SIZE)
        enemy_grid_y = int(self.y // TILE_SIZE)
        
        # 司令部のグリッド座標（固定位置）
        base_grid_x, base_grid_y = 7, 13
        
        # 各方向での攻撃可能性をチェック
        directions_to_check = [
            (UP, 0, -1),
            (DOWN, 0, 1),
            (LEFT, -1, 0),
            (RIGHT, 1, 0)
        ]
        
        best_direction = None
        
        # プレイヤーへの攻撃チェック（優先度1）
        for direction, dx, dy in directions_to_check:
            if self._can_hit_target(enemy_grid_x, enemy_grid_y, player_grid_x, player_grid_y, dx, dy):
                return direction
        
        # 司令部への攻撃チェック（優先度2）
        for direction, dx, dy in directions_to_check:
            if self._can_hit_target(enemy_grid_x, enemy_grid_y, base_grid_x, base_grid_y, dx, dy):
                return direction
        
        return None
    
    def _can_hit_target(self, start_x: int, start_y: int, target_x: int, target_y: int, 
                        dx: int, dy: int) -> bool:
        """
        指定された方向から目標への射線が通るかチェック
        
        Args:
            start_x, start_y: 敵タンクの位置
            target_x, target_y: 目標の位置
            dx, dy: チェックする方向ベクトル
            
        Returns:
            bool: 射線が通る場合 True
        """
        # 水平または垂直の直線上にない場合は攻撃不可
        if dx != 0 and start_y != target_y:
            return False
        if dy != 0 and start_x != target_x:
            return False
        
        # 射線上の障害物チェック（実装簡略化：基本的な距離チェックのみ）
        distance_x = abs(target_x - start_x)
        distance_y = abs(target_y - start_y)
        
        # 有効射程内（12タイル以内）で、正しい方向を向いている場合
        max_range = 12
        if dx > 0 and target_x > start_x and distance_x <= max_range:
            return True
        elif dx < 0 and target_x < start_x and distance_x <= max_range:
            return True
        elif dy > 0 and target_y > start_y and distance_y <= max_range:
            return True
        elif dy < 0 and target_y < start_y and distance_y <= max_range:
            return True
        
        return False
    
    def create_bullet(self) -> 'Bullet':
        """Create bullet in front of tank"""
        from bullet import Bullet
        
        # Calculate bullet starting position
        bullet_x = self.x + TILE_SIZE // 2
        bullet_y = self.y + TILE_SIZE // 2
        
        # Adjust position based on direction
        if self.direction == UP:
            bullet_y = self.y
        elif self.direction == DOWN:
            bullet_y = self.y + TILE_SIZE
        elif self.direction == LEFT:
            bullet_x = self.x
        elif self.direction == RIGHT:
            bullet_x = self.x + TILE_SIZE
        
        bullet_speed = BULLET_SPEED
        if self.enemy_type == TANK_FAST_SHOT:
            bullet_speed *= 2
        
        return Bullet(bullet_x, bullet_y, self.direction, bullet_speed, self.enemy_type)
    
    def take_damage(self) -> bool:
        """Handle enemy taking damage"""
        self.health -= 1
        if self.health <= 0:
            self.active = False
            return True
        return False
    
    def get_rect(self) -> Tuple[int, int, int, int]:
        """Get tank bounding rectangle for collision"""
        return (int(self.x), int(self.y), TILE_SIZE, TILE_SIZE)
    
    def get_score_value(self) -> int:
        """Get score value for destroying this enemy"""
        score_values = {
            TANK_LIGHT: 100,
            TANK_ARMORED: 200,
            TANK_FAST_SHOT: 300,
            TANK_HEAVY: 400
        }
        return score_values.get(self.enemy_type, 100)
    
    def draw(self) -> None:
        """敵タンク描画"""
        if not self.active:
            return
        
        # Check if sprite is loaded
        sprite_width = pyxel.images[0].width
        sprite_height = pyxel.images[0].height
        
        # Use sprites (pyxres file must be loaded)
        if sprite_width >= 256 and sprite_height >= 32:
            # Select sprite coordinates based on enemy type and direction
            sprite_x = 0
            sprite_y = 16
            
            if self.enemy_type == TANK_LIGHT:
                # TANK_LIGHT: [0,16], [16,16], [32,16], [48,16]
                if self.direction == UP:
                    sprite_x = 0    # [0,16]
                elif self.direction == RIGHT:
                    sprite_x = 16   # [16,16]
                elif self.direction == LEFT:
                    sprite_x = 32   # [32,16]
                elif self.direction == DOWN:
                    sprite_x = 48   # [48,16]
            elif self.enemy_type == TANK_ARMORED:
                # TANK_ARMORED: [64,16], [80,16], [96,16], [112,16]
                if self.direction == UP:
                    sprite_x = 64   # [64,16]
                elif self.direction == RIGHT:
                    sprite_x = 80   # [80,16]
                elif self.direction == LEFT:
                    sprite_x = 96   # [96,16]
                elif self.direction == DOWN:
                    sprite_x = 112  # [112,16]
            elif self.enemy_type == TANK_FAST_SHOT:
                # TANK_FAST_SHOT: [128,16], [144,16], [160,16], [176,16]
                if self.direction == UP:
                    sprite_x = 128  # [128,16]
                elif self.direction == RIGHT:
                    sprite_x = 144  # [144,16]
                elif self.direction == LEFT:
                    sprite_x = 160  # [160,16]
                elif self.direction == DOWN:
                    sprite_x = 176  # [176,16]
            elif self.enemy_type == TANK_HEAVY:
                # TANK_HEAVY: Normal [192,16] or Damaged [0,32] row
                if self.health <= 2:
                    # Damaged heavy tank sprites (y=32 row)
                    sprite_y = 32
                    if self.direction == UP:
                        sprite_x = 0   # [0,32]
                    elif self.direction == RIGHT:
                        sprite_x = 16  # [16,32]
                    elif self.direction == LEFT:
                        sprite_x = 32  # [32,32]
                    elif self.direction == DOWN:
                        sprite_x = 48  # [48,32]
                else:
                    # Normal heavy tank sprites (y=16 row)
                    if self.direction == UP:
                        sprite_x = 192  # [192,16]
                    elif self.direction == RIGHT:
                        sprite_x = 208  # [208,16]
                    elif self.direction == LEFT:
                        sprite_x = 224  # [224,16]
                    elif self.direction == DOWN:
                        sprite_x = 240  # [240,16]
            
            # Flash effect disabled - all enemies always visible
            show_sprite = True
            
            # Note: Item carrier blinking disabled for better visibility
            # if self.carries_item and (pyxel.frame_count // 6) % 2:
            #     show_sprite = False
            
            
            # Draw sprite only when not blinking and within screen bounds
            if show_sprite:
                # Add clipping check for drawing area
                draw_x = int(self.x)
                draw_y = int(self.y)
                
                # Only draw if sprite is at least partially visible on screen
                if (draw_x + 16 > 0 and draw_x < SCREEN_WIDTH and 
                    draw_y + 16 > 0 and draw_y < MAP_HEIGHT * TILE_SIZE):
                    pyxel.blt(draw_x, draw_y, 0, sprite_x, sprite_y, 16, 16)
        else:
            # Error: pyxres file not loaded properly
            draw_x = int(self.x)
            draw_y = int(self.y)
            
            # Only draw if within screen bounds
            if (draw_x + 16 > 0 and draw_x < SCREEN_WIDTH and 
                draw_y + 16 > 0 and draw_y < MAP_HEIGHT * TILE_SIZE):
                pyxel.rect(draw_x, draw_y, 16, 16, COLOR_RED)
                pyxel.text(draw_x, draw_y, "ERR", COLOR_WHITE)

class EnemyManager:
    def __init__(self) -> None:
        self.enemies: List[Enemy] = []
        self.spawn_queue: List[int] = []
        self.spawn_timer: int = 0
        self.enemies_spawned: int = 0
        self.enemies_to_spawn: int = ENEMIES_PER_STAGE
        
        # Fog animation before enemy spawn
        self.spawn_fog_active: bool = False
        self.spawn_fog_timer: int = 0
        self.spawn_fog_position: Tuple[int, int] = (0, 0)
        self.spawn_fog_sequence: List[int] = [1, 2, 1, 2]  # fog1, fog2, fog1, fog2
        self.spawn_fog_current: int = 0
        self.pending_enemy_type: Optional[int] = None
        
    def init_stage(self, stage_num: int) -> None:
        """Initialize enemies for new stage"""
        self.enemies.clear()
        self.spawn_queue.clear()
        self.enemies_spawned = 0
        self.enemies_destroyed = 0  # Track destroyed enemies for UI display
        self.enemies_to_spawn = ENEMIES_PER_STAGE
        self.spawn_timer = 0
        
        # Reset fog animation state
        self.spawn_fog_active = False
        self.spawn_fog_timer = 0
        self.spawn_fog_current = 0
        self.pending_enemy_type = None
        
        
        # Create spawn queue based on stage difficulty
        self.create_spawn_queue(stage_num)
    
    def create_spawn_queue(self, stage_num: int) -> None:
        """Create enemy spawn queue based on stage"""
        # Balanced enemy distribution for all stages
        scale = ENEMIES_PER_STAGE / 20.0
        
        # Base distribution with variety
        light_tanks = max(1, int((15 - min(stage_num, 12)) * scale))
        armored_tanks = max(1, min(int(3 * scale), int(stage_num * scale)))
        fast_shot_tanks = max(1, min(int(3 * scale), max(0, int((stage_num - 1) * scale))))
        heavy_tanks = max(0, min(int(2 * scale), max(0, int((stage_num - 3) * scale))))
        
        # Ensure total matches ENEMIES_PER_STAGE exactly
        total = light_tanks + armored_tanks + fast_shot_tanks + heavy_tanks
        if total < ENEMIES_PER_STAGE:
            light_tanks += ENEMIES_PER_STAGE - total
        elif total > ENEMIES_PER_STAGE:
            # Reduce from light tanks first
            excess = total - ENEMIES_PER_STAGE
            light_tanks = max(0, light_tanks - excess)
        
        # Create spawn list
        spawn_list = ([TANK_LIGHT] * light_tanks + 
                     [TANK_ARMORED] * armored_tanks +
                     [TANK_FAST_SHOT] * fast_shot_tanks +
                     [TANK_HEAVY] * heavy_tanks)
        
        random.shuffle(spawn_list)
        self.spawn_queue = spawn_list
    
    def update(self, map_manager, player, bullet_manager):
        """Update all enemies and spawning"""
        # Update existing enemies
        for enemy in self.enemies:
            enemy.update(map_manager, player, bullet_manager)
        
        # Remove inactive enemies immediately to prevent collision issues
        self.cleanup_inactive_enemies()
        
        # Spawn new enemies
        self.update_spawning()
    
    def cleanup_inactive_enemies(self) -> None:
        """Remove inactive enemies from the list"""
        inactive_count = len([e for e in self.enemies if not e.active])
        
        # Count destroyed enemies for UI display
        self.enemies_destroyed += inactive_count
        
        self.enemies = [enemy for enemy in self.enemies if enemy.active]
    
    def update_spawning(self) -> None:
        """Handle enemy spawning"""
        # Handle fog animation before spawning (don't interrupt once started)
        if self.spawn_fog_active:
            self.update_spawn_fog()
            return
        
        # Check spawn conditions only when not already spawning
        if not self.spawn_queue or len(self.enemies) >= 4:  # Max 4 enemies on screen
            return
        
        self.spawn_timer += 1
        if self.spawn_timer >= 64:  # Spawn every ~1 second
            self.start_spawn_sequence()
            self.spawn_timer = 0
    
    def start_spawn_sequence(self) -> None:
        """Start fog animation sequence before spawning enemy"""
        if not self.spawn_queue:
            return
        
        # Choose spawn position (top of screen), avoid occupied positions
        spawn_positions = [(0, 0), (6 * TILE_SIZE, 0), (12 * TILE_SIZE, 0)]
        available_positions = []
        
        for pos in spawn_positions:
            # Check if position is clear of existing enemies
            position_clear = True
            for enemy in self.enemies:
                if abs(enemy.x - pos[0]) < TILE_SIZE and abs(enemy.y - pos[1]) < TILE_SIZE:
                    position_clear = False
                    break
            if position_clear:
                available_positions.append(pos)
        
        # Use available position or fallback to any position
        if available_positions:
            self.spawn_fog_position = random.choice(available_positions)
        else:
            self.spawn_fog_position = random.choice(spawn_positions)
        
        # Store enemy type to spawn after fog animation
        self.pending_enemy_type = self.spawn_queue.pop(0)
        
        # Start fog animation
        self.spawn_fog_active = True
        self.spawn_fog_timer = 0
        self.spawn_fog_current = 0
    
    def update_spawn_fog(self) -> None:
        """Update fog animation before enemy spawn"""
        self.spawn_fog_timer += 1
        
        # Each fog sprite shows for 8 frames (0.13 seconds)
        if self.spawn_fog_timer >= 8:
            self.spawn_fog_timer = 0
            self.spawn_fog_current += 1
            
            # If fog sequence is complete, spawn the enemy
            if self.spawn_fog_current >= len(self.spawn_fog_sequence):
                self.spawn_enemy()
    
    def spawn_enemy(self) -> None:
        """Spawn a new enemy after fog animation"""
        if self.pending_enemy_type is None:
            self.reset_spawn_fog()
            return
        
        # Additional safety check: ensure we don't exceed max enemies
        if len(self.enemies) >= 4:
            # Put enemy back in queue for later spawning
            self.spawn_queue.insert(0, self.pending_enemy_type)
            self.reset_spawn_fog()
            return
        
        # Create enemy at fog position
        enemy = Enemy(self.spawn_fog_position[0], self.spawn_fog_position[1], self.pending_enemy_type)
        self.enemies.append(enemy)
        self.enemies_spawned += 1
        
        # Reset fog animation state
        self.reset_spawn_fog()
    
    def reset_spawn_fog(self) -> None:
        """Reset fog animation state"""
        self.spawn_fog_active = False
        self.spawn_fog_timer = 0
        self.spawn_fog_current = 0
        self.pending_enemy_type = None
    
    def get_active_count(self) -> int:
        """Get number of active enemies"""
        return len(self.enemies)
    
    def get_remaining_count(self) -> int:
        """Get number of enemies destroyed (for UI display)"""
        return self.enemies_destroyed
    
    def is_stage_complete(self) -> bool:
        """Check if all enemies are defeated"""
        return self.enemies_destroyed >= ENEMIES_PER_STAGE
    
    def clear_all(self) -> None:
        """Clear all enemies"""
        self.enemies.clear()
        self.spawn_queue.clear()
    
    def draw(self) -> None:
        """Draw all enemies"""
        for enemy in self.enemies:
            enemy.draw()
        
        # Draw fog animation if active
        if self.spawn_fog_active:
            self.draw_spawn_fog()
    
    def draw_spawn_fog(self) -> None:
        """Draw fog animation before enemy spawn"""
        if self.spawn_fog_current >= len(self.spawn_fog_sequence):
            return
        
        # Get current fog sprite (fog1 or fog2)
        fog_type = self.spawn_fog_sequence[self.spawn_fog_current]
        
        # Fog sprite coordinates in my_resource.pyxres
        if fog_type == 1:
            sprite_x = 176  # fog1 at (176,0)
        else:
            sprite_x = 192  # fog2 at (192,0)
        
        # Draw fog sprite at spawn position
        draw_x = int(self.spawn_fog_position[0])
        draw_y = int(self.spawn_fog_position[1])
        
        # Only draw if within screen bounds
        if (draw_x + 16 > 0 and draw_x < SCREEN_WIDTH and 
            draw_y + 16 > 0 and draw_y < MAP_HEIGHT * TILE_SIZE):
            pyxel.blt(draw_x, draw_y, 0, sprite_x, 0, TILE_SIZE, TILE_SIZE, 0)