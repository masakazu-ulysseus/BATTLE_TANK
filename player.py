# -*- coding: utf-8 -*-
"""
プレイヤータンクモジュール

以下を含むプレイヤー制御タンクを処理：
- 衝突検出付きのスムーズなグリッドベース移動システム
- 移動と発射の入力処理
- パワーレベル進行と能力
- ライフ管理と無敵フレーム
- 移動と同期したタンクエンジン音響効果
- 方向スプライトとパワーレベル表示による視覚的レンダリング

プレイヤータンクはスムーズ移動システムを使用し、入力により
数フレームかけて次のグリッド位置への移動をトリガーし、
グリッドベースの衝突検出を維持しながら流動的なアニメーションを提供。
"""

from typing import Tuple
import pyxel
from constants import *

class Player:
    """
    スムーズな移動と戦闘能力を持つプレイヤー制御タンク。
    
    機能:
    - スムーズ補間付きグリッドベース移動
    - 射撃速度、発射数、破壊能力に影響する4段階のパワーレベル
    - ダメージ後の無敵フレーム
    - パワーレベル視覚表示付き方向スプライトレンダリング
    - 移動入力と同期するエンジン音響効果
    
    属性:
        x (float): 現在のXピクセル座標
        y (float): 現在のYピクセル座標
        direction (int): 現在の向き (UP/DOWN/LEFT/RIGHT)
        power_level (int): 現在のパワーレベル (0-3、能力に影響)
        lives (int): 残りライフ数
        invincible_timer (int): ダメージ後の残り無敵フレーム数
        move_timer (int): 現在のスムーズ移動の残りフレーム数
        is_moving (bool): タンクが現在スムーズ移動中かどうか
        target_x (int): スムーズ移動の目的地X座標
        target_y (int): スムーズ移動の目的地Y座標
        move_sound_timer (int): エンジン音の間隔用タイマー
    """
    def __init__(self, x: int, y: int) -> None:
        """
        指定された位置でプレイヤータンクを初期化。
        
        引数:
            x (int): 開始Xピクセル座標
            y (int): 開始Yピクセル座標
        """
        # 現在位置（スムーズ移動中は小数可能）
        self.x: float = float(x)
        self.y: float = float(y)
        
        # タンク状態
        self.direction: int = UP  # 初期向き
        self.power_level: int = POWER_NORMAL  # 開始パワーレベル
        self.lives: int = PLAYER_LIVES  # 残りライフ
        self.invincible_timer: int = 0  # ダメージ後の無敵フレーム
        self.move_timer: int = 0  # スムーズ移動タイマー
        
        # スムーズ移動システム状態
        self.is_moving: bool = False  # 現在グリッド位置間を移動中かどうか
        self.target_x: int = x  # 現在移動の目的地X
        self.target_y: int = y  # 現在移動の目的地Y
        
        # エンジン音システム（初回使用時に初期化）
        self.move_sound_timer: int = 0  # エンジン音の間隔用タイマー
        
    def update(self, map_manager: 'MapManager') -> None:
        """
        各フレームでプレイヤータンクの状態、入力、移動を更新。
        
        処理順序:
        1. 無敵タイマーを更新（ダメージ後の免疫）
        2. 入力に基づくエンジン音響効果を処理
        3. 進行中の場合スムーズ移動を処理
        4. 現在移動中でない場合新しい入力を処理
        
        引数:
            map_manager (MapManager): 衝突検出用マップマネージャー
        """
        # ダメージ後の無敵フレームを減少
        # 無敵中はプレイヤーが点滅し、ダメージを受けない
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
        
        # エンジン音タイマーを更新（毎フレーム減少）
        if hasattr(self, 'move_sound_timer') and self.move_sound_timer > 0:
            self.move_sound_timer -= 1
        
        # 衝突による位置ずれを防ぐためグリッド整列を強制
        self.force_grid_alignment()
        
        # 入力状態に基づいた現実的なタンクエンジン音処理
        # スムーズ移動中でも、移動キーが押されている間はエンジン音が鳴る
        key_pressed = (pyxel.btn(KEY_UP) or pyxel.btn(KEY_DOWN) or 
                      pyxel.btn(KEY_LEFT) or pyxel.btn(KEY_RIGHT))
        
        if key_pressed:
            # 初回実行時にサウンドタイマーを初期化
            if not hasattr(self, 'move_sound_timer'):
                self.move_sound_timer = 0
                
            # キーが押されている間は定期的にエンジン音を再生
            # 連続的な「ブーーー」エンジン音効果を作成
            if self.move_sound_timer <= 0:
                pyxel.play(0, 0)  # 機械的なエンジンブザー音を再生
                self.move_sound_timer = 8  # 連続性のため音を8フレーム間隔で配置
        else:
            # 移動キーが押されていない時はタイマーをリセット
            # プレイヤーが入力を停止した時にエンジン音を停止
            if hasattr(self, 'move_sound_timer'):
                self.move_sound_timer = 0
        
        # スムーズ移動システムを処理
        # 現在グリッド位置間を移動中の場合、スムーズ移動を継続
        if self.move_timer > 0:
            self.move_timer -= 1
            self.smooth_move()  # 目標位置へ補間
            return  # 移動中は入力処理をスキップ
        
        # 新しい移動やアクション用のプレイヤー入力を処理
        self.handle_input(map_manager)
    
    def handle_input(self, map_manager: 'MapManager') -> None:
        """
        移動とアクション用のプレイヤー入力を処理。
        
        移動システム:
        - 矢印キーでタンクの方向と移動を制御
        - タンクは常に移動入力の方向を向く
        - 目的地が通行可能な場合のみ移動が発生
        - スムーズなグリッドベース移動を使用（ピクセル精密ではない）
        
        アクションシステム:
        - スペースキーで弾丸を発射（ゲームマネージャーが処理）
        - 発射入力検出のみ、実際の弾丸作成は外部で行う
        
        引数:
            map_manager (MapManager): 衝突検出用マップマネージャー
        """
        moved = False  # このフレームで移動が開始されたかを追跡
        
        # 方向移動入力を処理
        # 各方向で向きを更新し、移動を試行
        if pyxel.btn(KEY_UP):
            self.direction = UP  # 常に向きを更新
            if self.can_move(0, -TILE_SIZE, map_manager):  # 上方向移動が有効かチェック
                self.start_move(0, -TILE_SIZE)  # 上方向へのスムーズ移動を開始
                moved = True
        elif pyxel.btn(KEY_DOWN):
            self.direction = DOWN
            if self.can_move(0, TILE_SIZE, map_manager):  # 下方向移動をチェック
                self.start_move(0, TILE_SIZE)
                moved = True
        elif pyxel.btn(KEY_LEFT):
            self.direction = LEFT
            if self.can_move(-TILE_SIZE, 0, map_manager):  # 左方向移動をチェック
                self.start_move(-TILE_SIZE, 0)
                moved = True
        elif pyxel.btn(KEY_RIGHT):
            self.direction = RIGHT
            if self.can_move(TILE_SIZE, 0, map_manager):  # 右方向移動をチェック
                self.start_move(TILE_SIZE, 0)
                moved = True
        
        # 発射入力を処理（ボタン押下、長押しではない）
        # 発射音と弾丸作成はゲームマネージャーが処理
        if pyxel.btnp(KEY_FIRE):
            pyxel.play(0, 1)  # 発射音効果を直接再生
            # 注意: 実際の弾丸作成は game_manager.update_player() で発生
    
    def start_move(self, dx: int, dy: int) -> None:
        """
        隣接するグリッド位置へのスムーズ移動を開始。
        
        現在位置から目標位置まで複数フレームで補間するスムーズ移動
        システムを設定。これにより、グリッドベースのゲームロジックを
        維持しながら流体的なアニメーションを提供。
        
        引数:
            dx (int): Xオフセット（ピクセル単位、通常 ±TILE_SIZE または 0）
            dy (int): Yオフセット（ピクセル単位、通常 ±TILE_SIZE または 0）
        """
        # スムーズ移動の目標位置を計算
        self.target_x = self.x + dx
        self.target_y = self.y + dy
        
        # 移動時間を設定（8フレーム = 60FPSで約133ms）
        self.move_timer = 8  # 移動完了までのフレーム数
        self.is_moving = True  # スムーズ移動が活動中のフラグ
    
    def force_grid_alignment(self) -> None:
        """
        移動問題を防ぐためプレイヤー位置をタイルグリッドに強制整列。
        
        これは、衝突や他の相互作用によって引き起こされる位置ずれを防ぐ
        （x=55 の代わりに x=48 または x=64 のような非グリッド位置への押し出し）。
        プレイヤーが現在スムーズ移動遷移中でない場合のみ適用。
        """
        # スムーズ移動遷移中でない場合のみ強制整列
        if self.move_timer > 0 or self.is_moving:
            return
        
        # 最も近いグリッド位置を計算
        nearest_grid_x = round(self.x / TILE_SIZE) * TILE_SIZE
        nearest_grid_y = round(self.y / TILE_SIZE) * TILE_SIZE
        
        # 位置修正が必要かチェック
        if abs(self.x - nearest_grid_x) > 0.1 or abs(self.y - nearest_grid_y) > 0.1:
            self.x = float(nearest_grid_x)
            self.y = float(nearest_grid_y)
    
    def smooth_move(self) -> None:
        """
        目標位置へのスムーズ補間を1フレーム実行。
        
        線形補間を使用して現在位置から目標位置まで
        move_timerで指定された時間でスムーズに移動。
        移動完了時は、衝突検出用のグリッド整列を保証するため
        正確な目標位置にスナップ。
        
        目標位置計算が間違っていた場合の視覚的不具合を防ぐため
        境界クランプを含む。
        """
        # 移動完了すべきかチェック
        if self.move_timer <= 0:
            # 完璧なグリッド整列のため正確な目標位置にスナップ
            self.x = float(self.target_x)
            self.y = float(self.target_y)
            self.is_moving = False  # 移動完了
            return
        
        # このフレームの移動ステップを計算
        # 残りフレーム数に基づく単純な線形補間を使用
        move_x = (self.target_x - self.x) / (self.move_timer + 1)
        move_y = (self.target_y - self.y) / (self.move_timer + 1)
        
        # 境界違反デバッグ用に古い位置を保存
        old_x, old_y = self.x, self.y
        
        # 現在位置に移動ステップを適用
        self.x += move_x
        self.y += move_y
        
        # 安全チェック: 移動がマップ境界内に留まることを保証
        # 衝突検出が失敗した場合の視覚的不具合を防ぐ
        if self.x < 0 or self.x >= (MAP_WIDTH * TILE_SIZE):
            self.x = max(0, min(self.x, (MAP_WIDTH * TILE_SIZE) - TILE_SIZE))  # Xを有効範囲にクランプ
    
    def can_move(self, dx: int, dy: int, map_manager: 'MapManager') -> bool:
        """
        タンクが衝突なしに新しい位置に移動できるかチェック。
        
        以下を含む包括的な衝突検出を実行:
        1. 画面外への移動を防ぐ画面境界チェック
        2. 障害物と地形用のマップタイル衝突検出
        
        引数:
            dx (int): テストするXオフセット（ピクセル）
            dy (int): テストするYオフセット（ピクセル）
            map_manager (MapManager): タイル衝突検出用マップマネージャー
            
        戻り値:
            bool: 移動が有効な場合True、ブロックされた場合False
        """
        # 目的地位置を計算
        new_x = self.x + dx
        new_y = self.y + dy
        
        # 画面外移動を防ぐためグリッド境界をチェック
        # タンクはプレイ可能マップグリッド内に留まる必要がある（0からMAP_WIDTH-1、0からMAP_HEIGHT-1）
        max_x = (MAP_WIDTH - 1) * TILE_SIZE  # 最大有効X位置（15 * 16 = 240）
        max_y = (MAP_HEIGHT - 1) * TILE_SIZE  # 最大有効Y位置
        
        if new_x < 0 or new_x > max_x:
            return False
        if new_y < 0 or new_y > max_y:
            return False
        
        # マップタイル（壁、障害物など）との衝突をチェック
        return self.check_map_collision(new_x, new_y, map_manager)
    
    def check_map_collision(self, x: float, y: float, map_manager: 'MapManager') -> bool:
        """
        タンクがマップタイルとの衝突なしに位置を占有できるかチェック。
        
        タンクスプライト全体が通行可能地形に収まることを保証する4角衝突検出を使用。
        これによりタンクが壁に引っかかったり無効な位置を占有することを防ぐ。
        
        引数:
            x (float): テストするXピクセル座標
            y (float): テストするYピクセル座標
            map_manager (MapManager): タイル通行可能性チェック用マップマネージャー
            
        戻り値:
            bool: 位置が有効（全ての角が通行可能）な場合True、そうでなければFalse
        """
        # タンクの境界ボックスの4つの角を定義
        # タンクは TILE_SIZE x TILE_SIZE の正方形を占有
        corners = [
            (x, y),                                      # 左上角
            (x + TILE_SIZE - 1, y),                     # 右上角
            (x, y + TILE_SIZE - 1),                     # 左下角
            (x + TILE_SIZE - 1, y + TILE_SIZE - 1)      # 右下角
        ]
        
        # 各角を通行不可能タイルとの衝突について チェック
        for i, (corner_x, corner_y) in enumerate(corners):
            # タイル検索のためピクセル座標をグリッド座標に変換
            grid_x, grid_y = map_manager.pixel_to_grid(int(corner_x), int(corner_y))
            
            # このグリッド位置のタイルタイプと通行可能性を取得
            tile_type = map_manager.get_tile(grid_x, grid_y)
            passable = map_manager.is_passable(grid_x, grid_y)
            
            # いずれかの角が通行不可能タイル内にある場合、移動はブロック
            if not passable:
                return False
        
        # 全ての角が通行可能タイル内にある - 移動は有効
        return True
    
    def can_fire(self, bullets: list) -> bool:
        """
        パワーレベルと活動中弾丸数に基づいてプレイヤーが発射可能かチェック。
        
        パワーレベル別弾丸制限:
        - POWER_NORMAL/POWER_FAST_SHOT: 画面上最大1発
        - POWER_DOUBLE_SHOT/POWER_SUPER: 画面上最大2発
        
        これにより弾丸スパムを防ぎつつ、アップグレードされたタンクが
        複数同時弾丸による強力な火力を持つことを可能にする。
        
        引数:
            bullets (list): チェックする全活動中弾丸のリスト
            
        戻り値:
            bool: プレイヤーが別の弾丸を発射可能な場合True、そうでなければFalse
        """
        # プレイヤータンクに属する弾丸のみをカウント
        player_bullets = [b for b in bullets if b.owner_type == TANK_PLAYER]
        
        # 現在のパワーレベルに基づく弾丸制限をチェック
        if self.power_level >= POWER_DOUBLE_SHOT:
            # 上級パワーレベルは2発同時弾丸を許可
            return len(player_bullets) < 2
        else:
            # 基本パワーレベルは一度に1発のみ許可
            return len(player_bullets) < 1
    
    def fire(self) -> 'Bullet':
        """
        タンクの大砲から発射された弾丸発射体を作成。
        
        弾丸の特性はタンクの現在状態で決定:
        - 位置: 方向に基づいてタンクの砲口先端に配置
        - 速度: POWER_FAST_SHOT以上のレベルで増加
        - パワー: 破壊可能性のためタンクのパワーレベルを継承
        - 所有者: 衝突検出のためTANK_PLAYERとしてマーク
        
        戻り値:
            Bullet: 弾丸マネージャーに追加準備完了の新しい弾丸インスタンス
        """
        from bullet import Bullet  # 循環依存を避けるためローカルインポート
        
        # 弾丸をタンク中央で開始し、方向に基づいて調整
        bullet_x = self.x + TILE_SIZE // 2
        bullet_y = self.y + TILE_SIZE // 2
        
        # タンクの向きに基づいて弾丸を砲口先端に配置
        if self.direction == UP:
            bullet_y = self.y  # タンクの上端
        elif self.direction == DOWN:
            bullet_y = self.y + TILE_SIZE  # タンクの下端
        elif self.direction == LEFT:
            bullet_x = self.x  # タンクの左端
        elif self.direction == RIGHT:
            bullet_x = self.x + TILE_SIZE  # タンクの右端
        
        # パワーレベルに基づいて弾丸速度を計算
        bullet_speed = BULLET_SPEED
        if self.power_level >= POWER_FAST_SHOT:
            bullet_speed *= 2  # ファーストショット以上で2倍速度
        
        # 注意: 発射音響効果は game_manager が処理、ここではない
        
        # タンクの特性を持つ新しい弾丸を作成して返す
        return Bullet(bullet_x, bullet_y, self.direction, bullet_speed, TANK_PLAYER, self.power_level)
    
    def take_damage(self) -> bool:
        """
        敵弾丸や衝突によるプレイヤータンクのダメージを処理。
        
        ダメージシステム:
        - 無敵フレーム中はダメージを無視
        - ライフ数を1減少
        - ダメージ後2秒間の無敵を付与
        - 死亡時にパワーレベルを基本にリセット
        - ゲームオーバー検出用の死亡状態を返す
        
        戻り値:
            bool: プレイヤーが死亡（lives <= 0）した場合True、生存中の場合False
        """
        # プレイヤーが現在無敵の場合はダメージを無視
        if self.invincible_timer > 0:
            return False  # ダメージなし
        
        # ダメージ効果を適用
        self.lives -= 1  # ライフを1失う
        self.invincible_timer = 120  # 60FPSで2秒間の無敵
        self.power_level = POWER_NORMAL  # 死亡時に基本パワーにリセット
        
        # プレイヤーが現在死亡しているかチェック
        if self.lives <= 0:
            return True  # プレイヤー死亡 - ゲームオーバーをトリガー
        
        return False  # プレイヤーは残りライフで生存
    
    def add_power_up(self) -> None:
        """
        プレイヤーのパワーレベルを1段階上昇。
        
        パワーレベル進行:
        0. POWER_NORMAL: 標準弾丸の基本タンク
        1. POWER_FAST_SHOT: 弾丸が2倍速度で移動
        2. POWER_DOUBLE_SHOT: 2発の弾丸を同時発射可能
        3. POWER_SUPER: 鋼壁を破壊可能、最大パワー
        
        パワーレベルはPOWER_SUPERで上限に達し、それ以上増加不可。
        音響効果は衝突マネージャーによって外部で処理。
        """
        # まだ最大でない場合はパワーレベルを上昇
        if self.power_level < POWER_SUPER:
            self.power_level += 1
            # 注意: パワーアップ音響効果は衝突マネージャーが再生
    
    def get_rect(self) -> Tuple[int, int, int, int]:
        """
        衝突検出用のタンクの軸整列境界矩形を取得。
        
        使用用途:
        - タンク対タンク衝突検出
        - 弾丸対タンク衝突検出
        - アイテム拾得衝突検出
        
        戻り値:
            Tuple[int, int, int, int]: (x, y, width, height)の矩形
                - x: 左端ピクセル座標
                - y: 上端ピクセル座標
                - width: タンク幅（常にTILE_SIZE）
                - height: タンク高さ（常にTILE_SIZE）
        """
        return (int(self.x), int(self.y), TILE_SIZE, TILE_SIZE)
    
    def draw(self) -> None:
        """
        視覚効果付きでプレイヤータンクを画面にレンダリング。
        
        レンダリング機能:
        - 無敵点滅: 無敵フレーム中にタンクがオン/オフで点滅
        - 方向スプライト: 向きに基づいてタンクスプライトが変化
        - パワーレベル表示: パワーレベルでタンク色が変化（フォールバックモード）
        - スプライト vs プログラム描画: 利用可能であればスプライト使用、そうでなければプログラム描画
        
        視覚的パワーレベル表示（プログラムモードのみ）:
        - POWER_NORMAL: 黄色タンク本体
        - POWER_FAST_SHOT: 緑色タンク本体
        - POWER_DOUBLE_SHOT: シアンタンク本体
        - POWER_SUPER: 赤色タンク本体
        """
        # 無敵点滅効果を処理
        # 無敵中はタンクが10フレーム毎にオン/オフで点滅
        if self.invincible_timer > 0 and self.invincible_timer % 10 < 5:
            return  # フラッシュオフ期間中はレンダリングをスキップ
        
        # スプライトリソースの利用可能性をチェック
        sprite_width = pyxel.images[0].width
        sprite_height = pyxel.images[0].height
        
        # リソースが読み込まれている場合はスプライトベースレンダリングを使用
        if sprite_width >= 64 and sprite_height >= 16:
            # 方向タンクスプライトを使用したスプライトベースレンダリング
            # プレイヤースプライトは予約済み通行可能タイルエリアのため+16ピクセル右にオフセット
            sprite_x = 0  # デフォルトスプライトX座標
            
            # タンクの向きに基づいて適切なスプライトを選択
            if self.direction == UP:
                sprite_x = 16   # [16,0]で上向きプレイヤータンク
            elif self.direction == RIGHT:
                sprite_x = 32   # [32,0]で右向きプレイヤータンク
            elif self.direction == LEFT:
                sprite_x = 48   # [48,0]で左向きプレイヤータンク
            elif self.direction == DOWN:
                sprite_x = 64   # [64,0]で下向きプレイヤータンク
            
            # イメージバンク0から方向スプライトを描画
            # パラメーター: (dest_x, dest_y, img_bank, src_x, src_y, width, height, transparent_color)
            pyxel.blt(int(self.x), int(self.y), 0, sprite_x, 0, 16, 16, 0)  # 0 = 黒透明
        else:
            # スプライトが利用できない場合はプログラム描画にフォールバック
            
            # 現在のパワーレベルに基づいてタンク本体色を選択
            body_color = COLOR_YELLOW  # 基本パワー用デフォルト色
            if self.power_level == POWER_FAST_SHOT:
                body_color = COLOR_GREEN    # ファーストショット用緑
            elif self.power_level == POWER_DOUBLE_SHOT:
                body_color = COLOR_CYAN     # ダブルショット用シアン
            elif self.power_level == POWER_SUPER:
                body_color = COLOR_RED      # スーパーパワー用赤
            
            # メインタンク本体を描画（視覚的明瞭性のためフルタイルより小さく）
            pyxel.rect(int(self.x) + 2, int(self.y) + 2, TILE_SIZE - 4, TILE_SIZE - 4, body_color)
            
            # 左右両側にタンクキャタピラを描画
            pyxel.rect(int(self.x), int(self.y) + 4, 2, TILE_SIZE - 8, COLOR_DARK_GREY)
            pyxel.rect(int(self.x) + TILE_SIZE - 2, int(self.y) + 4, 2, TILE_SIZE - 8, COLOR_DARK_GREY)
            
            # タンクの向きに基づいて大砲砲身を描画
            cannon_color = COLOR_DARK_GREY
            center_x = int(self.x) + TILE_SIZE // 2
            center_y = int(self.y) + TILE_SIZE // 2
            
            if self.direction == UP:
                # タンク中央から上向きの大砲
                pyxel.rect(center_x - 1, int(self.y), 2, TILE_SIZE // 2, cannon_color)
            elif self.direction == DOWN:
                # タンク中央から下向きの大砲
                pyxel.rect(center_x - 1, center_y, 2, TILE_SIZE // 2, cannon_color)
            elif self.direction == LEFT:
                # タンク中央から左向きの大砲
                pyxel.rect(int(self.x), center_y - 1, TILE_SIZE // 2, 2, cannon_color)
            elif self.direction == RIGHT:
                # タンク中央から右向きの大砲
                pyxel.rect(center_x, center_y - 1, TILE_SIZE // 2, 2, cannon_color)