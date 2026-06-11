# -*- coding: utf-8 -*-
"""
スモークテスト

ゲームの主要ロジックを自動検証する（ウィンドウは一瞬生成されるが入力不要）。
PyxelはOpenGL必須のため、完全ヘッドレス環境では実行できない点に注意。

検証項目:
1. 全モジュールの初期化とリソース読み込み
2. ゲームループ600フレームの実行（敵スポーン・AI・弾丸・衝突を含む）
3. プレイヤー被弾時のリスポーン仕様
4. アイテムキャリア敵の出現順指定（4・11・18番目）
5. 敵の個体別弾数制限（owner_id）
6. 氷タイルの滑り挙動
7. ステージクリア集計画面の更新・描画
8. ハイスコアの保存・読み込み
9. ポーズのトグル

実行方法:
    python tests/smoke_test.py
"""

import os
import sys

# リポジトリルートをインポートパスに追加し、カレントを移動（リソース読み込みのため）
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import pyxel
from constants import *


def main() -> None:
    failures: list[str] = []

    def check(name: str, condition: bool) -> None:
        status = "OK" if condition else "NG"
        print(f"[{status}] {name}")
        if not condition:
            failures.append(name)

    # --- 1. 初期化 ---
    pyxel.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="smoke")
    # pyxel.load は実行スクリプト基準でパス解決するため絶対パスを指定
    pyxel.load(os.path.join(ROOT, SPRITE_FILE))

    from game_manager import GameManager
    gm = GameManager()
    check("GameManager 初期化", gm.state == STATE_TITLE)

    # --- サウンドシステム（docs/sound_system.md 準拠） ---
    check("ステージ開始ジングル(sound 8)が定義されている",
          len(pyxel.sounds[8].notes) > 0)
    check("SEチャンネルが役割別に分離されている",
          len({SOUND_CHANNEL_ENGINE, SOUND_CHANNEL_FIRE,
               SOUND_CHANNEL_EXPLOSION, SOUND_CHANNEL_ITEM}) == 4)

    # --- 2. ゲームループ600フレーム ---
    gm.start_new_game()
    for _ in range(600):
        gm.update()
        gm.draw()
    check("600フレーム実行（クラッシュなし）", True)
    check("敵がスポーンしている", gm.enemy_manager.enemies_spawned > 0)

    # --- 3. リスポーン仕様 ---
    gm.player.invincible_timer = 0
    gm.player.x, gm.player.y = 32.0, 32.0
    died = gm.player.take_damage()
    check("被弾しても残機があれば死亡しない", not died)
    check(
        "被弾後に開始位置へリスポーン",
        gm.player.x == PLAYER_START_GRID_X * TILE_SIZE
        and gm.player.y == PLAYER_START_GRID_Y * TILE_SIZE,
    )
    check("リスポーン無敵が付与される",
          gm.player.invincible_timer == RESPAWN_INVINCIBLE_FRAMES)

    # --- 4. アイテムキャリア出現順 ---
    from enemy import Enemy, EnemyManager
    em = EnemyManager()
    em.init_stage(1)
    carriers = []
    for order in range(1, ENEMIES_PER_STAGE + 1):
        e = Enemy(0, 0, TANK_LIGHT, carries_item=(order in ITEM_CARRIER_SPAWN_ORDER))
        if e.carries_item:
            carriers.append(order)
            check(f"キャリア敵({order}番目)はアイテム種別を保持", e.item_type is not None)
    check("キャリアは4・11・18番目", carriers == [4, 11, 18])

    # --- 5. 個体別弾数制限 ---
    from bullet import BulletManager
    bm = BulletManager(gm.game_context.explosion_manager)
    e1 = Enemy(0, 0, TANK_LIGHT)
    e2 = Enemy(64, 0, TANK_LIGHT)
    e1.fire_timer = 9999
    e2.fire_timer = 9999
    e1._execute_fire(bm)
    e2._execute_fire(bm)
    check("同タイプの敵2機が同時に発射できる", bm.get_bullet_count() == 2)
    owner_ids = {b.owner_id for b in bm.bullets}
    check("弾丸に個体識別子が設定される", owner_ids == {id(e1), id(e2)})

    # --- 6. 氷タイルの滑り ---
    gm.map_manager.load_stage(1)
    # プレイヤーの前方2タイルを氷・空にして滑りを検証
    gm.player.respawn()
    gm.player.invincible_timer = 0
    px, py = PLAYER_START_GRID_X, PLAYER_START_GRID_Y
    gm.map_manager.set_tile(px, py - 1, TILE_ICE)
    gm.map_manager.set_tile(px, py - 2, TILE_EMPTY)
    gm.player.direction = UP
    gm.player.start_move(0, -TILE_SIZE)  # 氷タイルへ移動開始
    for _ in range(MOVE_ANIMATION_FRAMES + 1):
        gm.player.move_timer -= 1
        gm.player.smooth_move(gm.map_manager)
    check("氷タイル上で同方向への滑りが継続する",
          gm.player.is_moving and gm.player.target_y == (py - 2) * TILE_SIZE)

    # --- 7. ステージクリア集計画面 ---
    gm.enemy_manager.destroyed_by_type = {TANK_LIGHT: 14, TANK_ARMORED: 3,
                                          TANK_FAST_SHOT: 2, TANK_HEAVY: 1}
    gm.stage_clear()
    check("ステージクリア状態へ遷移", gm.state == STATE_STAGE_CLEAR)
    check("ボーナスが記録される",
          gm.last_stage_bonus > 0 and gm.last_life_bonus >= 0)
    gm.draw()  # 集計画面の描画がクラッシュしないこと
    check("集計画面の描画", True)
    for _ in range(STAGE_CLEAR_TIMER + 1):
        gm.update()
    check("タイマー満了で次ステージへ進行", gm.state == STATE_GAME)

    # --- 8. ハイスコア永続化 ---
    gm.score = 99999
    gm.high_score = 0
    gm._update_high_score()
    check("ハイスコアがファイルに保存される", os.path.exists(HIGH_SCORE_FILE))
    check("保存したハイスコアを読み込める", gm._load_high_score() == 99999)
    os.remove(HIGH_SCORE_FILE)  # テスト後の清掃

    # --- 9. ポーズ ---
    gm.state = STATE_GAME
    gm.paused = True
    before = gm.enemy_manager.spawn_timer
    gm.update()
    gm.draw()
    check("ポーズ中はゲームが更新されない",
          gm.enemy_manager.spawn_timer == before)
    gm.paused = False

    # --- 結果 ---
    print()
    if failures:
        print(f"FAILED: {len(failures)} 件の検証に失敗: {failures}")
        sys.exit(1)
    print("ALL CHECKS PASSED")
    sys.exit(0)


if __name__ == "__main__":
    main()
