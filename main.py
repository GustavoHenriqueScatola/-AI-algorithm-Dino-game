import random
import threading
import traceback

import jogo

DINOSSAUROS = 100
TAXA_MUTACAO = 0.01
ELITE = True
GERACOES = 100
SEMENTE = 1

DIGITAR = ("selecionar", "cruzar", "mutar", "evoluir")
LIMITE = 20
PADRAO = (100, 0.01, True, 100, 1)
ESPERADA = 23


def linha_do_genetico(erro):
    for quadro in reversed(traceback.extract_tb(erro.__traceback__)):
        if quadro.filename.endswith("genetico.py"):
            return quadro
    return None


try:
    import genetico as ga
except SyntaxError as erro:
    print(f"\n  O genetico.py tem um erro de digitação na linha {erro.lineno}:")
    print(f"    {(erro.text or '').strip()}")
    print(f"  ({erro.msg})\n")
    raise SystemExit(1)
except ModuleNotFoundError as erro:
    print(f"\n  Não achei o {erro.name}.py nesta pasta.\n")
    raise SystemExit(1)
except Exception as erro:
    quadro = linha_do_genetico(erro)
    if quadro:
        print(f"\n  O genetico.py deu erro na linha {quadro.lineno}:")
        print(f"    {quadro.line}")
    else:
        print("\n  O genetico.py deu erro ao abrir:")
    print(f"  ({type(erro).__name__}: {erro})")
    print("  Toda linha digitada fica dentro de um def, com recuo.\n")
    raise SystemExit(1)


def qual_cacto(nota):
    return sum(1 for c in jogo.CACTOS if c <= nota)


def geracao_zero(tamanho):
    random.seed(SEMENTE)
    dinos = [ga.dna_aleatorio() for _ in range(tamanho)]
    return dinos, [jogo.correr(dna) for dna in dinos]


def genes(dna):
    return "".join(str(g) for g in dna)


def virgula(x):
    return f"{x:.1f}".replace(".", ",")


def testar_selecionar():
    dinos, notas = geracao_zero(100)
    sorteio = sum(1 for nota in notas if qual_cacto(nota) > 1)
    random.seed(SEMENTE)
    vencedores = [ga.selecionar(dinos, notas) for _ in range(1000)]
    if None in vencedores:
        return False, ("não devolveu um dinossauro.\n"
                       "    Falta o return, ou ele ficou dentro do if.")
    if not all(isinstance(v, list) and len(v) == jogo.PASSOS
               for v in vencedores):
        return False, (f"devolveu {vencedores[0]!r}, e não um DNA.\n"
                       "    Devolva dinos[vencedor], e não vencedor.")
    passaram = sum(1 for v in vencedores if qual_cacto(jogo.correr(v)) > 1)
    if passaram < 130:
        return False, (f"só {passaram} de 1000 vencedores passaram do 1º "
                       "cacto.\n    Fica quem foi MAIS longe: confira o > "
                       "do if.")
    if passaram < 210:
        return False, (f"{passaram} de 1000 vencedores passaram do 1º cacto, "
                       "e não uns 250.\n    O torneio ficou com 2: o return "
                       "está dentro do for?")
    return True, (f"{passaram} de 1000 vencedores passaram do 1º cacto; "
                  f"sorteando, {sorteio * 10}")


def testar_cruzar():
    pai = [0] * 20
    mae = [1] * 20
    random.seed(SEMENTE)
    filhos = []
    for _ in range(300):
        filho = ga.cruzar(pai, mae)
        filhos.append(filho)
        if filho is None:
            return False, "não devolveu nada: falta o return."
        if len(filho) != len(pai):
            return False, (f"de dois pais com 20 genes saiu um filho com "
                           f"{len(filho)}.\n    Confira as fatias: "
                           "pai[:corte] + mae[corte:].")
        corte = filho.index(1) if 1 in filho else len(filho)
        if filho != pai[:corte] + mae[corte:]:
            return False, (f"saiu o filho {genes(filho)}.\n    O começo vem "
                           "do pai e o fim da mãe: pai[:corte] + mae[corte:].")
    for copia, quem, corte in ((mae, "da mãe", 0), (pai, "do pai", 20)):
        if copia in filhos:
            return False, (f"um filho saiu inteiro {quem}: o corte deu "
                           f"{corte}.\n    O corte vai de 1 a 19: "
                           "random.randrange(1, len(pai)).")
    return True, f"de 20 zeros com 20 uns: {genes(filhos[0])}"


def testar_mutar():
    random.seed(SEMENTE)
    trocas_0 = trocas_1 = 0
    for _ in range(500):
        dna = [0] * 200 + [1] * 200
        antes = list(dna)
        depois = ga.mutar(dna, 0.01)
        if depois is None:
            return False, ("não devolveu nada.\n"
                           "    Falta o return, ou ele ficou dentro do if.")
        trocas_0 += sum(a != b for a, b in zip(antes[:200], depois[:200]))
        trocas_1 += sum(a != b for a, b in zip(antes[200:], depois[200:]))
    media = (trocas_0 + trocas_1) / 500
    if media < 1:
        return False, (f"trocam em média {virgula(media)} de 400 genes, e não "
                       "uns 4.\n    O return está dentro do for?")
    if media > 20:
        return False, (f"trocam em média {virgula(media)} de 400 genes, e não "
                       "uns 4.\n    Troca quando o sorteio é MENOR que a "
                       "taxa: confira o < do if.")
    if trocas_1 == 0:
        return False, ("o 0 vira 1, mas o 1 nunca vira 0.\n"
                       "    O gene novo é 1 - dna[i].")
    if trocas_0 == 0:
        return False, ("o 1 vira 0, mas o 0 nunca vira 1.\n"
                       "    O gene novo é 1 - dna[i].")
    return True, (f"com taxa 0.01, trocam em média {virgula(media)} de 400 "
                  "genes")


def rodar_evoluir():
    saida = {}

    def rodar():
        try:
            saida["historico"] = ga.evoluir(
                tamanho=DINOSSAUROS, geracoes=GERACOES, taxa=TAXA_MUTACAO,
                elite=ELITE, semente=SEMENTE)
        except Exception as erro:
            saida["erro"] = erro

    linha = threading.Thread(target=rodar, daemon=True)
    linha.start()
    linha.join(LIMITE)
    if linha.is_alive():
        raise TimeoutError
    if "erro" in saida:
        raise saida["erro"]
    return saida["historico"]


def testar_evoluir():
    try:
        historico = rodar_evoluir()
    except TimeoutError:
        return False, (f"passou de {LIMITE} s e não terminou.\n"
                       "    O nova.append está fora do while?")
    if historico is None:
        return False, ("não devolveu nada.\n"
                       "    Falta o return historico no fim, fora do for.")
    if len(historico) != GERACOES:
        return False, (f"devolveu {len(historico)} de {GERACOES} gerações.\n"
                       "    O return historico está dentro do for?")
    if len(historico) > 1 and historico[-1][2] is historico[0][2]:
        return False, ("a geração nunca muda.\n"
                       "    Falta o dinos = nova no fim do for, fora do "
                       "while.")
    if historico[0][2] != geracao_zero(DINOSSAUROS)[0]:
        return False, ("cada rodada sai diferente.\n"
                       "    Falta o random.seed(semente) no começo.")
    return True, historico


def explicar(erro):
    linhas = ["deu erro."]
    quadro = linha_do_genetico(erro)
    if quadro:
        linhas = [f"deu erro na linha {quadro.lineno} do genetico.py:",
                  f"    {quadro.line}"]
    linhas.append(f"    {type(erro).__name__}: {erro}")
    texto = str(erro)
    if texto.startswith(tuple(f"{nome}()" for nome in DIGITAR)):
        linhas.append("    Confira os parâmetros, no def e na chamada: os "
                      "nomes e a ordem.")
    elif "append() takes exactly one argument" in texto:
        linhas.append("    O append recebe uma coisa só: as três vão "
                      "juntas, em parênteses duplos.")
    elif (isinstance(erro, TypeError) and quadro
          and "randrange(" in (quadro.line or "")):
        linhas.append("    O randrange recebe um número: o tamanho, "
                      "len(...).")
    return "\n".join(linhas)


def primeiro_que_termina(historico):
    return next((g for g, (_, terminaram, _) in enumerate(historico)
                 if terminaram > 0), None)


def comparar(historico):
    if (DINOSSAUROS, TAXA_MUTACAO, ELITE, GERACOES, SEMENTE) != PADRAO:
        return "ok"
    x = primeiro_que_termina(historico)
    if x == ESPERADA:
        return "ok"
    if x is None:
        deu = f"ninguém terminou a pista em {GERACOES} gerações"
    else:
        deu = f"o primeiro terminou na geração {x}"
    return (f"roda, mas {deu}, e não na {ESPERADA}.\n"
            "    Compare o código com o do projetor, linha a linha.")


def conferir():
    testes = (testar_selecionar, testar_cruzar, testar_mutar, testar_evoluir)
    certas = {}
    for nome, teste in zip(DIGITAR, testes):
        if not hasattr(ga, nome):
            print(f"  falta digitar o {nome}")
            continue
        if nome == "evoluir":
            antes = [n for n in DIGITAR[:3] if n not in certas]
            if antes:
                print(f"  evoluir: primeiro, o {', o '.join(antes)} tem que "
                      "dar ok")
                continue
        try:
            certo, resposta = teste()
        except Exception as erro:
            print(f"  {nome}: {explicar(erro)}")
            continue
        if not certo:
            print(f"  {nome}: {resposta}")
            continue
        certas[nome] = resposta
        if nome == "evoluir":
            print(f"  evoluir: {comparar(resposta)}")
        else:
            print(f"  {nome}: ok ({resposta})")
    return certas


def resumir_zero(dinos, notas):
    contagem = {}
    for nota in notas:
        cacto = qual_cacto(nota)
        contagem[cacto] = contagem.get(cacto, 0) + 1
    partes = [f"{contagem[c]} no {c}º" for c in sorted(contagem)]
    print(f"  Geração 0: {len(dinos)} dinossauros sorteados, sem evolução.")
    print(f"  Bateram: {', '.join(partes)} cacto.")
    print(f"  O que foi mais longe parou no passo {max(notas)} de "
          f"{jogo.PASSOS}.")


def resumir(historico):
    total = len(historico[0][2])
    ultima = len(historico) - 1
    x = primeiro_que_termina(historico)
    ate = ultima if x is None else x
    passo = 5 if ate <= 40 else 10
    marcas = sorted(set(range(0, ate, passo)) | {ate, ultima})
    elite = "com" if ELITE else "sem"
    print(f"  {total} dinossauros, mutação {TAXA_MUTACAO}, {elite} elite, "
          f"semente {SEMENTE}")
    print("    geração  mais longe  terminaram")
    for g in marcas:
        melhor, terminaram, _ = historico[g]
        barra = "#" * (melhor // 10)
        print(f"    {g:>7}{melhor:>12}{terminaram:>7} de {total:<4} {barra}")
    if x is None:
        print(f"  Ninguém terminou a pista em {len(historico)} gerações.")
    else:
        print(f"  O primeiro dinossauro terminou a pista na geração {x}.")
    n = historico[-1][1]
    verbo = "terminou" if n == 1 else "terminaram"
    print(f"  Na geração {ultima}, {n} de {total} {verbo}.")
    melhores = [melhor for melhor, _, _ in historico]
    pioras = sum(1 for g in range(1, len(melhores))
                 if melhores[g] < melhores[g - 1])
    if pioras:
        print(f"  O mais longe piorou de uma geração para a seguinte "
              f"{pioras} {'vez' if pioras == 1 else 'vezes'}.")


def abrir_jogo(historico):
    try:
        import visual
    except ImportError:
        print("  O jogo precisa do pygame: rode com o py do venv.\n")
        return
    mostrar, _ = visual.escolher(historico)
    if len(mostrar) == 1:
        nomes = f"geração {mostrar[0]}"
    else:
        nomes = (f"gerações {', '.join(map(str, mostrar[:-1]))} e "
                 f"{mostrar[-1]}")
    print(f"  Abrindo o jogo: {nomes}. ESC fecha.\n")
    visual.jogar(historico)


def main():
    print()
    print("O DINOSSAURO E OS CACTOS: ALGORITMO GENÉTICO")
    print()
    certas = conferir()
    print()
    if not hasattr(ga, "evoluir"):
        dinos, notas = geracao_zero(DINOSSAUROS)
        resumir_zero(dinos, notas)
        historico = [(max(notas), notas.count(jogo.PASSOS), dinos)]
    elif "evoluir" in certas:
        historico = certas["evoluir"]
        resumir(historico)
    else:
        return
    print()
    abrir_jogo(historico)


if __name__ == "__main__":
    main()
