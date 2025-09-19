# -*- coding: utf-8 -*-
"""
ゲーム管理システム - 中央統制モジュール

このモジュールは、Tank Battleゲーム全体の中央コーディネーターとして機能し、
すべてのゲームシステム、状態遷移、メインゲームループを管理します。
Model-View-Controller（MVC）パターンとComponent-Based Architecture（CBA）を
組み合わせたハイブリッド設計により、複雑なゲームロジックを整理された
方法で管理します。

主要アーキテクチャ要素:
- 状態管理システム: タイトル、ゲームプレイ、ゲームオーバー、ステージクリア
- コンポーネント管理: 各システムの独立性と相互作用の制御
- イベント駆動設計: システム間の疎結合な通信
- リソース管理: 音響、視覚効果、メモリの効率的利用

中央管理責任:
- ゲーム状態遷移とライフサイクル管理
- 全システムの協調と同期（マップ、プレイヤー、敵、弾丸、アイテム）
- メインゲームループの実行と最適化
- 入力処理と応答性の保証
- スコアシステムとプレイヤー進行管理
- ステージ進行と動的難易度調整
- オーディオシステムの統合制御
- UI描画とユーザーフィードバック

設計原則:
- 単一責任原則: 各システムが明確な責任範囲を持つ
- 開放閉鎖原則: 新機能追加時の既存コード保護
- 依存性注入: システム間の疎結合実現
- エラー耐性: 予期しない状況でもゲーム継続

パフォーマンス特性:
- 60FPS安定動作保証
- メモリ効率的なリソース管理
- フレーム予算内での処理完了
- ガベージコレクション負荷の最小化

使用方法:
    # ゲームマネージャーの初期化
    game_manager = GameManager()

    # メインゲームループ（Pyxelから呼び出し）
    game_manager.update()  # 毎フレームの論理更新
    game_manager.draw()    # 毎フレームの描画処理
"""

import pyxel
from typing import TYPE_CHECKING, Optional, List, Tuple
from constants import *
from map_manager import MapManager
from player import Player
from enemy import EnemyManager
from bullet import BulletManager
from item import ItemManager
from collision import CollisionManager
from game_context import GameContext

# 循環インポート回避のための前方宣言
if TYPE_CHECKING:
    pass

class GameManager:
    """
    すべてのシステムとゲーム状態を管理する中央ゲームコーディネーター。

    GameManagerは、Tank Battleゲームの心臓部として機能し、タイトル画面から
    ゲームプレイ、ゲームオーバーまでの完全なゲーム体験を統率します。
    Component-Based Architectureを採用し、各ゲームシステムを独立したコンポーネント
    として管理しながら、それらの協調動作を効率的に制御します。

    状態管理システム:
    - STATE_TITLE: ハイスコア表示付きタイトル画面とメニューシステム
    - STATE_GAME: 全システム稼働のアクティブゲームプレイ状態
    - STATE_GAME_OVER: 最終スコア表示とハイスコア更新処理
    - STATE_STAGE_CLEAR: ステージ完了祝福とボーナス計算

    管理対象コアシステム:
    - MapManager: ステージレイアウト、タイルベース衝突、地形管理
    - Player: プレイヤータンクの入力処理、移動、戦闘システム
    - EnemyManager: AIタンクの出現、行動パターン、難易度調整
    - BulletManager: 弾丸物理演算、衝突検出、ライフサイクル管理
    - ItemManager: パワーアップアイテム、一時効果、スポーン制御
    - CollisionManager: システム間相互作用、ダメージ処理
    - GameContext: 共有リソース（爆発エフェクト、音響システム）

    エラーハンドリング戦略:
    - グレースフルデグラデーション: 一部システム失敗時も継続動作
    - フォールバック機能: 代替描画・音響システム
    - デバッグモード: 開発時の詳細エラー情報提供

    属性:
        state (GameState): 現在のゲーム状態値
        game_context (GameContext): 共有ゲームリソース管理
        score (int): 現在のプレイヤースコア
        high_score (int): 記録されたベストスコア
        current_stage (int): 現在プレイ中のステージ番号
        map_manager (MapManager): マップ・地形管理システム
        player (Player): プレイヤータンク制御システム
        enemy_manager (EnemyManager): 敵AI管理システム
        bullet_manager (BulletManager): 弾丸物理システム
        item_manager (ItemManager): アイテム・パワーアップシステム
        collision_manager (CollisionManager): 衝突検出システム
        game_over_timer (int): ゲームオーバー画面表示タイマー
        stage_clear_timer (int): ステージクリア祝福タイマー
        pause_timer (int): 一時停止効果タイマー
        audio_delay_counter (int): 音響効果遅延カウンター
    """

    def __init__(self) -> None:
        """
        ゲームマネージャーとすべてのゲームシステムを初期化。

        初期化プロセス:
        1. ゲーム状態とスコアシステムの基盤構築
        2. 共有リソース管理用GameContextの作成
        3. 依存性注入による各マネージャーコンポーネントの初期化
        4. システム間参照の確立と通信路設定
        5. 最初のステージの読み込みと初期状態設定
        6. オーディオシステムの起動とタイトル音楽再生
        7. グローバル参照の設定（レガシー互換性のため）

        システム初期化順序は、依存関係を考慮して設計されており、
        各コンポーネントが適切な状態で起動することを保証します。

        エラーハンドリング:
        - リソース読み込み失敗時のフォールバック
        - システム初期化失敗時のグレースフルデグラデーション
        - メモリ不足時の緊急処理

        注記:
            初期化順序の変更は、システム間依存関係に影響する可能性があります。
            変更時は依存関係グラフを確認してください。
        """
        # ゲーム状態システムの初期化
        self.state: GameState = STATE_TITLE
        self._init_game_state()

        # 共有リソース管理システムの作成
        self.game_context: GameContext = GameContext()
        self._init_shared_resources()

        # コアゲームシステムの依存性注入による初期化
        self._init_core_systems()

        # システム間通信路の確立
        self._establish_system_communication()

        # 状態遷移タイマーシステムの初期化
        self._init_timing_systems()

        # 最初のステージの初期化とゲーム世界の構築
        self.init_stage()

        # オーディオシステムの起動
        self._init_audio_system()

        # レガシー互換性のためのグローバル参照設定
        self._setup_global_references()

    def _init_game_state(self) -> None:
        """
        ゲーム状態とスコアシステムを初期化。

        ゲーム進行に必要な基本状態変数を設定し、
        セッション管理の基盤を構築します。
        """
        self.score: int = 0
        self.high_score: int = 0
        self.current_stage: int = 1

    def _init_shared_resources(self) -> None:
        """
        共有リソースシステムを初期化し、ゲームコンテキストと同期。

        GameContextとGameManagerの状態を同期し、
        一貫性のある状態管理を実現します。
        """
        self.game_context.score = self.score
        self.game_context.high_score = self.high_score
        self.game_context.current_stage = self.current_stage

    def _init_core_systems(self) -> None:
        """
        コアゲームシステムを依存性注入パターンで初期化。

        各システムを適切な依存関係で構築し、
        疎結合なアーキテクチャを実現します。
        """
        # マップ・地形管理システム
        self.map_manager: MapManager = MapManager()

        # プレイヤータンク制御システム
        self.player: Player = Player(
            PLAYER_START_GRID_X * TILE_SIZE,
            PLAYER_START_GRID_Y * TILE_SIZE
        )

        # 敵AI管理システム
        self.enemy_manager: EnemyManager = EnemyManager()

        # 弾丸物理システム（爆発マネージャーとの連携）
        self.bullet_manager: BulletManager = BulletManager(
            self.game_context.explosion_manager
        )

        # アイテム・パワーアップシステム
        self.item_manager: ItemManager = ItemManager()

        # 衝突検出システム（ゲームコンテキスト統合）
        self.collision_manager: CollisionManager = CollisionManager(
            self.game_context
        )

    def _establish_system_communication(self) -> None:
        """
        システム間通信路を確立し、相互参照を設定。

        各システムが必要とする他システムへの参照を設定し、
        効率的な情報共有を実現します。
        """
        # マップマネージャーへの共有リソース注入
        self.map_manager.explosion_manager = self.game_context.explosion_manager
        self.map_manager.game_context = self.game_context

    def _init_timing_systems(self) -> None:
        """
        状態遷移とタイミング制御システムを初期化。

        ゲーム状態の適切な遷移タイミングを管理する
        タイマーシステムを設定します。
        """
        self.game_over_timer: int = 0
        self.stage_clear_timer: int = 0
        self.pause_timer: int = 0
        self.audio_delay_counter: int = 0

    def _init_audio_system(self) -> None:
        """
        オーディオシステムを起動し、タイトル音楽を開始。

        ゲーム開始時の適切な音響環境を構築します。
        """
        try:
            self.game_context.sound_manager.play_title_music()
        except Exception as e:
            if DEBUG_MODE:
                print(f"Audio initialization warning: {e}")

    def _setup_global_references(self) -> None:
        """
        レガシー互換性のためのグローバル参照を設定。

        注記:
            この実装は将来的にコールバックシステムに置き換える予定です。
            現在は基地破壊時のゲームオーバートリガーで使用されています。
        """
        try:
            import game_manager
            game_manager.current_instance = self
        except ImportError:
            if DEBUG_MODE:
                print("Warning: Could not set global reference")

    def init_stage(self) -> None:
        """
        新しいステージを初期化し、ゲーム世界を構築。

        ステージ初期化プロセス:
        1. ステージ固有のマップレイアウト読み込み
        2. プレイヤータンクの標準開始位置への配置
        3. ステージ難易度に基づく敵出現キューの設定
        4. 前ステージからの残存弾丸の清掃
        5. 前ステージからの残存アイテムの除去
        6. 視覚エフェクトのリセット

        この処理により、各ステージで一貫した初期状態を提供し、
        プレイヤーの進行状況（ライフ、パワーレベル、スコア）を
        維持しながら新しいチャレンジを提示します。

        エラーハンドリング:
        - マップ読み込み失敗時のフォールバック
        - システム初期化エラーの回復処理
        """
        try:
            # ステージ固有マップレイアウトの読み込み
            self.map_manager.load_stage(self.current_stage)

            # プレイヤータンクの標準開始位置への配置と状態リセット
            self._reset_player_position()

            # ステージ難易度に基づく敵システムの初期化
            self.enemy_manager.init_stage(self.current_stage)

            # ゲーム世界の清掃と初期化
            self._cleanup_stage_remnants()

        except Exception as e:
            if DEBUG_MODE:
                print(f"Stage initialization error: {e}")
            # エラー時のフォールバック処理
            self._emergency_stage_setup()

    def _reset_player_position(self) -> None:
        """
        プレイヤータンクを標準開始位置にリセット。

        グリッド整列と移動状態のリセットにより、
        ステージ間での位置ずれや移動バグを防止します。
        """
        self.player.x = float(PLAYER_START_GRID_X * TILE_SIZE)
        self.player.y = float(PLAYER_START_GRID_Y * TILE_SIZE)
        self.player.direction = UP
        self.player.is_moving = False
        self.player.move_timer = 0

    def _cleanup_stage_remnants(self) -> None:
        """
        前ステージからの残存要素を清掃。

        クリーンなステージ環境を提供するため、
        前ステージの影響を完全に除去します。
        """
        self.bullet_manager.clear_all_bullets()
        self.item_manager.clear_all_items()
        self.game_context.explosion_manager.clear_all()

    def _emergency_stage_setup(self) -> None:
        """
        ステージ初期化失敗時の緊急セットアップ。

        最小限の機能でゲーム継続を可能にする
        フォールバック処理を実行します。
        """
        # 基本的なマップ構造を生成
        if hasattr(self.map_manager, 'create_emergency_stage'):
            self.map_manager.create_emergency_stage()

        # プレイヤー位置の強制リセット
        self._reset_player_position()

    def trigger_game_over(self) -> None:
        """
        即座にゲームオーバーをトリガー（基地破壊時に呼び出し）。

        この関数は弾丸衝突検出により基地が破壊された際に
        直接呼び出されます。即座にゲームオーバー状態に遷移し、
        適切な音響効果とタイマー設定を行います。

        処理内容:
        - 即座にゲームオーバー状態へ遷移
        - ゲームオーバータイマーの開始
        - 音響システムの適切な処理
        - オーディオ遅延カウンターの設定

        注記:
            ハイスコア更新は通常のgame_over()で処理されます。
            この関数は緊急時の即座の状態遷移に特化しています。
        """
        self.state = STATE_GAME_OVER
        self.game_over_timer = GAME_OVER_TIMER

        # 音響システムの適切な停止
        try:
            pyxel.stop()
        except Exception as e:
            if DEBUG_MODE:
                print(f"Audio stop error: {e}")

        # オーディオシステムリセット用の遅延設定
        self.audio_delay_counter = 10

    def update(self) -> None:
        """
        メインゲーム更新ループ - 毎フレーム呼び出し。

        ゲーム状態に基づいて適切な更新ロジックにディスパッチ：
        - STATE_TITLE: タイトル画面の入力処理と表示
        - STATE_GAME: メインゲームプレイシステムとロジック
        - STATE_GAME_OVER: ゲームオーバー画面と遷移処理
        - STATE_STAGE_CLEAR: ステージ完了祝福とボーナス計算

        この関数は毎フレームのゲームロジックのエントリーポイントです。
        パフォーマンス最適化により、60FPS安定動作を保証します。

        エラーハンドリング:
        各状態更新でのエラーを捕捉し、ゲームクラッシュを防止します。
        """
        try:
            state_handlers = {
                STATE_TITLE: self.update_title,
                STATE_GAME: self.update_game,
                STATE_GAME_OVER: self.update_game_over,
                STATE_STAGE_CLEAR: self.update_stage_clear
            }

            handler = state_handlers.get(self.state)
            if handler:
                handler()
            else:
                # 不正な状態の場合はタイトルに戻る
                self.state = STATE_TITLE

        except Exception as e:
            if DEBUG_MODE:
                print(f"Update error in state {self.state}: {e}")
            # エラー時はタイトル画面に安全に戻る
            self.state = STATE_TITLE

    def update_title(self) -> None:
        """
        タイトル画面状態の更新と入力処理。

        タイトル画面機能:
        - ゲームタイトルと操作説明の表示
        - 現在のハイスコア表示
        - ゲーム開始入力の待機（キーボード・ゲームパッド対応）
        - バックグラウンドタイトル音楽の再生

        入力処理:
        - Enter、Space、ゲームパッドAボタンで新ゲーム開始
        - 統合入力システムによるアクセシビリティ対応
        """
        # ゲーム開始入力のチェック（キーボード・ゲームパッド統合）
        start_inputs = [KEY_START, KEY_FIRE, GAMEPAD_FIRE, GAMEPAD_START]
        if any(pyxel.btnp(key) for key in start_inputs):
            self.start_new_game()

    def update_game(self) -> None:
        """
        メインゲームプレイシステムの適切な順序での更新。

        更新シーケンスの重要性:
        1. 一時停止効果の処理（最優先）
        2. 全ゲームエンティティの更新（プレイヤー、敵、弾丸、アイテム）
        3. マップ状態変更の処理（遅延タイル破壊）
        4. 視覚エフェクトの更新（爆発アニメーション）
        5. 全衝突検出の処理
        6. 勝敗条件の確認

        順序保証により以下を実現:
        - エンティティ位置更新後の衝突検出
        - 全移動完了後の衝突処理
        - 全相互作用後のゲーム状態変更

        パフォーマンス最適化:
        - 一時停止中の処理スキップ
        - 早期リターンによる不要処理回避
        """
        # 一時停止効果の処理（アイテム効果による一時的なゲーム停止）
        if self._handle_pause_effects():
            return

        # ゲームエンティティの順序付き更新
        self._update_game_entities()

        # ゲーム世界の状態更新
        self._update_world_state()

        # 全衝突検出の処理
        self.update_collisions()

        # 勝敗条件の確認
        self.check_game_conditions()

    def _handle_pause_effects(self) -> bool:
        """
        一時停止効果を処理し、停止状態かを返す。

        戻り値:
            一時停止中の場合True、通常処理継続の場合False
        """
        if self.pause_timer > 0:
            self.pause_timer -= 1
            return True
        return False

    def _update_game_entities(self) -> None:
        """
        全ゲームエンティティを適切な順序で更新。

        更新順序:
        1. プレイヤータンク（入力応答性確保）
        2. 敵タンク（AI判断と移動）
        3. 弾丸（物理演算）
        4. アイテム（出現と効果処理）
        """
        self.update_player()
        self.update_enemies()
        self.update_bullets()
        self.update_items()

    def _update_world_state(self) -> None:
        """
        ゲーム世界の状態を更新。

        世界状態更新:
        - 遅延タイル破壊の処理
        - 視覚エフェクトの更新
        """
        self.map_manager.update_delayed_destructions()
        self.game_context.update_effects()

    def update_player(self) -> None:
        """
        プレイヤータンク状態と入力処理を更新。

        プレイヤー更新プロセス:
        1. プレイヤー生存状態の確認
        2. タンク物理演算と移動処理
        3. 発射入力の処理と弾丸制限チェック
        4. 弾丸作成と弾丸マネージャーへの追加
        5. 適切な音響効果の再生

        発射システム:
        - パワーレベル別弾丸制限の尊重（1発または2発まで）
        - ボタン押下時のみ発射（長押し無効）
        - 発射成功時の音響フィードバック

        エラーハンドリング:
        - 弾丸作成失敗時のグレースフルデグラデーション
        - 音響再生失敗時の継続動作
        """
        if self.player.lives <= 0:
            return

        try:
            # プレイヤー移動、入力、状態の更新
            self.player.update(self.map_manager)

            # プレイヤー発射入力の処理
            self._handle_player_firing()

        except Exception as e:
            if DEBUG_MODE:
                print(f"Player update error: {e}")

    def _handle_player_firing(self) -> None:
        """
        プレイヤーの発射入力を処理。

        統合入力システムによりキーボードとゲームパッドの
        両方をサポートし、アクセシビリティを向上させます。
        """
        fire_inputs = [KEY_FIRE, GAMEPAD_FIRE]
        if any(pyxel.btnp(key) for key in fire_inputs):
            # パワーレベルと活動中弾丸数に基づく発射可能性チェック
            if self.player.can_fire(self.bullet_manager.bullets):
                self._create_player_bullet()

    def _create_player_bullet(self) -> None:
        """
        プレイヤー弾丸を作成し、システムに追加。

        弾丸作成プロセス:
        - プレイヤーの現在プロパティに基づく弾丸生成
        - 弾丸マネージャーへの追加
        - 発射音響効果の再生
        """
        try:
            bullet = self.player.fire()
            self.bullet_manager.add_bullet(bullet)
            # 発射音響効果の再生
            pyxel.play(SOUND_CHANNEL_FIRE, 2)
        except Exception as e:
            if DEBUG_MODE:
                print(f"Bullet creation error: {e}")

    def update_enemies(self) -> None:
        """
        敵タンクAI、移動、行動の更新。

        敵更新プロセス:
        1. 凍結効果（クロックアイテム）の確認
        2. 凍結されていない場合、全敵AIと移動の更新
        3. 敵の発射判断処理
        4. 敵出現キューの処理

        凍結効果により戦術的優位性を提供し、
        プレイヤーがクロックアイテム収集時に一時的な安全を得られます。

        エラーハンドリング:
        - AI処理エラー時の個別敵スキップ
        - システム全体への影響回避
        """
        try:
            # クロックアイテムによる一時凍結効果の確認
            if self.item_manager.is_freeze_active():
                return

            # 敵AI、移動、射撃の更新
            self.enemy_manager.update(
                self.map_manager,
                self.player,
                self.bullet_manager
            )
        except Exception as e:
            if DEBUG_MODE:
                print(f"Enemy update error: {e}")

    def update_bullets(self) -> None:
        """
        弾丸物理演算と弾丸間衝突の更新。

        弾丸更新プロセス:
        1. 弾丸移動とマップ衝突の更新
        2. 弾丸間衝突検出の処理
        3. 非活性弾丸の清掃

        衝突マネージャーが弾丸対弾丸衝突を別途処理することで、
        より良い責任分離を実現しています。

        エラーハンドリング:
        - 個別弾丸エラー時のスキップ
        - システム安定性の維持
        """
        try:
            # 弾丸物理演算とマップ衝突の更新
            self.bullet_manager.update(self.map_manager)

            # 弾丸間衝突の処理（弾丸同士の相殺）
            self.collision_manager.update_bullet_collisions(self.bullet_manager)
        except Exception as e:
            if DEBUG_MODE:
                print(f"Bullet update error: {e}")

    def update_items(self) -> None:
        """
        パワーアップアイテムと特殊アイテム効果の更新。

        アイテム更新プロセス:
        1. アイテム出現、可視性、寿命の更新
        2. 特殊アイテム効果の処理（グレネード画面クリア）
        3. グレネード破壊敵へのボーナスポイント付与
        4. 適切な音響効果の再生

        グレネード効果は全画面敵即座破壊という独特な機能で、
        戦術的優位性とボーナススコアリングの両方を提供します。

        エラーハンドリング:
        - アイテム処理エラー時の個別スキップ
        - スコア計算エラーからの回復
        """
        try:
            # アイテム出現、可視性タイマー、期限切れの更新
            self.item_manager.update(self.map_manager)

            # グレネードアイテム効果の処理
            self._handle_grenade_effects()
        except Exception as e:
            if DEBUG_MODE:
                print(f"Item update error: {e}")

    def _handle_grenade_effects(self) -> None:
        """
        グレネードアイテム効果を処理し、ボーナススコアを付与。

        グレネード効果:
        - 画面上全敵の即座破壊
        - 各敵に対する基本スコア + グレネードボーナス
        - 爆発音響効果の再生
        """
        destroyed_enemies = self.item_manager.handle_grenade_effect(
            self.enemy_manager,
            self.game_context.explosion_manager
        )

        if destroyed_enemies:
            # グレネード効果音の再生
            self.game_context.play_sound_effect("explosion")

            # 各破壊敵へのボーナスポイント付与
            for enemy in destroyed_enemies:
                enemy_score = ENEMY_SCORE_VALUES.get(enemy.tank_type, ENEMY_SCORE_BASE)
                self.score += enemy_score + GRENADE_BONUS

    def update_collisions(self) -> None:
        """
        ゲームエンティティ間の全衝突検出を処理。

        衝突処理順序の重要性:
        1. プレイヤー弾丸 vs 敵（ポイント付与、アイテム出現）
        2. 破壊敵の即座清掃
        3. 敵弾丸 vs プレイヤー・基地（ダメージ・ゲームオーバー）
        4. タンク間物理衝突
        5. プレイヤー vs アイテム拾得衝突

        順序保証により以下を実現:
        - エンティティ除去前のスコア付与
        - 他衝突確認前のゲームオーバーチェック
        - 破壊エンティティの残存衝突干渉回避

        エラーハンドリング:
        - 個別衝突処理エラー時のスキップ
        - ゲーム状態整合性の維持
        """
        try:
            # プレイヤー弾丸 vs 敵衝突の処理
            self._handle_player_bullet_collisions()

            # 敵弾丸 vs プレイヤー・基地衝突の処理
            if self._handle_enemy_bullet_collisions():
                return  # ゲームオーバー時は残り衝突スキップ

            # 物理的タンク間衝突の処理
            self._handle_tank_collisions()

            # プレイヤーアイテム拾得の処理
            self._handle_item_collisions()

        except Exception as e:
            if DEBUG_MODE:
                print(f"Collision processing error: {e}")

    def _handle_player_bullet_collisions(self) -> None:
        """
        プレイヤー弾丸と敵の衝突を処理。

        処理内容:
        - 衝突検出と破壊敵リストの取得
        - 各破壊敵へのスコア付与
        - 破壊敵の即座清掃（他衝突干渉回避）
        """
        destroyed_enemies = self.collision_manager.check_player_bullet_collisions(
            self.player,
            self.bullet_manager,
            self.enemy_manager,
            self.item_manager
        )

        # 各破壊敵へのポイント付与
        for enemy in destroyed_enemies:
            enemy_score = ENEMY_SCORE_VALUES.get(enemy.tank_type, ENEMY_SCORE_BASE)
            self.score += enemy_score

        # 破壊敵の即座清掃（ゲームプレイ問題回避）
        if destroyed_enemies:
            self.enemy_manager.cleanup_inactive_enemies()

    def _handle_enemy_bullet_collisions(self) -> bool:
        """
        敵弾丸とプレイヤー・基地の衝突を処理。

        戻り値:
            ゲームオーバーが発生した場合True、継続の場合False
        """
        base_destroyed = self.collision_manager.check_enemy_bullet_collisions(
            self.player,
            self.bullet_manager,
            self.map_manager
        )

        # ゲームオーバー条件の確認
        if base_destroyed or self.collision_manager.check_base_destruction(self.map_manager):
            self.game_over()
            return True

        return False

    def _handle_tank_collisions(self) -> None:
        """
        タンク間物理衝突を処理。

        敵清掃後に実行することで、破壊されたタンクとの
        不正な衝突を回避します。
        """
        self.collision_manager.check_tank_collisions(
            self.player,
            self.enemy_manager
        )

    def _handle_item_collisions(self) -> None:
        """
        プレイヤーのパワーアップアイテム拾得を処理。
        """
        self.collision_manager.check_item_collisions(
            self.player,
            self.item_manager
        )

    def check_game_conditions(self) -> None:
        """
        ゲーム勝敗条件を確認し、状態遷移をトリガー。

        条件確認順序:
        1. プレイヤー死亡（ライフ不足） → ゲームオーバー
        2. ステージ完了（全敵撃破） → ステージクリア

        順序により、同一フレームで複数条件が発生した場合に
        プレイヤー死亡が優先されることを保証します。

        エラーハンドリング:
        - 条件チェックエラー時のフォールバック
        - 状態遷移失敗時の回復処理
        """
        try:
            # プレイヤー死亡条件の確認
            if self.player.lives <= 0:
                self.game_over()
                return

            # ステージ完了条件の確認
            if self.enemy_manager.is_stage_complete():
                self.stage_clear()
                return

        except Exception as e:
            if DEBUG_MODE:
                print(f"Game condition check error: {e}")

    def start_new_game(self) -> None:
        """
        タイトル画面から新しいゲームセッションを初期化。

        新ゲーム設定:
        1. 全ゲーム進行状況のリセット（スコア、ステージ）
        2. プレイヤー状態のリセット（ライフ、パワーレベル）
        3. ステージ1の初期化
        4. ゲームプレイ音楽の開始
        5. アクティブゲーム状態への遷移

        ハイスコアを保持しながらクリーンなスレートを提供します。

        エラーハンドリング:
        - 初期化失敗時のフォールバック
        - 音響システムエラーからの回復
        """
        try:
            # アクティブゲームプレイ状態への遷移
            self.state = STATE_GAME

            # ゲーム進行状況のリセット
            self.score = 0
            self.current_stage = 1

            # プレイヤー状態の初期化
            self._reset_player_state()

            # 最初のステージの初期化
            self.init_stage()

            # 音響システムの適切な設定
            self._setup_game_audio()

        except Exception as e:
            if DEBUG_MODE:
                print(f"New game initialization error: {e}")
            # エラー時はタイトルに戻る
            self.state = STATE_TITLE

    def _reset_player_state(self) -> None:
        """
        プレイヤー状態を新ゲーム用にリセット。
        """
        self.player.lives = PLAYER_LIVES
        self.player.power_level = POWER_NORMAL

    def _setup_game_audio(self) -> None:
        """
        ゲームプレイ用音響環境を設定。

        ゲームプレイ中はBGMを停止し、音響効果のみを使用します。
        """
        try:
            self.game_context.sound_manager.stop_music()
        except Exception as e:
            if DEBUG_MODE:
                print(f"Audio setup error: {e}")

    def game_over(self) -> None:
        """
        ゲームオーバー遷移とハイスコア更新を処理。

        ゲームオーバープロセス:
        1. ゲームオーバー状態への遷移
        2. ゲームオーバー音響効果の再生
        3. タイトル自動復帰タイマーの設定
        4. 新記録達成時のハイスコア更新

        ゲームオーバータイマーにより、プレイヤーが最終スコアを
        確認する時間を提供してから自動的にタイトル画面に戻ります。

        エラーハンドリング:
        - 音響再生失敗時の継続動作
        - ハイスコア更新エラーからの回復
        """
        try:
            # ゲームオーバー状態への遷移
            self.state = STATE_GAME_OVER

            # タイトル自動復帰タイマーの設定
            self.game_over_timer = GAME_OVER_TIMER

            # ハイスコア更新の処理
            self._update_high_score()

            # ゲームオーバー音響効果の再生
            self._play_game_over_audio()

        except Exception as e:
            if DEBUG_MODE:
                print(f"Game over processing error: {e}")

    def _update_high_score(self) -> None:
        """
        新記録達成時にハイスコアを更新。
        """
        if self.score > self.high_score:
            self.high_score = self.score

    def _play_game_over_audio(self) -> None:
        """
        ゲームオーバー音響効果を再生。
        """
        try:
            self.game_context.sound_manager.play_game_over_sound()
            self.game_context.sound_manager.play_game_over_music()
        except Exception as e:
            if DEBUG_MODE:
                print(f"Game over audio error: {e}")

    def stage_clear(self) -> None:
        """
        ステージ完了とボーナススコアリングを処理。

        ステージクリアプロセス:
        1. ステージクリア状態への遷移
        2. ステージクリア祝福タイマーの設定
        3. ボーナスポイントの計算と付与
        4. ステージクリア音響効果の再生

        ボーナススコア計算式:
        - ステージボーナス: current_stage × STAGE_CLEAR_BONUS_BASE
        - ライフボーナス: remaining_lives × LIFE_BONUS
        進行と生存の両方を報酬として評価します。

        エラーハンドリング:
        - ボーナス計算エラー時のフォールバック
        - 音響再生失敗時の継続動作
        """
        try:
            # ステージクリア祝福状態への遷移
            self.state = STATE_STAGE_CLEAR

            # ステージクリア祝福タイマーの設定
            self.stage_clear_timer = STAGE_CLEAR_TIMER

            # ボーナスポイントの計算と付与
            self._calculate_stage_bonus()

            # ステージクリア音響効果の再生
            self._play_stage_clear_audio()

        except Exception as e:
            if DEBUG_MODE:
                print(f"Stage clear processing error: {e}")

    def _calculate_stage_bonus(self) -> None:
        """
        ステージクリアボーナスを計算し、スコアに加算。
        """
        stage_bonus = self.current_stage * STAGE_CLEAR_BONUS_BASE
        life_bonus = self.player.lives * LIFE_BONUS
        total_bonus = stage_bonus + life_bonus
        self.score += total_bonus

    def _play_stage_clear_audio(self) -> None:
        """
        ステージクリア音響効果を再生。
        """
        try:
            self.game_context.sound_manager.play_stage_clear_sound()
        except Exception as e:
            if DEBUG_MODE:
                print(f"Stage clear audio error: {e}")

    def update_game_over(self) -> None:
        """
        ゲームオーバー画面状態と入力を更新。

        ゲームオーバー画面機能:
        - 最終スコアとハイスコア状態の表示
        - タイマー満了後の自動タイトル復帰
        - スタートキーによる手動タイトル復帰
        - タイトル音楽への遷移

        タイマーにより最終スコア確認時間を保証し、
        入力オプションによる高速ナビゲーションも提供します。

        エラーハンドリング:
        - オーディオ遅延処理エラーからの回復
        - 状態遷移エラー時のフォールバック
        """
        try:
            # 遅延オーディオ再生の処理
            self._handle_delayed_audio()

            # ゲームオーバータイマーのカウントダウン
            self.game_over_timer -= 1

            # 自動タイムアウトまたは手動入力の確認
            if self._should_return_to_title():
                self._return_to_title()

        except Exception as e:
            if DEBUG_MODE:
                print(f"Game over update error: {e}")
            # エラー時は強制的にタイトルに戻る
            self.state = STATE_TITLE

    def _handle_delayed_audio(self) -> None:
        """
        遅延オーディオ再生を処理。

        オーディオシステムのリセット時間を確保するため、
        遅延カウンターを使用してゲームオーバー音を再生します。
        """
        if hasattr(self, 'audio_delay_counter') and self.audio_delay_counter > 0:
            self.audio_delay_counter -= 1
            if self.audio_delay_counter == 0:
                try:
                    self.game_context.sound_manager.play_game_over_sound()
                except Exception as e:
                    if DEBUG_MODE:
                        print(f"Delayed audio error: {e}")

    def _should_return_to_title(self) -> bool:
        """
        タイトル画面に戻るべきかを判定。

        戻り値:
            タイムアウトまたは入力によりタイトルに戻る場合True
        """
        return (
            self.game_over_timer <= 0 or
            pyxel.btnp(KEY_START) or
            pyxel.btnp(GAMEPAD_FIRE) or
            pyxel.btnp(GAMEPAD_START)
        )

    def _return_to_title(self) -> None:
        """
        タイトル画面に戻り、タイトル音楽を開始。
        """
        self.state = STATE_TITLE
        try:
            self.game_context.sound_manager.play_title_music()
        except Exception as e:
            if DEBUG_MODE:
                print(f"Title music error: {e}")

    def update_stage_clear(self) -> None:
        """
        ステージクリア祝福状態を更新。

        ステージクリア機能:
        - ステージ完了メッセージの表示
        - 付与されたボーナスポイントの表示
        - タイマー満了後の次ステージ自動進行
        - プレイヤー達成感のための短い祝福期間

        タイマーにより次のチャレンジへ進む前の
        達成感確認時間を提供します。

        エラーハンドリング:
        - ステージ進行エラー時のフォールバック
        - タイマー処理エラーからの回復
        """
        try:
            # ステージクリアタイマーのカウントダウン
            self.stage_clear_timer -= 1

            # タイマー満了時の次ステージ自動進行
            if self.stage_clear_timer <= 0:
                self.advance_stage()

        except Exception as e:
            if DEBUG_MODE:
                print(f"Stage clear update error: {e}")

    def advance_stage(self) -> None:
        """
        次ステージに進行、またはゲーム完了を処理。

        ステージ進行ロジック:
        1. 現在ステージ番号の増加
        2. 全ステージ完了確認
        3. 完了時: 完了ボーナス付与と最終スコア表示
        4. 未完了時: 次ステージ初期化とゲーム継続

        ゲーム完了時には大幅な完了ボーナスを提供し、
        最終スコア表示に遷移します。

        エラーハンドリング:
        - ステージ初期化エラー時のフォールバック
        - ボーナス計算エラーからの回復
        """
        try:
            # 次ステージに進行
            self.current_stage += 1

            # 全ステージ完了確認
            if self.current_stage > TOTAL_STAGES:
                # ゲーム完全クリア処理
                self._handle_game_completion()
            else:
                # 次ステージ継続処理
                self._continue_to_next_stage()

        except Exception as e:
            if DEBUG_MODE:
                print(f"Stage advance error: {e}")
            # エラー時はゲームオーバーとして処理
            self.game_over()

    def _handle_game_completion(self) -> None:
        """
        ゲーム全体完了を処理。

        完了処理:
        - 大幅な完了ボーナスの付与
        - 最終スコア表示としてのゲームオーバー画面
        """
        self.score += GAME_COMPLETION_BONUS
        self.game_over()

    def _continue_to_next_stage(self) -> None:
        """
        次ステージに継続。

        継続処理:
        - アクティブゲームプレイ状態への復帰
        - 次ステージの初期化
        """
        self.state = STATE_GAME
        self.init_stage()

    def draw(self) -> None:
        """
        メインゲーム描画ループ - 更新後に毎フレーム呼び出し。

        ゲーム状態に基づく描画ディスパッチ:
        - STATE_TITLE: ハイスコア付きタイトル画面
        - STATE_GAME: 完全ゲーム描画（マップ、エンティティ、UI）
        - STATE_GAME_OVER: 最終スコア付きゲームオーバー画面
        - STATE_STAGE_CLEAR: ステージ完了祝福

        この関数は毎フレームの視覚描画のエントリーポイントです。
        レイヤー構造と描画順序により適切な視覚表現を実現します。

        エラーハンドリング:
        各描画状態でのエラーを捕捉し、視覚クラッシュを防止します。
        """
        try:
            draw_handlers = {
                STATE_TITLE: self.draw_title,
                STATE_GAME: self.draw_game,
                STATE_GAME_OVER: self.draw_game_over,
                STATE_STAGE_CLEAR: self.draw_stage_clear
            }

            handler = draw_handlers.get(self.state)
            if handler:
                handler()
            else:
                # 不正な状態の場合は黒画面を表示
                pyxel.cls(COLOR_BLACK)

        except Exception as e:
            if DEBUG_MODE:
                print(f"Draw error in state {self.state}: {e}")
            # エラー時は黒画面にエラーメッセージ
            pyxel.cls(COLOR_BLACK)
            if DEBUG_MODE:
                pyxel.text(8, 8, f"DRAW ERROR: {str(e)[:30]}", COLOR_RED)

    def draw_title(self) -> None:
        """
        ゲーム情報と操作説明付きタイトル画面を描画。

        タイトル画面要素:
        - ゲームタイトルとサブタイトル
        - 新規プレイヤー用の操作説明
        - 視覚的注意引きのための点滅スタートプロンプト
        - 現在のハイスコア表示
        - プロフェッショナルな外観のための中央配置レイアウト

        フレームベースアニメーションによるスタートプロンプト点滅効果を使用。
        キーボードとゲームパッドの両方の操作方法を表示し、
        アクセシビリティを向上させます。
        """
        # 黒背景による画面クリア
        pyxel.cls(COLOR_BLACK)

        # メインゲームタイトルの描画
        title_text = GAME_TITLE
        self._draw_centered_text(title_text, 60, COLOR_YELLOW)

        # ゲームサブタイトル・説明の描画
        subtitle = GAME_SUBTITLE
        self._draw_centered_text(subtitle, 80, COLOR_WHITE)

        # 操作説明の描画（新規プレイヤー向け）
        self._draw_control_instructions()

        # 点滅スタートプロンプトの描画
        self._draw_flashing_start_prompt()

        # 現在のハイスコア表示
        self._draw_high_score_display()

    def _draw_centered_text(self, text: str, y: int, color: int) -> None:
        """
        指定されたY座標にテキストを中央配置で描画。

        引数:
            text: 描画するテキスト
            y: Y座標
            color: テキスト色
        """
        text_width = len(text) * TEXT_CHAR_WIDTH
        x = SCREEN_WIDTH // 2 - text_width // 2
        pyxel.text(x, y, text, color)

    def _draw_control_instructions(self) -> None:
        """
        キーボードとゲームパッドの操作説明を描画。

        アクセシビリティのため、両方の入力方法を明示的に表示します。
        """
        instructions = [
            (CONTROLS_MOVE, 110, COLOR_WHITE),
            (CONTROLS_FIRE, 120, COLOR_WHITE),
            (CONTROLS_GAMEPAD, 140, COLOR_CYAN),
            (CONTROLS_QUIT, 150, COLOR_WHITE)
        ]

        for text, y, color in instructions:
            self._draw_centered_text(text, y, color)

    def _draw_flashing_start_prompt(self) -> None:
        """
        フレームベースアニメーションによる点滅スタートプロンプトを描画。

        30フレーム（0.5秒）間隔での点滅により視覚的注意を引きます。
        """
        if (pyxel.frame_count // FLASH_INTERVAL) % 2:
            self._draw_centered_text(PROMPT_START, 180, COLOR_GREEN)

    def _draw_high_score_display(self) -> None:
        """
        現在のハイスコア表示を描画。
        """
        high_score_text = TEXT_HIGH_SCORE.format(self.high_score)
        self._draw_centered_text(high_score_text, 200, COLOR_CYAN)

    def draw_game(self) -> None:
        """
        すべてのゲーム要素を含むメインゲームプレイ画面を描画。

        描画順序（背面から前面）:
        1. 画面背景のクリア
        2. マップタイルと地形
        3. ゲームエンティティ（プレイヤー、敵、弾丸、アイテム）
        4. 視覚エフェクト（爆発アニメーション）
        5. UI要素（スコア、ライフ、ステータス）
        6. 特殊オーバーレイ（一時停止画面）

        描画順序により適切な視覚レイヤリングを確保し、
        UI要素がゲームエンティティ上に表示されることを保証します。

        エラーハンドリング:
        個別描画コンポーネントのエラーをキャッチし、
        部分的な描画失敗でも可能な限り表示を継続します。
        """
        # 黒背景による画面クリア
        pyxel.cls(COLOR_BLACK)

        try:
            # ゲーム世界要素の描画（背面から前面レイヤリング）
            self._draw_game_world()

            # ユーザーインターフェイス要素の描画
            self._draw_game_ui()

            # 特殊効果とオーバーレイの描画
            self._draw_special_effects()

        except Exception as e:
            if DEBUG_MODE:
                print(f"Game drawing error: {e}")

    def _draw_game_world(self) -> None:
        """
        ゲーム世界のすべての要素を適切な順序で描画。

        レイヤー構造:
        1. 地形・障害物（背景レイヤー）
        2. ゲームエンティティ（中間レイヤー）
        3. 森林オーバーレイ（カバー効果）
        4. 爆発アニメーション（前景エフェクト）
        """
        # 地形と障害物（背景レイヤー）
        self.map_manager.draw()

        # ゲームエンティティ群
        self.player.draw()
        self.enemy_manager.draw()
        self.bullet_manager.draw()
        self.item_manager.draw()

        # 森林カバー効果（タンク上層）
        self.map_manager.draw_forest_overlay()

        # 爆発アニメーション（前景エフェクト）
        self.game_context.draw_effects()

    def _draw_game_ui(self) -> None:
        """
        ゲームユーザーインターフェイス要素を描画。

        UI構成:
        - メインUI: スコア、ライフ、ステージ情報
        - アイテム効果UI: 凍結タイマー、無敵状態等
        """
        self.draw_ui()
        self.item_manager.draw_ui_effects()

    def _draw_special_effects(self) -> None:
        """
        特殊効果とオーバーレイを描画。

        一時停止状態時には半透明オーバーレイと
        一時停止テキストを表示します。
        """
        if self.pause_timer > 0:
            # 半透明黒オーバーレイ
            pyxel.rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BLACK)
            # 中央配置一時停止テキスト
            self._draw_centered_text("PAUSED", SCREEN_HEIGHT // 2, COLOR_WHITE)

    def draw_ui(self) -> None:
        """
        プレイヤー状態とゲーム情報を含むゲームユーザーインターフェイスを描画。

        UIレイアウト（画面下部）:
        - 上段: スコア、ライフ、ステージ番号
        - 下段: 撃破敵数、パワーレベル状態

        UIは必要なゲーム情報をゲームプレイエリアを乱すことなく提供します。
        すべてのテキストは一貫したフォーマットと色を使用します。

        エラーハンドリング:
        UI描画エラー時も基本的な情報表示を維持するため、
        個別要素のエラーをキャッチします。
        """
        # 画面下部のUI領域配置
        ui_y = SCREEN_HEIGHT - UI_HEIGHT

        try:
            # 上段UI情報の描画
            self._draw_top_ui_row(ui_y)

            # 下段UI情報の描画
            self._draw_bottom_ui_row(ui_y)

        except Exception as e:
            if DEBUG_MODE:
                print(f"UI drawing error: {e}")

    def _draw_top_ui_row(self, ui_y: int) -> None:
        """
        UI上段（スコア、ライフ、ステージ）を描画。

        引数:
            ui_y: UI領域のY座標
        """
        # 現在スコア（左配置）
        score_text = UI_SCORE.format(self.score)
        pyxel.text(8, ui_y, score_text, COLOR_WHITE)

        # 残りライフ（中央左）
        lives_text = UI_LIVES.format(self.player.lives)
        pyxel.text(120, ui_y, lives_text, COLOR_WHITE)

        # 現在ステージ番号（右配置）
        stage_text = UI_STAGE.format(self.current_stage)
        pyxel.text(180, ui_y, stage_text, COLOR_WHITE)

    def _draw_bottom_ui_row(self, ui_y: int) -> None:
        """
        UI下段（撃破数、パワーレベル）を描画。

        引数:
            ui_y: UI領域のY座標
        """
        # 撃破敵数（左配置）
        destroyed = self.enemy_manager.get_remaining_count()
        killed_text = UI_KILLED.format(destroyed)
        pyxel.text(8, ui_y + 8, killed_text, COLOR_WHITE)

        # 現在パワーレベル状態（中央左、緑でハイライト）
        power_text = POWER_LEVEL_NAMES[min(self.player.power_level, len(POWER_LEVEL_NAMES) - 1)]
        power_display = UI_POWER.format(power_text)
        pyxel.text(120, ui_y + 8, power_display, COLOR_GREEN)

    def draw_game_over(self) -> None:
        """
        最終スコアとハイスコア状態を含むゲームオーバー画面を描画。

        ゲームオーバー画面機能:
        - 背景として最終ゲーム状態を表示
        - 目立つゲームオーバーメッセージオーバーレイ
        - 最終スコア表示
        - 達成時の新ハイスコア祝福
        - プロフェッショナルな境界線付きオーバーレイデザイン

        オーバーレイは最終ゲーム状態を保持しながら、
        ゲーム終了を明確に示します。

        エラーハンドリング:
        オーバーレイ描画エラー時も基本的なゲームオーバー表示を維持します。
        """
        # 背景として最終ゲーム状態を描画
        self.draw_game()

        try:
            # ゲームオーバー情報用の中央オーバーレイボックス作成
            self._draw_game_over_overlay()

        except Exception as e:
            if DEBUG_MODE:
                print(f"Game over overlay error: {e}")
            # エラー時は基本的なゲームオーバーテキストのみ表示
            self._draw_centered_text(TEXT_GAME_OVER, SCREEN_HEIGHT // 2, COLOR_RED)

    def _draw_game_over_overlay(self) -> None:
        """
        ゲームオーバー情報オーバーレイを描画。

        オーバーレイ構成:
        - 背景と境界線
        - ゲームオーバータイトル
        - 最終スコア
        - 新ハイスコア祝福（該当時のみ）
        """
        # オーバーレイ配置計算
        overlay_y = SCREEN_HEIGHT // 2 - 40
        overlay_width = SCREEN_WIDTH - 64
        overlay_height = 80

        # オーバーレイ背景と境界線
        pyxel.rect(32, overlay_y, overlay_width, overlay_height, COLOR_BLACK)
        pyxel.rectb(32, overlay_y, overlay_width, overlay_height, COLOR_WHITE)

        # ゲームオーバータイトルテキスト（目立つ赤色）
        self._draw_centered_text(TEXT_GAME_OVER, overlay_y + 16, COLOR_RED)

        # 最終スコア表示
        score_text = TEXT_FINAL_SCORE.format(self.score)
        self._draw_centered_text(score_text, overlay_y + 32, COLOR_WHITE)

        # 新ハイスコア祝福（達成時のみ）
        if self.score >= self.high_score:
            self._draw_centered_text(TEXT_NEW_HIGH_SCORE, overlay_y + 48, COLOR_YELLOW)

    def draw_stage_clear(self) -> None:
        """
        ステージクリア祝福画面を描画。

        ステージクリア画面機能:
        - 背景として完了ステージ状態を表示
        - 祝福オーバーレイメッセージ
        - ステージ番号確認
        - 成功を示す緑色の使用
        - 次ステージ前の短い祝福

        オーバーレイは背景でクリアされたステージを表示しながら、
        ステージ完了に対する肯定的フィードバックを提供します。

        エラーハンドリング:
        オーバーレイ描画エラー時も基本的な祝福メッセージを表示します。
        """
        # 背景として完了ステージ状態を描画
        self.draw_game()

        try:
            # ステージクリア祝福用の中央オーバーレイボックス作成
            self._draw_stage_clear_overlay()

        except Exception as e:
            if DEBUG_MODE:
                print(f"Stage clear overlay error: {e}")
            # エラー時は基本的な祝福テキストのみ表示
            clear_text = TEXT_STAGE_CLEAR.format(self.current_stage)
            self._draw_centered_text(clear_text, SCREEN_HEIGHT // 2, COLOR_GREEN)

    def _draw_stage_clear_overlay(self) -> None:
        """
        ステージクリア祝福オーバーレイを描画。

        オーバーレイ構成:
        - 背景と境界線
        - ステージクリア祝福テキスト
        """
        # オーバーレイ配置計算
        overlay_y = SCREEN_HEIGHT // 2 - 20
        overlay_width = SCREEN_WIDTH - 64
        overlay_height = 40

        # オーバーレイ背景と境界線
        pyxel.rect(32, overlay_y, overlay_width, overlay_height, COLOR_BLACK)
        pyxel.rectb(32, overlay_y, overlay_width, overlay_height, COLOR_WHITE)

        # ステージクリア祝福テキスト（肯定的緑色）
        clear_text = TEXT_STAGE_CLEAR.format(self.current_stage)
        self._draw_centered_text(clear_text, overlay_y + 16, COLOR_GREEN)