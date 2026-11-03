import os
import random
import sys
from dataclasses import dataclass

import pygame as pg

os.chdir(os.path.dirname(os.path.abspath(__file__)))


# ===== 定数 =====
WIDTH = 1000  # 画面の幅
HEIGHT = 600  # 画面の高さ
FPS = 60  # 1秒あたりのフレーム数
GROUND_Y = 520  # 地面のy座標（キャラの足元）
GRAVITY = 1  # 1フレームごとに加算される落下速度
ROUND_TIME = 60  # 1ラウンドの制限時間（秒）

FIGHTER_W = 120  # キャラの表示幅
FIGHTER_H = 120  # キャラの表示高さ
MAX_HP = 100  # 最大体力
WALK_SPEED = 5  # 歩く速さ
JUMP_POWER = 20  # ジャンプの初速

ATTACK_W = 70  # 攻撃判定の幅
ATTACK_H = 40  # 攻撃判定の高さ
ATTACK_DAMAGE = 8  # 攻撃1回のダメージ
ATTACK_FRAMES = 15  # 攻撃が出ている時間（フレーム）
ATTACK_COOLDOWN = 25  # 次に攻撃できるまでの時間（フレーム）
HITSTUN_FRAMES = 12  # 攻撃を受けて動けない時間（フレーム）
KNOCKBACK = 12  # 攻撃を受けたときに押し戻される距離

# アニメーション速度（フレーム毎）
ANIM_SPEED_WALK = 10
ANIM_SPEED_ATTACK = 10

CELL_W = 120 # セルの横幅
CELL_H = 120 # セルの縦幅
CELL_MARGIN = 2  # セル間の枠線の幅

STAND_CELL = (0, 0) #棒立ち
WALK_CELLS = [(1, i) for i in range(8)]   # 歩き
ATTACK_CELL = (3, 3) # 攻撃
HITSTUN_CELL = (4, 2) #のけぞり

@dataclass
class KeyConfig:
    """
    プレイヤーごとのキー割り当て
    """
    left: int
    right: int
    jump: int
    attack: int

P1_KEYS = KeyConfig(left=pg.K_a, right=pg.K_d, jump=pg.K_w, attack=pg.K_f)
P2_KEYS = KeyConfig(left=pg.K_LEFT, right=pg.K_RIGHT, jump=pg.K_UP, attack=pg.K_l)


class Fighter(pg.sprite.Sprite):
    """
    格闘キャラクターの初期化を行う
    引数 name：キャラクター名
    引数 x：初期x座標
    引数 facing：向き（右:1, 左:-1）
    引数 keys：操作キー設定
    引数 img_path：画像ファイルのパス
    引数 color：画像がない場合の代替カラー
    """

    def __init__(self, name: str, x: int, facing: int, keys: KeyConfig,
                 img_path: str, color: tuple[int, int, int]) -> None:
        """
        スプライトシートから画像を読み込み、切り抜く
        引数 path：画像ファイルのパス
        引数 color：フォールバック用の色
        """
        super().__init__()
        self.name = name
        self.keys = keys
        self.facing = facing
        
        self.load_animations(img_path, color)
        
        self.anim_timer = 0
        self.anim_index = 0
        
        self.image = self.stand_img_right if facing == 1 else self.stand_img_left
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = GROUND_Y
        self.vy = 0  
        self.hp = MAX_HP
        self.attack_timer = 0  
        self.cooldown = 0  
        self.hitstun = 0  
        self.has_hit = False  

    def load_animations(self, path: str, color: tuple[int, int, int]) -> None:
        """
        スプライトシートから画像を読み込み、切り抜く
        引数 path：画像のパス
        引数 color：透過用の色
        """
        if os.path.exists(path):
            sheet = pg.image.load(path).convert()
            sheet.set_colorkey((0, 0, 0), pg.RLEACCEL)
            width, height = sheet.get_size()
            for x in range(width):
                for y in range(height):
                    r, g, b, *_ = sheet.get_at((x, y))
                    if r < 30 and g < 30 and b < 30:
                        sheet.set_at((x, y), (0, 0, 0))
        else:
            sheet = pg.Surface((CELL_W * 12, CELL_H * 5))
            sheet.fill(color)

        def get_cell(row: int, col: int) -> pg.Surface:
            """
            指定されたセルをシートから切り出し、画面表示用のサイズ
            引数 row：シートの行番号
            引数 col：シートの列番号
            戻り値：切り抜いたキャラクター画像のSurface
            """
            sub = pg.Surface((CELL_W, CELL_H), pg.SRCALPHA)
            # 枠線を考慮して切り抜く
            src_x = col * (CELL_W + CELL_MARGIN) + CELL_MARGIN
            src_y = row * (CELL_H + CELL_MARGIN) + CELL_MARGIN
            sub.blit(sheet, (0, 0), (src_x, src_y, CELL_W, CELL_H))
            return pg.transform.scale(sub, (FIGHTER_W, FIGHTER_H))

        self.stand_img_right = get_cell(STAND_CELL[0], STAND_CELL[1])
        self.stand_img_left = pg.transform.flip(self.stand_img_right, True, False)

        self.walk_imgs_right = [get_cell(r, c) for r, c in WALK_CELLS]
        self.walk_imgs_left = [pg.transform.flip(img, True, False) for img in self.walk_imgs_right]

        self.attack_img_right = get_cell(ATTACK_CELL[0], ATTACK_CELL[1])
        self.attack_img_left = pg.transform.flip(self.attack_img_right, True, False)

        self.hit_img_right = get_cell(HITSTUN_CELL[0], HITSTUN_CELL[1])
        self.hit_img_left = pg.transform.flip(self.hit_img_right, True, False)

    def is_on_ground(self) -> bool:
        """
        キャラクターが地面上にいるかを判定する
        戻り値：いる場合はTrue、空中の場合はFalse
        """
        return self.rect.bottom >= GROUND_Y

    def handle_input(self, key_lst: pg.key.ScancodeWrapper) -> None:
        """
        キー入力をごとの動作を処理する
        引数 key_lst：押下されているキーの状態リスト
        """
        if self.hitstun > 0:
            return
            
        dx = 0
        is_moving = False
        if key_lst[self.keys.left]:
            dx -= WALK_SPEED
            is_moving = True
        if key_lst[self.keys.right]:
            dx += WALK_SPEED
            is_moving = True
            
        self.rect.x += dx
        
        if key_lst[self.keys.jump] and self.is_on_ground():
            self.vy = -JUMP_POWER
            
        if key_lst[self.keys.attack] and self.cooldown == 0:
            self.attack_timer = ATTACK_FRAMES
            self.cooldown = ATTACK_COOLDOWN
            self.has_hit = False

        old_bottom = self.rect.bottom

        # 状態ごとに画像を設定する分岐
        if self.hitstun > 0:
            if self.facing == 1:
               self.image = self.hit_img_right 
            else:
                self.image = self.hit_img_left 
            
        elif not self.is_on_ground():
            if self.facing == 1:
                self.image = self.stand_img_right
            else:
                self.image = self.stand_img_left
            
        elif self.attack_timer > 0:
            if self.facing == 1:
                self.image = self.attack_img_right 
            else:
                self.image = self.attack_img_left

        elif is_moving:
            self.anim_timer += 1
            if self.anim_timer >= ANIM_SPEED_WALK:
                self.anim_timer = 0
                self.anim_index = (self.anim_index + 1) % len(self.walk_imgs_right)
            imgs = self.walk_imgs_right if self.facing == 1 else self.walk_imgs_left
            self.image = imgs[self.anim_index]
            
        else:
            self.image = self.stand_img_right if self.facing == 1 else self.stand_img_left
            self.anim_index = 0

        centerx = self.rect.centerx
        self.rect = self.image.get_rect()
        self.rect.centerx = centerx
        self.rect.bottom = old_bottom

    def face_to(self, other: "Fighter") -> None:
        """
        相手のいる方向を向く
        引数 other：相手キャラ
        """
        if self.attack_timer > 0:
            return
        self.facing = 1 if other.rect.centerx >= self.rect.centerx else -1

    def get_attack_rect(self) -> pg.Rect | None:
        """
        攻撃判定の矩形を返す（攻撃中でなければNone）
        """
        if self.attack_timer <= 0:
            return None
        atk = pg.Rect(0, 0, ATTACK_W, ATTACK_H)
        atk.centery = self.rect.top + FIGHTER_H // 3
        if self.facing == 1:
            atk.left = self.rect.right
        else:
            atk.right = self.rect.left
        return atk

    def take_damage(self, damage: int, from_dir: int) -> None:
        """
        ダメージを受けてのけぞる
        引数 damage：受けるダメージ量
        引数 from_dir：押し戻される向き（右:+1, 左:-1）
        """
        self.hp = max(0, self.hp - damage)
        self.hitstun = HITSTUN_FRAMES
        self.attack_timer = 0
        self.rect.x += KNOCKBACK * from_dir
        self.rect.clamp_ip(pg.Rect(0, 0, WIDTH, HEIGHT))
        self.image = self.hit_img_right if self.facing == 1 else self.hit_img_left

    def update(self) -> None:
        """
        重力・タイマー・画面端の処理を行う
        """
        self.vy += GRAVITY
        self.rect.y += self.vy
        if self.rect.bottom >= GROUND_Y:
            self.rect.bottom = GROUND_Y
            self.vy = 0
        self.rect.clamp_ip(pg.Rect(0, 0, WIDTH, HEIGHT))
        self.attack_timer = max(0, self.attack_timer - 1)
        self.cooldown = max(0, self.cooldown - 1)
        self.hitstun = max(0, self.hitstun - 1)

    def draw(self, screen: pg.Surface) -> None:
        """
        キャラと攻撃判定を描画する
        引数 screen：画面Surface
        """
        screen.blit(self.image, self.rect)
        atk = self.get_attack_rect()
        if atk is not None:
            pg.draw.rect(screen, (255, 220, 0), atk, 3)


def check_hit(attacker: Fighter, defender: Fighter) -> None:
    """
    攻撃側の攻撃が防御側に当たったか判定し、当たればダメージを与える
    引数 attacker：攻撃側キャラ
    引数 defender：防御側キャラ
    """
    atk = attacker.get_attack_rect()
    if atk is None or attacker.has_hit:
        return
    if atk.colliderect(defender.rect):
        defender.take_damage(ATTACK_DAMAGE, attacker.facing)
        attacker.has_hit = True


def push_apart(f1: Fighter, f2: Fighter) -> None:
    """
    キャラ同士が重ならないように押し離す
    引数 f1, f2：キャラ
    """
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


def draw_hp_bar(screen: pg.Surface, fighter: Fighter, x: int, font: pg.font.Font) -> None:
    """
    体力ゲージと名前を描画する
    引数 screen：画面Surface
    引数 fighter：対象キャラ
    引数 x：ゲージ左端のx座標
    引数 font：名前表示用フォント
    """
    bar_w, bar_h = 400, 24
    pg.draw.rect(screen, (80, 0, 0), (x, 20, bar_w, bar_h))
    hp_w = bar_w * fighter.hp // MAX_HP
    pg.draw.rect(screen, (0, 200, 60), (x, 20, hp_w, bar_h))
    pg.draw.rect(screen, (255, 255, 255), (x, 20, bar_w, bar_h), 2)
    screen.blit(font.render(fighter.name, True, (255, 255, 255)), (x, 50))


def draw_center_text(screen: pg.Surface, text: str, font: pg.font.Font, y: int) -> None:
    """
    画面中央に文字を描画する
    引数 screen：画面Surface
    引数 text：表示する文字列
    引数 font：フォント
    引数 y：文字の中心のy座標
    """
    txt = font.render(text, True, (255, 255, 255))
    screen.blit(txt, txt.get_rect(center=(WIDTH // 2, y)))


def judge_winner(p1: Fighter, p2: Fighter) -> str:
    """
    勝者を判定して表示用の文字列を返す
    引数 p1, p2：キャラ
    戻り値：結果の文字列
    """
    if p1.hp > p2.hp:
        return f"{p1.name} WIN!"
    if p2.hp > p1.hp:
        return f"{p2.name} WIN!"
    return "DRAW"


def create_fighters() -> tuple[Fighter, Fighter]:
    """
    2人のキャラを初期状態で生成する
    """
    p1 = Fighter("P1", 250, 1, P1_KEYS, "fig/player.png", (60, 120, 255))
    p2 = Fighter("P2", 750, -1, P2_KEYS, "fig/player.png", (255, 80, 80))
    return p1, p2


def load_random_bg() -> pg.Surface | None:
    """
    背景画像からランダムに1つ選んで読み込む
    戻り値：背景のSurface、存在しない場合はNone
    """
    bg_filenames = ["bg.png", "bg1.png", "bg2.png"]
    available_bgs = [f"fig/{name}" for name in bg_filenames if os.path.exists(f"fig/{name}")]
    
    if available_bgs:
        chosen_bg = random.choice(available_bgs)
        return pg.image.load(chosen_bg).convert()
    return None


def main() -> None:
    pg.display.set_caption("2D格闘ゲーム（仮）")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    clock = pg.time.Clock()
    font_s = pg.font.Font(None, 36)
    font_l = pg.font.Font(None, 100)
    
    bg_img = load_random_bg()

    p1, p2 = create_fighters()
    tmr = 0  
    result = ""  

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_r and result:
                p1, p2 = create_fighters()  
                bg_img = load_random_bg()  
                tmr = 0
                result = ""

        if not result:  # 対戦中の処理
            key_lst = pg.key.get_pressed()
            p1.handle_input(key_lst)
            p2.handle_input(key_lst)
            p1.update()
            p2.update()
            push_apart(p1, p2)
            p1.face_to(p2)
            p2.face_to(p1)
            check_hit(p1, p2)
            check_hit(p2, p1)
            tmr += 1
            remain = ROUND_TIME - tmr // FPS
            if p1.hp <= 0 or p2.hp <= 0 or remain <= 0:
                result = judge_winner(p1, p2)

        # 描画
        if bg_img is not None:
            screen.blit(bg_img, (0, 0))
        else:
            screen.fill((30, 30, 50))
            pg.draw.rect(screen, (90, 70, 50), (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
            
        p1.draw(screen)
        p2.draw(screen)
        draw_hp_bar(screen, p1, 40, font_s)
        draw_hp_bar(screen, p2, WIDTH - 440, font_s)
        remain = max(0, ROUND_TIME - tmr // FPS)
        draw_center_text(screen, str(remain), font_s, 32)
        
        if result:
            draw_center_text(screen, result, font_l, HEIGHT // 2 - 40)
            draw_center_text(screen, "R: Restart  /  Esc: Quit", font_s, HEIGHT // 2 + 30)
            
        pg.display.update()
        clock.tick(FPS)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()