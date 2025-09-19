# -*- coding: utf-8 -*-
"""
敵タンクシステムモジュール

Tank Battleゲームにおける敵タンクのAI、動作、管理を処理する。
異なるタイプの敵タンクの行動パターンと、敵の出現・管理システムを実装。

主要コンポーネント:
- Enemy: 個別の敵タンクのAIと動作
- EnemyManager: 敵の出現、管理、霧エフェクト制御

敵タンクタイプ:
- TANK_LIGHT: 基本的な敵タンク（HP: 1、標準性能）
- TANK_ARMORED: 高速移動敵タンク（HP: 1、移動速度2倍）
- TANK_FAST_SHOT: 連射敵タンク（HP: 1、高速射撃）
- TANK_HEAVY: 重装敵タンク（HP: 4、ダメージ時視覚変化）

設計原則:
- 予測可能だが挑戦的なAI行動
- ステージ進行に基づく動的な敵構成
- 効率的な出現管理とパフォーマンス最適化
- アイテムドロップシステムの統合
"""

from typing import List, Tuple, Optional, TYPE_CHECKING
import pyxel
import random

from constants import *

# 型ヒント用のインポート（循環インポート回避）
if TYPE_CHECKING:
    from map_manager import MapManager
    from player import Player
    from bullet import BulletManager


class Enemy:
    """
    個別の敵タンクのAI、動作、状態を管理するクラス。

    各敵タンクは独立したAIを持ち、プレイヤーや基地への攻撃、
    障害物回避、移動パターンを制御する。タンクタイプに応じて
    異なる能力と行動特性を持つ。

    属性:
        x (float): 現在のXピクセル座標
        y (float): 現在のYピクセル座標
        enemy_type (int): 敵タンクタイプ（TANK_LIGHT等）
        direction (int): 現在の向き（UP/DOWN/LEFT/RIGHT）
        health (int): 現在のヘルスポイント
        active (bool): タンクが活動中かどうか

        # 移動システム
        move_timer (int): スムーズ移動の残りフレーム数
        target_x (int): 移動目標のX座標
        target_y (int): 移動目標のY座標
        is_moving (bool): 現在移動中かどうか

        # AI制御
        ai_timer (int): AI判定用の汎用タイマー
        fire_timer (int): 発射間隔制御タイマー
        change_direction_timer (int): 方向転換タイマー

        # アイテムシステム
        carries_item (bool): アイテムを保持しているか
        item_type (Optional[int]): 保持しているアイテムタイプ
    """

    def __init__(self, x: int, y: int, enemy_type: int) -> None:
        """
        敵タンクを初期化する。

        Args:
            x (int): 初期Xピクセル座標
            y (int): 初期Yピクセル座標
            enemy_type (int): 敵タンクタイプ定数
        """
        # 基本位置と状態
        self.x: float = float(x)
        self.y: float = float(y)
        self.enemy_type: int = enemy_type
        self.direction: int = random.choice([UP, DOWN, LEFT, RIGHT])
        self.health: int = self._get_max_health()
        self.active: bool = True

        # スムーズ移動システム
        self.move_timer: int = 0
        self.target_x: int = x
        self.target_y: int = y
        self.is_moving: bool = False

        # AI制御タイマー
        self.ai_timer: int = 0
        self.fire_timer: int = 0
        self.change_direction_timer: int = random.randint(
            AI_DIRECTION_CHANGE_MIN, AI_DIRECTION_CHANGE_MAX
        )

        # アイテムシステム（25%の確率でアイテムを保持）
        self.carries_item: bool = False
        self.item_type: Optional[int] = None
        self._initialize_item_carrier()

    def _get_max_health(self) -> int:
        """
        敵タイプに基づく最大ヘルスポイントを取得する。

        Returns:
            int: タイプに応じた最大HP値
        """
        return ENEMY_HEALTH.get(self.enemy_type, 1)

    def _get_speed(self) -> int:
        """
        敵タイプに基づく移動速度を取得する。

        Returns:
            int: タイプに応じた移動速度倍率
        """
        return TANK_SPEED * ENEMY_SPEED_MULTIPLIER.get(self.enemy_type, 1)

    def _get_fire_rate(self) -> int:
        """
        敵タイプに基づく発射レートを取得する。

        Returns:
            int: 発射間隔フレーム数
        """
        return ENEMY_FIRE_RATE.get(self.enemy_type, 90)

    def _initialize_item_carrier(self) -> None:
        """
        アイテムキャリア設定を初期化する。

        25%の確率でランダムなアイテムを保持する敵として設定。
        """
        if random.random() < ITEM_CARRIER_PROBABILITY:
            self.carries_item = True
            # 全アイテムタイプからランダム選択
            available_items = [
                ITEM_STAR, ITEM_GRENADE, ITEM_TANK,
                ITEM_SHOVEL, ITEM_CLOCK, ITEM_HELMET
            ]
            self.item_type = random.choice(available_items)

    def update(self, map_manager: 'MapManager', player: 'Player',
               bullet_manager: 'BulletManager') -> None:
        """
        敵タンクのAI、移動、行動を毎フレーム更新する。

        更新処理順序:
        1. 境界チェックによる安全性確認
        2. 各種タイマーの更新
        3. スムーズ移動または新しいAI判定
        4. 発射判定と実行

        Args:
            map_manager (MapManager): 衝突検出用マップマネージャー
            player (Player): ターゲット追跡用プレイヤーインスタンス
            bullet_manager (BulletManager): 弾丸生成用マネージャー
        """
        if not self.active:
            return

        # 安全性チェック: 画面境界外のタンクを非活性化
        if self._is_out_of_bounds():
            self.active = False
            return

        # タイマー更新
        self._update_timers()

        # 移動処理：スムーズ移動中か新しいAI判定
        if self.move_timer > 0:
            self.move_timer -= 1
            self._smooth_move()
        else:
            self._update_ai(map_manager, player, bullet_manager)

        # 発射判定
        self._try_fire(bullet_manager, player)

    def _is_out_of_bounds(self) -> bool:
        """
        タンクが有効な境界外にいるかをチェックする。

        Returns:
            bool: 境界外の場合True
        """
        margin = TILE_SIZE  # 境界外許容範囲
        return (self.x < -margin or
                self.x >= SCREEN_WIDTH + margin or
                self.y < -margin or
                self.y >= MAP_HEIGHT * TILE_SIZE + margin)

    def _update_timers(self) -> None:
        """すべてのAI制御タイマーを更新する。"""
        self.ai_timer += 1
        self.fire_timer += 1
        self.change_direction_timer -= 1

    def _update_ai(self, map_manager: 'MapManager', player: 'Player',
                   bullet_manager: 'BulletManager') -> None:
        """
        敵タンクのAI行動を更新する。

        AI行動パターン:
        1. 定期的または障害物により方向転換
        2. 可能であれば前進移動
        3. 30%の確率でプレイヤーを追跡

        Args:
            map_manager (MapManager): 経路判定用
            player (Player): 追跡対象
            bullet_manager (BulletManager): 現在未使用
        """
        # 方向転換判定（定期的または前進不可時）
        if (self.change_direction_timer <= 0 or
            not self._can_move_forward(map_manager)):
            self._choose_new_direction(map_manager, player)
            self.change_direction_timer = random.randint(
                AI_DIRECTION_CHANGE_MIN, AI_DIRECTION_CHANGE_MAX
            )

        # 前進移動の試行
        if self._can_move_forward(map_manager):
            dx, dy = self._get_direction_vector()
            self._start_move(dx * TILE_SIZE, dy * TILE_SIZE)

    def _choose_new_direction(self, map_manager: 'MapManager',
                             player: 'Player') -> None:
        """
        新しい移動方向を選択する。

        選択アルゴリズム:
        1. 移動可能な方向を全て調査
        2. 30%の確率でプレイヤー方向を優先
        3. それ以外はランダム選択

        Args:
            map_manager (MapManager): 移動可能性チェック用
            player (Player): 追跡対象
        """
        # 移動可能な方向を調査
        possible_directions = []
        current_direction = self.direction

        for direction in [UP, DOWN, LEFT, RIGHT]:
            self.direction = direction
            if self._can_move_forward(map_manager):
                possible_directions.append(direction)

        # 元の方向に復元
        self.direction = current_direction

        if not possible_directions:
            return

        # プレイヤー追跡AI（30%の確率）
        if (random.random() < AI_PLAYER_TARGET_CHANCE and
            player.lives > 0):
            target_direction = self._calculate_player_direction(player)
            if target_direction in possible_directions:
                self.direction = target_direction
                return

        # ランダム方向選択
        self.direction = random.choice(possible_directions)

    def _calculate_player_direction(self, player: 'Player') -> int:
        """
        プレイヤーへの最短方向を計算する。

        Args:
            player (Player): 対象プレイヤー

        Returns:
            int: プレイヤー方向の方向定数
        """
        dx = player.x - self.x
        dy = player.y - self.y

        # より大きな距離の軸を優先
        if abs(dx) > abs(dy):
            return RIGHT if dx > 0 else LEFT
        else:
            return DOWN if dy > 0 else UP

    def _can_move_forward(self, map_manager: 'MapManager') -> bool:
        """
        現在の方向に前進可能かをチェックする。

        Args:
            map_manager (MapManager): 衝突検出用

        Returns:
            bool: 前進可能な場合True
        """
        dx, dy = self._get_direction_vector()
        return self._can_move(dx * TILE_SIZE, dy * TILE_SIZE, map_manager)

    def _get_direction_vector(self) -> Tuple[int, int]:
        """
        現在の方向の移動ベクトルを取得する。

        Returns:
            Tuple[int, int]: (dx, dy)の方向ベクトル
        """
        return DIRECTION_VECTORS.get(self.direction, (0, 0))

    def _start_move(self, dx: int, dy: int) -> None:
        """
        指定されたオフセットへのスムーズ移動を開始する。

        Args:
            dx (int): X方向オフセット（ピクセル）
            dy (int): Y方向オフセット（ピクセル）
        """
        self.target_x = self.x + dx
        self.target_y = self.y + dy
        self.move_timer = MOVE_ANIMATION_FRAMES
        self.is_moving = True

    def _smooth_move(self) -> None:
        """
        目標位置へのスムーズ移動を1フレーム実行する。

        境界チェック付きで安全な移動を保証。
        """
        if self.move_timer <= 0:
            # 移動完了：目標位置が有効な場合のみ設定
            if self._is_valid_position(self.target_x, self.target_y):
                self.x = float(self.target_x)
                self.y = float(self.target_y)
            self.is_moving = False
            return

        # 線形補間による移動
        move_x = (self.target_x - self.x) / (self.move_timer + 1)
        move_y = (self.target_y - self.y) / (self.move_timer + 1)

        self.x += move_x
        self.y += move_y

    def _is_valid_position(self, x: float, y: float) -> bool:
        """
        指定された位置が有効な範囲内かをチェックする。

        Args:
            x (float): チェックするX座標
            y (float): チェックするY座標

        Returns:
            bool: 有効な位置の場合True
        """
        return (0 <= x < SCREEN_WIDTH - TILE_SIZE and
                0 <= y < MAP_HEIGHT * TILE_SIZE - TILE_SIZE)

    def _can_move(self, dx: int, dy: int, map_manager: 'MapManager') -> bool:
        """
        指定されたオフセットに移動可能かをチェックする。

        Args:
            dx (int): X方向オフセット
            dy (int): Y方向オフセット
            map_manager (MapManager): 衝突検出用

        Returns:
            bool: 移動可能な場合True
        """
        new_x = self.x + dx
        new_y = self.y + dy

        # 画面境界チェック
        if not self._is_valid_position(new_x, new_y):
            return False

        # マップタイル衝突チェック
        return self._check_map_collision(new_x, new_y, map_manager)

    def _check_map_collision(self, x: float, y: float,
                           map_manager: 'MapManager') -> bool:
        """
        指定位置でのマップタイル衝突をチェックする。

        Args:
            x (float): チェックするX座標
            y (float): チェックするY座標
            map_manager (MapManager): マップデータアクセス用

        Returns:
            bool: 移動可能な場合True
        """
        # タンクの4つの角をチェック
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

    def _try_fire(self, bullet_manager: 'BulletManager', player: 'Player') -> None:
        """
        発射条件をチェックし、可能であれば弾丸を発射する。

        発射条件:
        1. 発射レート制限をクリア
        2. 既存弾丸数が制限以下
        3. 攻撃チャンス判定（戦術的 vs ランダム）

        Args:
            bullet_manager (BulletManager): 弾丸生成用
            player (Player): 攻撃対象の判定用
        """
        # 発射レート制限チェック
        if self.fire_timer < self._get_fire_rate():
            return

        # 既存弾丸数制限チェック
        existing_bullets = bullet_manager.get_bullets_by_owner(self.enemy_type)
        if len(existing_bullets) >= 1:
            return

        # 攻撃方向と発射確率の判定
        target_direction = self._get_best_attack_direction(player)

        # 戦術的攻撃（70%）vs ランダム攻撃（20%）
        fire_chance = 0.7 if target_direction else 0.2

        if random.random() < fire_chance:
            # 攻撃方向が決まっている場合は向きを変更
            if target_direction:
                self.direction = target_direction

            # 発射実行
            self._execute_fire(bullet_manager)

    def _get_best_attack_direction(self, player: 'Player') -> Optional[int]:
        """
        プレイヤーまたは基地への最適な攻撃方向を判定する。

        攻撃優先度:
        1. プレイヤーとの直線攻撃（水平/垂直）
        2. 基地との直線攻撃
        3. 攻撃不可能（None）

        Args:
            player (Player): 攻撃対象プレイヤー

        Returns:
            Optional[int]: 最適攻撃方向またはNone
        """
        # 座標をグリッド単位に変換
        player_grid_x = int(player.x // TILE_SIZE)
        player_grid_y = int(player.y // TILE_SIZE)
        enemy_grid_x = int(self.x // TILE_SIZE)
        enemy_grid_y = int(self.y // TILE_SIZE)

        # 各方向での攻撃可能性をチェック
        directions_to_check = [
            (UP, 0, -1),
            (DOWN, 0, 1),
            (LEFT, -1, 0),
            (RIGHT, 1, 0)
        ]

        # プレイヤーへの攻撃チェック（優先度1）
        for direction, dx, dy in directions_to_check:
            if self._can_hit_target(
                enemy_grid_x, enemy_grid_y,
                player_grid_x, player_grid_y,
                dx, dy
            ):
                return direction

        # 基地への攻撃チェック（優先度2）
        for direction, dx, dy in directions_to_check:
            if self._can_hit_target(
                enemy_grid_x, enemy_grid_y,
                BASE_GRID_X, BASE_GRID_Y,
                dx, dy
            ):
                return direction

        return None

    def _can_hit_target(self, start_x: int, start_y: int,
                       target_x: int, target_y: int,
                       dx: int, dy: int) -> bool:
        """
        指定された方向から目標への射線が有効かをチェックする。

        Args:
            start_x (int): 開始グリッドX座標
            start_y (int): 開始グリッドY座標
            target_x (int): 目標グリッドX座標
            target_y (int): 目標グリッドY座標
            dx (int): 方向ベクトルX成分
            dy (int): 方向ベクトルY成分

        Returns:
            bool: 射線が有効な場合True
        """
        # 直線上の配置チェック
        if dx != 0 and start_y != target_y:
            return False
        if dy != 0 and start_x != target_x:
            return False

        # 距離と方向の検証
        distance_x = abs(target_x - start_x)
        distance_y = abs(target_y - start_y)

        # 有効射程内（12タイル）で正しい方向への射撃
        if dx > 0 and target_x > start_x and distance_x <= AI_ATTACK_RANGE:
            return True
        elif dx < 0 and target_x < start_x and distance_x <= AI_ATTACK_RANGE:
            return True
        elif dy > 0 and target_y > start_y and distance_y <= AI_ATTACK_RANGE:
            return True
        elif dy < 0 and target_y < start_y and distance_y <= AI_ATTACK_RANGE:
            return True

        return False

    def _execute_fire(self, bullet_manager: 'BulletManager') -> None:
        """
        弾丸を生成し発射を実行する。

        Args:
            bullet_manager (BulletManager): 弾丸追加先マネージャー
        """
        # 発射タイマーをリセット
        self.fire_timer = 0

        # 弾丸を生成して追加
        bullet = self._create_bullet()
        bullet_manager.add_bullet(bullet)

    def _create_bullet(self) -> 'Bullet':
        """
        敵タンクの現在状態に基づいて弾丸を生成する。

        Returns:
            Bullet: 新しい弾丸インスタンス
        """
        from bullet import Bullet  # 循環インポート回避

        # 弾丸開始位置（タンク中央）
        bullet_x = self.x + TILE_SIZE // 2
        bullet_y = self.y + TILE_SIZE // 2

        # 方向に基づく位置調整（砲口先端）
        if self.direction == UP:
            bullet_y = self.y
        elif self.direction == DOWN:
            bullet_y = self.y + TILE_SIZE
        elif self.direction == LEFT:
            bullet_x = self.x
        elif self.direction == RIGHT:
            bullet_x = self.x + TILE_SIZE

        # タイプ別弾丸速度
        bullet_speed = BULLET_SPEED
        if self.enemy_type == TANK_FAST_SHOT:
            bullet_speed *= 2

        return Bullet(
            bullet_x, bullet_y, self.direction,
            bullet_speed, self.enemy_type
        )

    def take_damage(self) -> bool:
        """
        敵タンクにダメージを与える。

        Returns:
            bool: タンクが破壊された場合True
        """
        self.health -= 1
        if self.health <= 0:
            self.active = False
            return True
        return False

    def get_rect(self) -> Rectangle:
        """
        衝突検出用の境界矩形を取得する。

        Returns:
            Rectangle: (x, y, width, height)の矩形
        """
        return (int(self.x), int(self.y), TILE_SIZE, TILE_SIZE)

    def get_score_value(self) -> int:
        """
        この敵を撃破した時のスコア値を取得する。

        Returns:
            int: 敵タイプに応じたスコア値
        """
        return ENEMY_SCORE_VALUES.get(self.enemy_type, ENEMY_SCORE_BASE)

    def draw(self) -> None:
        """
        敵タンクを画面に描画する。

        描画機能:
        - タイプと方向に応じたスプライト選択
        - 重装タンクのダメージ状態表示
        - 画面境界クリッピング
        - エラー時のフォールバック表示
        """
        if not self.active:
            return

        # スプライトシステムの利用可能性をチェック
        sprite_width = pyxel.images[0].width
        sprite_height = pyxel.images[0].height

        if sprite_width >= MIN_SPRITE_WIDTH and sprite_height >= MIN_SPRITE_HEIGHT:
            self._draw_sprite()
        else:
            self._draw_fallback()

    def _draw_sprite(self) -> None:
        """スプライトベースの描画を実行する。"""
        sprite_coords = self._get_sprite_coordinates()

        if sprite_coords:
            sprite_x, sprite_y = sprite_coords
            draw_x, draw_y = int(self.x), int(self.y)

            # 画面境界内の場合のみ描画
            if self._is_sprite_visible(draw_x, draw_y):
                pyxel.blt(draw_x, draw_y, 0, sprite_x, sprite_y,
                         SPRITE_SIZE, SPRITE_SIZE, COLOR_BLACK)

    def _get_sprite_coordinates(self) -> Optional[Tuple[int, int]]:
        """
        現在の状態に応じたスプライト座標を取得する。

        Returns:
            Optional[Tuple[int, int]]: スプライト座標またはNone
        """
        # 重装タンクのダメージ状態チェック
        if (self.enemy_type == TANK_HEAVY and self.health <= 2):
            return TANK_HEAVY_DAMAGED_COORDS.get(self.direction)

        # 通常スプライト座標
        if self.enemy_type in ENEMY_SPRITE_COORDS:
            return ENEMY_SPRITE_COORDS[self.enemy_type].get(self.direction)

        return None

    def _draw_fallback(self) -> None:
        """スプライトが利用できない場合のフォールバック描画。"""
        draw_x, draw_y = int(self.x), int(self.y)

        if self._is_sprite_visible(draw_x, draw_y):
            # エラー表示
            pyxel.rect(draw_x, draw_y, SPRITE_SIZE, SPRITE_SIZE, COLOR_RED)
            pyxel.text(draw_x, draw_y, "ERR", COLOR_WHITE)

    def _is_sprite_visible(self, draw_x: int, draw_y: int) -> bool:
        """
        スプライトが画面内に表示されるかをチェックする。

        Args:
            draw_x (int): 描画X座標
            draw_y (int): 描画Y座標

        Returns:
            bool: 表示される場合True
        """
        return (draw_x + SPRITE_SIZE > 0 and draw_x < SCREEN_WIDTH and
                draw_y + SPRITE_SIZE > 0 and draw_y < MAP_HEIGHT * TILE_SIZE)


class EnemyManager:
    """
    敵タンクの出現、管理、霧エフェクト制御を行うシステム。

    EnemyManagerは敵タンクのライフサイクル全体を管理し、
    ステージ進行に基づいた敵構成の動的調整、出現前の霧エフェクト、
    パフォーマンス最適化のための敵数制限を実装する。

    主要機能:
    - ステージ別の敵構成自動生成
    - 最大4体の画面上敵数制限
    - 出現前の霧アニメーション制御
    - 敵の状態管理とクリーンアップ

    属性:
        enemies (List[Enemy]): 現在活動中の敵タンクリスト
        spawn_queue (List[int]): 出現待ちの敵タイプキュー
        spawn_timer (int): 次の出現までのカウントダウン
        enemies_spawned (int): このステージで出現した敵の総数
        enemies_destroyed (int): このステージで撃破された敵の数
        enemies_to_spawn (int): このステージの敵出現予定数

        # 霧エフェクト制御
        spawn_fog_active (bool): 霧アニメーション実行中フラグ
        spawn_fog_timer (int): 霧アニメーションタイマー
        spawn_fog_position (Tuple[int, int]): 霧表示位置
        spawn_fog_sequence (List[int]): 霧アニメーション順序
        spawn_fog_current (int): 現在の霧フレームインデックス
        pending_enemy_type (Optional[int]): 霧後に出現予定の敵タイプ
    """

    def __init__(self) -> None:
        """敵管理システムを初期化する。"""
        # 敵管理の基本状態
        self.enemies: List[Enemy] = []
        self.spawn_queue: List[int] = []
        self.spawn_timer: int = 0
        self.enemies_spawned: int = 0
        self.enemies_destroyed: int = 0
        self.enemies_to_spawn: int = ENEMIES_PER_STAGE

        # 霧エフェクト制御システム
        self.spawn_fog_active: bool = False
        self.spawn_fog_timer: int = 0
        self.spawn_fog_position: Tuple[int, int] = (0, 0)
        self.spawn_fog_sequence: List[int] = list(FOG_SEQUENCE)
        self.spawn_fog_current: int = 0
        self.pending_enemy_type: Optional[int] = None

    def init_stage(self, stage_num: int) -> None:
        """
        新しいステージ用の敵システムを初期化する。

        Args:
            stage_num (int): 初期化するステージ番号
        """
        # 敵状態のリセット
        self.enemies.clear()
        self.spawn_queue.clear()
        self.enemies_spawned = 0
        self.enemies_destroyed = 0
        self.enemies_to_spawn = ENEMIES_PER_STAGE
        self.spawn_timer = 0

        # 霧エフェクト状態のリセット
        self._reset_spawn_fog()

        # ステージ難易度に基づく出現キューの生成
        self._create_spawn_queue(stage_num)

    def _create_spawn_queue(self, stage_num: int) -> None:
        """
        ステージ番号に基づいて敵出現キューを生成する。

        Args:
            stage_num (int): 対象ステージ番号
        """
        # スケーリング係数（敵数に対する調整）
        scale = ENEMIES_PER_STAGE / 20.0

        # ステージ進行に基づく敵タイプ分布
        light_tanks = max(1, int((15 - min(stage_num, 12)) * scale))
        armored_tanks = max(1, min(int(3 * scale), int(stage_num * scale)))
        fast_shot_tanks = max(1, min(int(3 * scale),
                                   max(0, int((stage_num - 1) * scale))))
        heavy_tanks = max(0, min(int(2 * scale),
                                max(0, int((stage_num - 3) * scale))))

        # 合計数の調整
        total = light_tanks + armored_tanks + fast_shot_tanks + heavy_tanks
        if total < ENEMIES_PER_STAGE:
            light_tanks += ENEMIES_PER_STAGE - total
        elif total > ENEMIES_PER_STAGE:
            excess = total - ENEMIES_PER_STAGE
            light_tanks = max(0, light_tanks - excess)

        # 出現リストの生成とシャッフル
        spawn_list = (
            [TANK_LIGHT] * light_tanks +
            [TANK_ARMORED] * armored_tanks +
            [TANK_FAST_SHOT] * fast_shot_tanks +
            [TANK_HEAVY] * heavy_tanks
        )

        random.shuffle(spawn_list)
        self.spawn_queue = spawn_list

    def update(self, map_manager: 'MapManager', player: 'Player',
               bullet_manager: 'BulletManager') -> None:
        """
        敵システム全体を更新する。

        Args:
            map_manager (MapManager): 敵AI用マップアクセス
            player (Player): 敵AI用プレイヤー追跡
            bullet_manager (BulletManager): 敵弾丸管理
        """
        # 既存の敵を更新
        for enemy in self.enemies:
            enemy.update(map_manager, player, bullet_manager)

        # 非活性敵の即座クリーンアップ（衝突問題防止）
        self._cleanup_inactive_enemies()

        # 新しい敵の出現処理
        self._update_spawning()

    def _cleanup_inactive_enemies(self) -> None:
        """非活性化された敵をリストから削除する。"""
        # 破壊された敵の数をカウント
        inactive_count = len([e for e in self.enemies if not e.active])
        self.enemies_destroyed += inactive_count

        # 活性敵のみを保持
        self.enemies = [enemy for enemy in self.enemies if enemy.active]

    def _update_spawning(self) -> None:
        """敵出現システムを更新する。"""
        # 霧アニメーション中の場合は霧を更新
        if self.spawn_fog_active:
            self._update_spawn_fog()
            return

        # 出現条件のチェック
        if (not self.spawn_queue or
            len(self.enemies) >= MAX_ENEMIES_ON_SCREEN):
            return

        # 出現タイマーの更新
        self.spawn_timer += 1
        if self.spawn_timer >= ENEMY_SPAWN_INTERVAL:
            self._start_spawn_sequence()
            self.spawn_timer = 0

    def _start_spawn_sequence(self) -> None:
        """霧アニメーション付きの敵出現シーケンスを開始する。"""
        if not self.spawn_queue:
            return

        # 出現位置の選択（重複回避）
        spawn_positions = [
            (0, 0),
            (6 * TILE_SIZE, 0),
            (12 * TILE_SIZE, 0)
        ]
        available_positions = self._get_available_spawn_positions(spawn_positions)

        # 位置決定
        if available_positions:
            self.spawn_fog_position = random.choice(available_positions)
        else:
            self.spawn_fog_position = random.choice(spawn_positions)

        # 出現予定敵タイプを保存
        self.pending_enemy_type = self.spawn_queue.pop(0)

        # 霧アニメーション開始
        self.spawn_fog_active = True
        self.spawn_fog_timer = 0
        self.spawn_fog_current = 0

    def _get_available_spawn_positions(self,
                                     positions: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
        既存敵と重複しない出現位置をフィルタリングする。

        Args:
            positions (List[Tuple[int, int]]): 候補位置リスト

        Returns:
            List[Tuple[int, int]]: 利用可能な位置リスト
        """
        available_positions = []

        for pos in positions:
            position_clear = True
            for enemy in self.enemies:
                distance = ((enemy.x - pos[0])**2 + (enemy.y - pos[1])**2)**0.5
                if distance < TILE_SIZE:
                    position_clear = False
                    break

            if position_clear:
                available_positions.append(pos)

        return available_positions

    def _update_spawn_fog(self) -> None:
        """霧アニメーションを更新する。"""
        self.spawn_fog_timer += 1

        # 各霧フレームの表示時間経過をチェック
        if self.spawn_fog_timer >= FOG_FRAME_DURATION:
            self.spawn_fog_timer = 0
            self.spawn_fog_current += 1

            # 霧シーケンス完了時に敵を出現
            if self.spawn_fog_current >= len(self.spawn_fog_sequence):
                self._spawn_enemy()

    def _spawn_enemy(self) -> None:
        """霧アニメーション後に敵を実際に出現させる。"""
        if self.pending_enemy_type is None:
            self._reset_spawn_fog()
            return

        # 敵数制限の再確認
        if len(self.enemies) >= MAX_ENEMIES_ON_SCREEN:
            # キューに戻して後で再試行
            self.spawn_queue.insert(0, self.pending_enemy_type)
            self._reset_spawn_fog()
            return

        # 敵を生成して追加
        enemy = Enemy(
            self.spawn_fog_position[0],
            self.spawn_fog_position[1],
            self.pending_enemy_type
        )
        self.enemies.append(enemy)
        self.enemies_spawned += 1

        # 霧状態をリセット
        self._reset_spawn_fog()

    def _reset_spawn_fog(self) -> None:
        """霧アニメーション状態をリセットする。"""
        self.spawn_fog_active = False
        self.spawn_fog_timer = 0
        self.spawn_fog_current = 0
        self.pending_enemy_type = None

    def get_active_count(self) -> int:
        """
        現在活動中の敵数を取得する。

        Returns:
            int: 活動中敵数
        """
        return len(self.enemies)

    def get_remaining_count(self) -> int:
        """
        撃破された敵数を取得する（UI表示用）。

        Returns:
            int: 撃破済み敵数
        """
        return self.enemies_destroyed

    def is_stage_complete(self) -> bool:
        """
        ステージが完了したかをチェックする。

        Returns:
            bool: 全敵撃破完了の場合True
        """
        return self.enemies_destroyed >= ENEMIES_PER_STAGE

    def clear_all(self) -> None:
        """全ての敵と出現キューをクリアする。"""
        self.enemies.clear()
        self.spawn_queue.clear()

    def draw(self) -> None:
        """全ての敵と霧エフェクトを描画する。"""
        # 活動中の敵を描画
        for enemy in self.enemies:
            enemy.draw()

        # 霧アニメーションを描画
        if self.spawn_fog_active:
            self._draw_spawn_fog()

    def _draw_spawn_fog(self) -> None:
        """出現前の霧エフェクトを描画する。"""
        if self.spawn_fog_current >= len(self.spawn_fog_sequence):
            return

        # 現在の霧タイプを取得
        fog_type = self.spawn_fog_sequence[self.spawn_fog_current]

        # 霧スプライト座標
        if fog_type == 1:
            sprite_x, sprite_y = FOG_SPRITE_COORDS[0]  # 霧1
        else:
            sprite_x, sprite_y = FOG_SPRITE_COORDS[1]  # 霧2

        # 霧スプライトを描画
        draw_x = int(self.spawn_fog_position[0])
        draw_y = int(self.spawn_fog_position[1])

        # 画面境界内の場合のみ描画
        if (draw_x + TILE_SIZE > 0 and draw_x < SCREEN_WIDTH and
            draw_y + TILE_SIZE > 0 and draw_y < MAP_HEIGHT * TILE_SIZE):
            pyxel.blt(draw_x, draw_y, 0, sprite_x, sprite_y,
                     TILE_SIZE, TILE_SIZE, COLOR_BLACK)