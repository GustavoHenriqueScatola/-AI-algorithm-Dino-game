import random

PASSOS = 400
PULO = 4
SEMENTE_PISTA = 6


def criar_pista(semente=SEMENTE_PISTA, passos=PASSOS):
    rng = random.Random(semente)
    pista = [0] * passos
    posicao = 30
    while posicao < passos - 10:
        largura = rng.randint(1, 3)
        pista[posicao:posicao + largura] = [1] * largura
        posicao += rng.randint(20, 35)
    return pista


PISTA = criar_pista()
CACTOS = [p for p in range(PASSOS)
          if PISTA[p] == 1 and (p == 0 or PISTA[p - 1] == 0)]


def correr(dna, pista=PISTA):
    no_ar = 0
    for passo in range(len(pista)):
        if no_ar > 0:
            no_ar -= 1
        elif pista[passo] == 1:
            return passo
        elif dna[passo] == 1:
            no_ar = PULO
    return len(pista)


def pulos(dna, pista=PISTA):
    saidas = []
    no_ar = 0
    for passo in range(len(pista)):
        if no_ar > 0:
            no_ar -= 1
        elif pista[passo] == 1:
            break
        elif dna[passo] == 1:
            no_ar = PULO
            saidas.append(passo)
    return saidas
