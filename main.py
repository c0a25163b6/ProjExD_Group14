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
GRAVITY = 1  # 1フレームごとに加算される落下速度
ROUND_TIME = 60  # 1ラウンドの制限時間（秒）

FIGHTER_W = 80  # キャラの幅（当たり判定）
FIGHTER_H = 160  # キャラの高さ（当たり判定）
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
ADJUSTING_CPU_ATTACK_POINT = -10  # cpuが攻撃するときの攻撃計算の補助判定
AVOID_CHOICE_STANDARD_RATE = 0.33  # cpuが回避するときの逃げの選択基準の境目
AVOID_BACK_WALL_CHECK = 30  # CPU回避時の壁際判定の定数
GAME_TITLE = "FIGHTERS"  # ゲームタイトル
BACK_SELECT = "ESC : BACK"  # メニューセレクトのバックボタン用
CPU_MODE_TITLE = "CPU MODE SELECT"  # cpuのモードセレクトタイトル
MENU_TOP_Y = HEIGHT // 2  # メニューのテキスト表示の最上層部分
MENU_LINE_GAP = 60  # テキストの間隔
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


def load_fighter_image(path: str, color: tuple[int, int, int]) -> pg.Surface:
    """
    キャラ画像を読み込む。画像がなければ単色の四角で代用する
    引数 path：画像ファイルのパス
    引数 color：画像がないときの代わりの色
    戻り値：右向きのキャラ画像Surface
    """
    if os.path.exists(path):
        img = pg.image.load(path).convert_alpha()
        return pg.transform.scale(img, (FIGHTER_W, FIGHTER_H))
    img = pg.Surface((FIGHTER_W, FIGHTER_H))
    img.fill(color)
    pg.draw.rect(img, (255, 255, 255), (FIGHTER_W - 25, 20, 12, 12))  # 向きが分かるように目を描く
    return img


class Fighter(pg.sprite.Sprite):
    """
    格闘キャラクターに関するクラス
    """

    def __init__(self, name: str, x: int, facing: int, keys: KeyConfig,
                 img_path: str, color: tuple[int, int, int]) -> None:
        """
        キャラクターを生成する
        引数 name：表示名
        引数 x：初期位置のx座標（中心）
        引数 facing：向き（右:+1, 左:-1）
        引数 keys：操作キーの設定
        引数 img_path：右向き画像のパス
        引数 color：画像がないときの代わりの色
        """
        super().__init__()
        self.name = name
        self.keys = keys
        self.facing = facing
        self.img_right = load_fighter_image(img_path, color)
        self.img_left = pg.transform.flip(self.img_right, True, False)
        self.image = self.img_right if facing == 1 else self.img_left
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = GROUND_Y
        self.vy = 0  # 縦方向の速度
        self.hp = MAX_HP
        self.attack_timer = 0  # 攻撃判定が残っているフレーム数
        self.cooldown = 0  # 次の攻撃までの待ちフレーム数
        self.hitstun = 0  # のけぞりの残りフレーム数
        self.has_hit = False  # 今回の攻撃がすでに当たったか

    def is_on_ground(self) -> bool:
        """
        地面に立っているかを返す
        """
        return self.rect.bottom >= GROUND_Y

    def handle_input(self, key_lst: pg.key.ScancodeWrapper) -> None:
        """
        押されているキーに応じて移動・ジャンプ・攻撃を行う
        引数 key_lst：押下キーの真理値リスト
        """
        if self.hitstun > 0:  # のけぞり中は操作できない
            return
        dx = 0
        if key_lst[self.keys.left]:
            dx -= WALK_SPEED
        if key_lst[self.keys.right]:
            dx += WALK_SPEED
        self.rect.x += dx
        if key_lst[self.keys.jump] and self.is_on_ground():
            self.vy = -JUMP_POWER
        if key_lst[self.keys.attack] and self.cooldown == 0:
            self.attack_timer = ATTACK_FRAMES
            self.cooldown = ATTACK_COOLDOWN
            self.has_hit = False

    def face_to(self, other: "Fighter") -> None:
        """
        相手のいる方向を向く
        引数 other：相手キャラ
        """
        self.facing = 1 if other.rect.centerx >= self.rect.centerx else -1
        self.image = self.img_right if self.facing == 1 else self.img_left

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
        self.attack_timer = 0  # 攻撃を潰される
        self.rect.x += KNOCKBACK * from_dir
        self.rect.clamp_ip(pg.Rect(0, 0, WIDTH, HEIGHT))  # 画面外に押し出されないようにする

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
            pg.draw.rect(screen, (255, 220, 0), atk, 3)  # 攻撃判定を可視化


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
        attacker.has_hit = True  # 1回の攻撃で多段ヒットしないようにする


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
    p1 = Fighter("P1", 250, 1, P1_KEYS, "fig/p1.png", (60, 120, 255))
    cpu = CPUFighter("CPU", 750, -1, P2_KEYS, "fig/p2.png", (255, 80, 80), "normal")
    return p1, cpu


class MoveTuple(NamedTuple):
    """
    移動や攻撃などの一括管理用NamedTuple
    """
    left: bool = False  # 左移動
    right: bool = False  # 右移動
    jump: bool = False  # ジャンプ
    attack: int | None = None  # 攻撃
    defence: bool = False  # 防御


class DifficultyTuple(NamedTuple):
    """
    CPU難易度に関するNamedTuple
    """
    think_interval: int  # 思考速度のインターバル
    attack_rate: float  # 攻撃レート
    avoid_rate: float  # 回避レート


DIFFICULTY = {
    "weak": DifficultyTuple(think_interval=45,
                            attack_rate=0.3,
                            avoid_rate=0.15),
    "normal": DifficultyTuple(think_interval=30,
                              attack_rate=0.5,
                              avoid_rate=0.3),
    "strong": DifficultyTuple(think_interval=15,
                              attack_rate=0.75,
                              avoid_rate=0.75),
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

    def think_action(self, enemy: Fighter) -> MoveTuple:
        """
        距離や攻撃範囲を確認して攻撃、移動を判断する
        引数 enemy : 相手キャラ
        戻り値 : MoveTuple
        """
        distant_player = abs(enemy.rect.centerx - self.rect.centerx)  # 相手との距離計算
        attack_range = (FIGHTER_W//2 + ATTACK_W + FIGHTER_W//2
                        + ADJUSTING_CPU_ATTACK_POINT)  # 攻撃可能かどうかの判定を行うための計算
        attack_random_rate = random.random()  # 攻撃頻度のランダム数
        avoid_random_rate = random.random()  # 回避のランダム数
        avoid_choice_select = random.random()  # 回避選択のランダム数
        if enemy.cooldown == 0:
            if attack_range >= distant_player:
                if avoid_random_rate <= self.difficulty_param.avoid_rate:
                    if (self.rect.left <= AVOID_BACK_WALL_CHECK or
                            self.rect.right >= WIDTH - AVOID_BACK_WALL_CHECK):
                        if avoid_choice_select < AVOID_CHOICE_STANDARD_RATE * 2:
                            return MoveTuple(jump=True)
                        else:
                            pass  # 後でdefenceに変更
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
                            pass  # 後でdefenceに変更

        if attack_range >= distant_player:
            if attack_random_rate <= self.difficulty_param.attack_rate:
                return MoveTuple(attack=0)
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
        if self.hitstun > 0:
            self.was_hit = True
            return
        if self.was_hit:
            self.think_timer = 0
            self.was_hit = False
        if self.think_timer <= 0:
            self.action = self.think_action(enemy)
            self.think_timer = self.difficulty_param.think_interval
        else:
            self.think_timer -= 1
        if self.action.left:
            self.rect.x -= WALK_SPEED
        elif self.action.right:
            self.rect.x += WALK_SPEED
        if self.action.jump and self.is_on_ground():
            self.vy = -JUMP_POWER
        if self.action.attack is not None and self.cooldown == 0:
            self.attack_timer = ATTACK_FRAMES
            self.cooldown = ATTACK_COOLDOWN
            self.has_hit = False


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
            pass


def main() -> None:
    pg.display.set_caption("2D格闘ゲーム（仮）")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    clock = pg.time.Clock()
    font_s = pg.font.Font(None, 36)
    font_l = pg.font.Font(None, 100)
    bg_img = pg.image.load("fig/bg.png").convert() if os.path.exists("fig/bg.png") else None

    p1, p2 = create_fighters()
    tmr = 0  # 経過フレーム数
    result = ""  # 決着時の文字列（空なら対戦中）

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_r and result:
                p1, p2 = create_fighters()  # リスタート
                tmr = 0
                result = ""

        if not result:  # 対戦中の処理
            key_lst = pg.key.get_pressed()
            p1.handle_input(key_lst)
            p2.action_cpu(p1)
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
