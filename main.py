# -*- coding: utf-8 -*-
"""
Tank Battle - メインエントリーポイント

Battle Cityのクローンゲームのメインエントリーポイント。
Pyxelエンジンを初期化し、ゲームループを開始する。

機能:
- Pyxelエンジンの初期化とウィンドウ設定
- ゲームリソース（スプライト、サウンド）の読み込み
- ゲームマネージャーの初期化と実行
- エラーハンドリングとグレースフル終了

使用方法:
    python main.py

エラー処理:
- リソースファイルの読み込み失敗時に適切なエラーメッセージを表示
- 必要なファイルが存在しない場合のグレースフル終了
"""

import sys
from typing import NoReturn
import pyxel

from constants import *
from game_manager import GameManager


class TankBattle:
    """
    Tank Battleゲームのメインアプリケーションクラス。

    このクラスは以下の責任を持つ：
    - Pyxelエンジンの初期化と設定
    - ゲームリソースの読み込みと検証
    - ゲームマネージャーとの統合
    - メインゲームループの実行
    - エラー処理とクリーンアップ

    属性:
        game_manager (GameManager): ゲーム状態とシステムを管理するメインマネージャー
    """

    def __init__(self) -> None:
        """
        Tank Battleアプリケーションを初期化する。

        初期化プロセス:
        1. Pyxelエンジンを指定されたサイズとタイトルで初期化
        2. ゲームマネージャーインスタンスを作成
        3. 必要なリソースファイルを読み込み
        4. サウンドシステムを初期化
        5. メインゲームループを開始

        例外処理:
        - リソース読み込み失敗時は適切なエラーメッセージを表示し終了
        - その他の例外も捕捉してグレースフル終了を実行
        """
        try:
            # Pyxelエンジンを初期化（画面サイズとタイトルを設定）
            pyxel.init(
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
                title=GAME_TITLE
            )

            # ゲームマネージャーを初期化（ゲームシステムの中央制御）
            self.game_manager: GameManager = GameManager()

            # ゲームリソースを読み込み（スプライト、サウンド）
            self._init_resources()

            # Pyxelメインループを開始（60FPSで update() と draw() を呼び出し）
            pyxel.run(self.update, self.draw)

        except KeyboardInterrupt:
            # Ctrl+Cによる中断を適切に処理
            print("\nゲームが中断されました。")
            self._cleanup_and_exit(0)
        except Exception as e:
            # 予期しないエラーを処理
            print(f"予期しないエラーが発生しました: {e}")
            self._cleanup_and_exit(1)

    def _init_resources(self) -> None:
        """
        ゲームリソースファイルを読み込みと検証を行う。

        リソース読み込みプロセス:
        1. my_resource.pyxres ファイルの存在確認
        2. Pyxelリソースファイルの読み込み
        3. 読み込み成功をコンソールに報告
        4. サウンドシステムの再初期化（pyxel.load後に必要）

        例外処理:
        - ファイルが存在しない場合の適切なエラーメッセージ
        - 読み込み失敗時のグレースフル終了
        - リソース破損時の診断情報提供

        Raises:
            SystemExit: リソース読み込みに失敗した場合
        """
        try:
            # メインリソースファイルを読み込み
            # このファイルにはタンク、アイテム、エフェクトのスプライトが含まれる
            pyxel.load(SPRITE_FILE)
            print(f"リソースファイル '{SPRITE_FILE}' の読み込みに成功しました")

            # リソース読み込み後にサウンドシステムを再初期化
            # pyxel.load()はサウンドデータを上書きする可能性があるため
            self._init_sound_system()

        except FileNotFoundError:
            # リソースファイルが見つからない場合
            self._handle_resource_error(
                f"リソースファイル '{SPRITE_FILE}' が見つかりません。",
                "ファイルが正しい場所に存在することを確認してください。"
            )
        except Exception as e:
            # その他のリソース読み込みエラー
            self._handle_resource_error(
                f"リソースファイルの読み込み中にエラーが発生しました: {e}",
                "ファイルが破損していないか確認してください。"
            )

    def _init_sound_system(self) -> None:
        """
        ゲームサウンドシステムを初期化する。

        pyxel.load()によってサウンドデータが上書きされる可能性があるため、
        リソース読み込み後にサウンドシステムを再初期化する。

        初期化内容:
        - ゲーム効果音の定義と設定
        - 背景音楽の設定
        - サウンドチャンネルの割り当て
        """
        if hasattr(self.game_manager, 'game_context') and \
           hasattr(self.game_manager.game_context, 'sound_manager'):
            # ゲームマネージャー経由でサウンドマネージャーを初期化
            self.game_manager.game_context.sound_manager.init_sounds()
            self.game_manager.game_context.sound_manager.init_music()
            print("サウンドシステムの初期化が完了しました")
        else:
            print("警告: サウンドマネージャーが見つかりません")

    def _handle_resource_error(self, error_message: str, suggestion: str) -> NoReturn:
        """
        リソース読み込みエラーを処理し、適切なエラーメッセージを表示する。

        エラー処理プロセス:
        1. エラーメッセージをコンソールに表示
        2. 解決方法の提案を表示
        3. グレースフル終了を実行

        Args:
            error_message (str): 表示するエラーメッセージ
            suggestion (str): ユーザーへの解決方法の提案

        Returns:
            NoReturn: この関数は常にシステム終了を実行
        """
        print(f"\n{ERROR_RESOURCE_LOADING}")
        print(f"詳細: {error_message}")
        print(f"解決方法: {suggestion}")
        print(f"\n{ERROR_RESOURCE_MISSING}")
        self._cleanup_and_exit(1)

    def _cleanup_and_exit(self, exit_code: int) -> NoReturn:
        """
        リソースをクリーンアップしてアプリケーションを終了する。

        クリーンアップ処理:
        1. Pyxelエンジンの適切な終了
        2. 必要に応じて追加のリソース解放
        3. 指定された終了コードでシステム終了

        Args:
            exit_code (int): システム終了コード（0=正常終了、1=エラー終了）

        Returns:
            NoReturn: この関数は常にシステム終了を実行
        """
        try:
            # Pyxelエンジンを適切に終了
            pyxel.quit()
        except Exception:
            # 終了処理中のエラーは無視（既に問題があるため）
            pass

        # システムを指定された終了コードで終了
        sys.exit(exit_code)

    def update(self) -> None:
        """
        メインゲーム更新ループ - 60FPSで呼び出される。

        更新処理:
        1. ゲームマネージャーに制御を委譲
        2. グローバル入力（終了キー）を処理

        グローバル入力:
        - Qキー: 即座にゲームを終了

        この関数はPyxelエンジンによって毎フレーム自動的に呼び出される。
        """
        # メインゲームロジックをゲームマネージャーに委譲
        if hasattr(self, 'game_manager'):
            self.game_manager.update()

        # グローバル終了キーをチェック（どの画面からでも終了可能）
        if pyxel.btnp(KEY_QUIT):
            print("ユーザーによってゲームが終了されました")
            self._cleanup_and_exit(0)

    def draw(self) -> None:
        """
        メインゲーム描画ループ - 60FPSで呼び出される。

        描画処理:
        1. 画面を背景色でクリア
        2. ゲームマネージャーに描画を委譲

        この関数はPyxelエンジンによって毎フレーム自動的に呼び出される。
        すべての描画ロジックはゲームマネージャーとその配下のシステムが処理する。
        """
        # 画面を黒色でクリア
        pyxel.cls(COLOR_BLACK)

        # すべての描画をゲームマネージャーに委譲
        if hasattr(self, 'game_manager'):
            self.game_manager.draw()


def main() -> None:
    """
    アプリケーションのメインエントリーポイント。

    Tank Battleゲームのインスタンスを作成し、実行を開始する。
    この関数はスクリプトが直接実行された場合のみ呼び出される。

    エラー処理:
    - TankBattleクラスの初期化エラーを捕捉
    - 適切なエラーメッセージの表示
    """
    try:
        # Tank Battleゲームのメインインスタンスを作成して実行
        TankBattle()
    except Exception as e:
        print(f"ゲームの開始に失敗しました: {e}")
        sys.exit(1)


# スクリプトが直接実行された場合のみメイン関数を呼び出し
if __name__ == "__main__":
    main()