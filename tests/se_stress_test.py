# -*- coding: utf-8 -*-
"""
SEストレステスト - 再生コマンド蓄積によるオーディオ停止の検証

仮説（ユーザー報告）: 移動キー押しっぱなしでエンジン音の pyxel.play() が
8フレームごとに呼ばれ続け、再生コマンドの蓄積によりオーディオエンジンが
途中から音を再生しなくなる。

検証方法:
実ゲームと同条件の pyxel.run() メインループ内で play() を発行し、各チャンネルの
pyxel.play_pos()（オーディオスレッドが進めている再生位置）を監視する。
- 再生位置が2秒以上凍結 → オーディオエンジンの停止（事象の再現）

モード:
- spam: 旧実装相当。エンジン音を8フレームごとに再トリガー
- loop: 新実装相当。loop=True で1回だけ再生し、イベントSEのみ随時再生
- music: play() を一切呼ばず、タイトルBGM（playm ループ）のみ再生
         （凍結が play() 起因か時間経過起因かの切り分け用）

実行方法:
    python tests/se_stress_test.py [spam|loop|music] [継続秒数]
"""

import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import pyxel
from constants import *
from sound_manager import SoundManager

MONITOR_CHANNELS = (SOUND_CHANNEL_ENGINE, SOUND_CHANNEL_FIRE,
                    SOUND_CHANNEL_EXPLOSION)


class StressApp:
    """pyxel.run() 内でSE再生を連打し、オーディオ凍結を監視するアプリ。"""

    def __init__(self, mode: str, duration: float) -> None:
        self.mode = mode
        self.total_frames = int(duration * 60)
        self.frame = 0
        self.play_calls = 0
        self.freeze_events = 0
        self.first_freeze_at: float = -1.0
        self.key_held = True  # loopモード: キー押下状態の模擬
        self.prev_pos_snapshot = None
        self.last_pos_change = time.time()

        pyxel.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="se stress")
        SoundManager()  # 効果音・音楽を初期化

        print(f"ストレス開始: mode={mode}, {duration:.0f}秒間（{self.total_frames}フレーム）")

        # musicモード: play()を使わずBGMループのみ（凍結の切り分け用）
        if self.mode == "music":
            pyxel.playm(1, loop=True)

        pyxel.run(self.update, self.draw)

    def update(self) -> None:
        f = self.frame

        if self.mode == "music":
            pass  # playm のループ再生のみ。play() は一切呼ばない
        elif self.mode == "spam":
            # 旧実装相当: 8フレームごとにエンジン音を再トリガー
            if f % 8 == 0:
                pyxel.play(SOUND_CHANNEL_ENGINE, 0)
                self.play_calls += 1
        else:
            # 新実装相当: 10秒押して0.5秒離す、を繰り返す
            cycle = f % 630  # 600フレーム押下 + 30フレーム解放
            if cycle == 600 and self.key_held:
                self.key_held = False
                pyxel.stop(SOUND_CHANNEL_ENGINE)
            elif cycle == 0:
                self.key_held = True
            if self.key_held and pyxel.play_pos(SOUND_CHANNEL_ENGINE) is None:
                pyxel.play(SOUND_CHANNEL_ENGINE, 0, loop=True)
                self.play_calls += 1

        # 24フレーム(0.4秒)ごとに発射音＋爆発音（連射プレイ相当、musicモード以外）
        if self.mode != "music" and f % 24 == 0:
            pyxel.play(SOUND_CHANNEL_FIRE, 1)
            pyxel.play(SOUND_CHANNEL_EXPLOSION, 2)
            self.play_calls += 2

        # 再生位置の凍結検出（2秒以上一切変化しない）
        pos_snapshot = tuple(pyxel.play_pos(ch) for ch in MONITOR_CHANNELS)
        if pos_snapshot != self.prev_pos_snapshot:
            self.prev_pos_snapshot = pos_snapshot
            self.last_pos_change = time.time()
        elif time.time() - self.last_pos_change > 2.0:
            elapsed = f / 60
            print(f"[NG] {elapsed:6.1f}s: 再生位置が2秒以上凍結 {pos_snapshot}")
            if self.first_freeze_at < 0:
                self.first_freeze_at = elapsed
            self.last_pos_change = time.time()  # 重複報告を抑制
            self.freeze_events += 1

        # 20秒ごとに経過報告
        if f % 1200 == 0 and f > 0:
            print(f"  {f / 60:6.1f}s: play_calls={self.play_calls} "
                  f"pos={pos_snapshot} freeze={self.freeze_events}")

        # 終了判定
        if f >= self.total_frames:
            self._report_and_quit()
        self.frame += 1

    def _report_and_quit(self) -> None:
        print()
        print(f"結果: mode={self.mode} / play() {self.play_calls}回 / "
              f"凍結検出 {self.freeze_events}回")
        if self.freeze_events == 0:
            print("OK: オーディオエンジンは停止しませんでした")
        else:
            print(f"NG: オーディオエンジンの凍結を検出"
                  f"（初回発生: {self.first_freeze_at:.1f}秒）")
        pyxel.quit()

    def draw(self) -> None:
        pyxel.cls(COLOR_BLACK)
        pyxel.text(8, 8, f"SE STRESS [{self.mode}] {self.frame // 60}s", COLOR_WHITE)
        pyxel.text(8, 20, f"plays:{self.play_calls} freeze:{self.freeze_events}",
                   COLOR_WHITE)


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "loop"
    duration = float(sys.argv[2]) if len(sys.argv) > 2 else 120.0
    if mode not in ("spam", "loop", "music"):
        print(f"不明なモード: {mode}（spam / loop / music を指定）")
        sys.exit(2)
    StressApp(mode, duration)


if __name__ == "__main__":
    main()
