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
        # Sound 0: タンクエンジン音 - 可聴域の低音ワーブル（本家のアイドリング音風）
        # 4音 x speed4 = 16ティック = 60FPSで8フレーム。player側が8フレーム周期で
        # 再トリガーすることで連続音になり、キーを離すと自然に止まる
        pyxel.sounds[0].set(
            notes="c2d2e2d2",
            tones="ssss",
            volumes="3333",
            effects="nnnn",
            speed=4
        )

        # Sound 1: 発射音 - 下降ノイズによる鋭く短い射撃音
        pyxel.sounds[1].set(
            notes="g3c3",
            tones="nn",
            volumes="73",
            effects="fn",
            speed=5
        )

        # Sound 2: 爆発音 - 下降ノイズによる迫力ある爆発（約0.5秒）
        pyxel.sounds[2].set(
            notes="c2g1e1c1c1",
            tones="nnnnn",
            volumes="76543",
            effects="nnnnf",
            speed=12
        )

        # Sound 3: アイテム取得音 - 上昇アルペジオの明るい取得音
        pyxel.sounds[3].set(
            notes="g3c4e4g4",
            tones="pppp",
            volumes="5667",
            effects="nnnn",
            speed=6
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
        
        # Sound 6: パワーアップ音 - 2オクターブ上昇アルペジオで達成感を演出
        pyxel.sounds[6].set(
            notes="c3e3g3c4e4g4",
            tones="pppppp",
            volumes="455667",
            effects="nnnnnn",
            speed=8
        )

        # Sound 7: 敵撃破音 - 下降ノイズ（爆発音より軽め・短め）
        pyxel.sounds[7].set(
            notes="e2c2g1e1",
            tones="nnnn",
            volumes="7654",
            effects="nnnf",
            speed=10
        )

        # Sound 8: ステージ開始ジングル（本家バトルシティー風の上昇ファンファーレ）
        pyxel.sounds[8].set(
            notes="c3e3g3c4e4c4g3e3c3e3g3c4e4e4e4r",
            tones="tttttttttttttttt",
            volumes="5555666655556660",
            effects="nnnnnnnnnnnnnnnn",
            speed=12
        )
    
    def init_music(self):
        """背景音楽を初期化

        全曲オリジナル作曲（著作権配慮のため本家のメロディは使用しない）。
        構成は docs/sound_system.md を参照。

        - musics[1]: タイトル曲（本家風8bitミリタリーマーチ、8小節ループ）
        - musics[2]: ゲームオーバー曲（短調の哀悼メロディ、4小節）
        - musics[3]: エンディング曲（全クリア祝福のビクトリー曲、8小節ループ）
        """
        # =====================================================================
        # タイトル曲 - オリジナル8bitミリタリーマーチ（ハ長調・8小節）
        # =====================================================================

        # メロディ（パルス波）: 勇ましい行進曲調の主題
        pyxel.sounds[12].set(
            notes="c3c3e3g3c4rg3r"   # 第1小節: 主題（上昇ファンファーレ）
                  "a3a3c4a3g3re3r"   # 第2小節: 応答
                  "f3f3a3f3e3e3g3e3"  # 第3小節: 展開
                  "d3e3f3e3d3rb2r"   # 第4小節: 半終止
                  "c3c3e3g3c4rg3r"   # 第5小節: 主題再現
                  "a3a3c4a3g3re3r"   # 第6小節: 応答
                  "f3a3c4a3d4d4b3g3"  # 第7小節: クライマックス
                  "c4c4c4rc4rrr",    # 第8小節: 終止
            tones="p",
            volumes="76666566",
            effects="n",
            speed=16
        )

        # ベース（三角波）: マーチの「ブン・チャ」パターン
        pyxel.sounds[14].set(
            notes="c2rg1rc2rg1g1"
                  "a1re1ra1re1e1"
                  "f1rc2rf1rc2c2"
                  "g1rd2rg1rg1g1"
                  "c2rg1rc2rg1g1"
                  "a1re1ra1re1e1"
                  "f1rc2rd2rg1g1"
                  "c2c2g1g1c2rrr",
            tones="t",
            volumes="6",
            effects="n",
            speed=16
        )

        # ドラム（ノイズ）: バスドラム(c1)とスネア(d2)の行進リズム
        pyxel.sounds[15].set(
            notes="c1rd2rc1c1d2r" * 7 +  # 基本パターン x 7小節
                  "c1d2c1d2d2d2d2r",     # 第8小節: フィルイン
            tones="n",
            volumes="7464",
            effects="n",
            speed=16
        )

        # 3チャンネル同期のタイトルマーチ
        pyxel.musics[1].set([12], [14], [15], [])

        # =====================================================================
        # ゲームオーバー曲 - 短調の哀悼メロディ（イ短調・4小節、非ループ）
        # =====================================================================

        # メロディ（三角波）: ゆっくり下降する哀しい旋律
        pyxel.sounds[13].set(
            notes="a3rg3rf3re3r"     # 第1小節: 下降
                  "f3e3d3e3c3rrr"    # 第2小節: ため息
                  "e3rd3rc3rb2r"     # 第3小節: さらに下降
                  "a2a2a2rrrrr",     # 第4小節: 終止（主音）
            tones="t",
            volumes="65554443",
            effects="n",
            speed=24
        )

        # ベース（三角波）: 静かな伴奏
        pyxel.sounds[19].set(
            notes="a1re1ra1re1r"
                  "f1rc2rf1rc2r"
                  "c1rg1re1re1r"
                  "a1ra1ra1rrr",
            tones="t",
            volumes="4",
            effects="n",
            speed=24
        )

        pyxel.musics[2].set([13], [19], [], [])

        # =====================================================================
        # エンディング曲 - 全クリア祝福のビクトリー曲（ハ長調・8小節ループ）
        # =====================================================================

        # メロディ（パルス波）: 明るく華やかな祝福の旋律
        pyxel.sounds[9].set(
            notes="g3c4e4g4re4g4r"   # 第1小節: ビクトリーファンファーレ
                  "a4g4e4c4d4e4d4r"  # 第2小節: 喜びのフレーズ
                  "f4e4d4e4f4g4e4c4"  # 第3小節: 流れる展開
                  "d4e4d4b3c4rg3r"   # 第4小節: 半終止
                  "g3c4e4g4re4g4r"   # 第5小節: 主題再現
                  "a4a4g4e4g4a4a4r"  # 第6小節: 高揚
                  "c4e4g4e4a4g4e4d4"  # 第7小節: クライマックス
                  "c4c4c4rc4rrr",    # 第8小節: 終止
            tones="p",
            volumes="66677666",
            effects="n",
            speed=14
        )

        # ベース（三角波）
        pyxel.sounds[10].set(
            notes="c2rg1rc2rg1r"
                  "f1rc2rf1rc2r"
                  "f1ra1rg1rc2r"
                  "g1rd2rg1rg1r"
                  "c2rg1rc2rg1r"
                  "f1rc2rf1rc2r"
                  "a1re1rf1rg1r"
                  "c2c2g1g1c2rrr",
            tones="t",
            volumes="6",
            effects="n",
            speed=14
        )

        # ドラム（ノイズ）: 祝祭的なリズム
        pyxel.sounds[11].set(
            notes="c1rd2d2c1rd2r" * 7 +  # 基本パターン x 7小節
                  "d2d2d2d2c1c1c1r",     # 第8小節: フィルイン
            tones="n",
            volumes="6454",
            effects="n",
            speed=14
        )

        pyxel.musics[3].set([9], [10], [11], [])

        # =====================================================================
        # ステージクリア曲 - 勝利ファンファーレ（ハ長調・4小節・約2.7秒、非ループ）
        # =====================================================================

        # メロディ（パルス波）: 上昇アルペジオ→ヒット連打→駆け下がり→終止
        pyxel.sounds[20].set(
            notes="c3e3g3c4e4rc4r"   # 第1小節: 駆け上がるアルペジオ
                  "e4e4e4rg4g4g4r"   # 第2小節: 勝利のヒット連打
                  "a4g4f4e4f4e4d4c4"  # 第3小節: 華麗な駆け下がり
                  "g4a4g4e4c4rc4r",  # 第4小節: 弾んで終止
            tones="p",
            volumes="77777666",
            effects="n",
            speed=10
        )

        # ベース（三角波）: 力強い土台
        pyxel.sounds[21].set(
            notes="c2rg1rc2rg1r"
                  "c2rg1rc2rg1r"
                  "f1rc2rg1rg1r"
                  "c2c2g1g1c2rc2r",
            tones="t",
            volumes="6",
            effects="n",
            speed=10
        )

        # ドラム（ノイズ）: スネアロールから決めのヒットへ
        pyxel.sounds[22].set(
            notes="d2d2d2d2c1rd2r"   # 第1小節: スネアロールで開幕
                  "c1rd2rc1rd2r"     # 第2小節: マーチビート
                  "c1rd2rc1c1d2d2"   # 第3小節: 畳み掛け
                  "d2d2d2d2c1rc1r",  # 第4小節: ロール→決めの2発
            tones="n",
            volumes="5464",
            effects="n",
            speed=10
        )

        pyxel.musics[4].set([20], [21], [22], [])
    
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
    SOUND_STAGE_START = 8
    
    # Music constants
    MUSIC_GAME = 0
    MUSIC_TITLE = 1
    MUSIC_GAME_OVER = 2
    MUSIC_ENDING = 3
    MUSIC_STAGE_CLEAR = 4
    
    def play_move_sound(self):
        """タンク移動音を再生（エンジン専用チャンネル）"""
        self.play_sound(self.SOUND_MOVE, channel=SOUND_CHANNEL_ENGINE)

    def play_fire_sound(self):
        """弾丸発射音を再生（発射専用チャンネル）"""
        self.play_sound(self.SOUND_FIRE, channel=SOUND_CHANNEL_FIRE)

    def play_explosion_sound(self):
        """Play explosion sound"""
        self.play_sound(self.SOUND_EXPLOSION, channel=SOUND_CHANNEL_EXPLOSION)

    def play_item_sound(self):
        """Play item pickup sound"""
        self.play_sound(self.SOUND_ITEM, channel=SOUND_CHANNEL_ITEM)

    def play_stage_clear_sound(self):
        """Play stage clear sound"""
        self.play_sound(self.SOUND_STAGE_CLEAR, channel=SOUND_CHANNEL_ITEM)

    def play_stage_start_jingle(self):
        """ステージ開始ジングルを再生（本家準拠の開始ファンファーレ）"""
        self.play_sound(self.SOUND_STAGE_START, channel=SOUND_CHANNEL_ITEM)

    def play_game_over_sound(self):
        """Play game over sound"""
        self.play_sound(self.SOUND_GAME_OVER, channel=SOUND_CHANNEL_EXPLOSION)

    def play_power_up_sound(self):
        """Play power up sound"""
        self.play_sound(self.SOUND_POWER_UP, channel=SOUND_CHANNEL_ITEM)

    def play_enemy_destroyed_sound(self):
        """Play enemy destroyed sound"""
        self.play_sound(self.SOUND_ENEMY_DESTROYED, channel=SOUND_CHANNEL_EXPLOSION)
    
    def play_game_music(self):
        """Game background music disabled - using sound effects only"""
        pass  # No background music during gameplay
    
    def play_title_music(self):
        """Play title screen music"""
        self.play_music(self.MUSIC_TITLE)
    
    def play_game_over_music(self):
        """Play game over music"""
        self.play_music(self.MUSIC_GAME_OVER, loop=False)

    def play_ending_music(self):
        """エンディング曲を再生（全クリア祝福のビクトリー曲、ループ）"""
        self.play_music(self.MUSIC_ENDING, loop=True)

    def play_stage_clear_music(self):
        """ステージクリアBGMを再生（3chの勝利ファンファーレ、非ループ）"""
        self.play_music(self.MUSIC_STAGE_CLEAR, loop=False)
    
    def play_hit_sound(self):
        """Play player hit sound"""
        self.play_sound(self.SOUND_EXPLOSION, channel=SOUND_CHANNEL_EXPLOSION)

    def play_death_sound(self):
        """Play death sound"""
        self.play_sound(self.SOUND_GAME_OVER, channel=SOUND_CHANNEL_EXPLOSION)

    def play_pickup_sound(self):
        """Play item pickup sound"""
        self.play_sound(self.SOUND_ITEM, channel=SOUND_CHANNEL_ITEM)