# -*- coding: utf-8 -*-
"""
弾丸システムモジュール

このモジュールは、Tank Battleゲームにおける弾丸の物理演算、衝突検出、
および管理システムを実装します。個別の弾丸発射体とシステム全体の
弾丸管理を分離し、高パフォーマンスな弾丸システムを提供します。

主要機能:
- リアルタイム物理演算による弾丸移動
- タイル別の詳細な衝突検出とダメージシステム
- 弾丸同士の衝突と相殺メカニズム
- 爆発エフェクトとの統合
- 所有者ベースの弾丸管理とフィルタリング
- メモリ効率的な弾丸ライフサイクル管理

設計原則:
- 単一責任原則: 各クラスが明確な役割を持つ
- 高性能: 60FPSでの安定動作を保証
- 拡張性: 新しい弾丸タイプや効果の追加が容易
- エラー耐性: 不正な状態でもゲームクラッシュを防止

クラス構成:
    Bullet: 個別の弾丸発射体（物理演算、衝突、描画）
    BulletManager: 弾丸システム全体の管理（更新、衝突、清掃）

使用方法:
    # 弾丸マネージャーの初期化
    bullet_manager = BulletManager(explosion_manager)

    # 新しい弾丸の発射
    bullet = player.fire()
    bullet_manager.add_bullet(bullet)

    # 毎フレームの更新
    bullet_manager.update(map_manager)
    bullet_manager.update_bullet_collisions()
    bullet_manager.draw()
"""

import pyxel
from typing import TYPE_CHECKING, Optional, List, Tuple
from constants import *

# 循環インポート回避のための前方宣言
if TYPE_CHECKING:
    from map_manager import MapManager
    from explosion import ExplosionManager

class Bullet:
    """
    物理演算と衝突検出を持つ個別の弾丸発射体。

    各弾丸は独立した物理実体として動作し、マップとの衝突、
    他の弾丸との相互作用、視覚的レンダリングを担当します。
    弾丸の所有者情報を保持し、適切な衝突検出を実現します。

    物理システム:
    - オイラー積分による位置更新
    - 一定速度での直線移動
    - 画面境界での自動非活性化

    衝突システム:
    - タイル別の詳細な衝突判定
    - パワーレベルによる破壊能力の差異
    - 特殊タイル（基地、水域）への個別対応

    属性:
        x (float): 現在のXピクセル座標
        y (float): 現在のYピクセル座標
        direction (Direction): 移動方向定数
        speed (int): フレーム毎の移動速度（ピクセル単位）
        owner_type (TankType): この弾丸を発射したタンクタイプ
        power_level (PowerLevel): 破壊能力レベル
        active (bool): 弾丸の活動状態フラグ
        dx (float): X軸方向の速度成分
        dy (float): Y軸方向の速度成分
    """

    def __init__(
        self,
        x: float,
        y: float,
        direction: Direction,
        speed: int,
        owner_type: TankType,
        power_level: PowerLevel = POWER_NORMAL
    ) -> None:
        """
        新しい弾丸発射体を初期化。

        弾丸の初期位置、移動方向、速度、所有者情報を設定し、
        物理演算に必要な速度成分を事前計算します。

        引数:
            x: 開始Xピクセル座標
            y: 開始Yピクセル座標
            direction: 移動方向定数（UP/DOWN/LEFT/RIGHT）
            speed: フレーム毎の移動速度（ピクセル単位）
            owner_type: 弾丸を発射したタンクタイプ
            power_level: 破壊能力レベル（デフォルト: POWER_NORMAL）

        注記:
            速度成分は初期化時に計算され、毎フレームの計算コストを削減
        """
        # 基本属性の設定
        self.x: float = x
        self.y: float = y
        self.direction: Direction = direction
        self.speed: int = speed
        self.owner_type: TankType = owner_type
        self.power_level: PowerLevel = power_level
        self.active: bool = True

        # 方向ベクトルを使用した速度成分の効率的な計算
        direction_vector = DIRECTION_VECTORS.get(direction, (0, 0))
        self.dx: float = direction_vector[0] * speed
        self.dy: float = direction_vector[1] * speed

    def update(self, map_manager: 'MapManager') -> None:
        """
        弾丸の物理演算を更新し衝突を処理。

        毎フレーム実行される弾丸の状態更新処理：
        1. 物理演算による位置更新（オイラー積分）
        2. 画面境界チェックと自動非活性化
        3. マップタイルとの衝突検出と処理

        物理演算はシンプルなオイラー積分を使用し、
        60FPSでの安定した動作を保証します。

        引数:
            map_manager: 衝突検出用のゲームマップマネージャー

        副作用:
            - 位置座標の更新
            - 衝突時の弾丸非活性化
            - タイル破壊やゲームオーバーのトリガー
        """
        if not self.active:
            return

        # オイラー積分による位置更新
        self.x += self.dx
        self.y += self.dy

        # 画面境界チェック（ゲームエリア外での非活性化）
        if self._is_out_of_bounds():
            self.active = False
            return

        # マップタイルとの衝突検出と処理
        self._handle_map_collision(map_manager)

    def _is_out_of_bounds(self) -> bool:
        """
        弾丸が画面境界外にあるかチェック。

        ゲームエリアの境界を基準とした境界判定を実行。
        UI領域を除外したプレイ可能エリアのみを有効範囲とします。

        戻り値:
            境界外の場合True、有効範囲内の場合False
        """
        return (
            self.x < 0 or
            self.x >= SCREEN_WIDTH or
            self.y < 0 or
            self.y >= MAP_HEIGHT * TILE_SIZE
        )

    def _handle_map_collision(self, map_manager: 'MapManager') -> None:
        """
        マップタイルとの衝突を検出し適切に処理。

        タイルタイプ別の詳細な衝突処理：
        - TILE_BRICK: 常に破壊可能、爆発アニメーション付き
        - TILE_STEEL: スーパー弾丸のみ破壊可能、通常弾丸は阻止
        - TILE_BASE: ゲームオーバートリガー、爆発エフェクト
        - TILE_WATER/TILE_FOREST: 弾丸通過（衝突なし）
        - TILE_EMPTY/TILE_ICE: 弾丸通過（衝突なし）

        引数:
            map_manager: タイルアクセスと破壊処理用マネージャー

        副作用:
            - 爆発アニメーションの追加
            - タイル破壊のスケジューリング
            - ゲームオーバーのトリガー
            - 弾丸の非活性化
            - 音響効果の再生
        """
        # ピクセル座標をグリッド座標に変換
        grid_x, grid_y = map_manager.pixel_to_grid(int(self.x), int(self.y))

        # 破壊可能タイルとの衝突処理
        if map_manager.can_destroy(grid_x, grid_y, self.power_level):
            self._handle_destructible_collision(map_manager, grid_x, grid_y)
            return

        # 特殊タイルとの衝突処理
        tile_type = map_manager.get_tile(grid_x, grid_y)
        self._handle_special_tile_collision(tile_type, map_manager)

    def _handle_destructible_collision(
        self,
        map_manager: 'MapManager',
        grid_x: int,
        grid_y: int
    ) -> None:
        """
        破壊可能タイルとの衝突を処理。

        破壊可能タイル（レンガ、鉄壁）に対する標準的な衝突処理：
        1. 衝突地点での爆発アニメーション作成
        2. 遅延タイル破壊のスケジューリング
        3. 爆発音響効果の再生
        4. 弾丸の非活性化

        引数:
            map_manager: マップ管理とタイル破壊用
            grid_x: 衝突したタイルのグリッドX座標
            grid_y: 衝突したタイルのグリッドY座標
        """
        # 爆発アニメーションの作成
        self._create_explosion_effect(map_manager)

        # 遅延タイル破壊のスケジューリング（爆発アニメーション完了後）
        if map_manager.schedule_tile_destruction(grid_x, grid_y, DELAYED_DESTRUCTION_FRAMES):
            pyxel.play(SOUND_CHANNEL_FIRE, 2)  # 爆発音響効果

        self.active = False

    def _handle_special_tile_collision(
        self,
        tile_type: TileType,
        map_manager: 'MapManager'
    ) -> None:
        """
        特殊タイル（基地、鉄壁など）との衝突を処理。

        特殊タイルタイプ別の個別処理：
        - TILE_BASE: ゲームオーバートリガー
        - TILE_STEEL: 通常弾丸の阻止（スーパー弾丸は通過）
        - TILE_WATER: 弾丸通過（処理なし）

        引数:
            tile_type: 衝突したタイルのタイプ
            map_manager: 爆発エフェクト作成用
        """
        if tile_type == TILE_BASE:
            self._handle_base_collision(map_manager)
        elif tile_type == TILE_STEEL and self.power_level < POWER_SUPER:
            self._handle_steel_collision(map_manager)
        # TILE_WATER、TILE_FOREST、TILE_ICEは弾丸通過のため処理なし

    def _handle_base_collision(self, map_manager: 'MapManager') -> None:
        """
        基地への衝突を処理（ゲームオーバートリガー）。

        基地が破壊された場合の処理：
        1. 爆発アニメーションの作成
        2. ゲームオーバー状態のトリガー
        3. 爆発音響効果の再生
        4. 弾丸の非活性化

        引数:
            map_manager: 爆発エフェクト作成用

        注記:
            ゲームマネージャーへのアクセスは循環依存を避けるため
            動的インポートを使用（将来的に依存注入で改善予定）
        """
        # 爆発アニメーションの作成
        self._create_explosion_effect(map_manager)

        # ゲームオーバーのトリガー（TODO: 依存注入で改善）
        try:
            import game_manager
            if hasattr(game_manager, 'current_instance') and game_manager.current_instance:
                game_manager.current_instance.trigger_game_over()
        except (ImportError, AttributeError) as e:
            # ゲームマネージャーが利用できない場合のフォールバック
            # デバッグモード時のみエラーログを出力
            if DEBUG_MODE:
                print(f"Warning: Could not trigger game over: {e}")

        pyxel.play(SOUND_CHANNEL_FIRE, 2)  # 爆発音響効果
        self.active = False

    def _handle_steel_collision(self, map_manager: 'MapManager') -> None:
        """
        鉄壁への通常弾丸衝突を処理。

        スーパーパワー未満の弾丸が鉄壁に衝突した場合：
        1. 爆発アニメーションの作成
        2. 弾丸の非活性化（鉄壁は破壊されない）

        引数:
            map_manager: 爆発エフェクト作成用
        """
        self._create_explosion_effect(map_manager)
        self.active = False

    def _create_explosion_effect(self, map_manager: 'MapManager') -> None:
        """
        弾丸衝突地点で爆発アニメーションを作成。

        爆発マネージャーが利用可能な場合、弾丸の現在位置に
        爆発アニメーションを追加します。

        引数:
            map_manager: 爆発マネージャーアクセス用
        """
        if (hasattr(map_manager, 'explosion_manager') and
            map_manager.explosion_manager is not None):
            map_manager.explosion_manager.add_explosion(self.x, self.y)

    def get_rect(self) -> Rectangle:
        """
        衝突検出用の弾丸境界矩形を取得。

        弾丸の位置を中心とした2x2ピクセルの矩形を返します。
        この矩形は弾丸同士の衝突検出やエンティティとの
        衝突判定に使用されます。

        戻り値:
            弾丸の境界矩形 (x, y, width, height)
            - x: 左端ピクセル座標
            - y: 上端ピクセル座標
            - width: 矩形幅（常に2ピクセル）
            - height: 矩形高さ（常に2ピクセル）
        """
        return (int(self.x - 1), int(self.y - 1), 2, 2)

    def draw(self) -> None:
        """
        弾丸を画面に描画。

        所有者タイプに基づいた色分けによる視覚的描画：
        - プレイヤー弾丸: 黄色（COLOR_YELLOW）
        - 敵弾丸: 白色（COLOR_WHITE）

        弾丸は2x2ピクセルの正方形として描画され、
        中央に配置されます。非活性な弾丸は描画されません。

        描画仕様:
        - サイズ: 2x2ピクセル
        - 位置: 弾丸座標を中心とした正方形
        - 色: 所有者タイプに基づく識別色
        """
        if not self.active:
            return

        # 所有者タイプに基づく色選択
        color = POWER_LEVEL_COLORS.get(
            POWER_NORMAL if self.owner_type == TANK_PLAYER else POWER_NORMAL,
            COLOR_YELLOW if self.owner_type == TANK_PLAYER else COLOR_WHITE
        )

        # 2x2ピクセル正方形として描画（中央配置）
        pyxel.rect(int(self.x - 1), int(self.y - 1), 2, 2, color)


class BulletManager:
    """
    ゲーム内のすべての活動中弾丸とその相互作用を管理。

    このクラスは弾丸システム全体の制御中枢として機能し、
    複数の弾丸間の相互作用、ライフサイクル管理、
    パフォーマンス最適化を担当します。

    主要責任:
    - 活動中弾丸リストの維持と管理
    - 毎フレームの物理演算と衝突検出の実行
    - 弾丸同士の衝突検出と解決
    - 所有者別弾丸フィルタリングとクエリ機能
    - メモリ効率的な弾丸清掃とガベージコレクション
    - 爆発エフェクトとの統合

    パフォーマンス特性:
    - O(n)の更新処理（nは活動中弾丸数）
    - O(n²)の弾丸衝突検出（最適化により実際はより高速）
    - 自動メモリ管理による安定したパフォーマンス

    属性:
        bullets (List[Bullet]): 現在活動中のすべての弾丸リスト
        explosion_manager (ExplosionManager): 爆発アニメーション作成用
    """

    def __init__(self, explosion_manager: 'ExplosionManager') -> None:
        """
        弾丸管理システムを初期化。

        弾丸リストを空の状態で初期化し、爆発マネージャーとの
        連携を設定します。

        引数:
            explosion_manager: 弾丸衝突時の爆発アニメーション作成用

        注記:
            爆発マネージャーは弾丸衝突時のビジュアルフィードバック
            提供に必須のため、Noneの場合は例外が発生する可能性があります
        """
        self.bullets: List[Bullet] = []
        self.explosion_manager: 'ExplosionManager' = explosion_manager

    def add_bullet(self, bullet: Bullet) -> None:
        """
        新しい弾丸を活動中リストに追加。

        追加された弾丸は次回の更新サイクルから自動的に
        物理演算と衝突検出の対象となります。

        引数:
            bullet: 管理対象に追加する新しい弾丸インスタンス

        パフォーマンス:
            O(1) - リスト末尾への追加
        """
        self.bullets.append(bullet)

    def update(self, map_manager: 'MapManager') -> None:
        """
        すべての活動中弾丸を更新し清掃を実行。

        毎フレーム実行される弾丸システムの主要更新処理：
        1. 各弾丸の物理演算と衝突検出を更新
        2. 非活性化された弾丸をリストから除去

        この処理により、弾丸の動作とメモリ管理が
        自動的に実行されます。

        引数:
            map_manager: 弾丸のマップ衝突検出用

        パフォーマンス:
            O(n) - 弾丸数に比例（nは活動中弾丸数）

        副作用:
            - 各弾丸の位置更新
            - 衝突による弾丸非活性化
            - 非活性弾丸のメモリ解放
        """
        # 各弾丸の物理演算と衝突検出を更新
        for bullet in self.bullets:
            if bullet.active:
                bullet.update(map_manager)

        # 非活性弾丸の効率的な除去（メモリリーク防止）
        self.bullets = [bullet for bullet in self.bullets if bullet.active]

    def get_bullets_by_owner(self, owner_type: TankType) -> List[Bullet]:
        """
        指定された所有者タイプの弾丸をフィルタリング。

        特定のタンクタイプが発射した弾丸のみを抽出します。
        プレイヤーの発射制限チェックや敵弾丸の分析などに使用。

        引数:
            owner_type: フィルタ対象のタンクタイプ定数

        戻り値:
            指定されたタンクタイプが所有する活動中弾丸のリスト

        パフォーマンス:
            O(n) - 全弾丸数に比例

        使用例:
            player_bullets = bullet_manager.get_bullets_by_owner(TANK_PLAYER)
            if len(player_bullets) >= max_bullets:
                # プレイヤーの発射制限をチェック
        """
        return [bullet for bullet in self.bullets if bullet.owner_type == owner_type]

    def check_bullet_collision(self, bullet1: Bullet, bullet2: Bullet) -> bool:
        """
        2つの弾丸の軸整列境界ボックス（AABB）衝突を検出。

        効率的なAABB衝突検出アルゴリズムを使用して、
        2つの弾丸の境界矩形が重複しているかを判定します。

        引数:
            bullet1: 第1の弾丸
            bullet2: 第2の弾丸

        戻り値:
            弾丸が衝突している場合True、していない場合False

        アルゴリズム:
            両軸（X、Y）で矩形の重複をチェック。
            両軸で重複がある場合のみ衝突と判定。

        パフォーマンス:
            O(1) - 定数時間の矩形重複計算
        """
        rect1 = bullet1.get_rect()
        rect2 = bullet2.get_rect()

        # AABB衝突検出: 両軸での重複チェック
        return (
            rect1[0] < rect2[0] + rect2[2] and     # rect1.left < rect2.right
            rect1[0] + rect1[2] > rect2[0] and     # rect1.right > rect2.left
            rect1[1] < rect2[1] + rect2[3] and     # rect1.top < rect2.bottom
            rect1[1] + rect1[3] > rect2[1]         # rect1.bottom > rect2.top
        )

    def update_bullet_collisions(self) -> None:
        """
        異なる所有者の弾丸間の衝突を検出し解決。

        すべての弾丸ペアの衝突をチェックし、異なるタンクタイプが
        発射した弾丸同士が衝突した場合に相殺処理を実行します。
        同じ所有者の弾丸は互いに干渉しません。

        衝突処理:
        1. 全弾丸ペアの衝突検出（重複チェック回避）
        2. 異なる所有者間の衝突のみ処理
        3. 衝突地点での爆発アニメーション作成
        4. 両弾丸の非活性化
        5. 爆発音響効果の再生

        パフォーマンス:
            O(n²) - 理論値（実際は早期終了により高速化）
            nは活動中弾丸数

        最適化:
        - 非活性弾丸の早期スキップ
        - 同一所有者弾丸の衝突チェック回避
        - 重複ペアチェックの回避

        副作用:
            - 衝突した弾丸の非活性化
            - 爆発アニメーションの作成
            - 音響効果の再生
        """
        # 全弾丸ペアの衝突チェック（重複回避のため i+1 からスタート）
        for i, bullet1 in enumerate(self.bullets):
            if not bullet1.active:
                continue

            for bullet2 in self.bullets[i + 1:]:
                if not bullet2.active:
                    continue

                # 異なる所有者間の衝突のみ処理
                if bullet1.owner_type != bullet2.owner_type:
                    if self.check_bullet_collision(bullet1, bullet2):
                        self._resolve_bullet_collision(bullet1, bullet2)

    def _resolve_bullet_collision(self, bullet1: Bullet, bullet2: Bullet) -> None:
        """
        弾丸衝突の解決処理。

        2つの弾丸が衝突した際の詳細な解決処理：
        1. 衝突地点の計算（2つの弾丸の中点）
        2. 爆発アニメーションの作成
        3. 両弾丸の非活性化
        4. 音響効果の再生

        引数:
            bullet1: 衝突した第1の弾丸
            bullet2: 衝突した第2の弾丸
        """
        # 衝突地点を2つの弾丸の中点として計算
        collision_x = (bullet1.x + bullet2.x) / 2
        collision_y = (bullet1.y + bullet2.y) / 2

        # 衝突地点での爆発アニメーション作成
        if self.explosion_manager is not None:
            self.explosion_manager.add_explosion(collision_x, collision_y)

        # 両弾丸を非活性化（相殺）
        bullet1.active = False
        bullet2.active = False

        # 爆発音響効果の再生
        pyxel.play(SOUND_CHANNEL_FIRE, 2)

    def clear_bullets_by_owner(self, owner_type: TankType) -> None:
        """
        指定された所有者タイプの弾丸をすべて非活性化。

        特定のタンクタイプが破壊された際や、ゲームイベント時に
        そのタンクの弾丸をすべて除去する際に使用します。
        即座に削除せず非活性化することで、次の更新サイクルで
        安全に清掃されます。

        引数:
            owner_type: 非活性化対象のタンクタイプ

        使用例:
            # 敵タンクが破壊された際にその弾丸をすべて除去
            bullet_manager.clear_bullets_by_owner(TANK_LIGHT)

        パフォーマンス:
            O(n) - 全弾丸数に比例
        """
        for bullet in self.bullets:
            if bullet.owner_type == owner_type:
                bullet.active = False

    def clear_all_bullets(self) -> None:
        """
        すべての弾丸を即座に除去。

        ステージ遷移、ゲームリセット、その他すべての弾丸を
        即座に除去する必要がある場面で使用します。
        メモリから直接削除するため、次回の更新を待たずに
        即座にクリーンな状態になります。

        使用例:
            # ステージクリア時にすべての弾丸をクリア
            bullet_manager.clear_all_bullets()

        パフォーマンス:
            O(1) - リストの完全クリア
        """
        self.bullets.clear()

    def get_bullet_count(self) -> int:
        """
        現在の活動中弾丸数を取得。

        デバッグやパフォーマンス監視、ゲームバランス調整などに
        使用する活動中弾丸の総数を返します。

        戻り値:
            現在活動中の弾丸数
        """
        return len(self.bullets)

    def get_bullet_count_by_owner(self, owner_type: TankType) -> int:
        """
        指定された所有者タイプの活動中弾丸数を取得。

        特定のタンクタイプが発射した弾丸の数をカウントします。
        発射制限のチェックや統計情報の取得に使用されます。

        引数:
            owner_type: カウント対象のタンクタイプ

        戻り値:
            指定されたタンクタイプの活動中弾丸数
        """
        return len(self.get_bullets_by_owner(owner_type))

    def draw(self) -> None:
        """
        すべての活動中弾丸を画面に描画。

        各弾丸の描画メソッドを呼び出し、すべての活動中弾丸を
        画面にレンダリングします。この処理は毎フレームの
        描画パスで実行されます。

        描画順序:
        弾丸はリストの順序で描画されるため、後に追加された
        弾丸が前面に表示されます。

        パフォーマンス:
            O(n) - 活動中弾丸数に比例
        """
        for bullet in self.bullets:
            if bullet.active:
                bullet.draw()