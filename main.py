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


@dataclass
class KeyConfig:
    """
    プレイヤーごとのキー割り当て
    """
    left: int
    right: int
    jump: int
    attack: int
    special: int


P1_KEYS = KeyConfig(left=pg.K_a, right=pg.K_d, jump=pg.K_w, attack=pg.K_f, special=pg.K_g)
P2_KEYS = KeyConfig(left=pg.K_LEFT, right=pg.K_RIGHT, jump=pg.K_UP, attack=pg.K_l, special=pg.K_j)


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
        # 必殺技の設定(必殺技)
        self.super_gauge = 0  # 必殺技ゲージ
        self.combo_timer = 0  # コンボが途切れるまでの時間
        self.combo_count = 0  # 連続で攻撃を当てた回数

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
        ダメージを受けてのけぞる。
        引数 damage：受けるダメージ量
        引数 from_dir：押し戻される向き（右:+1, 左:-1）
        """
        # ダメージを受けたら、自分が続けていたコンボをリセットする
        self.combo_count = 0
        self.combo_timer = 0
        self.hp = max(0, self.hp - damage)
        self.hitstun = HITSTUN_FRAMES
        self.attack_timer = 0  # 攻撃を潰される
        self.rect.x += KNOCKBACK * from_dir
        self.rect.clamp_ip(pg.Rect(0, 0, WIDTH, HEIGHT))

        # ダメージを受けたら必殺技ゲージを増やす
        self.super_gauge = min(
            MAX_SUPER_GAGE,
            self.super_gauge + DAMAGE_GAUGE_UP
        )

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
        self.combo_timer = max(0, self.combo_timer - 1)

        # 最後のヒットから90フレーム経過したらコンボをリセットする
        if self.combo_timer == 0:
            self.combo_count = 0

    def draw(self, screen: pg.Surface) -> None:
        """
        キャラと攻撃判定を描画する
        引数 screen：画面Surface
        """
        screen.blit(self.image, self.rect)
        atk = self.get_attack_rect()
        if atk is not None:
            pg.draw.rect(screen, (255, 220, 0), atk, 3)  # 攻撃判定を可視化


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


def check_hit(attacker: Fighter, defender: Fighter) -> None:
    """通常攻撃が当たったか判定し、ダメージとゲージを処理する。"""
    atk = attacker.get_attack_rect()

    if atk is None or attacker.has_hit:
        return
    if atk.colliderect(defender.rect):
        # 通常攻撃と必殺技で共通のコンボ・ダメージ処理を使う
        apply_hit(attacker, defender, ATTACK_DAMAGE)

        # 今回の攻撃は命中済み
        attacker.has_hit = True

        # コンボ数に応じて必殺技ゲージの増加量を決める
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

    # 必殺技ゲージ（必殺技）
    gauge_y = 78
    gauge_h = 12
    pg.draw.rect(screen, (50, 50, 50), (x, gauge_y, bar_w, gauge_h))
    gauge_w = bar_w * fighter.super_gauge // MAX_SUPER_GAGE
    pg.draw.rect(screen, (0, 150, 255), (x, gauge_y, gauge_w, gauge_h))
    pg.draw.rect(screen, (255, 255, 255), (x, gauge_y, bar_w, gauge_h), 1)

    # コンボ数（2回以上つながったときだけ表示）（必殺技）
    if fighter.combo_count >= 2 and fighter.combo_timer > 0:
        combo_text = font.render(f"{fighter.combo_count} COMBO", True, (255, 230, 50))
        screen.blit(combo_text, (x, 98))


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
    p2 = Fighter("P2", 750, -1, P2_KEYS, "fig/p2.png", (255, 80, 80))
    return p1, p2


def main() -> None:
    pg.display.set_caption("2D格闘ゲーム（仮）")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    clock = pg.time.Clock()
    font_s = pg.font.Font(None, 36)
    font_l = pg.font.Font(None, 100)
    bg_img = pg.image.load("fig/bg.png").convert() if os.path.exists("fig/bg.png") else None
    # 必殺技のグループを作成
    super_attacks = pg.sprite.Group()

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
                super_attacks.empty()  # 画面に残っている必殺技を消す
                tmr = 0
                result = ""

        if not result:  # 対戦中の処理
            key_lst = pg.key.get_pressed()
            p1.handle_input(key_lst)
            p2.handle_input(key_lst)

            # 必殺技キーが押され、ゲージが満タンなら必殺技を発射
            if key_lst[p1.keys.special] and p1.super_gauge >= SUPER_GAGE_REQUIRE:
                super_attacks.add(SuperAttack(p1))
                p1.super_gauge = 0

            if key_lst[p2.keys.special] and p2.super_gauge >= SUPER_GAGE_REQUIRE:
                super_attacks.add(SuperAttack(p2))
                p2.super_gauge = 0

            p1.update()
            p2.update()
            super_attacks.update()  # 必殺技の位置を更新する
            push_apart(p1, p2)
            p1.face_to(p2)
            p2.face_to(p1)
            check_hit(p1, p2)
            check_hit(p2, p1)

            # 必殺技が相手に当たったか判定
            for super_attack in list(super_attacks):  # 必殺技を一つずつ確認
                if super_attack.owner is p1:  # 誰が撃った弾なのか確認する
                    defender = p2
                else:
                    defender = p1

                if super_attack.rect.colliderect(defender.rect):
                    apply_hit(
                        super_attack.owner,
                        defender,
                        super_attack.damage
                    )
                    super_attack.kill()  # 必殺技を消す

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
        super_attacks.draw(screen)  # 必殺技を画面に描画する
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
