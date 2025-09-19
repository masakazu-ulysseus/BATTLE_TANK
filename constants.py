# -*- coding: utf-8 -*-
"""
タンクバトルゲーム定数モジュール

このモジュールは、Tank Battleゲーム全体で使用されるすべての定数、設定値、
構成パラメータを一元管理します。ゲームバランス、視覚設定、システム
パラメータの信頼できる単一情報源として機能します。

設計原則:
- 全ての定数を論理的なカテゴリに分類
- 明確で自己説明的な名前を使用
- 関連する定数をグループ化
- ゲームバランス調整の容易性を考慮

カテゴリ:
- 画面・表示設定
- ゲームバランス・進行設定
- グリッドシステム・空間定数
- エンティティタイプ・分類
- 物理・移動パラメータ
- 視覚デザイン（色・描画）
- 入力キーマッピング
- ゲーム状態管理

使用方法:
    from constants import *
    # すべての定数を直接利用可能
    if entity_type == TANK_PLAYER:
        # プレイヤー専用ロジック
"""

import pyxel
from typing import Final

# =============================================================================
# 画面・表示設定
# =============================================================================

# 画面解像度設定（ピクセル単位）
SCREEN_WIDTH: Final[int] = 256   # 画面全体の幅（ピクセル）
SCREEN_HEIGHT: Final[int] = 240  # 画面全体の高さ（ピクセル）

# UI領域確保（下部16ピクセルをゲーム情報表示に使用）
UI_HEIGHT: Final[int] = 16       # 画面下部のUI表示エリア高さ

# =============================================================================
# ゲームバランス・進行設定
# =============================================================================

# ステージ進行パラメータ
TOTAL_STAGES: Final[int] = 16                    # ゲーム内の最大ステージ数
ENEMIES_PER_STAGE: Final[int] = 10              # ステージあたりの敵出現数（リリース用バランス）
PLAYER_LIVES: Final[int] = 3                    # プレイヤーの初期ライフ数
MAX_PLAYER_LIVES: Final[int] = 9                # プレイヤーの最大ライフ数

# 敵出現制御
MAX_ENEMIES_ON_SCREEN: Final[int] = 4           # 同時に画面に存在できる敵の最大数
ENEMY_SPAWN_INTERVAL: Final[int] = 64           # 敵の出現間隔（フレーム数）

# スコアリングシステム
ENEMY_SCORE_BASE: Final[int] = 100              # 基本敵撃破スコア
GRENADE_BONUS: Final[int] = 200                 # グレネード使用時のボーナススコア
STAGE_CLEAR_BONUS_BASE: Final[int] = 100        # ステージクリアボーナス（ステージ数×この値）
LIFE_BONUS: Final[int] = 500                    # 残りライフボーナス（ライフ数×この値）
GAME_COMPLETION_BONUS: Final[int] = 10000       # 全ステージクリア時の特別ボーナス

# =============================================================================
# グリッドシステム・空間定数
# =============================================================================

# タイルベースグリッドシステム（16x16ピクセルタイルを使用）
TILE_SIZE: Final[int] = 16                                       # 各グリッドセルのサイズ（ピクセル）
MAP_WIDTH: Final[int] = SCREEN_WIDTH // TILE_SIZE               # グリッド幅: 16タイル
MAP_HEIGHT: Final[int] = (SCREEN_HEIGHT - UI_HEIGHT) // TILE_SIZE # グリッド高さ: 14タイル

# 基地（司令部）位置（固定）
BASE_GRID_X: Final[int] = 7                     # 基地のグリッドX座標
BASE_GRID_Y: Final[int] = 13                    # 基地のグリッドY座標

# プレイヤー初期位置（基地の直前）
PLAYER_START_GRID_X: Final[int] = 7             # プレイヤー開始グリッドX座標
PLAYER_START_GRID_Y: Final[int] = 11            # プレイヤー開始グリッドY座標

# =============================================================================
# 方向定数
# =============================================================================

# 移動・向き方向（タンクの向きと弾丸の進行方向で使用）
UP: Final[int] = 0      # 上方向（-Y軸）
DOWN: Final[int] = 1    # 下方向（+Y軸）
LEFT: Final[int] = 2    # 左方向（-X軸）
RIGHT: Final[int] = 3   # 右方向（+X軸）

# 方向ベクトルマッピング（座標計算用）
DIRECTION_VECTORS: Final[dict[int, tuple[int, int]]] = {
    UP: (0, -1),
    DOWN: (0, 1),
    LEFT: (-1, 0),
    RIGHT: (1, 0)
}

# =============================================================================
# エンティティタイプ分類
# =============================================================================

# タンクタイプ識別子（行動パターン、スプライト、衝突検出で使用）
TANK_PLAYER: Final[int] = 0      # プレイヤー操作タンク
TANK_LIGHT: Final[int] = 1       # 軽装敵タンク（HP: 1、標準性能）
TANK_ARMORED: Final[int] = 2     # 装甲敵タンク（HP: 1、移動速度2倍）
TANK_FAST_SHOT: Final[int] = 3   # 連射敵タンク（HP: 1、高速射撃）
TANK_HEAVY: Final[int] = 4       # 重装敵タンク（HP: 4、ダメージ時スプライト変更）

# 敵タンク設定
ENEMY_TYPES: Final[list[int]] = [TANK_LIGHT, TANK_ARMORED, TANK_FAST_SHOT, TANK_HEAVY]

# 敵タンク基本ヘルス設定
ENEMY_HEALTH: Final[dict[int, int]] = {
    TANK_LIGHT: 1,
    TANK_ARMORED: 1,
    TANK_FAST_SHOT: 1,
    TANK_HEAVY: 4
}

# 敵タンクスコア値
ENEMY_SCORE_VALUES: Final[dict[int, int]] = {
    TANK_LIGHT: 100,
    TANK_ARMORED: 200,
    TANK_FAST_SHOT: 300,
    TANK_HEAVY: 400
}

# =============================================================================
# 物理・移動パラメータ
# =============================================================================

# 基本移動速度（60FPSでフレームあたりピクセル数）
TANK_SPEED: Final[int] = 1       # タンクの基本移動速度
BULLET_SPEED: Final[int] = 2     # 弾丸の基本進行速度

# スムーズ移動システム
MOVE_ANIMATION_FRAMES: Final[int] = 8    # スムーズ移動完了までのフレーム数

# 敵AI設定
AI_DIRECTION_CHANGE_MIN: Final[int] = 60   # 方向転換の最小間隔（フレーム）
AI_DIRECTION_CHANGE_MAX: Final[int] = 180  # 方向転換の最大間隔（フレーム）
AI_PLAYER_TARGET_CHANCE: Final[float] = 0.3  # プレイヤーを狙う確率
AI_ATTACK_RANGE: Final[int] = 12           # 敵の攻撃有効射程（タイル数）

# 敵タンク速度設定
ENEMY_SPEED_MULTIPLIER: Final[dict[int, int]] = {
    TANK_LIGHT: 1,
    TANK_ARMORED: 2,     # 装甲タンクは2倍速
    TANK_FAST_SHOT: 1,
    TANK_HEAVY: 1
}

# 敵タンク発射レート設定（フレーム間隔）
ENEMY_FIRE_RATE: Final[dict[int, int]] = {
    TANK_LIGHT: 90,        # 1.5秒間隔
    TANK_ARMORED: 90,      # 1.5秒間隔
    TANK_FAST_SHOT: 30,    # 0.5秒間隔（高速射撃）
    TANK_HEAVY: 90         # 1.5秒間隔
}

# =============================================================================
# パワーアップ進行システム
# =============================================================================

# プレイヤータンクのパワーレベル（星アイテムによる段階的アップグレード）
POWER_NORMAL: Final[int] = 0      # 基本タンク: 通常弾丸、最大1発
POWER_FAST_SHOT: Final[int] = 1   # 高速弾丸: 弾丸速度2倍、最大1発
POWER_DOUBLE_SHOT: Final[int] = 2 # ダブルショット: 通常速度、最大2発
POWER_SUPER: Final[int] = 3       # スーパータンク: 鉄壁破壊可能、最大2発

# パワーレベル名称（UI表示用）
POWER_LEVEL_NAMES: Final[list[str]] = ["NORMAL", "FAST", "DOUBLE", "SUPER"]

# パワーレベル別弾丸制限
POWER_BULLET_LIMITS: Final[dict[int, int]] = {
    POWER_NORMAL: 1,
    POWER_FAST_SHOT: 1,
    POWER_DOUBLE_SHOT: 2,
    POWER_SUPER: 2
}

# パワーレベル別弾丸速度倍率
POWER_SPEED_MULTIPLIER: Final[dict[int, int]] = {
    POWER_NORMAL: 1,
    POWER_FAST_SHOT: 2,    # ファーストショットは2倍速
    POWER_DOUBLE_SHOT: 1,
    POWER_SUPER: 1
}

# =============================================================================
# マップタイルシステム
# =============================================================================

# タイルタイプ識別子（地形の挙動と描画を定義）
TILE_EMPTY: Final[int] = 0    # 通行可能な空間（視覚なし、衝突なし）
TILE_BRICK: Final[int] = 1    # 破壊可能な茶色壁（移動阻止、全弾丸で破壊可能）
TILE_STEEL: Final[int] = 2    # 破壊困難な灰色壁（移動阻止、スーパー弾丸のみ破壊可能）
TILE_WATER: Final[int] = 3    # 青い水域（タンク移動阻止、弾丸は通過）
TILE_FOREST: Final[int] = 4   # 緑の森カバー（通行可能、視覚的カバーのみ）
TILE_ICE: Final[int] = 5      # 氷地形（通行可能、現在のステージでは未使用）
TILE_BASE: Final[int] = 6     # プレイヤーベース（破壊されるとゲームオーバー）

# タイル通行可能性設定
PASSABLE_TILES: Final[set[int]] = {TILE_EMPTY, TILE_FOREST, TILE_ICE}
IMPASSABLE_TILES: Final[set[int]] = {TILE_BRICK, TILE_STEEL, TILE_WATER, TILE_BASE}

# タイル破壊可能性設定
DESTRUCTIBLE_BY_NORMAL: Final[set[int]] = {TILE_BRICK}
DESTRUCTIBLE_BY_SUPER: Final[set[int]] = {TILE_BRICK, TILE_STEEL}

# スプライト座標設定（my_resource.pyxres内の位置）
TILE_SPRITE_COORDS: Final[dict[int, tuple[int, int]]] = {
    TILE_BRICK: (0, 48),
    TILE_STEEL: (16, 48),
    TILE_WATER: (32, 48),
    TILE_FOREST: (48, 48),
    TILE_ICE: (64, 48),
    TILE_BASE: (80, 48)
}

# =============================================================================
# 視覚デザイン - PYXEL カラーパレット
# =============================================================================

# 標準Pyxel 16色パレット（インデックス0-15）
# スプライト、テキスト、プログラム描画を含むすべての描画で使用
COLOR_BLACK: Final[int] = 0        # 背景、オーバーレイの暗さ、透明色
COLOR_DARK_BLUE: Final[int] = 1    # 水の基本色
COLOR_DARK_PURPLE: Final[int] = 2  # 特殊効果（未使用）
COLOR_DARK_GREEN: Final[int] = 3   # 森の基本色
COLOR_BROWN: Final[int] = 4        # レンガ壁の基本色
COLOR_DARK_GREY: Final[int] = 5    # タンクの履帯、砲身の詳細
COLOR_LIGHT_GREY: Final[int] = 6   # 鉄壁の基本色
COLOR_WHITE: Final[int] = 7        # テキスト、UI要素、ハイライト、敵弾丸
COLOR_RED: Final[int] = 8          # ゲームオーバーテキスト、スーパーパワーレベル、エラー表示
COLOR_ORANGE: Final[int] = 9       # 特殊効果（未使用）
COLOR_YELLOW: Final[int] = 10      # プレイヤータンク、ベース、タイトルテキスト、プレイヤー弾丸
COLOR_GREEN: Final[int] = 11       # ファーストショットパワー、成功テキスト、UI強調
COLOR_CYAN: Final[int] = 12        # ダブルショットパワー、水のハイライト、ゲームパッド表示
COLOR_LIGHT_BLUE: Final[int] = 13  # 特殊効果（未使用）
COLOR_PINK: Final[int] = 14        # 特殊効果（未使用）
COLOR_PEACH: Final[int] = 15       # 特殊効果（未使用）

# パワーレベル別色設定
POWER_LEVEL_COLORS: Final[dict[int, int]] = {
    POWER_NORMAL: COLOR_YELLOW,
    POWER_FAST_SHOT: COLOR_GREEN,
    POWER_DOUBLE_SHOT: COLOR_CYAN,
    POWER_SUPER: COLOR_RED
}

# =============================================================================
# アイテムシステム - パワーアップ・コレクタブル
# =============================================================================

# パワーアップアイテムタイプ（特定の敵が破壊されたときに出現）
ITEM_STAR: Final[int] = 0      # プレイヤーのパワーレベルを上昇（POWER_SUPERまで）
ITEM_GRENADE: Final[int] = 1   # 画面上のすべての敵を即座に破壊
ITEM_TANK: Final[int] = 2      # エクストラライフを付与（最大9ライフまで）
ITEM_SHOVEL: Final[int] = 3    # ベースを鉄壁で一時的に保護
ITEM_CLOCK: Final[int] = 4     # すべての敵を一時的に凍結
ITEM_HELMET: Final[int] = 5    # 一時的な無敵状態を付与

# アイテム効果時間設定（フレーム数）
ITEM_EFFECT_DURATION: Final[dict[int, int]] = {
    ITEM_SHOVEL: 600,   # 10秒間の基地保護
    ITEM_CLOCK: 300,    # 5秒間の敵凍結
    ITEM_HELMET: 600    # 10秒間の無敵状態
}

# アイテムキャリア確率
ITEM_CARRIER_PROBABILITY: Final[float] = 0.25  # 25%の敵がアイテムを持つ

# アイテム表示設定
ITEM_VISIBILITY_DURATION: Final[int] = 600  # アイテムの表示時間（10秒）
ITEM_SPRITE_SIZE: Final[int] = 16           # アイテムスプライトサイズ

# アイテムスプライト座標（my_resource.pyxres内の位置）
ITEM_SPRITE_COORDS: Final[dict[int, tuple[int, int]]] = {
    ITEM_STAR: (0, 80),
    ITEM_GRENADE: (16, 80),
    ITEM_TANK: (32, 80),
    ITEM_SHOVEL: (48, 80),
    ITEM_CLOCK: (64, 80),
    ITEM_HELMET: (80, 80)
}

# =============================================================================
# 爆発・エフェクトシステム
# =============================================================================

# 爆発アニメーション設定
EXPLOSION_FRAME_DURATION: Final[int] = 8    # 各爆発フレームの表示時間
EXPLOSION_TOTAL_FRAMES: Final[int] = 3      # 爆発アニメーションの総フレーム数
EXPLOSION_TOTAL_DURATION: Final[int] = EXPLOSION_FRAME_DURATION * EXPLOSION_TOTAL_FRAMES

# 爆発スプライト座標
EXPLOSION_SPRITE_COORDS: Final[list[tuple[int, int]]] = [
    (208, 0),  # 小爆発
    (224, 0),  # 中爆発
    (240, 0)   # 大爆発
]

# 霧エフェクト（敵出現前）設定
FOG_ANIMATION_FRAMES: Final[int] = 4        # 霧アニメーションのフレーム数
FOG_FRAME_DURATION: Final[int] = 8          # 各霧フレームの表示時間
FOG_SPRITE_COORDS: Final[list[tuple[int, int]]] = [
    (176, 0),  # 霧1
    (192, 0)   # 霧2
]
FOG_SEQUENCE: Final[list[int]] = [1, 2, 1, 2]  # 霧アニメーション順序

# =============================================================================
# オーディオ・サウンドシステム
# =============================================================================

# サウンドチャンネル設定
SOUND_CHANNEL_ENGINE: Final[int] = 0        # エンジン音・移動音
SOUND_CHANNEL_FIRE: Final[int] = 1          # 発射音・爆発音
SOUND_CHANNEL_ITEM: Final[int] = 2          # アイテム音・効果音
SOUND_CHANNEL_MUSIC: Final[int] = 3         # 音楽・BGM

# サウンド再生間隔
ENGINE_SOUND_INTERVAL: Final[int] = 8       # エンジン音の再生間隔

# =============================================================================
# ゲーム状態管理
# =============================================================================

# メインゲーム状態（どのシステムがアクティブで何が描画されるかを制御）
STATE_TITLE: Final[int] = 0       # ハイスコア表示付きタイトル画面
STATE_GAME: Final[int] = 1        # すべてのシステムが動作するアクティブゲームプレイ
STATE_GAME_OVER: Final[int] = 2   # 最終スコア付きゲームオーバー画面
STATE_STAGE_CLEAR: Final[int] = 3 # ステージクリア祝福画面

# 状態遷移タイマー設定
GAME_OVER_TIMER: Final[int] = 300   # ゲームオーバー画面表示時間（5秒）
STAGE_CLEAR_TIMER: Final[int] = 120 # ステージクリア画面表示時間（2秒）

# =============================================================================
# 入力コントロールマッピング
# =============================================================================

# プレイヤー入力コントロール（Pyxelキー定数にマッピング）
KEY_UP: Final[int] = pyxel.KEY_UP       # タンクを上に移動
KEY_DOWN: Final[int] = pyxel.KEY_DOWN   # タンクを下に移動
KEY_LEFT: Final[int] = pyxel.KEY_LEFT   # タンクを左に移動
KEY_RIGHT: Final[int] = pyxel.KEY_RIGHT # タンクを右に移動
KEY_FIRE: Final[int] = pyxel.KEY_SPACE  # 弾丸を発射
KEY_START: Final[int] = pyxel.KEY_RETURN # ゲーム開始、画面進行
KEY_QUIT: Final[int] = pyxel.KEY_Q      # ゲーム終了

# ゲームパッド1コントロール（モバイル対応・アクセシビリティ向上）
GAMEPAD_UP: Final[int] = pyxel.GAMEPAD1_BUTTON_DPAD_UP       # ゲームパッドで上に移動
GAMEPAD_DOWN: Final[int] = pyxel.GAMEPAD1_BUTTON_DPAD_DOWN   # ゲームパッドで下に移動
GAMEPAD_LEFT: Final[int] = pyxel.GAMEPAD1_BUTTON_DPAD_LEFT   # ゲームパッドで左に移動
GAMEPAD_RIGHT: Final[int] = pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT # ゲームパッドで右に移動
GAMEPAD_FIRE: Final[int] = pyxel.GAMEPAD1_BUTTON_A           # ゲームパッドで弾丸発射・メニュー操作（統合）
GAMEPAD_START: Final[int] = pyxel.GAMEPAD1_BUTTON_B          # ゲームパッドでゲーム開始、画面進行

# =============================================================================
# デバッグ・開発設定
# =============================================================================

# 開発時の設定（製品版では調整が必要）
DEBUG_MODE: Final[bool] = False             # デバッグ情報の表示制御
ENEMY_SPAWN_DEBUG: Final[bool] = False      # 敵出現デバッグ情報
COLLISION_DEBUG: Final[bool] = False        # 衝突判定可視化

# タイマー関連設定
INVINCIBLE_FRAMES: Final[int] = 120         # プレイヤー無敵時間（2秒）
DELAYED_DESTRUCTION_FRAMES: Final[int] = 24 # タイル破壊遅延時間

# UI関連設定
TEXT_CHAR_WIDTH: Final[int] = 4             # Pyxelフォントの文字幅
FLASH_INTERVAL: Final[int] = 30             # 点滅エフェクトの間隔（0.5秒）

# =============================================================================
# スプライトシステム設定
# =============================================================================

# スプライトファイル設定
SPRITE_FILE: Final[str] = "my_resource.pyxres"
SPRITE_SIZE: Final[int] = 16                # 標準スプライトサイズ

# プレイヤースプライト座標（通行可能タイル領域を避けるため+16オフセット）
PLAYER_SPRITE_OFFSET: Final[int] = 16
PLAYER_SPRITE_COORDS: Final[dict[int, tuple[int, int]]] = {
    UP: (16, 0),
    RIGHT: (32, 0),
    LEFT: (48, 0),
    DOWN: (64, 0)
}

# 敵スプライト座標
ENEMY_SPRITE_COORDS: Final[dict[int, dict[int, tuple[int, int]]]] = {
    TANK_LIGHT: {
        UP: (0, 16), RIGHT: (16, 16), LEFT: (32, 16), DOWN: (48, 16)
    },
    TANK_ARMORED: {
        UP: (64, 16), RIGHT: (80, 16), LEFT: (96, 16), DOWN: (112, 16)
    },
    TANK_FAST_SHOT: {
        UP: (128, 16), RIGHT: (144, 16), LEFT: (160, 16), DOWN: (176, 16)
    },
    TANK_HEAVY: {
        UP: (192, 16), RIGHT: (208, 16), LEFT: (224, 16), DOWN: (240, 16)
    }
}

# 重装タンクダメージ時スプライト座標
TANK_HEAVY_DAMAGED_COORDS: Final[dict[int, tuple[int, int]]] = {
    UP: (0, 32), RIGHT: (16, 32), LEFT: (32, 32), DOWN: (48, 32)
}

# スプライト読み込み検証用の最小サイズ
MIN_SPRITE_WIDTH: Final[int] = 256
MIN_SPRITE_HEIGHT: Final[int] = 48

# =============================================================================
# エラーメッセージ・ユーザー向け文字列
# =============================================================================

# エラーメッセージ
ERROR_RESOURCE_LOADING: Final[str] = "ERROR: Failed to load my_resource.pyxres"
ERROR_RESOURCE_MISSING: Final[str] = "Please ensure my_resource.pyxres file exists and is valid."
ERROR_SPRITE_FALLBACK: Final[str] = "Using fallback rendering due to missing sprites"

# ゲーム表示テキスト
GAME_TITLE: Final[str] = "TANK BATTLE"
GAME_SUBTITLE: Final[str] = "DEFEND YOUR BASE!"

# 操作説明テキスト
CONTROLS_MOVE: Final[str] = "ARROW KEYS: MOVE"
CONTROLS_FIRE: Final[str] = "SPACE: FIRE"
CONTROLS_GAMEPAD: Final[str] = "GAMEPAD: D-PAD MOVE, A-BUTTON FIRE"
CONTROLS_QUIT: Final[str] = "Q: QUIT"
PROMPT_START: Final[str] = "PRESS ENTER OR A BUTTON TO START"

# ゲーム状態表示テキスト
TEXT_HIGH_SCORE: Final[str] = "HIGH SCORE: {:06d}"
TEXT_GAME_OVER: Final[str] = "GAME OVER"
TEXT_FINAL_SCORE: Final[str] = "FINAL SCORE: {:06d}"
TEXT_NEW_HIGH_SCORE: Final[str] = "NEW HIGH SCORE!"
TEXT_STAGE_CLEAR: Final[str] = "STAGE {} CLEAR!"

# UI表示テキスト
UI_SCORE: Final[str] = "SCORE:{:06d}"
UI_LIVES: Final[str] = "LIVES:{}"
UI_STAGE: Final[str] = "STAGE:{:02d}"
UI_KILLED: Final[str] = "KILLED:{:02d}"
UI_POWER: Final[str] = "POWER:{}"

# =============================================================================
# 型定義用エイリアス
# =============================================================================

# 座標系
GridPosition = tuple[int, int]              # グリッド座標 (x, y)
PixelPosition = tuple[float, float]         # ピクセル座標 (x, y)
Rectangle = tuple[int, int, int, int]       # 矩形 (x, y, width, height)
SpriteCoord = tuple[int, int]              # スプライト座標 (x, y)

# ゲーム状態
GameState = int                            # ゲーム状態値
PowerLevel = int                           # パワーレベル値
Direction = int                            # 方向値
TankType = int                             # タンクタイプ値
TileType = int                             # タイルタイプ値
ItemType = int                             # アイテムタイプ値