import pyxel
from constants import *

class CollisionManager:
    def __init__(self, game_context):
        self.game_context = game_context
    
    def check_rect_collision(self, rect1, rect2):
        """二つの矩形が衝突するかチェックする"""
        return (rect1[0] < rect2[0] + rect2[2] and
                rect1[0] + rect1[2] > rect2[0] and
                rect1[1] < rect2[1] + rect2[3] and
                rect1[1] + rect1[3] > rect2[1])
    
    def check_player_bullet_collisions(self, player, bullet_manager, enemy_manager, item_manager):
        """プレイヤー弾丸と敵・アイテムの衝突をチェックする"""
        player_bullets = bullet_manager.get_bullets_by_owner(TANK_PLAYER)
        destroyed_enemies = []
        
        for bullet in player_bullets:
            if not bullet.active:
                continue
            
            bullet_rect = bullet.get_rect()
            
            # 敵との衝突をチェック
            for enemy in enemy_manager.enemies:
                if not enemy.active:
                    continue
                
                enemy_rect = enemy.get_rect()
                if self.check_rect_collision(bullet_rect, enemy_rect):
                    # 弾丸位置に爆発アニメーションを追加
                    self.game_context.create_explosion(bullet.x, bullet.y)
                    
                    # 敵がダメージを受ける
                    if enemy.take_damage():
                        # 敵が破壊された
                        destroyed_enemies.append(enemy)
                        pyxel.play(1, 7)  # 敵破壊音
                        
                        # 敵がアイテムを持っていた場合はドロップ
                        if enemy.carries_item:
                            item_manager.spawn_item(enemy.x + TILE_SIZE//2, 
                                                  enemy.y + TILE_SIZE//2, 
                                                  enemy.item_type)
                        
                    bullet.active = False
                    break
        
        return destroyed_enemies
    
    def check_enemy_bullet_collisions(self, player, bullet_manager, map_manager):
        """敵弾丸とプレイヤー・ベースの衝突をチェックする"""
        enemy_bullets = []
        
        # すべての敵弾丸を収集
        for enemy_type in [TANK_LIGHT, TANK_ARMORED, TANK_FAST_SHOT, TANK_HEAVY]:
            enemy_bullets.extend(bullet_manager.get_bullets_by_owner(enemy_type))
        
        for bullet in enemy_bullets:
            if not bullet.active:
                continue
            
            bullet_rect = bullet.get_rect()
            
            # プレイヤーとの衝突をチェック
            if player.lives > 0:
                player_rect = player.get_rect()
                if self.check_rect_collision(bullet_rect, player_rect):
                    # 弾丸位置に爆発アニメーションを追加
                    self.game_context.create_explosion(bullet.x, bullet.y)
                    
                    # プレイヤーがダメージを受ける
                    if player.take_damage():
                        # プレイヤーが死亡 - game_managerにゲームオーバー音を任せる
                        pass
                    else:
                        # プレイヤーが打たれたが生き残った - ヒット音を再生
                        self.game_context.sound_manager.play_hit_sound()
                    
                    bullet.active = False
                    continue
            
            # ベースとの衝突をチェック
            base_x, base_y = map_manager.base_position
            base_rect = (base_x * TILE_SIZE, base_y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            
            if self.check_rect_collision(bullet_rect, base_rect):
                # 弾丸位置に爆発アニメーションを追加
                self.game_context.create_explosion(bullet.x, bullet.y)
                
                # ベース破壊 - ゲームオーバー
                map_manager.set_tile(base_x, base_y, TILE_EMPTY)
                bullet.active = False
                # trigger_game_over()にゲームオーバー音を任せる
                return True  # ゲームオーバーを通知
        
        return False
    
    def check_tank_collisions(self, player, enemy_manager):
        """タンク同士の衝突をチェックする"""
        if player.lives <= 0:
            return
        
        player_rect = player.get_rect()
        
        for enemy in enemy_manager.enemies:
            if not enemy.active:
                continue
            
            enemy_rect = enemy.get_rect()
            if self.check_rect_collision(player_rect, enemy_rect):
                # タンクを引き離す
                self.resolve_tank_collision(player, enemy)
    
    def resolve_tank_collision(self, tank1, tank2):
        """二つのタンクを引き離して衝突を解決する"""
        # 重なりを計算
        rect1 = tank1.get_rect()
        rect2 = tank2.get_rect()
        
        x1, y1, w1, h1 = rect1
        x2, y2, w2, h2 = rect2
        
        # 中心点を計算
        center1_x = x1 + w1 // 2
        center1_y = y1 + h1 // 2
        center2_x = x2 + w2 // 2
        center2_y = y2 + h2 // 2
        
        # 押し出す方向を計算
        dx = center1_x - center2_x
        dy = center1_y - center2_y
        
        # 重なりに基づいて引き離す
        if abs(dx) > abs(dy):
            # 水平方向の分離
            if dx > 0:
                tank1.x = tank2.x + TILE_SIZE
            else:
                tank1.x = tank2.x - TILE_SIZE
        else:
            # 垂直方向の分離
            if dy > 0:
                tank1.y = tank2.y + TILE_SIZE
            else:
                tank1.y = tank2.y - TILE_SIZE
        
        # タンクが範囲内に留まるようにする
        tank1.x = max(0, min(tank1.x, SCREEN_WIDTH - TILE_SIZE))
        tank1.y = max(0, min(tank1.y, (MAP_HEIGHT * TILE_SIZE) - TILE_SIZE))
    
    def check_item_collisions(self, player, item_manager):
        """プレイヤーとアイテムの衝突をチェックする"""
        if player.lives <= 0:
            return
        
        player_rect = player.get_rect()
        
        for item in item_manager.items:
            if not item.active:
                continue
            
            item_rect = item.get_rect()
            if self.check_rect_collision(player_rect, item_rect):
                # プレイヤーがアイテムを収集
                item.active = False
                self.apply_item_effect(player, item, item_manager)
                pyxel.play(2, 3)  # アイテム収集音
    
    def apply_item_effect(self, player, item, item_manager):
        """アイテム効果をプレイヤーに適用する"""
        if item.item_type == ITEM_STAR:
            # タンクをパワーアップ
            player.add_power_up()
            pyxel.play(2, 6)  # パワーアップ音
        
        elif item.item_type == ITEM_GRENADE:
            # 画面上のすべての敵を破壊（ゲームマネージャーで処理）
            item_manager.grenade_collected = True
        
        elif item.item_type == ITEM_TANK:
            # エクストラライフ
            if player.lives < 9:  # 最大9ライフ
                player.lives += 1
        
        elif item.item_type == ITEM_SHOVEL:
            # 鉄壁でベースを一時的に保護
            item_manager.shovel_timer = 600  # 10秒
        
        elif item.item_type == ITEM_CLOCK:
            # すべての敵を凍結
            item_manager.freeze_timer = 300  # 5秒
        
        elif item.item_type == ITEM_HELMET:
            # 一時的な無敵状態
            player.invincible_timer = 600  # 10秒
    
    def update_bullet_collisions(self, bullet_manager):
        """弾丸同士の衝突を更新する"""
        bullet_manager.update_bullet_collisions()
    
    def check_base_destruction(self, map_manager):
        """ベースが破壊されたかチェックする"""
        base_x, base_y = map_manager.base_position
        return map_manager.get_tile(base_x, base_y) != TILE_BASE