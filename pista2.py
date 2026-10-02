import random

COMPRIMENTO = 500
PULO = (1, 2, 3, 3, 2, 1)
AGACHA = 2
TIPOS = ("cacto pequeno", "cacto grande", "passaro baixo", "passaro alto")
LARGURA = {"cacto pequeno": 1, "cacto grande": 3, "passaro baixo": 1,
           "passaro alto": 1}
ALTURA_PARA_PASSAR = {"cacto pequeno": 1, "cacto grande": 2,
                      "passaro baixo": 3}


def criar_pista(numero):
    rng = random.Random(numero)
    pista = []
    passo = rng.randint(20, 40)
    curta = False
    while passo < COMPRIMENTO - 20:
        tipo = rng.choice(TIPOS)
        pista.append((passo, tipo))
        curta = not curta and rng.random() < 0.5
        folga = rng.randint(5, 7) if curta else rng.randint(8, 25)
        passo += LARGURA[tipo] + folga
    return pista


def correr(decidir, dna, numero):
    pista = criar_pista(numero)
    perigo = {}
    for chegada, tipo in pista:
        for casa in range(chegada, chegada + LARGURA[tipo]):
            perigo[casa] = tipo
    no_ar = 0
    abaixado = 0
    proximo = 0
    for passo in range(COMPRIMENTO):
        altura = PULO[-no_ar] if no_ar else 0
        agachado = abaixado > 0
        no_ar = max(no_ar - 1, 0)
        abaixado = max(abaixado - 1, 0)
        tipo = perigo.get(passo)
        if tipo == "passaro alto" and not agachado:
            return passo
        if tipo in ALTURA_PARA_PASSAR and altura < ALTURA_PARA_PASSAR[tipo]:
            return passo
        if altura or agachado:
            continue
        while proximo < len(pista) and pista[proximo][0] <= passo:
            proximo += 1
        if proximo == len(pista):
            return COMPRIMENTO
        chegada, tipo = pista[proximo]
        distancia = chegada - passo
        if tipo.startswith("passaro"):
            distancia = 2 * distancia
        acao = decidir(dna, {"passo": passo, "distancia": distancia,
                             "tipo": tipo})
        if acao == 1:
            no_ar = len(PULO)
        elif acao == 2:
            abaixado = AGACHA
        elif acao != 0:
            raise ValueError(f"o decidir devolveu {acao!r}, e tem que ser "
                             "0, 1 ou 2")
    return COMPRIMENTO
