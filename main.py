import os
import random
import sys
from dataclasses import dataclass
from typing import NamedTuple

import pygame as pg

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ===== 定数 =====
WIDTH = 1000  # 画面の幅
HEIGHT = 600  # 画面の高さ
FPS = 60  # 1秒あたりのフレーム数
GROUND_Y = 520  # 地面のy座標（キャラの足元）
GRAVITY = 0.6  # 重力加速度
ROUND_TIME = 60  # 1ラウンドの制限時間（秒）

FIGHTER_W = 100  # キャラの幅
FIGHTER_H = 140  # キャラの高さ
MAX_HP = 100  # 最大体力
WALK_SPEED = 5  # 歩く速さ
JUMP_POWER = 20  # ジャンプの初速

PUNCH_W, PUNCH_H = 60, 30
PUNCH_DAMAGE = 5
PUNCH_FRAMES, PUNCH_COOLDOWN = 8, 14
KICK_W, KICK_H = 90, 40
KICK_DAMAGE = 12
KICK_FRAMES, KICK_COOLDOWN = 14, 28
UPPER_W, UPPER_H = 50, 90
UPPER_DAMAGE = 15
UPPER_FRAMES, UPPER_COOLDOWN = 16, 30
UPPER_MOVE = 30  # アッパー時動作補正
AIR_W, AIR_H = 70, 60
AIR_DAMAGE = 8
AIR_FRAMES, AIR_COOLDOWN = 12, 18
HITSTUN_FRAMES = 12  # のけぞり時間（通常連打では繋がらない長さ）
KNOCKBACK = 20  # ノックバック距離（大きく飛ばして目押しなしの連打ハメを防止）
MAX_COMBO_LIMIT = 10  # 最大コンボ上限（10ヒットで相手は強制復帰・ダウン立ち上がり）
ADJUSTING_CPU_ATTACK_POINT = -10  # cpuが攻撃するときの攻撃計算の補助判定
AVOID_CHOICE_STANDARD_RATE = 0.33  # cpuが回避するときの逃げの選択基準の境目
AVOID_BACK_WALL_CHECK = 30  # CPU回避時の壁際判定の定数
GAME_TITLE = "FIGHTERS"  # ゲームタイトル
BACK_SELECT = "ESC : BACK"  # メニューセレクトのバックボタン用
CPU_MODE_TITLE = "CPU MODE SELECT"  # cpuのモードセレクトタイトル
CONTROLS_TITLE = "CONTROLS"  # 操作説明のタイトル
MENU_TOP_Y = HEIGHT // 2  # メニューのテキスト表示の最上層部分
MENU_LINE_GAP = 60  # テキストの間隔
DEF_CHOICE_RATE = 0.5  # 防御判断の基準レート
TEXT_SPACE = 35  # 文字の間隔
TEXT_TOP = MENU_TOP_Y - 80  # 文字記載の開始位置
CONTROLS_1P = {
    "move": "LEFT/RIGHT: A/D",
    "jump": "JUMP: W",
    "punch": "PUNCH: C",
    "kick": "KICK: V",
    "upper": "UPPER: F",
    "barrier_up": "BARRIER_UP: R",
    "barrier_md": "BARRIER_MD: S",
    "special": "SPECIAL: Z"
}
CONTROLS_2P = {
    "move": "LEFT/RIGHT: LEFT/RIGHT",
    "jump": "JUMP: UP",
    "punch": "PUNCH: ,",
    "kick": "KICK: M",
    "upper": "UPPER: K",
    "barrier_up": "BARRIER_UP: /",
    "barrier_md": "BARRIER_MD: DOWN",
    "special": "SPECIAL: P"
}
TITLE = {
    "2p": "1 : 2P BATTLE",
    "cpu": "2 : CPU BATTLE",
    "controls": "3 : CONTROLS",
}
TITLE_KEY = {
    pg.K_1: "2p",
    pg.K_2: "cpu",
    pg.K_3: "controls"
}
CPU_MODE_SELECT = {
    "weak": "1 : CPU WEAK",
    "normal": "2 : CPU NORMAL",
    "strong": "3 : CPU STRONG"
}
CPU_SELECT_KEY = {
    pg.K_1: "weak",
    pg.K_2: "normal",
    pg.K_3: "strong",
}

# 必殺技の設定
MAX_SUPER_GAGE = 100
SUPER_GAGE_UP = 1
SUPER_GAGE_REQUIRE = 15
SUPER_DAMAGE = 20
SUPER_SPEED = 25
COMBO_RESET_FRAMES = 90


@dataclass
class KeyConfig:
    """
    プレイヤーごとのキー割り当て（移動・攻撃用）
    """
    left: int
    right: int
    jump: int
    punch: int  # パンチ用キー
    kick: int   # キック用キー
    upper: int  # アッパー用キー
    special: int  # 必殺技キー


# P1: WASD(移動), C(パンチ), V(キック), F(アッパー)
P1_KEYS = KeyConfig(left=pg.K_a, right=pg.K_d, jump=pg.K_w, punch=pg.K_c, kick=pg.K_v, upper=pg.K_f, special=pg.K_z)
P2_KEYS = KeyConfig(left=pg.K_LEFT, right=pg.K_RIGHT, jump=pg.K_UP, punch=pg.K_COMMA, kick=pg.K_m, upper=pg.K_k, special=pg.K_p)


def load_fighter_image(path: str, color: tuple[int, int, int]) -> pg.Surface:
    """
    キャラ画像を読み込み、白背景を透明化して返す関数。

    path : 読み込む画像ファイルのパス
    color : 画像がない場合に代用する四角形の色 (R, G, B)

    Returns:
        pg.Surface: 処理済みの画像
    """
    if os.path.exists(path):
        try:
            img = pg.image.load(path).convert_alpha()
            img = pg.transform.scale(img, (FIGHTER_W, FIGHTER_H))

            # 白背景の透明化処理
            width, height = img.get_size()
            for x in range(width):
                for y in range(height):
                    r, g, b, a = img.get_at((x, y))
                    if r > 200 and g > 200 and b > 200:
                        img.set_at((x, y), (255, 255, 255, 0))
            return img
        except Exception:
            pass

    # 画像が存在しない場合（四角形を生成）
    img = pg.Surface((FIGHTER_W, FIGHTER_H))
    img.fill(color)
    pg.draw.rect(img, (255, 255, 255), (FIGHTER_W - 25, 20, 12, 12))
    return img

# 試験用に入れてます
class SuperAttack(pg.sprite.Sprite):
    """必殺技（ビーム）エフェクトのクラス"""
    def __init__(self, fighter: "Fighter") -> None:
        """
        fighter : 必殺技を放ったキャラクターのインスタンス
        """
        super().__init__()

        beam_path = os.path.join("fig/bb", "beam.png")
        if os.path.exists(beam_path):
            try:
                img = pg.image.load(beam_path).convert_alpha()
                self.image = pg.transform.scale(img, (90, 45))
                w, h = self.image.get_size()
                for x in range(w):
                    for y in range(h):
                        r, g, b, a = self.image.get_at((x, y))
                        if r > 200 and g > 200 and b > 200:
                            self.image.set_at((x, y), (255, 255, 255, 0))
            except Exception:
                self.image = pg.Surface((60, 30), pg.SRCALPHA)
                self.image.fill((255, 0, 0, 128))
        else:
            self.image = pg.Surface((60, 30), pg.SRCALPHA)
            self.image.fill((255, 0, 0, 128))

        if fighter.facing == 1:
            self.image = pg.transform.flip(self.image, True, False)

        self.rect = self.image.get_rect()
        self.rect.centery = fighter.rect.centery

        if fighter.facing == 1:
            self.rect.left = fighter.rect.right
        else:
            self.rect.right = fighter.rect.left

        self.speed = SUPER_SPEED * fighter.facing
        self.damage = SUPER_DAMAGE
        self.owner = fighter

    def update(self):
        """ビームを毎フレーム移動させ、画面外に出たら消滅させる"""
        self.rect.x += self.speed
        if self.rect.right < 0 or self.rect.left > WIDTH:
            self.kill()


class Fighter(pg.sprite.Sprite):
    """格闘キャラクターの挙動やアニメーションを管理するクラス"""

    def __init__(self, name: str, x: int, facing: int, keys: KeyConfig,
                 img_path: str, color: tuple[int, int, int]) -> None:
        """
        name : プレイヤー名
        x : 初期配置のX座標
        facing : キャラクターが向いている向き (1: 右向き, -1: 左向き)
        keys : キーの割り当て設定
        img_path : 立ち絵画像のパス
        color (tuple[int, int, int]): 画像がない場合の代用カラー
        """
        super().__init__()
        self.name = name
        self.keys = keys
        self.facing = facing

        base_dir = "fig/bb"
        self.anim_stand = load_fighter_image(img_path, color)

        punch_path = os.path.join(base_dir, "panch.png")
        self.anim_punch = load_fighter_image(punch_path, color)

        jump_path = os.path.join(base_dir, "jamp.png")
        if not os.path.exists(jump_path):
            jump_path = os.path.join(base_dir, "jump.png")
        self.anim_jump = load_fighter_image(jump_path, color)

        special_path = os.path.join(base_dir, "ex.png")
        self.anim_special = load_fighter_image(special_path, color)

        damage_path = os.path.join(base_dir, "damage.png")
        if not os.path.exists(damage_path):
            damage_path = os.path.join(base_dir, "hit.png")
        self.anim_damage = load_fighter_image(damage_path, color)

        lose_path = os.path.join(base_dir, "lose.png")
        self.anim_lose = load_fighter_image(lose_path, color) if os.path.exists(lose_path) else self.anim_damage

        walk_dir = os.path.join(base_dir, "walk")
        if os.path.exists(walk_dir):
            self.anim_walk_frames = [
                load_fighter_image(os.path.join(walk_dir, "walk1.png"), color),
                load_fighter_image(os.path.join(walk_dir, "walk2.png"), color),
                load_fighter_image(os.path.join(walk_dir, "walk3.png"), color),
            ]
        else:
            self.anim_walk_frames = [self.anim_stand]

        self.walk_anim_index = 0
        self.walk_anim_timer = 0

        self.current_anim = self.anim_stand
        self.rect = self.current_anim.get_rect()
        self.rect.centerx = x
        self.rect.bottom = GROUND_Y
        self.vy = 0
        self.vx = 0
        self.hp = MAX_HP
        self.attack_timer = 0 # 攻撃判定が残っているフレーム数
        self.cooldown = 0 # 次の攻撃までの待ちフレーム数
        self.hitstun = 0 # のけぞりの残りフレーム数
        self.has_hit = False # 今回の攻撃がすでに当たったか

        self.attack_type: str | None = None
        self.current_damage = 0
        self.can_cancel = False
        self.combo_count = 0

        self.prev_punch = False
        self.prev_kick = False
        self.prev_upper = False

        self.is_moving = False
        self.is_defeated = False  # 敗北フラグ

        self.special_pose_timer = 0
        self.super_gauge = 0
        self.combo_timer = 0

        self.update_image_facing()

    def update_image_facing(self) -> None:
        """キャラクターの向いている向きに合わせて画像を左右反転させる"""
        if self.facing == 1:
            self.image = self.current_anim
        else:
            self.image = pg.transform.flip(self.current_anim, True, False)

    def is_on_ground(self) -> bool:
        """キャラクターが地面の上にいるかどうかを判定する"""
        return self.rect.bottom >= GROUND_Y

    def start_attack(
        self, atk_type: str, frames: int, cooldown: int, damage: int
    ) -> None:
        """
        技を発動し、パラメータとキャンセル状態を更新する
        """
        self.attack_type = atk_type
        self.attack_timer = frames
        self.cooldown = cooldown
        self.current_damage = damage
        self.has_hit = False
        self.can_cancel = False
        self.current_anim = self.anim_punch
        self.update_image_facing()

    def handle_input(self, key_lst: pg.key.ScancodeWrapper) -> None:
        """
        キー入力に応じて移動や攻撃を行う

        kpg.key.ScancodeWrapper: 押されているキーの一覧リスト
        """
        if self.is_defeated or self.hitstun > 0 or self.special_pose_timer > 0:
            return

        dx = 0
        self.is_moving = False

        if key_lst[self.keys.left]:
            dx -= WALK_SPEED
            self.is_moving = True
        if key_lst[self.keys.right]:
            dx += WALK_SPEED
            self.is_moving = True
        self.rect.x += dx

        if key_lst[self.keys.jump] and self.is_on_ground():
            self.vy = -JUMP_POWER

        punch_trig = key_lst[self.keys.punch] and not self.prev_punch
        kick_trig = key_lst[self.keys.kick] and not self.prev_kick
        upper_trig = key_lst[self.keys.upper] and not self.prev_upper

        can_act = (self.cooldown == 0) or self.can_cancel

        if can_act:
            if not self.is_on_ground() and (punch_trig or kick_trig):
                self.start_attack("air", AIR_FRAMES, AIR_COOLDOWN, AIR_DAMAGE)
            elif self.is_on_ground() and upper_trig:
                self.start_attack("upper", UPPER_FRAMES, UPPER_COOLDOWN, UPPER_DAMAGE)
            elif punch_trig:
                self.start_attack("punch", PUNCH_FRAMES, PUNCH_COOLDOWN, PUNCH_DAMAGE)
            elif kick_trig:
                self.start_attack("kick", KICK_FRAMES, KICK_COOLDOWN, KICK_DAMAGE)

        self.prev_punch = bool(key_lst[self.keys.punch])
        self.prev_kick = bool(key_lst[self.keys.kick])
        self.prev_upper = bool(key_lst[self.keys.upper])

    def face_to(self, other: "Fighter") -> None:
        """
        相手のプレイヤーの方向を常に向くように設定する

        Fighter: 向き合う相手のキャラクターインスタンス
        """
        if self.is_defeated or self.special_pose_timer > 0:
            return
        self.facing = 1 if other.rect.centerx >= self.rect.centerx else -1
        self.update_image_facing()

    def get_attack_rect(self) -> pg.Rect | None:
        """攻撃判定の矩形（Rect）を生成して返す"""
        if self.is_defeated or self.attack_timer <= 0:
            return None

        if self.attack_type == "upper":
            atk = pg.Rect(0, 0, UPPER_W, UPPER_H)
            atk.bottom = self.rect.top + 20
            atk.centerx = self.rect.centerx + (30 * self.facing)
        elif self.attack_type == "air":
            atk = pg.Rect(0, 0, AIR_W, AIR_H)
            atk.top = self.rect.centery
            if self.facing == 1:
                atk.left = self.rect.centerx
            else:
                atk.right = self.rect.centerx
        elif self.attack_type == "punch":
            atk = pg.Rect(0, 0, PUNCH_W, PUNCH_H)
            atk.centery = self.rect.top + FIGHTER_H // 4
            if self.facing == 1:
                atk.left = self.rect.right
            else:
                atk.right = self.rect.left
        else:  # "kick"
            atk = pg.Rect(0, 0, KICK_W, KICK_H)
            atk.centery = self.rect.top + (FIGHTER_H * 2) // 3
            if self.facing == 1:
                atk.left = self.rect.right
            else:
                atk.right = self.rect.left

        return atk

    def take_damage(self, damage: int, from_dir: int) -> None:
        """
        ダメージを受けてのけぞる
        引数 damage：受けるダメージ量
        引数 from_dir：押し戻される向き（右:+1, 左:-1)
        """
        if self.is_defeated:
            return
        self.hp = max(0, self.hp - damage)
        self.hitstun = HITSTUN_FRAMES
        self.attack_timer = 0
        self.special_pose_timer = 0
        self.rect.x += KNOCKBACK * from_dir
        self.rect.clamp_ip(pg.Rect(0, 0, WIDTH, HEIGHT))

    def trigger_defeat(self, attacker_centerx: int) -> None:
        """
        K.O.演出の処理を行う
        引数 attacker_centerx : 相手のX座標
        """
        if self.is_defeated:
            return
        self.is_defeated = True
        self.current_anim = self.anim_lose
        self.update_image_facing()

        if self.rect.centerx < attacker_centerx:
            self.vx = -5.5
        else:
            self.vx = 5.5
        self.vy = -14

    def update(self) -> None:
        """毎フレームの位置計算、重力、アニメーション状態の更新を行う"""
        if self.is_defeated:
            self.vy += GRAVITY
            self.rect.y += self.vy
            self.rect.x += self.vx
            if self.rect.bottom >= GROUND_Y:
                self.rect.bottom = GROUND_Y
                self.vx = 0
            self.rect.clamp_ip(pg.Rect(0, 0, WIDTH, HEIGHT))
            return

        self.vy += GRAVITY
        self.rect.y += self.vy
        if self.rect.bottom >= GROUND_Y:
            self.rect.bottom = GROUND_Y
            self.vy = 0
        self.rect.clamp_ip(pg.Rect(0, 0, WIDTH, HEIGHT))

        if self.hitstun > 0:
            self.current_anim = self.anim_damage
            self.update_image_facing()
        elif self.special_pose_timer > 0:
            self.special_pose_timer -= 1
            self.current_anim = self.anim_special
            self.update_image_facing()
        elif self.attack_timer > 0:
            self.attack_timer -= 1
            if self.attack_timer == 0:
                self.current_anim = self.anim_stand
                self.update_image_facing()
                self.attack_type = None
        elif not self.is_on_ground():
            self.current_anim = self.anim_jump
            self.update_image_facing()
        else:
            if self.is_moving:
                self.walk_anim_timer += 1
                if self.walk_anim_timer >= 8:
                    self.walk_anim_timer = 0
                    self.walk_anim_index = (self.walk_anim_index + 1) % len(self.anim_walk_frames)
                    self.current_anim = self.anim_walk_frames[self.walk_anim_index]
                    self.update_image_facing()
            else:
                self.walk_anim_index = 0
                self.walk_anim_timer = 0
                self.current_anim = self.anim_stand
                self.update_image_facing()
        if self.attack_timer == 0 and self.cooldown == 0:
            self.can_cancel = False
        self.cooldown = max(0, self.cooldown - 1)
        self.hitstun = max(0, self.hitstun - 1)
        self.combo_timer = max(0, self.combo_timer - 1)
        if self.combo_timer == 0:
            self.combo_count = 0

    def draw(self, screen: pg.Surface) -> None:
        """
        画面にキャラクターを描画する

        screen (pg.Surface): 描画
        """
        screen.blit(self.image, self.rect)
        atk = self.get_attack_rect()
        if atk is not None:
            pg.draw.rect(screen, (255, 220, 0), atk, 3)


def check_hit(attacker: Fighter, defender: Fighter) -> int:
    """
    攻撃判定と被弾処理。10コンボ到達時は相手を強制復帰させる
    引数 attacker : 攻撃
    引数 defender : 防御

    戻り値 int: ヒットストップ用のフレーム数
    """
    if defender.is_defeated:
        return 0
    atk = attacker.get_attack_rect()
    if atk is None or attacker.has_hit:
        return 0
    if atk.colliderect(defender.rect):
        defender.take_damage(attacker.current_damage, attacker.facing)
        attacker.has_hit = True
        attacker.combo_count += 1
        attacker.combo_timer = COMBO_RESET_FRAMES
        attacker.super_gauge = min(MAX_SUPER_GAGE, attacker.super_gauge + SUPER_GAGE_UP * 5)

        # 10ヒット制限：10ヒットに達したら強制復帰（相手ののけぞり解除・コンボ終了）
        if attacker.combo_count >= MAX_COMBO_LIMIT:
            defender.hitstun = 0
            attacker.combo_count = 0
            attacker.can_cancel = False
        else:
            # キックはコンボ締め技のためキャンセル不可、パンチ等の小技のみキャンセル可能
            if attacker.attack_type != "kick":
                attacker.can_cancel = True
        return 8
    return 0


def push_apart(f1: Fighter, f2: Fighter) -> None:
    """
    2人のプレイヤーが重なり合って埋まらないように押し離す

    引数 f1 : プレイヤー1
    引数 f2 : プレイヤー2
    """
    if f1.is_defeated or f2.is_defeated:
        return
    if not f1.rect.colliderect(f2.rect):
        return
    overlap = min(f1.rect.right, f2.rect.right) - max(f1.rect.left, f2.rect.left)
    shift = overlap // 2 + 1
    if f1.rect.centerx <= f2.rect.centerx:
        f1.rect.x -= shift
        f2.rect.x += shift
    else:
        f1.rect.x += shift
        f2.rect.x -= shift
    f1.rect.clamp_ip(pg.Rect(0, 0, WIDTH, HEIGHT))
    f2.rect.clamp_ip(pg.Rect(0, 0, WIDTH, HEIGHT))


def draw_hp_bar(screen: pg.Surface, fighter: Fighter, x: int, font: pg.font.Font, font_combo: pg.font.Font, is_p2: bool = False, tmr: int = 0) -> None:
    """
    体力バー、必殺技ゲージ、プレイヤー名、コンボ数などを画面上に描画する

    引数 screen (pg.Surface): 描画先
    引数 fighter : 対象のキャラクター
    引数 x : 描画開始のX座標
    引数 font : テキスト用フォント
    引数 font_combo : コンボ表示用
    引数 is_p2 (: プレイヤー2側のバー
    引数 tmr : ゲーム内経過フレーム数
    """
    bar_w, bar_h = 380, 22
    y = 25
    hp_w = bar_w * fighter.hp // MAX_HP

    pg.draw.rect(screen, (20, 20, 20), (x - 2, y - 2, bar_w + 4, bar_h + 4), border_radius=4)
    pg.draw.rect(screen, (70, 70, 70), (x, y, bar_w, bar_h))

    if fighter.hp <= 25:
        hp_color = (220, 40, 40)
    else:
        hp_color = (40, 220, 90)

    if not is_p2:
        pg.draw.rect(screen, hp_color, (x, y, hp_w, bar_h))
    else:
        pg.draw.rect(screen, hp_color, (x + (bar_w - hp_w), y, hp_w, bar_h))

    pg.draw.rect(screen, (240, 240, 240), (x, y, bar_w, bar_h), 2, border_radius=3)

    name_surface = font.render(fighter.name, True, (255, 255, 255))
    if not is_p2:
        screen.blit(name_surface, (x, y + bar_h + 5))
    else:
        screen_rect = name_surface.get_rect()
        screen_rect.topright = (x + bar_w, y + bar_h + 5)
        screen.blit(name_surface, screen_rect)

    gauge_y = y + bar_h + 30
    gauge_h = 10
    pg.draw.rect(screen, (50, 50, 50), (x, gauge_y, bar_w, gauge_h))
    gauge_w = bar_w * fighter.super_gauge // MAX_SUPER_GAGE

    if fighter.super_gauge >= MAX_SUPER_GAGE:
        flash = int(180 + 75 * (pg.math.Vector2(0, 1).rotate(tmr * 15).y))
        gauge_color = (255, flash, 0)
        border_color = (255, 255, 100)
    else:
        gauge_color = (0, 150, 255)
        border_color = (255, 255, 255)

    if not is_p2:
        pg.draw.rect(screen, gauge_color, (x, gauge_y, gauge_w, gauge_h))
    else:
        pg.draw.rect(screen, gauge_color, (x + (bar_w - gauge_w), gauge_y, gauge_w, gauge_h))
    pg.draw.rect(screen, border_color, (x, gauge_y, bar_w, gauge_h), 1)

    if fighter.combo_count >= 2 and fighter.combo_timer > 0:
        combo_color = (255, 60, 60) if fighter.combo_count >= 5 else (255, 230, 50)
        combo_text = font_combo.render(f"{fighter.combo_count} COMBO!!", True, combo_color)
        if not is_p2:
            screen.blit(combo_text, (x, gauge_y + gauge_h + 4))
        else:
            c_rect = combo_text.get_rect()
            c_rect.topright = (x + bar_w, gauge_y + gauge_h + 4)
            screen.blit(combo_text, c_rect)


def draw_center_text(screen: pg.Surface, text: str, font: pg.font.Font, y: int, color=(255, 255, 255)) -> None:
    """
    画面中央にテキストを描画する

    引数 screen : 描画先の画面サーフェス
    引数 text : 描画する文字列
    引数 font : 使用するフォント
    引数 y : 描画するY座標
    引数 color (tuple[int, int, int]): 文字の色 (R, G, B)
    """
    txt = font.render(text, True, color)
    rect = txt.get_rect(center=(WIDTH // 2, y))
    shadow = font.render(text, True, (0, 0, 0))
    screen.blit(shadow, (rect.x + 2, rect.y + 2))
    screen.blit(txt, rect)


def judge_winner(p1: Fighter, p2: Fighter) -> str:
    """
    HPを比較して勝者（あるいは引き分け）の文字列を決定する

    引数 p1 (Fighter): プレイヤー1
    引数 p2 (Fighter): プレイヤー2

    戻り値 str: 勝敗結果のテキスト
    """
    if p1.hp > p2.hp:
        return f"{p1.name} WIN!"
    if p2.hp > p1.hp:
        return f"{p2.name} WIN!"
    return "DRAW"


def create_fighters(mode: str | None) -> tuple[Fighter, Fighter]:
    """
    2人のキャラを初期状態で生成する
    引数 mode: Noneなら2Pプレイ,
               str(weak,normal,strong)ならCPU対戦
    """
    p1 = Fighter("P1", 250, 1, P1_KEYS, "fig/bb/stand.png", (60, 120, 255))
    if mode is None:
        p2 = Fighter("P2", 750, -1, P2_KEYS, "fig/bb/stand.png", (255, 80, 80))
    else:
        p2 = CPUFighter(f'CPU {mode.upper()}', 750, -1, P2_KEYS,
                        "fig/bb/stand.png", (255, 80, 80), mode)
    return p1, p2


def load_random_bg() -> pg.Surface | None:
    """
    背景画像からランダムに1つ選んで読み込む

    戻り値：背景のSurface、存在しない場合はNone
    """

    import random

    bg_filenames = ["bg.png", "bg1.png", "bg2.png"]
    bgs = [f"fig/bb/{name}" for name in bg_filenames if os.path.exists(f"fig/bb/{name}")]

    if bgs:
        chosen_bg = random.choice(bgs)
        # 画面サイズ（WIDTH, HEIGHT）に合わせて自動リサイズすると確実です
        img = pg.image.load(chosen_bg).convert()
        return pg.transform.scale(img, (WIDTH, HEIGHT))
    return None


class MoveTuple(NamedTuple):
    """
    移動や攻撃などの一括管理用NamedTuple
    """
    left: bool = False  # 左移動
    right: bool = False  # 右移動
    jump: bool = False  # ジャンプ
    attack: str | None = None  # 攻撃
    defence: str | None = None  # 防御
    special: bool = False  # 必殺技


class DifficultyTuple(NamedTuple):
    """
    CPU難易度に関するNamedTuple
    """
    think_interval: int  # 思考速度のインターバル
    attack_rate: float  # 攻撃レート
    avoid_rate: float  # 回避レート
    think_jitter: int  # 思考のゆらぎ
    max_combo: int  # 最大コンボ数
    chase_rate: float  # 追撃レート
    whiff_back_avoid: float  # 空振り時回避レート


DIFFICULTY = {
    "weak": DifficultyTuple(think_interval=45,
                            attack_rate=0.3,
                            avoid_rate=0.15,
                            think_jitter=15,
                            max_combo=3,
                            chase_rate=0.3,
                            whiff_back_avoid=0.4),
    "normal": DifficultyTuple(think_interval=30,
                              attack_rate=0.5,
                              avoid_rate=0.3,
                              think_jitter=6,
                              max_combo=6,
                              chase_rate=0.5,
                              whiff_back_avoid=0.75),
    "strong": DifficultyTuple(think_interval=15,
                              attack_rate=0.75,
                              avoid_rate=0.75,
                              think_jitter=2,
                              max_combo=10,
                              chase_rate=0.8,
                              whiff_back_avoid=0.9),
}


class CPUFighter(Fighter):
    """
    CPUキャラクター生成とそれの操作頭脳のクラス
    """
    def __init__(self, name: str, x: int, facing: int,
                 keys: KeyConfig, img_path: str,
                 color: tuple[int, int, int],
                 cpu_difficulty: str) -> None:
        """
        CPUキャラクターを生成する
        引数 cpu_difficulty : cpuの強さ(weak, normal, strong)
        引数 name：表示名
        引数 x：初期位置のx座標（中心）
        引数 facing：向き（右:+1, 左:-1）
        引数 keys：操作キーの設定
        引数 img_path：右向き画像のパス
        引数 color：画像がないときの代わりの色
        継承 : Fighterクラス
        """
        super().__init__(name, x, facing, keys, img_path, color)
        self.cpu_difficulty = cpu_difficulty  # cpuの強さの変数
        self.difficulty_param = DIFFICULTY[cpu_difficulty]  # 難易度パラメーター
        self.think_timer = 0  # 次の思考までの残りフレーム数
        self.action = MoveTuple()  # 行動選択
        self.was_hit = False  # 直前に攻撃を受けたかどうかの判定
        self.chase_count = 0  # 追撃カウント
        self.attack_hit = False  # 攻撃判定瞬間記録用

    def select_action(self, enemy: Fighter, distance: int) -> str | None:
        """
        技選択用メソッド
        引数 enemy (Fighter): 敵キャラ
        引数 distance (int): 相手との距離
        戻り値 str | None: 技
        """
        punch_range = (FIGHTER_W//2 + PUNCH_W + FIGHTER_W//2
                       + ADJUSTING_CPU_ATTACK_POINT)  # 攻撃可能かどうかの判定を行うための計算(punch)
        kick_range = (FIGHTER_W//2 + KICK_W + FIGHTER_W//2
                      + ADJUSTING_CPU_ATTACK_POINT)  # 攻撃可能かどうかの判定を行うための計算(kick)
        upper_range = (UPPER_MOVE + (UPPER_W + FIGHTER_W)//2)  # 攻撃可能かどうかの判定を行うための計算(upper)
        air_range = (AIR_W + FIGHTER_W//2)  # 攻撃可能かどうかの判定を行うための計算(air)
        if not self.is_on_ground() and distance <= air_range:
            return "air"
        if not enemy.is_on_ground() and distance <= upper_range:
            return "upper"
        if distance <= punch_range:
            return "punch"
        if distance <= kick_range:
            return "kick"
        else:
            return None

    def select_defence(self, enemy: Fighter) -> str:
        """
        防御を選択する用メソッド
        引数 enemy: 相手キャラ
        戻り値 str
        """
        if not enemy.is_on_ground():
            return "up"
        else:
            if DEF_CHOICE_RATE >= random.random():
                return "up"
            else:
                return "md"

    def think_action(self, enemy: Fighter) -> MoveTuple:
        """
        距離や攻撃範囲を確認して攻撃、移動を判断する
        引数 enemy : 相手キャラ
        戻り値 : MoveTuple
        """
        distant_player = abs(enemy.rect.centerx - self.rect.centerx)  # 相手との距離計算
        decide_action = self.select_action(enemy, distant_player)
        decide_defence = self.select_defence(enemy)
        attack_random_rate = random.random()  # 攻撃頻度のランダム数
        avoid_random_rate = random.random()  # 回避のランダム数
        avoid_choice_select = random.random()  # 回避選択のランダム数
        chase_random = random.random()  # 追撃ランダム数
        whiff_random = random.random()  # 後退回避ランダム数
        if enemy.hitstun > 0:
            if self.chase_count < self.difficulty_param.max_combo:
                if (decide_action is not None and
                        chase_random < self.difficulty_param.chase_rate):
                    self.chase_count += 1
                    return MoveTuple(attack=decide_action)
                else:
                    if self.facing == +1:
                        return MoveTuple(right=True)
                    else:
                        return MoveTuple(left=True)
            elif self.chase_count == self.difficulty_param.max_combo:
                if self.facing == +1:
                    return MoveTuple(left=True)
                else:
                    return MoveTuple(right=True)
        else:
            self.chase_count = 0
            if self.cooldown > 0 and whiff_random < self.difficulty_param.whiff_back_avoid:
                if self.facing == +1:
                    return MoveTuple(left=True)
                else:
                    return MoveTuple(right=True)
        if enemy.cooldown == 0:
            if decide_action is not None:
                if avoid_random_rate <= self.difficulty_param.avoid_rate:
                    if (self.rect.left <= AVOID_BACK_WALL_CHECK or
                            self.rect.right >= WIDTH - AVOID_BACK_WALL_CHECK):
                        if avoid_choice_select < AVOID_CHOICE_STANDARD_RATE * 2:
                            return MoveTuple(jump=True)
                        else:
                            return MoveTuple(defence=decide_defence)
                    else:
                        if avoid_choice_select < AVOID_CHOICE_STANDARD_RATE:
                            return MoveTuple(jump=True)
                        elif (AVOID_CHOICE_STANDARD_RATE <=
                              avoid_choice_select <
                              AVOID_CHOICE_STANDARD_RATE * 2):
                            if self.facing == +1:
                                return MoveTuple(left=True)
                            else:
                                return MoveTuple(right=True)
                        else:
                            return MoveTuple(defence=decide_defence)

        if decide_action is not None:
            if attack_random_rate <= self.difficulty_param.attack_rate:
                return MoveTuple(attack=decide_action)
            else:
                return MoveTuple()
        elif self.facing == +1:
            return MoveTuple(right=True)
        else:
            return MoveTuple(left=True)

    def action_cpu(self, enemy: Fighter) -> None:
        """
        cpuの行動を実行するメソッド
        引数 enemy: 相手キャラ
        戻り値: None
        """
        interval = self.difficulty_param.think_interval
        jitter = self.difficulty_param.think_jitter
        if self.hitstun > 0:
            self.was_hit = True
            return
        if not self.attack_hit and self.has_hit:
            self.think_timer = 0
        self.attack_hit = self.has_hit
        if self.was_hit:
            self.think_timer = 0
            self.was_hit = False
        if self.think_timer <= 0:
            self.action = self.think_action(enemy)
            self.think_timer = (max(0, interval +
                                    random.randint(-jitter, jitter)))
        else:
            self.think_timer -= 1
        self.is_moving = False
        if self.action.left:
            self.rect.x -= WALK_SPEED
            self.is_moving = True
        elif self.action.right:
            self.rect.x += WALK_SPEED
            self.is_moving = True
        if self.action.jump and self.is_on_ground():
            self.vy = -JUMP_POWER
        if (self.action.attack is not None and
                (self.cooldown == 0 or self.can_cancel)):
            if self.action.attack == "punch":
                self.start_attack(atk_type="punch",
                                  frames=PUNCH_FRAMES,
                                  cooldown=PUNCH_COOLDOWN,
                                  damage=PUNCH_DAMAGE)
            if self.action.attack == "kick":
                self.start_attack(atk_type="kick",
                                  frames=KICK_FRAMES,
                                  cooldown=KICK_COOLDOWN,
                                  damage=KICK_DAMAGE)
            if self.action.attack == "upper":
                self.start_attack(atk_type="upper",
                                  frames=UPPER_FRAMES,
                                  cooldown=UPPER_COOLDOWN,
                                  damage=UPPER_DAMAGE)
            if self.action.attack == "air":
                self.start_attack(atk_type="air",
                                  frames=AIR_FRAMES,
                                  cooldown=AIR_COOLDOWN,
                                  damage=AIR_DAMAGE)
            self.action = self.action._replace(attack=None)


def title_select(screen: pg.Surface,
                 font_s: pg.font.Font,
                 font_l: pg.font.Font,
                 clock: pg.time.Clock) -> str:
    """
    プレイヤー開始時のタイトル表示とモード選択用
    引数 screen : 表示用
    引数 font_s/l : タイトル、モード選択フォント用
    引数 clock : タイマー用
    戻り値 : str(2p/cpu/controls)
    """
    bg_img = pg.image.load("fig/bg.png").convert() if os.path.exists("fig/bg.png") else None
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                pg.quit()
                sys.exit()
            if event.type == pg.KEYDOWN:
                if event.key in TITLE_KEY:
                    return TITLE_KEY[event.key]
        if bg_img is not None:
            screen.blit(bg_img, (0, 0))
        else:
            screen.fill((30, 30, 50))
            pg.draw.rect(screen, (90, 70, 50), (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
        draw_center_text(screen=screen, text=GAME_TITLE, font=font_l, y=HEIGHT // 4)
        for i, text in enumerate(TITLE.values()):
            draw_center_text(screen=screen, text=text, font=font_s,
                             y=MENU_TOP_Y + i * MENU_LINE_GAP)
        pg.display.update()
        clock.tick(FPS)


def cpu_mode_select(screen: pg.Surface,
                    font_s: pg.font.Font,
                    font_l: pg.font.Font,
                    clock: pg.time.Clock) -> str | None:
    """
    CPUの難易度選択用画面
    引数 screen : 表示用
    引数 font_s/l : タイトル、モード選択フォント用
    引数 clock : タイマー用
    戻り値 : str(weak,normal,strong), Escで戻ったらNone
    """
    bg_img = pg.image.load("fig/bg.png").convert() if os.path.exists("fig/bg.png") else None
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                return None
            if event.type == pg.KEYDOWN:
                if event.key in CPU_SELECT_KEY:
                    return CPU_SELECT_KEY[event.key]
        if bg_img is not None:
            screen.blit(bg_img, (0, 0))
        else:
            screen.fill((30, 30, 50))
            pg.draw.rect(screen, (90, 70, 50), (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
        draw_center_text(screen=screen, text=CPU_MODE_TITLE, font=font_l, y=HEIGHT // 4)
        for i, text in enumerate(CPU_MODE_SELECT.values()):
            draw_center_text(screen=screen, text=text, font=font_s,
                             y=MENU_TOP_Y + i * MENU_LINE_GAP)
        draw_center_text(screen=screen, text=BACK_SELECT, font=font_s,
                         y=MENU_TOP_Y + 3 * MENU_LINE_GAP)
        pg.display.update()
        clock.tick(FPS)


def controls(screen: pg.Surface,
             font_s: pg.font.Font,
             font_l: pg.font.Font,
             clock: pg.time.Clock) -> None:
    """
    操作説明の画面
    引数 screen : 表示用
    引数 font_s/l : フォント用
    引数 clock : タイマー用
    戻り値 : Escで戻ったらNone
    """
    bg_img = pg.image.load("fig/bg.png").convert() if os.path.exists("fig/bg.png") else None
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                return None
        if bg_img is not None:
            screen.blit(bg_img, (0, 0))
        else:
            screen.fill((30, 30, 50))
            pg.draw.rect(screen, (90, 70, 50), (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
        draw_center_text(screen=screen, text=CONTROLS_TITLE, font=font_l, y=HEIGHT // 4)
        player_1 = font_s.render("1P", True, (255, 255, 255))
        player_2 = font_s.render("2P", True, (255, 255, 255))
        screen.blit(player_1, player_1.get_rect(center=(WIDTH // 4, TEXT_TOP - TEXT_SPACE)))
        screen.blit(player_2, player_2.get_rect(center=(WIDTH * 3 // 4, TEXT_TOP - TEXT_SPACE)))
        draw_center_text(screen=screen, text=BACK_SELECT,
                         font=font_s, y=TEXT_TOP + len(CONTROLS_1P) * TEXT_SPACE)
        for i, text_1p in enumerate(CONTROLS_1P.values()):
            y = TEXT_TOP + i * TEXT_SPACE
            txt_1p = font_s.render(text_1p, True, (255, 255, 255))
            screen.blit(txt_1p, txt_1p.get_rect(center=(WIDTH // 4, y)))
        for i, text_2p in enumerate(CONTROLS_2P.values()):
            y = TEXT_TOP + i * TEXT_SPACE
            txt_2p = font_s.render(text_2p, True, (255, 255, 255))
            screen.blit(txt_2p, txt_2p.get_rect(center=(WIDTH * 3 // 4, y)))
        pg.display.update()
        clock.tick(FPS)


def menu_flow(screen: pg.Surface,
              font_s: pg.font.Font,
              font_l: pg.font.Font,
              clock: pg.time.Clock) -> str | None:
    """
    タイトルから難易度選択までの画面の流れの管理
    引数 screen : 表示用
    引数 font_s/l : タイトル、モード選択フォント用
    引数 clock : タイマー用
    戻り値 : str(weak,normal,strong), None(2p対戦用),
            タイトルEscでゲーム終了,
            難易度選択でescでタイトルに戻る
    """
    while True:
        title = title_select(screen, font_s, font_l, clock)
        if title == "2p":
            return None
        elif title == "cpu":
            mode_select = cpu_mode_select(screen, font_s, font_l, clock)
            if mode_select is not None:
                return mode_select
        elif title == "controls":
            controls(screen, font_s, font_l, clock)


def main() -> None:
    """ゲームのメインループを管理する関数"""
    pg.init()
    pg.display.set_caption("2D格闘ゲーム（完全版）")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    clock = pg.time.Clock()

    font_s = pg.font.Font(None, 24)
    font_m = pg.font.Font(None, 32)
    font_l = pg.font.Font(None, 72)
    font_combo = pg.font.Font(None, 26)

    super_attacks = pg.sprite.Group()
    menu = menu_flow(screen, font_s, font_l, clock)
    p1, p2 = create_fighters(menu)
    bg_img = load_random_bg()

    tmr = 0
    result = ""
    hit_stop_frames = 0
    KO_delay = 0

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                pg.quit()
                sys.exit()
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_r and result:
                p1, p2 = create_fighters(menu)
                super_attacks.empty()
                bg_img = load_random_bg()
                tmr = 0
                result = ""
                hit_stop_frames = 0
                KO_delay = 0

        if not result:
            if hit_stop_frames > 0:
                hit_stop_frames -= 1
            else:
                key_lst = pg.key.get_pressed()

                if not p1.is_defeated and not p2.is_defeated:
                    p1.handle_input(key_lst)
                    if isinstance(p2, CPUFighter):
                        p2.action_cpu(p1)
                    else:
                        p2.handle_input(key_lst)

                    if key_lst[p1.keys.special] and p1.super_gauge >= SUPER_GAGE_REQUIRE and p1.special_pose_timer == 0:
                        super_attacks.add(SuperAttack(p1))
                        p1.super_gauge = 0
                        p1.special_pose_timer = 30

                    if key_lst[p2.keys.special] and p2.super_gauge >= SUPER_GAGE_REQUIRE and p2.special_pose_timer == 0 and not isinstance(p2, CPUFighter):
                        super_attacks.add(SuperAttack(p2))
                        p2.super_gauge = 0
                        p2.special_pose_timer = 30

                p1.update()
                p2.update()
                super_attacks.update()

                if not p1.is_defeated and not p2.is_defeated:
                    push_apart(p1, p2)
                    p1.face_to(p2)
                    p2.face_to(p1)

                    stop_p1 = check_hit(p1, p2)
                    stop_p2 = check_hit(p2, p1)
                    if stop_p1 > 0:
                        hit_stop_frames = stop_p1
                    elif stop_p2 > 0:
                        hit_stop_frames = stop_p2

                for super_attack in list(super_attacks):
                    defender = p2 if super_attack.owner is p1 else p1
                    if defender.is_defeated:
                        continue
                    if super_attack.rect.colliderect(defender.rect):
                        defender.take_damage(super_attack.damage, super_attack.owner.facing)
                        super_attack.kill()
                        hit_stop_frames = 10

                if (p1.hp <= 0 or p2.hp <= 0) and not p1.is_defeated and not p2.is_defeated:
                    if p1.hp <= 0:
                        p1.trigger_defeat(p2.rect.centerx)
                    if p2.hp <= 0:
                        p2.trigger_defeat(p1.rect.centerx)

                if p1.is_defeated or p2.is_defeated:
                    KO_delay += 1
                    if KO_delay > 90:
                        result = judge_winner(p1, p2)

                tmr += 1
                remain = max(0, ROUND_TIME - tmr // FPS)
                if remain <= 0 and not p1.is_defeated and not p2.is_defeated:
                    result = judge_winner(p1, p2)

        # 画面描画の実行
        if bg_img is not None:
            screen.blit(bg_img, (0, 0))
        else:
            screen.fill((30, 30, 50))
            pg.draw.rect(screen, (90, 70, 50), (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))

        p1.draw(screen)
        p2.draw(screen)
        super_attacks.draw(screen)

        draw_hp_bar(screen, p1, 50, font_s, font_combo, is_p2=False, tmr=tmr)
        draw_hp_bar(screen, p2, WIDTH - 430, font_s, font_combo, is_p2=True, tmr=tmr)

        remain = max(0, ROUND_TIME - tmr // FPS)
        timer_bg_rect = pg.Rect(WIDTH // 2 - 35, 15, 70, 45)
        pg.draw.rect(screen, (20, 20, 20), timer_bg_rect, border_radius=8)
        pg.draw.rect(screen, (200, 200, 200), timer_bg_rect, 2, border_radius=8)
        draw_center_text(screen, str(remain), font_m, 37)

        if result:
            overlay = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            screen.blit(overlay, (0, 0))

            draw_center_text(screen, result, font_l, HEIGHT // 2 - 40, color=(255, 220, 0))
            draw_center_text(screen, "R: Restart  /  Esc: Quit", font_s, HEIGHT // 2 + 40)

        pg.display.update()
        clock.tick(FPS)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()