import os
import sys
from dataclasses import dataclass

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

# --- 各種技の性能設定 ---
# パンチ（Cキー / カンマキー：小技、ヒットキャンセル可能）
PUNCH_W, PUNCH_H = 60, 30
PUNCH_DAMAGE = 5
PUNCH_FRAMES, PUNCH_COOLDOWN = 8, 14

# キック（Vキー / Mキー：コンボ締め用の重い技、キャンセル不可）
KICK_W, KICK_H = 90, 40
KICK_DAMAGE = 12
KICK_FRAMES, KICK_COOLDOWN = 14, 28

# アッパーカット（Fキー / Kキー：単体対空技）
UPPER_W, UPPER_H = 50, 90
UPPER_DAMAGE = 15
UPPER_FRAMES, UPPER_COOLDOWN = 16, 30

# ジャンプ攻撃（空中攻撃）
AIR_W, AIR_H = 70, 60
AIR_DAMAGE = 8
AIR_FRAMES, AIR_COOLDOWN = 12, 18

HITSTUN_FRAMES = 12  # のけぞり時間（通常連打では繋がらない長さ）
KNOCKBACK = 20  # ノックバック距離（大きく飛ばして目押しなしの連打ハメを防止）
MAX_COMBO_LIMIT = 10  # 最大コンボ上限（10ヒットで相手は強制復帰・ダウン立ち上がり）

# 必殺技の設定
MAX_SUPER_GAGE = 100
SUPER_GAGE_UP = 1
SUPER_GAGE_REQUIRE = 15
SUPER_DAMAGE = 20
SUPER_SPEED = 25
COMBO_RESET_FRAMES = 90

# 必殺技の設定(必殺技)
MAX_SUPER_GAGE = 100  # 最大ゲージ
SUPER_GAGE_UP = 1  # 通常攻撃が当たったときの増加量
SUPER_GAGE_REQUIRE = 15  # 必殺技発動に必要なゲージ量
SUPER_GAGE_ATTACK_DAMAGE = 20  # 必殺技のダメージ
SUPER_GAGE_ATTACK_FRAMES = 100  # 必殺技が出ている時間（フレーム）
SUPER_SPEED = 30  # 必殺技の移動速度(ピクセル数/フレーム)
DAMAGE_GAUGE_UP = 5  # ダメージを受けたときのゲージ増加量
COMBO_DAMAGE_RATE = 0.1  # コンボごとのダメージ減少率
MIN_DAMAGE_RATE = 0.5  # 基本ダメージの50％を下限にする
MAX_COMBO_COUNT = 10  # 最大コンボ数
COMBO_RESET_FRAMES = 90  # 最後のヒットからコンボ表示が消えるまでの時間
COMBO_LINK_FRAMES = 35  # 前のヒットからこのフレーム以内に当てるとコンボ継続

BGM_DIR = "BGM"  # BGMを置くフォルダ
SE_DIR = "SE"  # 効果音を置くフォルダ
BGM_VOLUME = 0.3  # BGMの音量（0.0〜1.0）
SE_VOLUME = 0.7  # 効果音の音量（0.0〜1.0）
ATTACK_SE = {
    "punch": "punch",#パンチ
    "kick": "kick",#キック
    "upper": "upper",#アッパー    
    "air": "air",#空中攻撃
    "super": "super",# 必殺技
     "guard": "guard",# ガード 
}
GUARD_SE = "guard"  # ガードされたときに鳴らす効果音の名前

P1_SE_KEYS = {
    pg.K_c: "punch",  # パンチ
    pg.K_v: "kick",  # キック
    pg.K_f: "upper",  # アッパーカット
    pg.K_w: "air",  # ジャンプ攻撃
    pg.K_r: "guard",  # ガード
    pg.K_t: "guard",  # ガード
    pg.K_z: "super",  # 必殺技
}

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

class BGMManager:
    """
    ゲーム内のBGM再生・停止・音量変更を管理するクラス（追加機能）
    """
    def __init__(self, bgm_path: str, volume: float = 0.5) -> None:
        pg.mixer.init()  # ミキサーの初期化
        self.bgm_path = bgm_path
        self.volume = volume
        self.is_playing = False

    def play(self, loops: int = -1) -> None:
        if os.path.exists(self.bgm_path):
            pg.mixer.music.load(self.bgm_path)  # 音源ファイルの読み込み
            pg.mixer.music.set_volume(self.volume)
            pg.mixer.music.play(loops=loops)  # BGM再生
            self.is_playing = True

    def stop(self) -> None:
        if self.is_playing:
            pg.mixer.music.stop()  # BGM停止
            self.is_playing = False

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

class SEManager:
    """
    効果音（SE）の読み込みと再生を管理するクラス（追加機能）
    """

    def __init__(self, se_files: dict[str, str], volume: float = SE_VOLUME) -> None:
        """
        効果音をまとめて読み込む
        引数 se_files：{効果音の名前: ファイル名}の辞書
        引数 volume：音量（0.0〜1.0）
        """
        pg.mixer.init()
        self.sounds: dict[str, pg.mixer.Sound] = {}
        for name, file_name in se_files.items():
            path = os.path.join(SE_DIR, file_name)
            if os.path.exists(path):  # ファイルがなくてもゲームが落ちないようにする
                snd = pg.mixer.Sound(path)
                snd.set_volume(volume)
                self.sounds[name] = snd

    def play(self, name: str) -> None:
        """
        名前を指定して効果音を1回鳴らす
        引数 name：効果音の名前
        """
        snd = self.sounds.get(name)
        if snd is not None:
            snd.play()
    def stop_all(self) -> None:
        """
        鳴っている効果音をすべて止める（BGMは止まらない）
        """
        pg.mixer.stop()


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


class SuperAttack(pg.sprite.Sprite):
    """
    必殺技に関するクラス
    """
    def __init__(self, fighter: "Fighter") -> None:
        """
        必殺技を生成する
        引数 fighter:必殺技を出すキャラ
        """
        super().__init__()

        self.image = pg.Surface((60, 30), pg.SRCALPHA)  # 幅60、高さ30の画像を作る。
        self.image.fill((255, 0, 0, 128))  # 半透明の赤色で塗りつぶす

        self.rect = self.image.get_rect()  # 画像と同じ大きさの当たり判定を作る。
        self.rect.centery = fighter.rect.centery  # キャラクターの中心の高さに合わせる。

        # キャラクターの向きに合わせて出現位置を決める。
        if fighter.facing == 1:  # 右を向いている時
            self.rect.left = fighter.rect.right  # キャラクターの右端に合わせる。
        else:
            self.rect.right = fighter.rect.left  # 左を向いているときはキャラクターの左端に合わせる。

        self.speed = SUPER_SPEED * fighter.facing  # キャラクターの向きに合わせて移動速度を決める。
        self.damage = SUPER_GAGE_ATTACK_DAMAGE  # 必殺技のダメージ量を設定する。
        self.owner = fighter  # 必殺技を出したキャラクターを記録する。(必殺技が誰のものか判定するため)

    def update(self) -> None:
        """必殺技を移動させ、画面外に出たら削除する。"""
        self.rect.x += self.speed  # 必殺技を移動させる
        if self.rect.right < 0 or self.rect.left > WIDTH:  # 画面外に出たら消す
            self.kill()  # 必殺技を消す


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
        self.super_gauge = 0  # 必殺技ゲージ
        self.combo_timer = 0  # コンボが途切れるまでの時間
        self.combo_count = 0  # 連続で攻撃を当てた回数

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
        ダメージを受けてのけぞる。
        引数 damage：受けるダメージ量
        引数 from_dir：押し戻される向き（右:+1, 左:-1
        引数 from_dir (int): 攻撃された方向（吹き飛ぶ向きの基準）
        """
        # ダメージを受けたら、自分が続けていたコンボをリセットする
        self.combo_count = 0
        self.combo_timer = 0
        if self.is_defeated:
            return
        self.hp = max(0, self.hp - damage)
        self.hitstun = HITSTUN_FRAMES
        self.attack_timer = 0
        self.special_pose_timer = 0
        self.rect.x += KNOCKBACK * from_dir
        self.rect.clamp_ip(pg.Rect(0, 0, WIDTH, HEIGHT))

        # ダメージを受けたら必殺技ゲージを増やす
        self.super_gauge = min(
            MAX_SUPER_GAGE,
            self.super_gauge + DAMAGE_GAUGE_UP
        )

    def trigger_defeat(self, attacker_centerx: int) -> None:
        """
        重力・タイマー・画面端・のけぞり・K.O.演出などの処理を行う
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

        # 最後のヒットから90フレーム経過したらコンボをリセットする
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


def apply_hit(
        attacker: Fighter,
        defender: Fighter,
        base_damage: int,
        hitstun_frames: int = HITSTUN_FRAMES,
) -> None:
    """攻撃命中時のコンボ数とダメージを共通処理する。"""

    frames_since_hit = COMBO_RESET_FRAMES - attacker.combo_timer
    if attacker.combo_timer > 0 and frames_since_hit <= COMBO_LINK_FRAMES:
        # 前回のヒットから35フレーム以内に当たったらコンボ継続
        attacker.combo_count = min(MAX_COMBO_COUNT, attacker.combo_count + 1)
    else:
        # 前回のヒットから35フレームを超えたら新しいコンボにする
        attacker.combo_count = 1

    attacker.combo_timer = COMBO_RESET_FRAMES

    damage_rate = max(
        MIN_DAMAGE_RATE,
        1 - (attacker.combo_count - 1) * COMBO_DAMAGE_RATE
    )
    damage = max(1, int(base_damage * damage_rate))
    defender.take_damage(damage, attacker.facing)

    # take_damage 側で付与されていなくても、ここで必ずのけぞらせる
    defender.hitstun = max(defender.hitstun, hitstun_frames)


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
        apply_hit(attacker, defender, attacker.current_damage)
        attacker.has_hit = True
        attacker.super_gauge = min(MAX_SUPER_GAGE, attacker.super_gauge + SUPER_GAGE_UP)

        if attacker.combo_count < 5:
            gauge_up = SUPER_GAGE_UP
        elif attacker.combo_count < MAX_COMBO_COUNT:
            gauge_up = SUPER_GAGE_UP * 2
        else:
            gauge_up = SUPER_GAGE_UP * 3

        # 攻撃が当たったら必殺技ゲージを増やす
        attacker.super_gauge = min(
            MAX_SUPER_GAGE,
            attacker.super_gauge + gauge_up
        )
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
    
    引数　screen (pg.Surface): 描画先
    引数　fighter : 対象のキャラクター
    引数　x : 描画開始のX座標
    引数　font : テキスト用フォント
    引数　font_combo : コンボ表示用
    引数　is_p2 (: プレイヤー2側のバー
    引数　tmr : ゲーム内経過フレーム数
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


def create_fighters() -> tuple[Fighter, Fighter]:
    """2人のプレイヤーインスタンスを生成して初期位置で返す"""
    p1 = Fighter("P1", 250, 1, P1_KEYS, "fig/bb/stand.png", (60, 120, 255))
    p2 = Fighter("P2", 750, -1, P2_KEYS, "fig/bb/stand.png", (255, 80, 80))
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


    # BGMマネージャーの生成と再生
    bgm = BGMManager(os.path.join(BGM_DIR, "BGM1.wav"), volume=BGM_VOLUME)
    bgm.play()

    se = SEManager({
        "punch": "punch.mp3",
        "kick": "kick.mp3",
        "upper": "upper.mp3",
        "air": "air.mp3",
        "super": "super.mp3",
        "guard": "guard.mp3",
    })
    
    p1, p2 = create_fighters()
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
                p1, p2 = create_fighters()  
                super_attacks.empty()
                bg_img = load_random_bg() 
                tmr = 0
                result = ""
                bgm.play()  # BGMを再開する
                hit_stop_frames = 0
                KO_delay = 0
                continue  # Rはガードキーでもあるので、この回はSEを鳴らさない

        if not result:  
            if hit_stop_frames > 0:
                hit_stop_frames -= 1
            else:
                key_lst = pg.key.get_pressed()
                
                if not p1.is_defeated and not p2.is_defeated:
                    p1.handle_input(key_lst)
                    p2.handle_input(key_lst)

                    if key_lst[p1.keys.special] and p1.super_gauge >= SUPER_GAGE_REQUIRE and p1.special_pose_timer == 0:
                        super_attacks.add(SuperAttack(p1))
                        p1.super_gauge = 0
                        p1.special_pose_timer = 30

                    if key_lst[p2.keys.special] and p2.super_gauge >= SUPER_GAGE_REQUIRE and p2.special_pose_timer == 0:
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
                        bgm.stop()  # 決着したらBGMを止める
                        se.stop_all()  # 鳴っている効果音も止める

                tmr += 1
                remain = max(0, ROUND_TIME - tmr // FPS)
                if remain <= 0 and not p1.is_defeated and not p2.is_defeated:
                    result = judge_winner(p1, p2)
                    bgm.stop()  # 決着したらBGMを止める
                    se.stop_all()  # 鳴っている効果音も止める

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
