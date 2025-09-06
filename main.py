import pyxel
from constants import *
from game_manager import GameManager

class TankBattle:
    def __init__(self):
        pyxel.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="Tank Battle")
        
        # ゲームコンポーネントを初期化
        self.game_manager = GameManager()
        
        # Pyxelリソースを初期化
        self.init_resources()
        
        pyxel.run(self.update, self.draw)
    
    def init_resources(self):
        """スプライトとサウンドを初期化する"""
        # タンクスプライトを含むpyxresファイルを読み込み
        try:
            pyxel.load("my_resource.pyxres")
            print("Resources loaded successfully")
            # リソース読み込み後にサウンドを初期化
            self.init_sounds()
        except Exception as e:
            print(f"ERROR: Failed to load my_resource.pyxres: {e}")
            print("Please ensure my_resource.pyxres file exists and is valid.")
            pyxel.quit()
            exit(1)
    
    
    def init_sounds(self):
        """リソース読み込み後にゲームサウンドを初期化する"""
        # pyxel.load()によってサウンドが上書きされる可能性があるため再初期化
        self.game_manager.game_context.sound_manager.init_sounds()
        self.game_manager.game_context.sound_manager.init_music()
    
    def update(self):
        """メインゲーム更新ループ"""
        self.game_manager.update()
        
        # Qキーで終了
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()
    
    def draw(self):
        """メインゲーム描画ループ"""
        pyxel.cls(COLOR_BLACK)
        self.game_manager.draw()

if __name__ == "__main__":
    TankBattle()