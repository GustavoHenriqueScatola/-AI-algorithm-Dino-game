import copy
import hashlib
import io
import json
import os
import random
import statistics
import subprocess
import sys
import textwrap
import time
import traceback
import types
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PASTA = Path(__file__).resolve().parent
ARQUIVO = PASTA / "dino2.py"
MOTOR = PASTA / "pista2.py"
ORIGINAL = "69f5be7014701968e47dba273732feec783ce21878417035938972d21f1a5f1e"
SEMENTES = [1, 2, 3, 4, 5]
PISTAS_NOVAS = 20
SORTEADOS = 20
VEZES = 2
METADE = 10
ORCAMENTO = 5000
TETO = 4 * ORCAMENTO
CORTE = 120
IMPRESSO = 10
TESTE = random.Random(2026).sample(range(100000, 1000000), PISTAS_NOVAS)
NOME = {"cacto pequeno": "cacto pequeno", "cacto grande": "cacto grande",
        "passaro baixo": "pássaro baixo", "passaro alto": "pássaro alto"}
ACAO = {0: "seguir (0)", 1: "pular (1)", 2: "agachar (2)"}


class Estourou(BaseException):
    pass


def milhar(n):
    return f"{n:,}".replace(",", ".")


def impressao(caminho):
    texto = caminho.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def onde_bateu(pista, largura, distancia):
    for indice, (chegada, tipo) in enumerate(pista):
        if chegada <= distancia < chegada + largura[tipo]:
            return indice, tipo
    return None, None


def descrever(erro):
    linha = None
    for quadro in traceback.extract_tb(erro.__traceback__):
        if quadro.filename == str(ARQUIVO):
            linha = quadro.lineno
    texto = f"{type(erro).__name__}: {erro}"[:160]
    if linha:
        texto += f" (dino2.py, linha {linha})"
    if "not in tuple" in str(erro) or "not in list" in str(erro):
        texto += (". Quer dizer: procurou numa lista uma coisa que não está "
                  "nela. O tipo vem sem acento: \"passaro alto\"")
    if "empty range" in str(erro):
        texto += (". Quer dizer: o sorteio não tinha número para escolher. "
                  "No cruzar, com um DNA de 1 número, não tem onde cortar")
    return texto


def acoes_por_tipo(modulo, motor, sorteados):
    vistas = {tipo: set() for tipo in motor.TIPOS}
    for dna in sorteados:
        for tipo in motor.TIPOS:
            passo = 2 if tipo.startswith("passaro") else 1
            for distancia in range(passo, 41 * passo, passo):
                acao = modulo.decidir(copy.deepcopy(dna), {
                    "passo": 200, "distancia": distancia, "tipo": tipo})
                vistas[tipo].add(acao if acao in ACAO else repr(acao))
    return {tipo: sorted(vistas[tipo], key=str) for tipo in motor.TIPOS}


def filho():
    pedido = json.loads(sys.stdin.read())
    sys.path.insert(0, str(PASTA))
    tela = sys.stdout
    sys.stdout = io.StringIO()
    resposta = {}
    try:
        import pista2
        prova = types.ModuleType("pista2_prova")
        exec(compile(MOTOR.read_text(encoding="utf-8-sig"), str(MOTOR), "exec"),
             prova.__dict__)
        correr_original = pista2.correr
        criar_original = pista2.criar_pista
        conta = {"corridas": 0, "pistas": 0, "contando": False}

        def correr(decidir, dna, numero):
            if conta["contando"]:
                conta["corridas"] += 1
                if conta["corridas"] > TETO:
                    raise Estourou()
            return correr_original(decidir, dna, numero)

        def criar_pista(numero):
            conta["pistas"] += 1
            return criar_original(numero)

        pista2.correr = correr
        pista2.criar_pista = criar_pista
        modulo = types.ModuleType("dino2")
        modulo.__file__ = str(ARQUIVO)
        sys.modules["dino2"] = modulo
        fonte = ARQUIVO.read_text(encoding="utf-8-sig")
        conta["contando"] = True
        exec(compile(fonte, str(ARQUIVO), "exec"), modulo.__dict__)
        inicio = time.perf_counter()
        dna = modulo.resolver(pedido["semente"])
        resposta["segundos"] = time.perf_counter() - inicio
        conta["contando"] = False
        resposta["corridas"] = conta["corridas"]
        if dna is None:
            raise ValueError("o resolver() não devolveu nada: falta o return "
                             "com o melhor DNA")
        antes = conta["pistas"]
        provas = []
        for numero in TESTE:
            distancia = prova.correr(modulo.decidir, copy.deepcopy(dna),
                                     numero)
            indice, tipo = onde_bateu(prova.criar_pista(numero), prova.LARGURA,
                                      distancia)
            provas.append([distancia, indice, tipo])
        if conta["pistas"] != antes:
            raise RuntimeError("o decidir() chamou o criar_pista(), e ele só "
                               "pode olhar a visao")
        resposta["provas"] = provas
        try:
            sorteados = [modulo.dna_aleatorio(random.Random(k))
                         for k in range(SORTEADOS)]
            medias = []
            for sorteado in sorteados:
                medias.append(statistics.mean(
                    prova.correr(modulo.decidir, copy.deepcopy(sorteado), s)
                    for s in TESTE))
            resposta["sorteados"] = statistics.mean(medias)
            resposta["acoes"] = acoes_por_tipo(modulo, prova, sorteados)
        except (Exception, SystemExit) as erro:
            resposta["erro_sorteio"] = descrever(erro)
    except Estourou:
        resposta["erro"] = (f"o resolver() passou de {milhar(TETO)} corridas "
                            f"e foi interrompido. A meta 8 pede até "
                            f"{milhar(ORCAMENTO)}")
        resposta["corridas"] = TETO + 1
    except (Exception, SystemExit) as erro:
        resposta["erro"] = descrever(erro)
    impresso = sys.stdout.getvalue().splitlines()
    resposta["impresso"] = [linha[:70] for linha in impresso[:IMPRESSO]]
    resposta["impressas"] = len(impresso)
    sys.stdout = tela
    print(json.dumps(resposta), flush=True)
    os._exit(0)


def rodar(semente):
    ambiente = dict(os.environ, PYTHONIOENCODING="utf-8",
                    PYTHONDONTWRITEBYTECODE="1")
    try:
        feito = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--filho"],
            input=json.dumps({"semente": semente}), capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=CORTE,
            cwd=PASTA, env=ambiente)
    except subprocess.TimeoutExpired:
        return {"erro": f"passou de {CORTE} s e foi interrompido. Vejam "
                        f"quantas corridas o resolver() faz (o limite é "
                        f"{milhar(ORCAMENTO)}) e se o decidir() faz alguma "
                        f"conta pesada"}
    linhas = [linha for linha in feito.stdout.splitlines() if linha.strip()]
    try:
        return json.loads(linhas[-1])
    except (IndexError, ValueError):
        fim = feito.stderr.strip().splitlines() or ["parou sem mensagem"]
        return {"erro": fim[-1][:160]}


def explicar(texto):
    for linha in textwrap.wrap(texto, 58):
        print("        " + linha)


def contagem(tipos):
    conta = Counter(NOME[t] for t in tipos if t)
    return ", ".join(f"{nome} {n}" for nome, n in conta.most_common())


def medir(r):
    if "erro" in r:
        return None
    provas = r["provas"]
    distancias = [d for d, _, _ in provas]
    return {
        "passou": sum(1 for _, i, _ in provas if i != 0),
        "no_primeiro": [t for _, i, t in provas if i == 0],
        "terminou": sum(1 for d, _, t in provas if t is None),
        "bateu": [t for _, _, t in provas if t],
        "media": statistics.mean(distancias),
        "sorteados": r.get("sorteados"),
        "acoes": r.get("acoes"),
        "erro_sorteio": r.get("erro_sorteio"),
    }


def porque_acao(m):
    if m is None:
        return "a rodada deu erro"
    if m["erro_sorteio"]:
        return f"o dna_aleatorio() ou o decidir() deu erro: {m['erro_sorteio']}"
    for tipo, acoes in m["acoes"].items():
        if not set(ACAO) <= set(acoes):
            feitas = " e ".join(ACAO.get(a, str(a)) for a in acoes)
            return (f"diante do {NOME[tipo]}, os {SORTEADOS} DNAs sorteados só "
                    f"fizeram {feitas}. A ação também tem que sair do DNA: "
                    f"quem descobre o que cada obstáculo pede é o genético")
    return None


def porque_meta(numero, m):
    n = PISTAS_NOVAS
    if m is None:
        return "a rodada deu erro"
    if numero == 3:
        if m["erro_sorteio"]:
            return f"o dna_aleatorio() deu erro: {m['erro_sorteio']}"
        if m["media"] < VEZES * m["sorteados"]:
            return (f"nas pistas novas, o campeão chega em média ao passo "
                    f"{m['media']:.0f}, e {SORTEADOS} DNAs sorteados pelo "
                    f"dna_aleatorio() chegam ao {m['sorteados']:.0f}. Tem que "
                    f"ser pelo menos {VEZES} vezes mais longe")
    if numero == 4 and m["passou"] < n:
        return (f"bateu no 1º obstáculo em {n - m['passou']} das {n} pistas "
                f"novas ({contagem(m['no_primeiro'])})")
    if numero == 5 and m["terminou"] < METADE:
        return (f"terminou {m['terminou']} das {n} pistas novas. Onde bateu: "
                f"{contagem(m['bateu'])}")
    if numero == 6 and m["terminou"] < n:
        texto = (f"terminou {m['terminou']} das {n} pistas novas. Onde bateu: "
                 f"{contagem(m['bateu'])}")
        if m["terminou"] >= METADE:
            texto += (". Se nas pistas do treino ele termina tudo, ele "
                      "decorou o treino")
        return texto
    return None


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    print()
    print("=" * 62)
    print("  O DINOSSAURO, FASE 2: placar do dino2.py")
    print("=" * 62)
    for caminho in (ARQUIVO, MOTOR):
        if not caminho.exists():
            print(f"  Não achei o {caminho.name} nesta pasta.")
            print()
            return
    if impressao(MOTOR) != ORIGINAL:
        print("  O pista2.py foi mudado. Copiem de novo o da pasta base:")
        print("  o placar só vale com o jogo original.")
        print()
        return
    try:
        compile(ARQUIVO.read_text(encoding="utf-8-sig"), str(ARQUIVO), "exec")
    except SyntaxError as erro:
        print(f"  O dino2.py tem erro de digitação na linha {erro.lineno}:")
        explicar(str(erro.msg))
        print()
        return
    print(f"  rodando o resolver() nas sementes {SEMENTES[0]} a {SEMENTES[-1]}")
    print(f"  e testando cada campeão em {PISTAS_NOVAS} pistas novas...",
          flush=True)
    inicio = time.perf_counter()
    with ThreadPoolExecutor(len(SEMENTES)) as grupo:
        respostas = list(grupo.map(rodar, SEMENTES))
    segundos = time.perf_counter() - inicio
    print(f"  pronto, em {segundos:.1f} s".replace(".", ","))
    erros = {}
    for semente, r in zip(SEMENTES, respostas):
        if "erro" in r:
            erros.setdefault(r["erro"], []).append(str(semente))
    for texto, quais in list(erros.items())[:3]:
        onde = ("todas as sementes" if len(quais) == len(SEMENTES)
                else "semente " + ", ".join(quais))
        print(f"  erro em {onde}:")
        explicar(texto)
    medidas = [medir(r) for r in respostas]

    def celula(m, chave):
        if m is None:
            return "x"
        return f"{m[chave]:.0f}" if chave == "media" else str(m[chave])

    print()
    print(f"  {'semente':<28}" + "".join(f"{s:>7}" for s in SEMENTES))
    for texto, chave in ((f"passou do 1º obstáculo", "passou"),
                         ("terminou a pista", "terminou"),
                         ("distância média", "media")):
        print(f"  {texto:<28}"
              + "".join(f"{celula(m, chave):>7}" for m in medidas))

    def corridas(r):
        if "corridas" not in r:
            return "x"
        if r["corridas"] > TETO:
            return ">" + milhar(TETO)
        return milhar(r["corridas"])

    print(f"  {'corridas no resolver()':<28}"
          + "".join(f"{corridas(r):>7}" for r in respostas))
    print(f"  (nas {PISTAS_NOVAS} pistas novas, de 500 passos)")
    if medidas[0] and medidas[0]["sorteados"] is not None:
        print(f"  {SORTEADOS} DNAs sorteados pelo dna_aleatorio(): média de "
              f"{medidas[0]['sorteados']:.0f} passos")
    if any(m is None for m in medidas):
        print("  x: a rodada deu erro")
    print()
    metas = []

    def linha(numero, texto, porque):
        metas.append(porque is None)
        situacao = "OK" if porque is None else "FALTA"
        print(f"  {numero}  {texto} ".ljust(54, ".") + f" {situacao}")
        if porque:
            explicar(porque)

    primeira = next((f"semente {s}: {r['erro']}" for s, r
                     in zip(SEMENTES, respostas) if "erro" in r), None)
    linha(1, f"roda sem erro nas {len(SEMENTES)} sementes", primeira)
    m1 = medidas[0]
    linha(2, "a ação sai do DNA", porque_acao(m1))
    linha(3, f"vai {VEZES} vezes mais longe que um DNA sorteado",
          porque_meta(3, m1))
    linha(4, f"passa do 1º obstáculo nas {PISTAS_NOVAS} pistas novas",
          porque_meta(4, m1))
    linha(5, f"termina pelo menos {METADE} das {PISTAS_NOVAS} pistas novas",
          porque_meta(5, m1))
    linha(6, f"termina as {PISTAS_NOVAS} pistas novas", porque_meta(6, m1))
    porque = None
    for semente, m in zip(SEMENTES, medidas):
        for numero in (3, 4, 5, 6):
            motivo = porque_meta(numero, m)
            if motivo and porque is None:
                porque = f"semente {semente}, meta {numero}: {motivo}"
    linha(7, f"metas 3 a 6 nas sementes {SEMENTES[0]} a {SEMENTES[-1]}", porque)
    contas = [r.get("corridas") for r in respostas]
    porque = None
    if max(c or 0 for c in contas) > TETO:
        pior = SEMENTES[contas.index(max(c or 0 for c in contas))]
        porque = f"o resolver({pior}) passou de {milhar(TETO)} corridas"
    elif any("erro" in r for r in respostas):
        porque = "rodada com erro não conta: todas têm que terminar"
    elif min(contas) == 0:
        porque = ("o resolver() não fez nenhuma corrida: o DNA tem que sair "
                  "do genético")
    elif max(contas) > ORCAMENTO:
        pior = SEMENTES[contas.index(max(contas))]
        porque = f"o resolver({pior}) fez {milhar(max(contas))} corridas"
    linha(8, f"até {milhar(ORCAMENTO)} corridas por resolver()", porque)
    impresso = respostas[0].get("impresso") or []
    if impresso:
        print()
        print(f"  o dino2.py imprimiu {respostas[0]['impressas']} linhas na "
              f"semente {SEMENTES[0]}. As primeiras:")
        for texto in impresso:
            print("    " + texto)
    print()
    print(f"  placar: {sum(metas)} de {len(metas)}")
    print()


if __name__ == "__main__":
    if "--filho" in sys.argv:
        filho()
    else:
        main()
