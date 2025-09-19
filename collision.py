# -*- coding: utf-8 -*-
"""
衝突検出システムモジュール

Tank Battleゲームにおける全ての衝突検出と解決を管理する。
異なるゲームエンティティ間の相互作用を統一的に処理し、
ゲームルールに基づいた適切な反応を実装する。

主要な衝突タイプ:
- プレイヤー弾丸 vs 敵タンク
- 敵弾丸 vs プレイヤータンク
- 敵弾丸 vs 基地
- タンク vs タンク（物理的接触）
- プレイヤー vs アイテム
- 弾丸 vs 弾丸

設計原則:
- 軸整列境界ボックス（AABB）による効率的な衝突検出
- 明確な責任分離による保守性
- ゲームロジックと衝突検出の分離
- 拡張可能なアイテム効果システム
"""

from typing import List, TYPE_CHECKING
import pyxel

from constants import *

# 型ヒント用のインポート（循環インポート回避）
if TYPE_CHECKING:
    from player import Player
    from enemy import EnemyManager
    from bullet import BulletManager
    from item import ItemManager
    from map_manager import MapManager
    from game_context import GameContext


class CollisionManager:
    """
    ゲーム内の全衝突検出と解決を管理するシステム。

    CollisionManagerは全てのゲームエンティティ間の衝突を検出し、
    ゲームルールに従って適切な反応を実行する。軸整列境界ボックス
    （AABB）を使用して効率的な衝突検出を実現。

    主要機能:
    - 矩形同士の衝突検出アルゴリズム
    - プレイヤー弾丸による敵撃破処理
    - 敵弾丸によるダメージ処理
    - タンク間の物理的衝突解決
    - アイテム収集とエフェクト適用
    - 爆発エフェクトとサウンド統合

    属性:
        game_context (GameContext): 共有リソース（爆発、サウンド）へのアクセス
    """

    def __init__(self, game_context: 'GameContext') -> None:
        """
        衝突管理システムを初期化する。

        Args:
            game_context (GameContext): 爆発エフェクトとサウンド管理用の
                                      共有ゲームコンテキスト
        """
        self.game_context = game_context

    def check_rect_collision(self, rect1: Rectangle, rect2: Rectangle) -> bool:
        """
        二つの軸整列境界矩形が重複するかを判定する。

        軸整列境界ボックス（AABB）衝突検出アルゴリズムを使用。
        2つの矩形が両軸（X軸とY軸）で重複する場合のみ衝突と判定。

        Args:
            rect1 (Rectangle): 第一矩形 (x, y, width, height)
            rect2 (Rectangle): 第二矩形 (x, y, width, height)

        Returns:
            bool: 矩形が重複している場合True、していない場合False

        Note:
            矩形の境界が接触している場合（edge-to-edge）は重複とみなさない。
        """
        x1, y1, w1, h1 = rect1
        x2, y2, w2, h2 = rect2

        # AABB衝突検出: 両軸で重複している場合のみ衝突
        return (x1 < x2 + w2 and        # rect1.left < rect2.right
                x1 + w1 > x2 and        # rect1.right > rect2.left
                y1 < y2 + h2 and        # rect1.top < rect2.bottom
                y1 + h1 > y2)           # rect1.bottom > rect2.top

    def check_player_bullet_collisions(self, player: 'Player', bullet_manager: 'BulletManager',
                                     enemy_manager: 'EnemyManager', item_manager: 'ItemManager') -> List:
        """
        プレイヤー弾丸と敵タンクの衝突を検出し処理する。

        処理フロー:
        1. 全プレイヤー弾丸をスキャン
        2. 各弾丸について全敵タンクとの衝突をチェック
        3. 衝突時に爆発エフェクトを生成
        4. 敵にダメージを与えて破壊判定
        5. 破壊された敵からアイテムドロップを処理
        6. 弾丸を非活性化

        Args:
            player (Player): プレイヤータンクインスタンス
            bullet_manager (BulletManager): 弾丸管理システム
            enemy_manager (EnemyManager): 敵タンク管理システム
            item_manager (ItemManager): アイテム管理システム

        Returns:
            List[Enemy]: 破壊された敵タンクのリスト（スコア計算用）

        Side Effects:
            - 破壊された敵タンクを非活性化
            - 衝突した弾丸を非活性化
            - 爆発アニメーションを追加
            - 敵破壊サウンドを再生
            - アイテムドロップを生成
        """
        # プレイヤーの弾丸のみを対象とする
        player_bullets = bullet_manager.get_bullets_by_owner(TANK_PLAYER)
        destroyed_enemies = []

        for bullet in player_bullets:
            if not bullet.active:
                continue

            bullet_rect = bullet.get_rect()

            # 全ての活動中敵タンクとの衝突をチェック
            for enemy in enemy_manager.enemies:
                if not enemy.active:
                    continue

                enemy_rect = enemy.get_rect()
                if self.check_rect_collision(bullet_rect, enemy_rect):
                    # 衝突地点に爆発エフェクトを追加
                    self.game_context.create_explosion(bullet.x, bullet.y)

                    # 敵にダメージを与えて破壊判定
                    if enemy.take_damage():
                        # 敵が破壊された場合
                        destroyed_enemies.append(enemy)

                        # 敵破壊サウンドを再生
                        pyxel.play(SOUND_CHANNEL_FIRE, 7)  # 敵破壊音

                        # 敵がアイテムを持っていた場合はドロップ
                        if enemy.carries_item and enemy.item_type is not None:
                            item_manager.spawn_item(
                                enemy.x + TILE_SIZE // 2,
                                enemy.y + TILE_SIZE // 2,
                                enemy.item_type
                            )

                    # 弾丸を非活性化（衝突により消費）
                    bullet.active = False
                    break  # この弾丸は処理完了

        return destroyed_enemies

    def check_enemy_bullet_collisions(self, player: 'Player', bullet_manager: 'BulletManager',
                                    map_manager: 'MapManager') -> bool:
        """
        敵弾丸とプレイヤー/基地の衝突を検出し処理する。

        処理フロー:
        1. 全敵タイプの弾丸を収集
        2. プレイヤータンクとの衝突をチェック
        3. 基地との衝突をチェック
        4. 衝突時に適切なダメージ処理を実行

        Args:
            player (Player): プレイヤータンクインスタンス
            bullet_manager (BulletManager): 弾丸管理システム
            map_manager (MapManager): マップ管理システム（基地位置取得用）

        Returns:
            bool: 基地が破壊された場合True（ゲームオーバートリガー用）

        Side Effects:
            - プレイヤーにダメージを与える
            - 基地を破壊（ゲームオーバー）
            - 爆発アニメーションを追加
            - 適切なサウンドエフェクトを再生
            - 衝突した弾丸を非活性化
        """
        # 全ての敵タイプから弾丸を収集
        enemy_bullets = []
        for enemy_type in ENEMY_TYPES:
            enemy_bullets.extend(bullet_manager.get_bullets_by_owner(enemy_type))

        for bullet in enemy_bullets:
            if not bullet.active:
                continue

            bullet_rect = bullet.get_rect()

            # プレイヤータンクとの衝突をチェック
            if player.lives > 0:  # プレイヤーが生存中のみ
                player_rect = player.get_rect()
                if self.check_rect_collision(bullet_rect, player_rect):
                    # 衝突地点に爆発エフェクトを追加
                    self.game_context.create_explosion(bullet.x, bullet.y)

                    # プレイヤーにダメージを与える
                    if player.take_damage():
                        # プレイヤーが死亡した場合
                        # ゲームオーバーサウンドはgame_managerが処理
                        pass
                    else:
                        # プレイヤーが生存している場合はヒット音を再生
                        self.game_context.sound_manager.play_hit_sound()

                    bullet.active = False
                    continue

            # 基地との衝突をチェック
            base_x, base_y = map_manager.base_position
            base_rect = (
                base_x * TILE_SIZE,
                base_y * TILE_SIZE,
                TILE_SIZE,
                TILE_SIZE
            )

            if self.check_rect_collision(bullet_rect, base_rect):
                # 基地に衝突 - ゲームオーバー
                self.game_context.create_explosion(bullet.x, bullet.y)

                # 基地タイルを破壊（空タイルに変更）
                map_manager.set_tile(base_x, base_y, TILE_EMPTY)
                bullet.active = False

                # 基地破壊によるゲームオーバーを通知
                # サウンドはtrigger_game_over()が処理
                return True

        return False

    def check_tank_collisions(self, player: 'Player', enemy_manager: 'EnemyManager') -> None:
        """
        タンク同士の物理的衝突を検出し解決する。

        処理フロー:
        1. プレイヤーが生存中かチェック
        2. 全敵タンクとプレイヤーの衝突をチェック
        3. 衝突時に物理的分離を実行

        物理的分離:
        - 重なり方向を計算
        - プレイヤーを適切な位置に移動
        - 画面境界内に位置を制限

        Args:
            player (Player): プレイヤータンクインスタンス
            enemy_manager (EnemyManager): 敵タンク管理システム

        Side Effects:
            - プレイヤー位置を調整
            - 画面境界内への位置制限を適用
        """
        if player.lives <= 0:
            return  # プレイヤーが死亡している場合は処理しない

        player_rect = player.get_rect()

        for enemy in enemy_manager.enemies:
            if not enemy.active:
                continue

            enemy_rect = enemy.get_rect()
            if self.check_rect_collision(player_rect, enemy_rect):
                # タンク同士の衝突を物理的に解決
                self._resolve_tank_collision(player, enemy)

    def _resolve_tank_collision(self, tank1: 'Player', tank2) -> None:
        """
        二つのタンク間の物理的衝突を解決する。

        衝突解決アルゴリズム:
        1. 両タンクの中心点を計算
        2. 重なり方向を判定（水平 vs 垂直）
        3. より大きな重なりの軸で分離
        4. tank1（通常はプレイヤー）を適切な位置に移動
        5. 画面境界内に位置を制限

        Args:
            tank1 (Player): 移動対象のタンク（通常はプレイヤー）
            tank2: 固定対象のタンク（通常は敵）

        Side Effects:
            - tank1の位置を調整
            - 画面境界チェックと位置制限
        """
        rect1 = tank1.get_rect()
        rect2 = tank2.get_rect()

        x1, y1, w1, h1 = rect1
        x2, y2, w2, h2 = rect2

        # 各タンクの中心点を計算
        center1_x = x1 + w1 // 2
        center1_y = y1 + h1 // 2
        center2_x = x2 + w2 // 2
        center2_y = y2 + h2 // 2

        # 中心点間の距離ベクトルを計算
        dx = center1_x - center2_x
        dy = center1_y - center2_y

        # より大きな重なりの軸で分離を実行
        if abs(dx) > abs(dy):
            # 水平方向の分離
            if dx > 0:
                # tank1を右側に移動
                tank1.x = tank2.x + TILE_SIZE
            else:
                # tank1を左側に移動
                tank1.x = tank2.x - TILE_SIZE
        else:
            # 垂直方向の分離
            if dy > 0:
                # tank1を下側に移動
                tank1.y = tank2.y + TILE_SIZE
            else:
                # tank1を上側に移動
                tank1.y = tank2.y - TILE_SIZE

        # タンクが画面境界内に留まるよう位置を制限
        max_x = SCREEN_WIDTH - TILE_SIZE
        max_y = (MAP_HEIGHT * TILE_SIZE) - TILE_SIZE

        tank1.x = max(0, min(tank1.x, max_x))
        tank1.y = max(0, min(tank1.y, max_y))

    def check_item_collisions(self, player: 'Player', item_manager: 'ItemManager') -> None:
        """
        プレイヤーとアイテムの衝突を検出し処理する。

        処理フロー:
        1. プレイヤーが生存中かチェック
        2. 全活動中アイテムとの衝突をチェック
        3. 衝突時にアイテムを収集
        4. アイテム効果を適用
        5. アイテム収集サウンドを再生

        Args:
            player (Player): プレイヤータンクインスタンス
            item_manager (ItemManager): アイテム管理システム

        Side Effects:
            - アイテムを非活性化（収集済み）
            - プレイヤーにアイテム効果を適用
            - アイテム収集サウンドを再生
        """
        if player.lives <= 0:
            return  # プレイヤーが死亡している場合は処理しない

        player_rect = player.get_rect()

        for item in item_manager.items:
            if not item.active:
                continue

            item_rect = item.get_rect()
            if self.check_rect_collision(player_rect, item_rect):
                # アイテムを収集（非活性化）
                item.active = False

                # アイテム効果をプレイヤーに適用
                self._apply_item_effect(player, item, item_manager)

                # アイテム収集サウンドを再生
                pyxel.play(SOUND_CHANNEL_ITEM, 3)  # アイテム収集音

    def _apply_item_effect(self, player: 'Player', item, item_manager: 'ItemManager') -> None:
        """
        収集されたアイテムの効果をプレイヤーまたはゲーム状態に適用する。

        各アイテムタイプの効果:
        - ITEM_STAR: プレイヤーパワーレベルを上昇
        - ITEM_GRENADE: 全敵を破壊（遅延処理）
        - ITEM_TANK: エクストラライフを付与
        - ITEM_SHOVEL: 基地を一時的に鉄壁で保護
        - ITEM_CLOCK: 全敵を一時的に凍結
        - ITEM_HELMET: プレイヤーに一時的な無敵状態を付与

        Args:
            player (Player): 効果を適用するプレイヤー
            item: 収集されたアイテムインスタンス
            item_manager (ItemManager): 特殊効果管理用アイテムマネージャー

        Side Effects:
            - プレイヤー状態の変更
            - アイテムマネージャーでの特殊効果フラグ設定
            - 適切なサウンドエフェクトの再生
        """
        if item.item_type == ITEM_STAR:
            # プレイヤーパワーレベルを上昇
            player.add_power_up()
            pyxel.play(SOUND_CHANNEL_ITEM, 6)  # パワーアップサウンド

        elif item.item_type == ITEM_GRENADE:
            # 画面上の全敵を破壊（ゲームマネージャーで遅延処理）
            item_manager.grenade_collected = True

        elif item.item_type == ITEM_TANK:
            # エクストラライフを付与（最大ライフ数まで）
            if player.lives < MAX_PLAYER_LIVES:
                player.lives += 1

        elif item.item_type == ITEM_SHOVEL:
            # 基地を鉄壁で一時的に保護
            item_manager.shovel_timer = ITEM_EFFECT_DURATION[ITEM_SHOVEL]

        elif item.item_type == ITEM_CLOCK:
            # 全敵を一時的に凍結
            item_manager.freeze_timer = ITEM_EFFECT_DURATION[ITEM_CLOCK]

        elif item.item_type == ITEM_HELMET:
            # プレイヤーに一時的な無敵状態を付与
            player.invincible_timer = ITEM_EFFECT_DURATION[ITEM_HELMET]

    def update_bullet_collisions(self, bullet_manager: 'BulletManager') -> None:
        """
        弾丸同士の衝突検出と処理を実行する。

        この処理はBulletManagerの弾丸間衝突システムに委譲する。
        異なる所有者の弾丸同士が衝突した場合、両方が破壊される。

        Args:
            bullet_manager (BulletManager): 弾丸管理システム

        Side Effects:
            - 衝突した弾丸を非活性化
            - 衝突地点に爆発エフェクトを追加
            - 弾丸衝突サウンドを再生
        """
        bullet_manager.update_bullet_collisions()

    def check_base_destruction(self, map_manager: 'MapManager') -> bool:
        """
        基地が破壊されているかを確認する。

        基地の現在のタイルタイプをチェックし、TILE_BASEでない場合は
        破壊されたと判定する。これは主にゲームオーバー条件の確認に使用。

        Args:
            map_manager (MapManager): マップ管理システム

        Returns:
            bool: 基地が破壊されている場合True、無傷の場合False
        """
        base_x, base_y = map_manager.base_position
        return map_manager.get_tile(base_x, base_y) != TILE_BASE