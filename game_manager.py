# -*- coding: utf-8 -*-
"""
ゲームマネージャー - 中央オーケストレーター

GameManagerはタンクバトルゲーム全体の中央コーディネーターとして機能し、
すべてのゲームシステム、状態遷移、メインゲームループを管理する。

主要な責任:
- ゲーム状態管理（タイトル、ゲームプレイ、ゲームオーバー、ステージクリア）
- すべてのゲームシステムの協調（マップ、プレイヤー、敵、弾丸、アイテム）
- メイン更新・描画ループ
- 入力処理と状態遷移
- スコア追跡とハイスコア管理
- ステージ進行と難易度調整
- オーディオシステム統合
- UI描画とゲーム情報表示

アーキテクチャ:
GameManagerはコンポーネントベースアーキテクチャを使用し、各主要ゲームシステムを
専用のマネージャークラスで管理する。これにより関心の分離を促進し、
コードベースの保守性を向上させる。

ゲームループ:
1. すべてのゲームシステムを適切な順序で更新
2. 衝突と相互作用を処理
3. 勝敗条件をチェック
4. すべての視覚要素を描画
5. 状態遷移を処理
"""

from typing import TYPE_CHECKING
import pyxel
from constants import *
from map_manager import MapManager
from player import Player
from enemy import EnemyManager
from bullet import BulletManager
from item import ItemManager
from collision import CollisionManager
from game_context import GameContext

if TYPE_CHECKING:
    pass

class GameManager:
    """
    すべてのシステムとゲーム状態を管理する中央ゲームコーディネーター。
    
    GameManagerはタイトル画面からゲームプレイ、ゲームオーバーまでの
    ゲーム体験全体を統率する。すべての主要ゲームシステムへの参照を維持し、
    それらの相互作用を協調する。
    
    ゲーム状態:
    - STATE_TITLE: ハイスコア表示付きタイトル画面
    - STATE_GAME: すべてのシステムが動作するアクティブゲームプレイ
    - STATE_GAME_OVER: 最終スコア付きゲームオーバー画面
    - STATE_STAGE_CLEAR: ステージクリア祝福画面
    
    管理するコアシステム:
    - MapManager: ステージレイアウトとタイルベース衝突
    - Player: プレイヤータンクの制御と状態
    - EnemyManager: AIタンクのスポーンと行動
    - BulletManager: 弾丸の物理と衝突
    - ItemManager: パワーアップと一時効果
    - CollisionManager: システム間衝突検出
    - GameContext: 共有リソース（爆発、サウンド）
    
    属性:
        state (int): 現在のゲーム状態（STATE_*定数）
        game_context (GameContext): 共有ゲームリソース
        score (int): 現在のプレイヤースコア
        high_score (int): 達成したベストスコア
        current_stage (int): 現在アクティブなステージ番号
        ゲームシステム用の各種マネージャーインスタンス
        状態遷移用のタイマー変数
    """
    def __init__(self) -> None:
        """
        ゲームマネージャーとすべてのゲームシステムを初期化する。
        
        セットアッププロセス:
        1. ゲーム状態とスコアシステムを初期化
        2. 共有リソース用の一元化ゲームコンテキストを作成
        3. 適切な依存関係ですべてのマネージャーコンポーネントを初期化
        4. 通信用のシステム間参照を設定
        5. 最初のステージを読み込み、タイトル音楽を開始
        6. ベース破壊コールバック用のグローバル参照を作成
        
        システム間の適切な依存性注入を確実にするため、
        初期化順序が重要である。
        """
        # ゲーム状態を初期化
        self.state: int = STATE_TITLE  # タイトル画面から開始
        
        # 共有リソース用の一元化ゲームコンテキストを作成
        # これにより爆発効果とサウンド管理をすべてのシステムに提供
        self.game_context: GameContext = GameContext()
        
        # スコアと進行システムを初期化
        self.score: int = 0            # 現在のゲームスコア
        self.high_score: int = 0       # 達成したベストスコア
        self.current_stage: int = 1    # ステージ1から開始
        
        # システム間アクセス用にゲーム状態をコンテキストと同期
        self.game_context.score = self.score
        self.game_context.high_score = self.high_score
        self.game_context.current_stage = self.current_stage
        
        # 依存性注入でコアゲームシステムを初期化
        self.map_manager: MapManager = MapManager()
        self.player: Player = Player(7 * TILE_SIZE, 11 * TILE_SIZE)  # ベースの前に配置
        self.enemy_manager: EnemyManager = EnemyManager()
        self.bullet_manager: BulletManager = BulletManager(self.game_context.explosion_manager)
        self.item_manager: ItemManager = ItemManager()
        self.collision_manager: CollisionManager = CollisionManager(self.game_context)
        
        # 通信用のシステム間参照を確立
        # マップマネージャーは弾丸-タイル衝突用の爆発効果が必要
        self.map_manager.explosion_manager = self.game_context.explosion_manager
        self.map_manager.game_context = self.game_context
        
        # 遷移用のゲーム状態タイミング変数
        self.game_over_timer: int = 0    # ゲームオーバー画面用カウントダウン
        self.stage_clear_timer: int = 0  # ステージクリア画面用カウントダウン
        self.pause_timer: int = 0        # 一時停止効果用カウントダウン
        
        # デフォルトレイアウトで最初のステージを初期化
        self.init_stage()
        
        # タイトル画面音楽で開始
        self.game_context.sound_manager.play_title_music()
        
        # ベース破壊用のグローバル参照を作成（弾丸衝突で使用）
        # TODO: 適切なコールバックシステムを使用するようリファクタリングが必要
        import game_manager
        game_manager.current_instance = self
    
    def init_stage(self) -> None:
        """
        Initialize a stage with fresh game state.
        
        Stage initialization process:
        1. Load map layout (hardcoded Stage 1, procedural others)
        2. Reset player position to standard starting position
        3. Setup enemy spawn queue based on stage difficulty
        4. Clear all projectiles from previous stage
        5. Remove all items from previous stage
        
        This provides a clean slate for each new stage while maintaining
        player progression (lives, power level, score).
        """
        # Load stage-specific map layout and obstacles
        self.map_manager.load_stage(self.current_stage)
        
        # Reset player to standard starting position (same for all stages)
        # This ensures grid alignment and prevents movement bugs from stage transitions
        self.player.x = float(7 * TILE_SIZE)  # x = 112 (grid position 7)
        self.player.y = float(11 * TILE_SIZE) # y = 176 (grid position 11)
        self.player.direction = UP             # Face upward (toward enemies)
        self.player.is_moving = False          # Ensure not in movement transition
        self.player.move_timer = 0             # Reset movement timer
        
        
        # Initialize enemy spawning system for this stage
        # Enemy count and types scale with stage number
        self.enemy_manager.init_stage(self.current_stage)
        
        # Clear all projectiles to prevent carryover between stages
        self.bullet_manager.clear_all_bullets()
        
        # Clear all power-up items from previous stage
        self.item_manager.clear_all_items()
        
        # Clear all explosion animations from previous stage
        self.game_context.explosion_manager.clear_all()
    
    def trigger_game_over(self) -> None:
        """
        Trigger immediate game over (called when base is destroyed).
        
        This is called directly by bullet collision detection when the base
        is hit. It immediately transitions to game over state with appropriate
        audio and timer setup.
        
        Effects:
        - Immediately change to game over state
        - Start game over timer (2 seconds)
        - Play game over sound effects
        - Does not update high score (handled in normal game_over())
        """
        # Immediately transition to game over state
        self.state = STATE_GAME_OVER
        
        # Set timer for automatic return to title (5 seconds at 60 FPS)
        self.game_over_timer = 300
        
        # Stop title music to free audio channels
        pyxel.stop()
        
        # Add delay counter for audio system to reset
        self.audio_delay_counter = 10  # Wait 10 frames before playing game over audio
    
    def update(self) -> None:
        """
        Main game update loop - called every frame.
        
        Dispatches update logic based on current game state:
        - STATE_TITLE: Handle title screen input and display
        - STATE_GAME: Run main gameplay systems and logic
        - STATE_GAME_OVER: Handle game over screen and transition
        - STATE_STAGE_CLEAR: Handle stage completion celebration
        
        This is the entry point for all game logic each frame.
        """
        if self.state == STATE_TITLE:
            self.update_title()        # Title screen logic
        elif self.state == STATE_GAME:
            self.update_game()         # Main gameplay logic
        elif self.state == STATE_GAME_OVER:
            self.update_game_over()    # Game over screen logic
        elif self.state == STATE_STAGE_CLEAR:
            self.update_stage_clear()  # Stage clear celebration logic
    
    def update_title(self) -> None:
        """
        Update title screen state and handle input.
        
        Title screen features:
        - Display game title and instructions
        - Show current high score
        - Wait for player input to start new game
        - Play title music in background
        
        Input handling:
        - Enter or Space key starts new game
        """
        # Check for game start input
        if pyxel.btnp(KEY_START) or pyxel.btnp(KEY_FIRE):
            self.start_new_game()  # Transition to gameplay
    
    def update_game(self) -> None:
        """
        Update main gameplay systems in proper order.
        
        Update sequence is critical for proper game logic:
        1. Handle pause effects first
        2. Update all game entities (player, enemies, bullets, items)
        3. Update map changes (delayed tile destruction)
        4. Update visual effects (explosions)
        5. Process all collision detection
        6. Check win/lose conditions
        
        The order ensures that:
        - Entity positions are updated before collision detection
        - Collisions are processed after all movement
        - Game state changes happen after all interactions
        """
        # Handle pause effects (item-induced temporary game pause)
        if self.pause_timer > 0:
            self.pause_timer -= 1
            return  # Skip all other updates during pause
        
        # Update all game entities in proper sequence
        self.update_player()     # Player input and movement
        self.update_enemies()    # Enemy AI and movement
        self.update_bullets()    # Projectile physics
        self.update_items()      # Item spawning and effects
        
        # Update map state changes
        self.map_manager.update_delayed_destructions()  # Tile destruction timers
        
        # Update visual effects system
        self.game_context.update_effects()  # Explosion animations
        
        # Process all collision detection after entity updates
        self.update_collisions()
        
        # Check for game win/lose conditions
        self.check_game_conditions()
    
    def update_player(self) -> None:
        """
        Update player tank state and handle player input.
        
        Player update process:
        1. Check if player is alive (has lives remaining)
        2. Update player tank physics and movement
        3. Handle firing input with bullet limit checking
        4. Create and add bullets to bullet manager
        5. Play appropriate sound effects
        
        Firing system:
        - Respects power level bullet limits (1 or 2 bullets max)
        - Only creates bullets when fire key is pressed (not held)
        - Plays fire sound effect on successful shot
        """
        # Only update player if alive
        if self.player.lives > 0:
            # Update player movement, input, and state
            self.player.update(self.map_manager)
            
            # Handle player firing input
            if pyxel.btnp(KEY_FIRE):  # Button press, not hold
                # Check if player can fire based on power level and active bullets
                if self.player.can_fire(self.bullet_manager.bullets):
                    # Create new bullet with player's current properties
                    bullet = self.player.fire()
                    self.bullet_manager.add_bullet(bullet)
                    
                    # Play fire sound effect (using explosion sound as working alternative)
                    pyxel.play(0, 2)  # TODO: Replace with proper fire sound
    
    def update_enemies(self) -> None:
        """
        Update enemy tank AI, movement, and behavior.
        
        Enemy update process:
        1. Check for freeze effect from clock power-up
        2. If not frozen, update all enemy AI and movement
        3. Handle enemy firing decisions
        4. Process enemy spawning queue
        
        The freeze effect completely stops enemy updates, providing
        tactical advantage to the player when clock items are collected.
        """
        # Check for temporary freeze effect from clock item
        if self.item_manager.is_freeze_active():
            return  # Skip all enemy updates during freeze
        
        # Update enemy AI, movement, and shooting
        # Enemies need references to map, player, and bullets for AI decisions
        self.enemy_manager.update(self.map_manager, self.player, self.bullet_manager)
    
    def update_bullets(self) -> None:
        """
        Update bullet physics and bullet-to-bullet collisions.
        
        Bullet update process:
        1. Update bullet movement and map collision
        2. Handle bullet-to-bullet collision detection
        3. Clean up inactive bullets
        
        The collision manager handles bullet-vs-bullet collisions separately
        from other collision types for better organization.
        """
        # Update bullet physics and map collisions
        self.bullet_manager.update(self.map_manager)
        
        # Handle bullet-to-bullet collisions (bullets can destroy each other)
        self.collision_manager.update_bullet_collisions(self.bullet_manager)
    
    def update_items(self) -> None:
        """
        Update power-up items and handle special item effects.
        
        Item update process:
        1. Update item spawning, visibility, and lifetime
        2. Process special item effects (grenade screen-clear)
        3. Award bonus points for grenade-destroyed enemies
        4. Play appropriate sound effects
        
        The grenade effect is unique in that it destroys all enemies
        instantly, providing both tactical advantage and bonus scoring.
        """
        # Update item spawning, visibility timers, and expiration
        self.item_manager.update(self.map_manager)
        
        # Handle special grenade item effect (destroys all on-screen enemies)
        destroyed_enemies = self.item_manager.handle_grenade_effect(self.enemy_manager, self.game_context.explosion_manager)
        
        if destroyed_enemies:
            # Play explosion sound for grenade effect
            self.game_context.play_sound_effect("explosion")
            
            # Award bonus points for each enemy destroyed by grenade
            for enemy in destroyed_enemies:
                # Base enemy score plus grenade usage bonus
                self.score += enemy.get_score_value() + 200
    
    def update_collisions(self) -> None:
        """
        Process all collision detection between game entities.
        
        Collision processing order:
        1. Player bullets vs enemies (awards points, spawns items)
        2. Clean up destroyed enemies immediately
        3. Enemy bullets vs player and base (triggers damage/game over)
        4. Tank-to-tank physical collisions
        5. Player vs item pickup collisions
        
        The order is important to ensure:
        - Score is awarded before entities are removed
        - Game over is checked before other collisions
        - Destroyed entities don't interfere with remaining collision checks
        """
        # Handle player bullet vs enemy collisions
        destroyed_enemies = self.collision_manager.check_player_bullet_collisions(
            self.player, self.bullet_manager, self.enemy_manager, self.item_manager)
        
        # Award points for each enemy destroyed by player
        for enemy in destroyed_enemies:
            self.score += enemy.get_score_value()
        
        # Immediately clean up destroyed enemies to prevent gameplay issues
        # This prevents destroyed enemies from blocking movement or participating in other collisions
        if destroyed_enemies:
            self.enemy_manager.cleanup_inactive_enemies()
        
        # Handle enemy bullet vs player/base collisions
        base_destroyed = self.collision_manager.check_enemy_bullet_collisions(
            self.player, self.bullet_manager, self.map_manager)
        
        # Check for game over conditions (base destroyed or player out of lives)
        if base_destroyed or self.collision_manager.check_base_destruction(self.map_manager):
            self.game_over()  # Trigger game over sequence
            return           # Skip remaining collision checks
        
        # Handle tank-to-tank physical collisions (after enemy cleanup)
        self.collision_manager.check_tank_collisions(self.player, self.enemy_manager)
        
        # Handle player pickup of power-up items
        self.collision_manager.check_item_collisions(self.player, self.item_manager)
    
    def check_game_conditions(self) -> None:
        """
        Check for game win/lose conditions and trigger state transitions.
        
        Condition checking order:
        1. Player death (no lives remaining) -> Game Over
        2. Stage completion (all enemies defeated) -> Stage Clear
        
        The order ensures that player death takes precedence over stage
        completion if both occur in the same frame.
        """
        # Check for player death condition
        if self.player.lives <= 0:
            self.game_over()  # Trigger game over sequence
            return           # Don't check other conditions
        
        # Check for stage completion condition
        if self.enemy_manager.is_stage_complete():
            self.stage_clear()  # Trigger stage clear sequence
            return             # Don't check other conditions
    
    def start_new_game(self) -> None:
        """
        Initialize a fresh game session from the title screen.
        
        New game setup:
        1. Reset all game progress (score, stage)
        2. Reset player state (lives, power level)
        3. Initialize Stage 1
        4. Start gameplay music
        5. Transition to active game state
        
        This provides a clean slate while preserving high score.
        """
        # Transition to active gameplay state
        self.state = STATE_GAME
        
        # Reset game progress
        self.score = 0             # Start with zero score
        self.current_stage = 1     # Begin with Stage 1
        
        # Reset player to starting condition
        self.player.lives = PLAYER_LIVES        # Full lives
        self.player.power_level = POWER_NORMAL  # Basic power level
        
        # Initialize first stage
        self.init_stage()
        
        # Stop title music - no background music during gameplay (sound effects only)
        self.game_context.sound_manager.stop_music()
    
    def game_over(self) -> None:
        """
        Handle game over transition and high score updates.
        
        Game over process:
        1. Transition to game over state
        2. Play game over sound effects
        3. Set timer for automatic return to title
        4. Update high score if current score is better
        
        The game over timer allows players to see their final score
        before automatically returning to the title screen.
        """
        # Transition to game over state
        self.state = STATE_GAME_OVER
        
        # Set timer for automatic return to title (5 seconds at 60 FPS)
        self.game_over_timer = 300
        
        # Update high score if player achieved new record
        if self.score > self.high_score:
            self.high_score = self.score
        
        # Play game over sound effects through sound manager
        self.game_context.sound_manager.play_game_over_sound()
        self.game_context.sound_manager.play_game_over_music()
    
    def stage_clear(self) -> None:
        """
        Handle stage completion and bonus scoring.
        
        Stage clear process:
        1. Transition to stage clear state
        2. Set timer for stage clear celebration
        3. Calculate and award bonus points
        4. Play stage clear sound effect
        
        Bonus scoring formula:
        - Stage bonus: current_stage * 100 points
        - Life bonus: remaining_lives * 500 points
        This rewards both progression and survival.
        """
        # Transition to stage clear celebration state
        self.state = STATE_STAGE_CLEAR
        
        # Set timer for stage clear celebration (2 seconds at 60 FPS)
        self.stage_clear_timer = 120
        
        # Calculate and award stage completion bonuses
        stage_bonus = (self.current_stage * 100) + (self.player.lives * 500)
        self.score += stage_bonus
        
        # Play stage clear sound effect
        self.game_context.sound_manager.play_stage_clear_sound()
    
    def update_game_over(self) -> None:
        """
        Update game over screen state and handle input.
        
        Game over screen features:
        - Display final score and high score status
        - Automatic return to title after timer expires
        - Manual return to title with start key
        - Transition back to title music
        
        The timer ensures players have time to see their final score,
        while the input option allows faster navigation.
        """
        # Handle delayed audio playback
        if hasattr(self, 'audio_delay_counter') and self.audio_delay_counter > 0:
            self.audio_delay_counter -= 1
            if self.audio_delay_counter == 0:
                # Play game over sound
                self.game_context.sound_manager.play_game_over_sound()
        
        # Countdown game over timer
        self.game_over_timer -= 1
        
        # Check for automatic timeout or manual input
        if self.game_over_timer <= 0 or pyxel.btnp(KEY_START):
            # Return to title screen
            self.state = STATE_TITLE
            # Start title music
            self.game_context.sound_manager.play_title_music()
    
    def update_stage_clear(self) -> None:
        """
        Update stage clear celebration state.
        
        Stage clear features:
        - Display stage completion message
        - Show bonus points awarded
        - Automatic advancement to next stage after timer
        - Brief celebration period for player satisfaction
        
        The timer provides a moment of accomplishment before
        continuing to the next challenge.
        """
        # Countdown stage clear timer
        self.stage_clear_timer -= 1
        
        # Automatically advance to next stage when timer expires
        if self.stage_clear_timer <= 0:
            self.advance_stage()  # Progress to next stage or end game
    
    def advance_stage(self) -> None:
        """
        Progress to the next stage or complete the game.
        
        Stage progression logic:
        1. Increment current stage number
        2. Check if all stages completed
        3. If completed: Award completion bonus and show final score
        4. If not completed: Initialize next stage and continue gameplay
        
        Game completion provides a substantial bonus reward and
        transitions to the final score display.
        """
        # Progress to next stage
        self.current_stage += 1
        
        # Check if player has completed all stages
        if self.current_stage > TOTAL_STAGES:
            # Player has beaten the entire game!
            self.score += 10000  # Substantial completion bonus
            self.game_over()     # Show final score with completion status
        else:
            # Continue to next stage
            self.state = STATE_GAME  # Return to active gameplay
            self.init_stage()        # Initialize next stage
    
    def draw(self) -> None:
        """
        Main game render loop - called every frame after update.
        
        Dispatches rendering based on current game state:
        - STATE_TITLE: Title screen with high score
        - STATE_GAME: Full game rendering (map, entities, UI)
        - STATE_GAME_OVER: Game over screen with final score
        - STATE_STAGE_CLEAR: Stage completion celebration
        
        This is the entry point for all visual rendering each frame.
        """
        if self.state == STATE_TITLE:
            self.draw_title()        # Title screen rendering
        elif self.state == STATE_GAME:
            self.draw_game()         # Main gameplay rendering
        elif self.state == STATE_GAME_OVER:
            self.draw_game_over()    # Game over screen rendering
        elif self.state == STATE_STAGE_CLEAR:
            self.draw_stage_clear()  # Stage clear celebration rendering
    
    def draw_title(self) -> None:
        """
        Render the title screen with game information and instructions.
        
        Title screen elements:
        - Game title and subtitle
        - Control instructions for new players
        - Flashing start prompt for visual attention
        - Current high score display
        - Centered layout for professional appearance
        
        Uses frame-based animation for the start prompt blinking effect.
        """
        # Clear screen with black background
        pyxel.cls(COLOR_BLACK)
        
        # Main game title
        title_text = "TANK BATTLE"
        text_width = len(title_text) * 4  # Pyxel font is 4 pixels wide per character
        pyxel.text(SCREEN_WIDTH // 2 - text_width // 2, 60, title_text, COLOR_YELLOW)
        
        # Game subtitle/description
        subtitle = "DEFEND YOUR BASE!"
        sub_width = len(subtitle) * 4
        pyxel.text(SCREEN_WIDTH // 2 - sub_width // 2, 80, subtitle, COLOR_WHITE)
        
        # Control instructions for new players (centered)
        move_text = "ARROW KEYS: MOVE"
        move_width = len(move_text) * 4
        pyxel.text(SCREEN_WIDTH // 2 - move_width // 2, 120, move_text, COLOR_WHITE)
        
        fire_text = "SPACE: FIRE"
        fire_width = len(fire_text) * 4
        pyxel.text(SCREEN_WIDTH // 2 - fire_width // 2, 130, fire_text, COLOR_WHITE)
        
        quit_text = "Q: QUIT"
        quit_width = len(quit_text) * 4
        pyxel.text(SCREEN_WIDTH // 2 - quit_width // 2, 140, quit_text, COLOR_WHITE)
        
        # Flashing start prompt (blinks every 30 frames = 0.5 seconds)
        if (pyxel.frame_count // 30) % 2:  # On/off every 30 frames
            start_text = "PRESS ENTER TO START"
            start_width = len(start_text) * 4
            pyxel.text(SCREEN_WIDTH // 2 - start_width // 2, 180, start_text, COLOR_GREEN)
        
        # Current high score display
        high_score_text = f"HIGH SCORE: {self.high_score:06d}"
        hs_width = len(high_score_text) * 4
        pyxel.text(SCREEN_WIDTH // 2 - hs_width // 2, 200, high_score_text, COLOR_CYAN)
    
    def draw_game(self) -> None:
        """
        Render the main gameplay screen with all game elements.
        
        Rendering order (back to front):
        1. Clear screen background
        2. Map tiles and terrain
        3. Game entities (player, enemies, bullets, items)
        4. Visual effects (explosions)
        5. UI elements (score, lives, status)
        6. Special overlays (pause screen)
        
        The rendering order ensures proper visual layering with UI
        elements appearing on top of game entities.
        """
        # Clear screen with black background
        pyxel.cls(COLOR_BLACK)
        
        # Draw game world elements (back to front layering)
        self.map_manager.draw()     # Terrain and obstacles (background layer)
        self.player.draw()          # Player tank
        self.enemy_manager.draw()   # Enemy tanks
        self.bullet_manager.draw()  # Projectiles
        self.item_manager.draw()    # Power-up items
        self.map_manager.draw_forest_overlay()  # Forest tiles above tanks for cover effect
        self.game_context.draw_effects()  # Explosion animations (foreground effects)
        
        # Draw user interface elements
        self.draw_ui()  # Score, lives, stage info
        
        # Draw special item effect indicators
        self.item_manager.draw_ui_effects()  # Freeze timer, invincibility status, etc.
        
        # Draw pause overlay if game is paused
        if self.pause_timer > 0:
            # Semi-transparent black overlay
            pyxel.rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BLACK)
            # Centered pause text
            pause_text = "PAUSED"
            text_width = len(pause_text) * 4
            pyxel.text(SCREEN_WIDTH // 2 - text_width // 2, SCREEN_HEIGHT // 2, pause_text, COLOR_WHITE)
    
    def draw_ui(self) -> None:
        """
        Render the game user interface with player status and game information.
        
        UI Layout (bottom of screen):
        - Top row: Score, Lives, Stage number
        - Bottom row: Remaining enemies, Power level status
        
        The UI provides essential game information without cluttering
        the gameplay area. All text uses consistent formatting and colors.
        """
        # Position UI at bottom of screen, above the reserved UI area
        ui_y = SCREEN_HEIGHT - 16
        
        # Top row of UI information
        # Current score (left aligned)
        pyxel.text(8, ui_y, f"SCORE:{self.score:06d}", COLOR_WHITE)
        
        # Remaining lives (center-left)
        pyxel.text(120, ui_y, f"LIVES:{self.player.lives}", COLOR_WHITE)
        
        # Current stage number (right aligned)
        pyxel.text(180, ui_y, f"STAGE:{self.current_stage:02d}", COLOR_WHITE)
        
        # Bottom row of UI information
        # Destroyed enemies count (left aligned)
        destroyed = self.enemy_manager.get_remaining_count()
        pyxel.text(8, ui_y + 8, f"KILLED:{destroyed:02d}", COLOR_WHITE)
        
        # Current power level status (center-left, highlighted in green)
        power_names = ["NORMAL", "FAST", "DOUBLE", "SUPER"]
        power_text = power_names[min(self.player.power_level, 3)]  # Cap at max index
        pyxel.text(120, ui_y + 8, f"POWER:{power_text}", COLOR_GREEN)
    
    def draw_game_over(self) -> None:
        """
        Render the game over screen with final score and high score status.
        
        Game over screen features:
        - Shows final game state in background
        - Prominent game over message overlay
        - Final score display
        - New high score celebration if achieved
        - Professional bordered overlay design
        
        The overlay preserves the final game state while clearly
        indicating the game has ended.
        """
        # Draw final game state as background
        self.draw_game()
        
        # Create centered overlay box for game over information
        overlay_y = SCREEN_HEIGHT // 2 - 40  # Center vertically
        overlay_width = SCREEN_WIDTH - 64     # Leave margins on sides
        overlay_height = 80
        
        # Draw overlay background and border
        pyxel.rect(32, overlay_y, overlay_width, overlay_height, COLOR_BLACK)   # Background
        pyxel.rectb(32, overlay_y, overlay_width, overlay_height, COLOR_WHITE)  # Border
        
        # Game over title text (prominent red color)
        game_over_text = "GAME OVER"
        text_width = len(game_over_text) * 4
        pyxel.text(SCREEN_WIDTH // 2 - text_width // 2, overlay_y + 16, game_over_text, COLOR_RED)
        
        # Final score display
        score_text = f"FINAL SCORE: {self.score:06d}"
        score_width = len(score_text) * 4
        pyxel.text(SCREEN_WIDTH // 2 - score_width // 2, overlay_y + 32, score_text, COLOR_WHITE)
        
        # New high score celebration (only if achieved)
        if self.score >= self.high_score:
            hs_text = "NEW HIGH SCORE!"
            hs_width = len(hs_text) * 4
            pyxel.text(SCREEN_WIDTH // 2 - hs_width // 2, overlay_y + 48, hs_text, COLOR_YELLOW)
    
    def draw_stage_clear(self) -> None:
        """
        Render the stage clear celebration screen.
        
        Stage clear screen features:
        - Shows completed stage state in background
        - Celebratory overlay message
        - Stage number acknowledgment
        - Positive green color for success
        - Brief celebration before next stage
        
        The overlay provides positive feedback for stage completion
        while showing the cleared stage in the background.
        """
        # Draw completed stage state as background
        self.draw_game()
        
        # Create centered overlay box for stage clear celebration
        overlay_y = SCREEN_HEIGHT // 2 - 20  # Center vertically
        overlay_width = SCREEN_WIDTH - 64     # Leave margins on sides
        overlay_height = 40
        
        # Draw overlay background and border
        pyxel.rect(32, overlay_y, overlay_width, overlay_height, COLOR_BLACK)   # Background
        pyxel.rectb(32, overlay_y, overlay_width, overlay_height, COLOR_WHITE)  # Border
        
        # Stage clear celebration text (positive green color)
        clear_text = f"STAGE {self.current_stage} CLEAR!"
        text_width = len(clear_text) * 4
        pyxel.text(SCREEN_WIDTH // 2 - text_width // 2, overlay_y + 16, clear_text, COLOR_GREEN)