import pyxel
import random
from constants import *

class Item:
    def __init__(self, x, y, item_type):
        self.x = x - TILE_SIZE // 2  # スポーン位置を中央に配置
        self.y = y - TILE_SIZE // 2
        self.item_type = item_type
        self.active = True
        self.timer = 600  # 消失まで10秒
        self.flash_timer = 0
    
    def update(self):
        """アイテム更新"""
        if not self.active:
            return
        
        self.timer -= 1
        self.flash_timer += 1
        
        # 消失直前に点滅開始
        if self.timer <= 120:  # 最後の2秒
            if self.timer <= 0:
                self.active = False
    
    def get_rect(self):
        """衝突用アイテム境界矩形取得"""
        return (int(self.x), int(self.y), TILE_SIZE, TILE_SIZE)
    
    def draw(self):
        """アイテム描画"""
        if not self.active:
            return
        
        # Flash when about to disappear
        if self.timer <= 120 and (self.flash_timer // 15) % 2:
            return
        
        # Draw item based on type
        if self.item_type == ITEM_STAR:
            self.draw_star()
        elif self.item_type == ITEM_GRENADE:
            self.draw_grenade()
        elif self.item_type == ITEM_TANK:
            self.draw_tank()
        elif self.item_type == ITEM_SHOVEL:
            self.draw_shovel()
        elif self.item_type == ITEM_CLOCK:
            self.draw_clock()
        elif self.item_type == ITEM_HELMET:
            self.draw_helmet()
    
    def draw_star(self):
        """Draw star power-up"""
        # Use sprite from my_resource.pyxres at position (0,80)
        pyxel.blt(int(self.x), int(self.y), 0, 0, 80, TILE_SIZE, TILE_SIZE, 0)
    
    def draw_grenade(self):
        """Draw grenade item"""
        # Use sprite from my_resource.pyxres at position (16,80)
        pyxel.blt(int(self.x), int(self.y), 0, 16, 80, TILE_SIZE, TILE_SIZE, 0)
    
    def draw_tank(self):
        """Draw tank (1UP) item"""
        # Use sprite from my_resource.pyxres at position (32,80)
        pyxel.blt(int(self.x), int(self.y), 0, 32, 80, TILE_SIZE, TILE_SIZE, 0)
    
    def draw_shovel(self):
        """Draw shovel item"""
        # Use sprite from my_resource.pyxres at position (48,80)
        pyxel.blt(int(self.x), int(self.y), 0, 48, 80, TILE_SIZE, TILE_SIZE, 0)
    
    def draw_clock(self):
        """Draw clock item"""
        # Use sprite from my_resource.pyxres at position (64,80)
        pyxel.blt(int(self.x), int(self.y), 0, 64, 80, TILE_SIZE, TILE_SIZE, 0)
    
    def draw_helmet(self):
        """Draw helmet item"""
        # Use sprite from my_resource.pyxres at position (80,80)
        pyxel.blt(int(self.x), int(self.y), 0, 80, 80, TILE_SIZE, TILE_SIZE, 0)

class ItemManager:
    def __init__(self):
        self.items = []
        self.grenade_collected = False
        self.shovel_timer = 0
        self.freeze_timer = 0
        
        # Base protection tiles (for shovel effect) - stores (x, y, original_tile_type)
        self.base_protection_tiles = []
    
    def spawn_item(self, x, y, item_type):
        """Spawn an item at specified location"""
        item = Item(x, y, item_type)
        self.items.append(item)
    
    def update(self, map_manager):
        """Update all items and special effects"""
        # Update items
        for item in self.items:
            item.update()
        
        # Remove inactive items
        self.items = [item for item in self.items if item.active]
        
        # Update special effect timers
        self.update_shovel_effect(map_manager)
        self.update_freeze_effect()
    
    def update_shovel_effect(self, map_manager):
        """Update base protection effect"""
        if self.shovel_timer > 0:
            # Apply base protection
            if not self.base_protection_tiles:
                self.apply_base_protection(map_manager)
            
            self.shovel_timer -= 1
            
            # Flash warning when about to end
            if self.shovel_timer <= 120:  # Last 2 seconds
                if (self.shovel_timer // 30) % 2:
                    # Flash protection tiles - show original tiles
                    for x, y, original_tile in self.base_protection_tiles:
                        if map_manager.get_tile(x, y) == TILE_STEEL:
                            map_manager.set_tile(x, y, original_tile)
                else:
                    # Restore steel walls
                    for x, y, original_tile in self.base_protection_tiles:
                        if map_manager.get_tile(x, y) != TILE_STEEL:
                            map_manager.set_tile(x, y, TILE_STEEL)
        else:
            # Remove base protection
            if self.base_protection_tiles:
                self.remove_base_protection(map_manager)
    
    def apply_base_protection(self, map_manager):
        """Apply steel wall protection around base"""
        base_x, base_y = map_manager.base_position
        
        # Define protection pattern around base
        protection_pattern = [
            (-1, -1), (0, -1), (1, -1),
            (-1,  0),          (1,  0),
            (-1,  1), (0,  1), (1,  1)
        ]
        
        self.base_protection_tiles.clear()
        
        for dx, dy in protection_pattern:
            tile_x = base_x + dx
            tile_y = base_y + dy
            
            if (0 <= tile_x < MAP_WIDTH and 0 <= tile_y < MAP_HEIGHT):
                # Save original tile type and replace with steel
                original_tile = map_manager.get_tile(tile_x, tile_y)
                self.base_protection_tiles.append((tile_x, tile_y, original_tile))
                map_manager.set_tile(tile_x, tile_y, TILE_STEEL)
    
    def remove_base_protection(self, map_manager):
        """Remove base protection and restore original tiles"""
        for tile_x, tile_y, original_tile in self.base_protection_tiles:
            # Restore original tile type
            if map_manager.get_tile(tile_x, tile_y) == TILE_STEEL:
                map_manager.set_tile(tile_x, tile_y, original_tile)
        
        self.base_protection_tiles.clear()
    
    def update_freeze_effect(self):
        """Update enemy freeze effect"""
        if self.freeze_timer > 0:
            self.freeze_timer -= 1
    
    def is_freeze_active(self):
        """Check if freeze effect is active"""
        return self.freeze_timer > 0
    
    def handle_grenade_effect(self, enemy_manager, explosion_manager):
        """Handle grenade effect (destroy all enemies with explosions)"""
        if not self.grenade_collected:
            return []
        
        self.grenade_collected = False
        destroyed_enemies = []
        
        # Destroy all active enemies with explosion effects
        for enemy in enemy_manager.enemies:
            if enemy.active:
                # Create explosion at enemy position
                explosion_manager.add_explosion(
                    enemy.x + TILE_SIZE // 2, 
                    enemy.y + TILE_SIZE // 2
                )
                enemy.active = False
                destroyed_enemies.append(enemy)
        
        return destroyed_enemies
    
    def clear_all_items(self):
        """Clear all items and effects"""
        self.items.clear()
        self.grenade_collected = False
        self.shovel_timer = 0
        self.freeze_timer = 0
        self.base_protection_tiles.clear()
    
    def get_active_count(self):
        """Get number of active items"""
        return len([item for item in self.items if item.active])
    
    def draw(self):
        """Draw all items"""
        for item in self.items:
            item.draw()
    
    def draw_ui_effects(self):
        """Draw UI indicators for active effects"""
        # Position in UI area, right side to avoid overlap with STAGE display
        ui_y = SCREEN_HEIGHT - 8   # Bottom row to avoid STAGE text overlap
        ui_y_bottom = SCREEN_HEIGHT - 16   # Previous position if multiple effects
        
        # Display effects on right side of screen, stacked vertically if multiple
        effect_x = 200  # Right side of screen
        current_y = ui_y
        
        if self.shovel_timer > 0:
            pyxel.text(effect_x, current_y, "SHOVEL", COLOR_WHITE)
            current_y = ui_y_bottom  # Move to next line
        
        if self.freeze_timer > 0:
            pyxel.text(effect_x, current_y, "FREEZE", COLOR_CYAN)
            current_y = ui_y_bottom  # Move to next line if more effects
        
        if self.grenade_collected:
            pyxel.text(effect_x, current_y, "BOMB", COLOR_RED)