"""
ゲームコンテキスト - ゲームの一元的依存関係管理
"""
from explosion import ExplosionManager
from sound_manager import SoundManager


class GameContext:
    """共有ゲームリソースとマネージャーの一元管理コンテナ"""
    
    def __init__(self):
        # 他のシステムが依存するコアマネージャー
        self.explosion_manager = ExplosionManager()
        self.sound_manager = SoundManager()
        
        # システム間で必要になる可能性のあるゲーム状態
        self.current_stage = 1
        self.score = 0
        self.high_score = 0
        
    def create_explosion(self, x, y, play_sound=True):
        """サウンドオプション付きで爆発を作成する一元管理メソッド"""
        self.explosion_manager.add_explosion(x, y)
        if play_sound:
            self.sound_manager.play_explosion_sound()
            
    def play_sound_effect(self, sound_type):
        """一元管理された効果音再生"""
        if sound_type == "explosion":
            self.sound_manager.play_explosion_sound()
        elif sound_type == "hit":
            self.sound_manager.play_hit_sound()
        elif sound_type == "death":
            self.sound_manager.play_death_sound()
        elif sound_type == "pickup":
            self.sound_manager.play_pickup_sound()
        elif sound_type == "power_up":
            self.sound_manager.play_power_up_sound()
        elif sound_type == "enemy_destroyed":
            self.sound_manager.play_enemy_destroyed_sound()
            
    def reset_effects(self):
        """すべての視覚効果をリセットする"""
        self.explosion_manager.clear_all()
        
    def update_effects(self):
        """すべての視覚効果を更新する"""
        self.explosion_manager.update()
        
    def draw_effects(self):
        """すべての視覚効果を描画する"""
        self.explosion_manager.draw()