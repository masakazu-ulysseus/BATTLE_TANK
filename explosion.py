import pyxel
from constants import *

class Explosion:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.active = True
        self.timer = 0
        self.animation_sequence = [1, 2, 3]  # 小、中、大
        self.current_frame = 0
        self.frame_duration = 8  # 各爆発スプライトを8フレーム表示
        
    def update(self):
        """爆発アニメーションを更新する"""
        if not self.active:
            return
            
        self.timer += 1
        
        # frame_durationごとにフレームを変更
        if self.timer >= self.frame_duration:
            self.timer = 0
            self.current_frame += 1
            
            # アニメーションシーケンスが完了したら爆発を無効化
            if self.current_frame >= len(self.animation_sequence):
                self.active = False
    
    def draw(self):
        """爆発アニメーションを描画する"""
        if not self.active or self.current_frame >= len(self.animation_sequence):
            return
        
        # 現在の爆発スプライトタイプを取得
        explosion_type = self.animation_sequence[self.current_frame]
        
        # my_resource.pyxres内の爆発スプライト座標
        if explosion_type == 1:
            sprite_x = 224  # 小爆発 (224,0)位置
        elif explosion_type == 2:
            sprite_x = 240  # 中爆発 (240,0)位置
        else:
            sprite_x = 240  # 大爆発 - とりあえず中爆発と同じを使用
        
        # 衝撃点を中心に爆発を配置
        draw_x = int(self.x - TILE_SIZE // 2)
        draw_y = int(self.y - TILE_SIZE // 2)
        
        # 画面内の場合のみ描画
        if (draw_x + TILE_SIZE > 0 and draw_x < SCREEN_WIDTH and 
            draw_y + TILE_SIZE > 0 and draw_y < MAP_HEIGHT * TILE_SIZE):
            pyxel.blt(draw_x, draw_y, 0, sprite_x, 0, TILE_SIZE, TILE_SIZE, 0)

class ExplosionManager:
    def __init__(self):
        self.explosions = []
    
    def add_explosion(self, x, y):
        """指定位置に爆発を追加する"""
        explosion = Explosion(x, y)
        self.explosions.append(explosion)
    
    def update(self):
        """すべての爆発を更新する"""
        for explosion in self.explosions:
            explosion.update()
        
        # 非アクティブな爆発を削除
        self.explosions = [explosion for explosion in self.explosions if explosion.active]
    
    def clear_all(self):
        """すべての爆発をクリアする"""
        self.explosions.clear()
    
    def draw(self):
        """すべての爆発を描画する"""
        for explosion in self.explosions:
            explosion.draw()