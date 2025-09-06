# -*- coding: utf-8 -*-
"""
サウンド管理システム

タンクバトルゲームの全音響面を処理：
- Pyxelサウンド合成を使用したプロシージャル効果音生成
- 背景音楽の作曲と再生
- 効果音トリガーとチャンネル管理
- 音声状態管理（有効/無効）
- 適切なタイミングでの協調音響体験

サウンドシステムは外部音声ファイルではなくPyxelの内蔵音響合成を使用し、
すべての音をプログラムで作成します。これにより一貫した音質を確保し、
ファイル依存関係を削減します。

音響アーキテクチャ：
- 効果音：さまざまなチャンネル上の8つの異なる効果
- 背景音楽：3つの異なる音楽トラック（タイトル、ゲーム、ゲームオーバー）
- チャンネル管理：適切なチャンネル割り当てによる音声競合の防止
- プロシージャル生成：Pyxelサウンド合成APIによるすべての音声作成
"""

import pyxel
from constants import *

class SoundManager:
    """
    効果音と背景音楽を含むすべてのゲーム音声を管理します。
    
    SoundManagerはすべてのゲーム音声に対する集中インターフェースを提供し、
    一貫した音質と適切なリソース管理を確保します。
    
    機能：
    - Pyxel合成を使用したプロシージャル音生成
    - ループ制御付きの複数背景音楽トラック
    - チャンネル割り当て付き効果音管理
    - 音声有効/無効機能
    - すべてのゲームシステム向け一貫API
    
    利用可能な効果音：
    - タンク移動音（エンジン音）
    - 弾丸発射音
    - 爆発音（弾丸、敵、タイル）
    - アイテム取得音
    - ステージクリア祝賀音
    - ゲームオーバー/死亡音
    - パワーアップ取得音
    - 敵撃破音
    
    音楽トラック：
    - タイトル画面音楽（ループ）
    - メインゲーム音楽（ループ）
    - ゲームオーバー音楽（非ループ）
    
    属性：
        sound_enabled (bool): 効果音が有効かどうか
        music_enabled (bool): 背景音楽が有効かどうか
    """
    def __init__(self) -> None:
        """
        サウンド管理システムを初期化します。
        
        セットアップ処理：
        1. デフォルトで効果音と音楽の両方を有効にする
        2. プロシージャル合成ですべての効果音を初期化する
        3. すべての背景音楽トラックを初期化する
        4. 即座に使用できるよう音声システムを準備する
        """
        # 音声状態設定
        self.sound_enabled: bool = True   # 効果音有効
        self.music_enabled: bool = True   # 背景音楽有効
        
        # すべての音声コンテンツを初期化
        self.init_sounds()  # 効果音作成
        self.init_music()   # 音楽トラック作成
    
    def init_sounds(self):
        """効果音を初期化"""
        # Sound 0: Tank movement (engine sound) - short consistent buzz
        pyxel.sounds[0].set(
            notes="c0c0c0",
            tones="s",
            volumes="555",
            effects="nnn",
            speed=20
        )
        
        # Sound 1: Bullet fire - Made louder for testing
        pyxel.sounds[1].set(
            notes="a3a3a3a3",
            tones="nnnn",
            volumes="7777",
            effects="vvvv",
            speed=15
        )
        
        # Sound 2: Explosion
        pyxel.sounds[2].set(
            notes="c1e1g1c2",
            tones="n",
            volumes="4321",
            effects="vvvv",
            speed=30
        )
        
        # Sound 3: Item pickup
        pyxel.sounds[3].set(
            notes="c4e4g4c4",
            tones="t",
            volumes="1111",
            effects="vvvv",
            speed=20
        )
        
        # Sound 4: Stage clear - Victory fanfare (タタタターン タンタンタンタターン)
        pyxel.sounds[4].set(
            notes="c4c4c4e4rg4g4g4c4rc4",
            tones="ttttttttttt",
            volumes="66677777777",
            effects="nnnnnnnnnnn",
            speed=20
        )
        
        # Sound 5: Game over / Death - Same melody as Music 2
        pyxel.sounds[5].set(
            notes="e3rc3re3f3g3rf3e3rc3a2g2",
            tones="ttttttttttttt",
            volumes="5555666555433",
            effects="nnnnnnnnnnnnn",
            speed=30
        )
        
        # Sound 6: Power up
        pyxel.sounds[6].set(
            notes="c4e4g4",
            tones="t",
            volumes="111",
            effects="vvv",
            speed=15
        )
        
        # Sound 7: Enemy destroyed
        pyxel.sounds[7].set(
            notes="g2c2e2",
            tones="n",
            volumes="321",
            effects="vvv",
            speed=25
        )
    
    def init_music(self):
        """背景音楽を初期化"""
        # Game music removed - using sound effects only for better gameplay focus
        
        # Title screen music - War Movie March (Based on Pyxel sample)
        
        # MELODY - River Kwai March Whistle (from accurate MIDI)
        pyxel.sounds[12].set(
            "e3e3e3e3 f3f3f3f3 g3g3g3g3 c4c4c4c4 e3e3e3e3 f3f3f3f3 g3g3g3g3 c4c4c4c4 e3e3e3e3 f3f3f3f3 g3g3g3g3 c4c4c4c4 e3e3e3e3 f3f3f3f3 g3g3g3g3 c4c4c4c4 g3g3g3g3 g3g3g3g3 g3g3g3r e3e3e3e3 c4c4c4c4 b3b3b3b3 a3a3a3a3 g3g3g3g3 c4c4c4c4 c4c4c4c4 c4c4c4r a3a3a3a3 f4f4f4f4 e4e4e4e4 d4d4d4d4 c4c4c4c4",
            "p",
            "6",
            "vffn fnff vffs vfnn vffn fnff vffs vfnn vffn fnff vffs vfnn vffn fnff vffn fnff vffn fnff vffs vfnn vffn fnff vffs vfnn vffn fnff vffs vfnn vffn fnff vffs vfnn",
            30
        )
        
        # BASS - Following the whistle melody chord progression (128 notes)
        pyxel.sounds[14].set(
            "c1c1c1c1 f1f1f1f1 c1c1c1c1 c1c1c1c1 c1c1c1c1 f1f1f1f1 c1c1c1c1 c1c1c1c1 c1c1c1c1 f1f1f1f1 c1c1c1c1 c1c1c1c1 c1c1c1c1 f1f1f1f1 c1c1c1c1 c1c1c1c1 g1g1g1g1 g1g1g1g1 g1g1g1r c1c1c1c1 c1c1c1c1 g1g1g1g1 d1d1d1d1 g1g1g1g1 c1c1c1c1 c1c1c1c1 c1c1c1r f1f1f1f1 f1f1f1f1 c1c1c1c1 g1g1g1g1 c1c1c1c1",
            "t",
            "7",
            "nnnn nnnn nnnn nnnn nnnn nnnn nnnn nnnn nnnn nnnn nnnn nnnn nnnn nnnn nnnn nnnn nnnn nnnn nnnn nnnn nnnn nnnn nnnn nnnn nnnn nnnn nnnn nnnn nnnn nnnn nnnn nnnn",
            30
        )
        
        # DRUMS - Authentic Military March Pattern (Snare & Bass Drum)
        pyxel.sounds[15].set(
            "c1r d2c1 c1r d2c1 c1r d2c1 c1r d2c1 c1r d2c1 c1r d2c1 c1r d2c1 c1r d2c1 c1r d2c1 c1r d2c1 c1r d2c1 c1r d2c1 c1r d2c1 c1r d2c1 c1r d2c1 c1r d2c1 c1c1d2d2 c1c1d2d2 c1c1d2r c1r d2c1 c1r d2c1 c1c1d2d2 c1r d2c1 c1c1d2d2 c1r d2c1 c1r d2c1 c1r d2r c1c1d2d2 c1c1d2d2 c1c1d2d2 c1c1d2d2 c1c1d2c1",
            "n",
            "6",
            "vfff vfff vfff vfff vfff vfff vfff vfff vfff vfff vfff vfff vfff vfff vfff vfff vvvv vvvv vvvn vfff vfff vvvv vfff vvvv vfff vfff vffn vvvv vvvv vvvv vvvv vvvv",
            30
        )
        
        # Create synchronized 3-channel war march
        pyxel.musics[1].set([12], [14], [15], [])
        
        # No stage clear BGM - using simple sound effect instead
        
        # Game over music (channel 2) - Beautiful sad melody
        pyxel.sounds[13].set(
            notes="e3rc3re3f3g3rf3e3rc3a2g2",
            tones="ttttttttttttt",
            volumes="5555666555433",
            effects="nnnnnnnnnnnnn",
            speed=30
        )
        
        pyxel.musics[2].set([13], [], [], [])
    
    def play_sound(self, sound_id, channel=0):
        """効果音を再生"""
        if self.sound_enabled:
            pyxel.play(channel, sound_id)
    
    def play_music(self, music_id, loop=True):
        """背景音楽を再生"""
        if self.music_enabled:
            pyxel.playm(music_id, loop=loop)
    
    def stop_music(self):
        """全音楽を停止"""
        pyxel.stop()
    
    def toggle_sound(self):
        """効果音のオン/オフを切り替え"""
        self.sound_enabled = not self.sound_enabled
        return self.sound_enabled
    
    def toggle_music(self):
        """音楽のオン/オフを切り替え"""
        self.music_enabled = not self.music_enabled
        if not self.music_enabled:
            self.stop_music()
        return self.music_enabled
    
    def set_volume(self, volume):
        """マスター音量設定（0.0〜1.0）"""
        # Pyxel doesn't have master volume control, but we can implement muting
        if volume <= 0.0:
            self.sound_enabled = False
            self.music_enabled = False
        else:
            self.sound_enabled = True
            self.music_enabled = True
    
    # Sound effect constants for easy access
    SOUND_MOVE = 0
    SOUND_FIRE = 1
    SOUND_EXPLOSION = 2
    SOUND_ITEM = 3
    SOUND_STAGE_CLEAR = 4
    SOUND_GAME_OVER = 5
    SOUND_POWER_UP = 6
    SOUND_ENEMY_DESTROYED = 7
    
    # Music constants
    MUSIC_GAME = 0
    MUSIC_TITLE = 1
    MUSIC_GAME_OVER = 2
    MUSIC_STAGE_CLEAR = 3
    
    def play_move_sound(self):
        """タンク移動音を再生"""
        self.play_sound(self.SOUND_MOVE)
    
    def play_fire_sound(self):
        """弾丸発射音を再生"""
        self.play_sound(self.SOUND_FIRE)
    
    def play_explosion_sound(self):
        """Play explosion sound"""
        self.play_sound(self.SOUND_EXPLOSION, channel=1)
    
    def play_item_sound(self):
        """Play item pickup sound"""
        self.play_sound(self.SOUND_ITEM, channel=2)
    
    def play_stage_clear_sound(self):
        """Play stage clear sound (on channel 3 to avoid BGM conflict)"""
        self.play_sound(self.SOUND_STAGE_CLEAR, channel=3)
    
    def play_game_over_sound(self):
        """Play game over sound"""
        self.play_sound(self.SOUND_GAME_OVER, channel=1)
    
    def play_power_up_sound(self):
        """Play power up sound"""
        self.play_sound(self.SOUND_POWER_UP, channel=2)
    
    def play_enemy_destroyed_sound(self):
        """Play enemy destroyed sound"""
        self.play_sound(self.SOUND_ENEMY_DESTROYED, channel=1)
    
    def play_game_music(self):
        """Game background music disabled - using sound effects only"""
        pass  # No background music during gameplay
    
    def play_title_music(self):
        """Play title screen music"""
        self.play_music(self.MUSIC_TITLE)
    
    def play_game_over_music(self):
        """Play game over music"""
        self.play_music(self.MUSIC_GAME_OVER, loop=False)
    
    def play_stage_clear_music(self):
        """Play stage clear music - disabled, using sound effect instead"""
        pass  # No stage clear BGM
    
    def play_hit_sound(self):
        """Play player hit sound"""
        self.play_sound(self.SOUND_EXPLOSION, channel=1)
    
    def play_death_sound(self):
        """Play death sound"""
        self.play_sound(self.SOUND_GAME_OVER, channel=1)
    
    def play_pickup_sound(self):
        """Play item pickup sound"""
        self.play_sound(self.SOUND_ITEM, channel=2)