# -*- coding: utf-8 -*-
"""
弾丸システムモジュール

以下の弾丸メカニズムを処理：
- 弾丸の物理演算と移動
- 異なるタイルタイプとのマップ衝突検出
- 弾丸同士の衝突システム
- 爆発エフェクトの統合
- 所有者ベースの弾丸管理

クラス:
    Bullet: 物理演算と衝突を持つ個別の発射体
    BulletManager: すべての活動中弾丸とその相互作用を管理
"""

import pyxel
from constants import *

class Bullet:
    """
    物理演算と衝突検出を持つ個別の弾丸発射体。
    
    属性:
        x (float): 現在のXピクセル座標
        y (float): 現在のYピクセル座標  
        direction (int): 移動方向 (UP/DOWN/LEFT/RIGHT)
        speed (int): フレーム毎の移動速度（ピクセル単位）
        owner_type (int): この弾丸を発射したタンクタイプ (TANK_PLAYER/TANK_*)
        power_level (int): 破壊能力に影響する弾丸パワーレベル
        active (bool): 弾丸がまだ活動中で更新すべきかどうか
        dx (float): フレーム毎のX速度成分（ピクセル単位）
        dy (float): フレーム毎のY速度成分（ピクセル単位）
    """
    
    def __init__(self, x: float, y: float, direction: int, speed: int, owner_type: int, power_level: int = POWER_NORMAL) -> None:
        """
        新しい弾丸発射体を初期化。
        
        引数:
            x (float): 開始Xピクセル座標
            y (float): 開始Yピクセル座標
            direction (int): 移動方向定数 (UP/DOWN/LEFT/RIGHT)
            speed (int): フレーム毎の移動速度（ピクセル単位）
            owner_type (int): 弾丸を発射したタンクタイプ (TANK_PLAYER/TANK_*)
            power_level (int, optional): 破壊能力用の弾丸パワー。デフォルトはPOWER_NORMAL。
        """
        self.x: float = x
        self.y: float = y
        self.direction: int = direction
        self.speed: int = speed
        self.owner_type: int = owner_type
        self.power_level: int = power_level
        self.active: bool = True
        
        # 方向に基づいて速度成分を計算
        # 方向定数を2D速度ベクトルに変換
        self.dx: float = 0.0
        self.dy: float = 0.0
        
        if direction == UP:
            self.dy = -speed  # 負のYは画面座標で上向きに移動
        elif direction == DOWN:
            self.dy = speed   # 正のYは下向きに移動
        elif direction == LEFT:
            self.dx = -speed  # 負のXは左向きに移動
        elif direction == RIGHT:
            self.dx = speed   # 正のXは右向きに移動
    
    def update(self, map_manager: 'MapManager') -> None:
        """
        弾丸の物理演算を更新し衝突を処理。
        
        各フレームで以下の操作を実行：
        1. 速度成分により弾丸を移動
        2. 画面境界衝突をチェック（境界外で非活性化）
        3. マップタイル衝突をチェック（タイル破壊または弾丸非活性化）
        
        引数:
            map_manager (MapManager): 衝突検出用のゲームマップマネージャー
        """
        if not self.active:
            return
        
        # 位置に速度を適用（オイラー積分）
        self.x += self.dx
        self.y += self.dy
        
        # 画面境界をチェック - ゲームエリア外の場合弾丸を非活性化
        # 画面境界: X [0, SCREEN_WIDTH], Y [0, MAP_HEIGHT * TILE_SIZE]
        if (self.x < 0 or self.x >= SCREEN_WIDTH or 
            self.y < 0 or self.y >= MAP_HEIGHT * TILE_SIZE):
            self.active = False
            return
        
        # マップタイルとの衝突をチェック（マップ修正または弾丸非活性化の可能性）
        self.check_map_collision(map_manager)
    
    def check_map_collision(self, map_manager: 'MapManager') -> None:
        """
        Check bullet collision with map tiles and handle destruction/blocking.
        
        Collision behavior by tile type:
        - TILE_BRICK: Always destructible, schedules destruction animation
        - TILE_STEEL: Only destructible by POWER_SUPER bullets, otherwise blocks
        - TILE_BASE: Triggers game over when hit, never actually destroyed
        - TILE_WATER/TILE_FOREST: Bullets pass through (no collision)
        - TILE_EMPTY/TILE_ICE: Bullets pass through (no collision)
        
        Side effects:
        - May add explosion animation via explosion_manager
        - May schedule tile destruction with 24-frame delay
        - May trigger game over for base hits
        - Deactivates bullet on collision
        
        Args:
            map_manager (MapManager): Game map for tile access and destruction
        """
        # Convert pixel coordinates to grid coordinates for tile lookup
        grid_x, grid_y = map_manager.pixel_to_grid(int(self.x), int(self.y))
        
        # Check if bullet can destroy the tile at this position
        # This handles TILE_BRICK (always) and TILE_STEEL (POWER_SUPER only)
        if map_manager.can_destroy(grid_x, grid_y, self.power_level):
            # Add explosion animation at bullet impact point
            if hasattr(map_manager, 'explosion_manager') and map_manager.explosion_manager:
                map_manager.explosion_manager.add_explosion(self.x, self.y)
            
            # Schedule tile destruction after explosion animation completes (24 frames)
            # This allows the explosion to play before the tile disappears
            if map_manager.schedule_tile_destruction(grid_x, grid_y, 24):
                pyxel.play(0, 2)  # Play explosion sound effect
            self.active = False  # Bullet is consumed by destroying the tile
            return
        
        # Get tile type for special collision handling
        tile_type = map_manager.get_tile(grid_x, grid_y)
        
        # Handle base destruction - triggers immediate game over
        if tile_type == TILE_BASE:
            # Add explosion animation at impact point
            if hasattr(map_manager, 'explosion_manager') and map_manager.explosion_manager:
                map_manager.explosion_manager.add_explosion(self.x, self.y)
            
            # Trigger game over through global game manager reference
            # TODO: This should be refactored to use proper dependency injection
            import game_manager
            if hasattr(game_manager, 'current_instance'):
                game_manager.current_instance.trigger_game_over()
            
            pyxel.play(0, 2)  # Play explosion sound
            self.active = False
            return
        
        # Handle indestructible tile collision
        if tile_type == TILE_STEEL and self.power_level < POWER_SUPER:
            # Steel blocks normal bullets but not super bullets
            if hasattr(map_manager, 'explosion_manager') and map_manager.explosion_manager:
                map_manager.explosion_manager.add_explosion(self.x, self.y)
            self.active = False  # Bullet blocked by steel
        elif tile_type == TILE_WATER:
            # Water allows bullets to pass through (like forests)
            # No collision detection needed - bullet continues moving
            pass
    
    def get_rect(self) -> tuple[int, int, int, int]:
        """
        Get bullet's axis-aligned bounding rectangle for collision detection.
        
        Creates a 2x2 pixel rectangle centered on the bullet position.
        Used for bullet-to-bullet collision detection and entity collision.
        
        Returns:
            tuple[int, int, int, int]: Rectangle as (x, y, width, height)
                - x: Left edge pixel coordinate
                - y: Top edge pixel coordinate  
                - width: Rectangle width (always 2 pixels)
                - height: Rectangle height (always 2 pixels)
        """
        return (int(self.x - 1), int(self.y - 1), 2, 2)
    
    def draw(self) -> None:
        """
        Render the bullet on screen as a colored square.
        
        Visual properties:
        - Player bullets: Yellow color (COLOR_YELLOW)
        - Enemy bullets: White color (COLOR_WHITE)
        - Size: 2x2 pixel square centered on bullet position
        - Only draws if bullet is active
        
        Uses Pyxel's rect() function for rendering.
        """
        if not self.active:
            return
        
        # Choose bullet color based on owner type
        # Player bullets are yellow for easy identification
        color = COLOR_YELLOW if self.owner_type == TANK_PLAYER else COLOR_WHITE
        
        # Draw bullet as a small centered square
        # Position is offset by -1 to center the 2x2 square on bullet coordinates
        pyxel.rect(int(self.x - 1), int(self.y - 1), 2, 2, color)

class BulletManager:
    """
    ゲーム内のすべての活動中弾丸とその相互作用を管理。
    
    責任:
    - すべてのソースからの活動中弾丸リストを維持
    - 各フレームで弾丸物理演算と衝突検出を更新
    - 弾丸同士の衝突検出と解決を処理
    - ゲームロジック用の所有者タイプ別弾丸フィルタリング提供
    - 弾丸清掃とメモリ管理を管理
    
    属性:
        bullets (list[Bullet]): 現在活動中のすべての弾丸リスト
        explosion_manager (ExplosionManager): 爆発アニメーション用マネージャー
    """
    
    def __init__(self, explosion_manager: 'ExplosionManager') -> None:
        """
        Initialize the bullet management system.
        
        Args:
            explosion_manager (ExplosionManager): Manager for creating explosion
                animations when bullets collide with each other
        """
        self.bullets: list[Bullet] = []  # Active bullets from all tanks
        self.explosion_manager = explosion_manager  # For collision explosions
    
    def add_bullet(self, bullet: Bullet) -> None:
        """
        Add a new bullet to the active bullet list.
        
        The bullet will be updated each frame until it becomes inactive
        due to collision, boundary exit, or manual deactivation.
        
        Args:
            bullet (Bullet): New bullet instance to manage
        """
        self.bullets.append(bullet)
    
    def update(self, map_manager: 'MapManager') -> None:
        """
        Update all active bullets and perform cleanup.
        
        Performs the following operations each frame:
        1. Update each bullet's physics and collision detection
        2. Remove inactive bullets from the active list
        
        This is called once per frame during the main game loop.
        
        Args:
            map_manager (MapManager): Map manager for bullet collision detection
        """
        # Update physics and collision for each active bullet
        for bullet in self.bullets:
            bullet.update(map_manager)
        
        # Clean up inactive bullets to prevent memory leaks
        # This removes bullets that hit something or left the screen
        self.bullets = [bullet for bullet in self.bullets if bullet.active]
    
    def get_bullets_by_owner(self, owner_type: int) -> list[Bullet]:
        """
        Filter bullets by their owner tank type.
        
        Used for game logic that needs to check specific bullet types,
        such as limiting player bullet count based on power level.
        
        Args:
            owner_type (int): Tank type constant (TANK_PLAYER, TANK_LIGHT, etc.)
            
        Returns:
            list[Bullet]: List of active bullets from the specified tank type
        """
        return [bullet for bullet in self.bullets if bullet.owner_type == owner_type]
    
    def check_bullet_collision(self, bullet1: Bullet, bullet2: Bullet) -> bool:
        """
        Check if two bullets' bounding rectangles overlap (AABB collision).
        
        Uses Axis-Aligned Bounding Box collision detection to determine
        if two bullet rectangles intersect. This is used for bullet-to-bullet
        collision detection where bullets from different owners can destroy
        each other on impact.
        
        Args:
            bullet1 (Bullet): First bullet to test
            bullet2 (Bullet): Second bullet to test
            
        Returns:
            bool: True if bullets are colliding, False otherwise
        """
        # Get axis-aligned bounding rectangles for both bullets
        rect1 = bullet1.get_rect()  # (x, y, width, height)
        rect2 = bullet2.get_rect()
        
        # AABB collision detection: rectangles overlap if they overlap on both axes
        return (rect1[0] < rect2[0] + rect2[2] and     # rect1.left < rect2.right
                rect1[0] + rect1[2] > rect2[0] and     # rect1.right > rect2.left
                rect1[1] < rect2[1] + rect2[3] and     # rect1.top < rect2.bottom
                rect1[1] + rect1[3] > rect2[1])        # rect1.bottom > rect2.top
    
    def update_bullet_collisions(self) -> None:
        """
        Detect and resolve collisions between bullets from different owners.
        
        Checks all pairs of active bullets for collision. When bullets from
        different tank types collide, both are destroyed and an explosion
        animation is created at the midpoint of the collision.
        
        This prevents bullets from the same owner from destroying each other
        and allows for strategic bullet interception gameplay.
        
        Side effects:
        - Deactivates both bullets in a collision
        - Creates explosion animation at collision point
        - Plays explosion sound effect
        """
        # Check all pairs of bullets for collision (avoid duplicate checks)
        for i, bullet1 in enumerate(self.bullets):
            for j, bullet2 in enumerate(self.bullets[i + 1:], i + 1):
                # Only check collisions between active bullets from different owners
                if (bullet1.active and bullet2.active and 
                    bullet1.owner_type != bullet2.owner_type):
                    
                    if self.check_bullet_collision(bullet1, bullet2):
                        # Calculate collision point as midpoint between bullets
                        collision_x = (bullet1.x + bullet2.x) / 2
                        collision_y = (bullet1.y + bullet2.y) / 2
                        
                        # Create explosion animation at collision point
                        self.explosion_manager.add_explosion(collision_x, collision_y)
                        
                        # Deactivate both bullets (they destroy each other)
                        bullet1.active = False
                        bullet2.active = False
                        
                        # Play explosion sound effect
                        # TODO: Refactor to use consistent sound system
                        if hasattr(self, 'game_context'):
                            self.game_context.play_sound_effect("explosion")
                        else:
                            pyxel.play(0, 2)  # Fallback explosion sound
    
    def clear_bullets_by_owner(self, owner_type: int) -> None:
        """
        Deactivate all bullets belonging to a specific tank type.
        
        Used for game events like tank destruction where all bullets
        from that tank should be removed from the game. Bullets are
        marked inactive rather than immediately removed to allow for
        proper cleanup in the next update cycle.
        
        Args:
            owner_type (int): Tank type whose bullets to clear (TANK_PLAYER, etc.)
        """
        for bullet in self.bullets:
            if bullet.owner_type == owner_type:
                bullet.active = False  # Mark for cleanup in next update()
    
    def clear_all_bullets(self) -> None:
        """
        Remove all bullets immediately from the game.
        
        Used for stage transitions, game resets, or other events where
        all projectiles should be instantly cleared. This provides a
        clean slate for the next game state.
        """
        self.bullets.clear()  # Immediately remove all bullets from memory
    
    def draw(self) -> None:
        """
        Render all active bullets to the screen.
        
        Calls the draw method on each active bullet to render them
        as colored squares. This is called once per frame during the
        main rendering pass.
        """
        for bullet in self.bullets:
            bullet.draw()  # Each bullet handles its own rendering