import bisect
import math
import os
import random

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import pygame

import jogo

QUANTAS = 4
VELOCIDADE = 32
LENTO_ZERO = 0.4
FPS = 60
ANTES = 1.0
DEPOIS = 1.6
FIM = 5.0

LARGURA = 1200
ALTURA = 420
CHAO = 330
DINO_X = 190
PX = 44
PERNAS_X = 5
BATEU = 55
PULO_ALTURA = 125
PIXEL = 3
PIXEL_CACTO = 2
SOME = 14

COR_FUNDO = (247, 247, 247)
COR_DINO = (83, 83, 83)
COR_FANTASMA = (150, 150, 150, 90)
COR_BATEU = (150, 150, 150)
COR_CACTO = (83, 83, 83)
COR_NUVEM = (215, 215, 215)
COR_TEXTO = (83, 83, 83)
COR_FRACO = (160, 160, 160)

CORPO = [
    ".............########.",
    "............##o#######",
    "............##########",
    "............##########",
    "............##########",
    "............#####.....",
    "............########..",
    "#..........#####......",
    "#.........#######.....",
    "##.......##########...",
    "###.....########..#...",
    "###############.......",
    ".##############.......",
    "..#############.......",
    "...###########........",
    "....#########.........",
    ".....#######..........",
]
PERNAS = {
    "paradas": ["......##..##..........",
                "......#....#..........",
                "......#....#..........",
                "......##...##........."],
    "frente no ar": ["......##..###.........",
                     "......#...............",
                     "......#...............",
                     "......##.............."],
    "tras no ar": ["......###.##..........",
                   "...........#..........",
                   "...........#..........",
                   "...........##........."],
}
OLHO_X = {(0, 13): "o", (0, 14): "#", (0, 15): "o", (1, 14): "o",
          (2, 13): "o",
          (2, 15): "o", (1, 13): "#", (1, 15): "#"}

CACTO = [
    ".....###.....",
    "....#####....",
    "....#####....",
    "....#####....",
    "....#####.##.",
    "....#####.###",
    ".##.#####.###",
    "###.#####.###",
    "###.#####.###",
    "###.#####.###",
    "###.########.",
    "###.#######..",
    "###.#####....",
    "#########....",
    ".########....",
    "....#####....",
    "....#####....",
    "....#####....",
    "....#####....",
    "....#####....",
    "....#####....",
    "....#####....",
    "....#####....",
    "....#####....",
    "....#####....",
    "....#####....",
]

NUVEM = [
    ".........######.........",
    ".......##......##.......",
    "......#..........#......",
    "..####............###...",
    ".#...................#..",
    "#.....................##",
    "########################",
]


def sprite(matriz, cor, pixel):
    s = pygame.Surface((len(matriz[0]) * pixel, len(matriz) * pixel),
                       pygame.SRCALPHA)
    for y, linha in enumerate(matriz):
        for x, ponto in enumerate(linha):
            if ponto == "#":
                s.fill(cor, (x * pixel, y * pixel, pixel, pixel))
            elif ponto == "o":
                s.fill(COR_FUNDO + cor[3:], (x * pixel, y * pixel, pixel,
                                             pixel))
    return s


def dinossauro(pernas, cor, morto=False):
    matriz = [list(linha) for linha in CORPO + PERNAS[pernas]]
    if morto:
        for (y, x), ponto in OLHO_X.items():
            matriz[y + 1][x] = ponto
    return sprite(["".join(linha) for linha in matriz], cor, PIXEL)


def altura(saidas, t):
    i = bisect.bisect_right(saidas, t) - 1
    if i < 0:
        return 0
    u = (t - saidas[i]) / (jogo.PULO + 1)
    if u >= 1:
        return 0
    return PULO_ALTURA * math.sin(math.pi * u)


def escolher(historico):
    primeiro = next((g for g, (_, terminaram, _) in enumerate(historico)
                     if terminaram > 0), None)
    ultima = len(historico) - 1 if primeiro is None else primeiro
    mostrar = sorted({ultima * i // (QUANTAS - 1) for i in range(QUANTAS)})
    if mostrar[-1] != len(historico) - 1:
        mostrar.append(len(historico) - 1)
    return mostrar, primeiro


class Corrida:
    def __init__(self, numero, dinos):
        self.numero = numero
        self.fim = [jogo.correr(dna) for dna in dinos]
        self.saidas = [jogo.pulos(dna) for dna in dinos]
        self.mais_longe = max(self.fim)
        self.lider = self.fim.index(self.mais_longe)
        self.total = len(dinos)
        self.terminaram = self.fim.count(jogo.PASSOS)


class Tela:
    def __init__(self):
        if os.name == "nt":
            import ctypes
            ctypes.windll.user32.SetProcessDPIAware()
        pygame.init()
        self.tela = pygame.display.set_mode((LARGURA, ALTURA))
        pygame.display.set_caption("O dinossauro e os cactos: "
                                   "algoritmo genético")
        self.relogio = pygame.time.Clock()
        self.fonte = pygame.font.SysFont("consolas", 24, bold=True)
        self.media = pygame.font.SysFont("consolas", 30, bold=True)
        self.grande = pygame.font.SysFont("consolas", 46, bold=True)
        self.velocidade = VELOCIDADE
        self.pausado = False
        self.fechado = False
        self.tempo_pernas = 0.0
        self.lider = {p: dinossauro(p, COR_DINO) for p in PERNAS}
        self.fantasma = {p: dinossauro(p, COR_FANTASMA) for p in PERNAS}
        self.morto = dinossauro("paradas", COR_DINO, morto=True)
        self.bateu = dinossauro("paradas", COR_BATEU, morto=True)
        self.cactos = [sprite(CACTO, COR_CACTO, PIXEL_CACTO),
                       sprite([linha[::-1] for linha in CACTO], COR_CACTO,
                              PIXEL_CACTO)]
        self.nuvem = sprite(NUVEM, COR_NUVEM, PIXEL)
        rng = random.Random(3)
        fim = (jogo.PASSOS + 40) * PX + LARGURA
        self.pedras = [(x, rng.randint(6, 18), rng.choice((2, 3, 4, 6)))
                       for x in range(-LARGURA, fim, 13)
                       if rng.random() < 0.55]
        self.nuvens = [(i * 480 + rng.randint(0, 200), rng.randint(55, 90))
                       for i in range(5)]

    def eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.fechado = True
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    self.fechado = True
                elif evento.key == pygame.K_SPACE:
                    self.pausado = not self.pausado
                elif evento.key in (pygame.K_UP, pygame.K_RIGHT):
                    self.velocidade = min(256, self.velocidade * 2)
                elif evento.key in (pygame.K_DOWN, pygame.K_LEFT):
                    self.velocidade = max(4, self.velocidade // 2)

    def escrever(self, texto, fonte, cor, x, y, centro=False):
        img = fonte.render(texto, True, cor)
        if centro:
            x -= img.get_width() // 2
        self.tela.blit(img, (x, y))

    def pernas(self, h):
        if h > 0:
            return "paradas"
        return ("frente no ar", "tras no ar")[int(self.tempo_pernas * 10) % 2]

    def cenario(self, t):
        self.tela.fill(COR_FUNDO)
        largura_nuvens = 2400
        for x, y in self.nuvens:
            xn = (x - t * PX * 0.2) % largura_nuvens - 200
            if xn < LARGURA:
                self.tela.blit(self.nuvem, (xn, y))
        pygame.draw.line(self.tela, COR_DINO, (0, CHAO), (LARGURA, CHAO), 2)
        deslocamento = DINO_X - t * PX
        for x, dy, w in self.pedras:
            xp = x + deslocamento
            if -10 < xp < LARGURA:
                pygame.draw.line(self.tela, COR_DINO, (xp, CHAO + dy),
                                 (xp + w, CHAO + dy), 2)
        for c in range(jogo.PASSOS):
            if jogo.PISTA[c] == 1:
                x = DINO_X + (c - t) * PX
                if -PX < x < LARGURA:
                    img = self.cactos[(c * 7) % 3 == 0]
                    self.tela.blit(img, (x + (PX - img.get_width()) // 2,
                                         CHAO - img.get_height() + 3))
        self.bandeira(DINO_X + (jogo.PASSOS - t) * PX)

    def bandeira(self, x):
        if not -40 < x < LARGURA:
            return
        pygame.draw.line(self.tela, COR_DINO, (x, CHAO), (x, CHAO - 120), 4)
        lado = 12
        for i in range(4):
            for j in range(3):
                cor = COR_DINO if (i + j) % 2 == 0 else COR_FUNDO
                pygame.draw.rect(self.tela, cor, (x + 2 + i * lado,
                                                  CHAO - 120 + j * lado,
                                                  lado, lado))
        pygame.draw.rect(self.tela, COR_DINO,
                         (x + 2, CHAO - 120, 4 * lado, 3 * lado), 2)

    def dinossauros(self, corrida, t):
        y_chao = CHAO - self.morto.get_height() + 4
        for i, fim in enumerate(corrida.fim):
            if fim < jogo.PASSOS and t >= fim and i != corrida.lider:
                idade = t - fim
                if idade < SOME:
                    self.bateu.set_alpha(int(220 * (1 - idade / SOME)))
                    x = DINO_X + (fim - t) * PX - BATEU
                    self.tela.blit(self.bateu, (x, y_chao + idade * 2))
        for i, (fim, saidas) in enumerate(zip(corrida.fim, corrida.saidas)):
            if i != corrida.lider and (t < fim or fim == jogo.PASSOS):
                h = altura(saidas, t)
                self.tela.blit(self.fantasma[self.pernas(h)],
                               (DINO_X - PERNAS_X, y_chao - h))
        fim = corrida.fim[corrida.lider]
        if t >= fim and fim < jogo.PASSOS:
            self.tela.blit(self.morto, (DINO_X - BATEU, y_chao))
        else:
            h = altura(corrida.saidas[corrida.lider], t)
            self.tela.blit(self.lider[self.pernas(h)],
                           (DINO_X - PERNAS_X, y_chao - h))

    def placar(self, corrida, t):
        vivos = sum(1 for fim in corrida.fim
                    if t < fim or fim == jogo.PASSOS)
        distancia = int(min(t, jogo.PASSOS))
        texto = (f"GERAÇÃO {corrida.numero}   VIVOS {vivos}/{corrida.total}"
                 f"   DISTÂNCIA {distancia:05d}")
        img = self.fonte.render(texto, True, COR_TEXTO)
        self.tela.blit(img, (LARGURA - img.get_width() - 30, 22))
        self.escrever("ESPAÇO pausa   setas: velocidade   ESC fecha",
                      self.fonte, COR_FRACO, 30, ALTURA - 40)

    def quadro(self, corrida, t, aviso=None, detalhe=None):
        self.cenario(t)
        self.dinossauros(corrida, t)
        self.placar(corrida, t)
        if aviso:
            self.escrever(aviso, self.grande, COR_TEXTO, LARGURA // 2, 120,
                          centro=True)
        if detalhe:
            self.escrever(detalhe, self.fonte, COR_TEXTO, LARGURA // 2, 180,
                          centro=True)
        if self.pausado:
            self.escrever("PAUSA", self.media, COR_FRACO, 30, 22)

    def esperar(self, segundos, corrida, t, aviso, detalhe=None):
        espera = 0.0
        while not self.fechado and espera < segundos:
            self.eventos()
            dt = self.relogio.tick(FPS) / 1000
            if not self.pausado:
                espera += dt
            self.quadro(corrida, t, aviso, detalhe)
            pygame.display.flip()

    def correr(self, corrida, primeiro, ultima):
        self.esperar(ANTES, corrida, 0, f"GERAÇÃO {corrida.numero}",
                     f"{corrida.total} dinossauros largam juntos")
        ate = corrida.mais_longe
        if ate == jogo.PASSOS:
            ate += 3
        lento = LENTO_ZERO if corrida.numero == 0 else 1
        t = 0.0
        while not self.fechado and t < ate:
            self.eventos()
            dt = self.relogio.tick(FPS) / 1000
            if not self.pausado:
                t = min(ate, t + dt * self.velocidade * lento)
                self.tempo_pernas += dt
            self.quadro(corrida, t)
            pygame.display.flip()
        aviso, detalhe = resultado(corrida, primeiro)
        self.esperar(FIM if ultima else DEPOIS, corrida, t, aviso, detalhe)


def resultado(corrida, primeiro):
    n, total = corrida.terminaram, corrida.total
    if corrida.numero == primeiro:
        detalhe = (f"o primeiro a chegar ao fim: geração {primeiro}"
                   if n == 1 else
                   f"{n} de {total} chegaram ao fim na geração {primeiro}")
        return "TERMINOU A PISTA!", detalhe
    if n > 0:
        verbo = "TERMINOU" if n == 1 else "TERMINARAM"
        return (f"{n} DE {total} {verbo} A PISTA",
                f"o primeiro tinha chegado na geração {primeiro}")
    return ("TODOS BATERAM",
            f"o melhor chegou à distância {corrida.mais_longe} de "
            f"{jogo.PASSOS}")


def jogar(historico):
    mostrar, primeiro = escolher(historico)
    tela = Tela()
    for g in mostrar:
        if tela.fechado:
            break
        tela.correr(Corrida(g, historico[g][2]), primeiro, g == mostrar[-1])
    pygame.quit()
