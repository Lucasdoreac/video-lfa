"""Gera video/index.html a partir do roteiro de narração.

Cada cena tem: narração (legenda), duração calculada pelo número de palavras e, quando
for o caso, um trecho real de código extraído dos arquivos do projeto, com o nome do
arquivo e as linhas mostradas no cabeçalho.
"""

import html
import math
import pathlib
import re

PROJETO = pathlib.Path(__file__).resolve().parent.parent
RAIZ = PROJETO.parent
PALAVRAS_POR_SEGUNDO = 2.4   # ritmo de fala pausado, pt-BR
FOLGA = 1.5                  # segundos a mais por cena para respirar
DURACAO_MINIMA = 4.0


def ler(arquivo):
    return (PROJETO / arquivo).read_text(encoding="utf-8").splitlines()


def trecho_funcao(arquivo, nome, max_linhas=16):
    linhas = ler(arquivo)
    ini = next(i for i, l in enumerate(linhas) if re.match(rf"\s*def {nome}\(", l))
    indent = len(linhas[ini]) - len(linhas[ini].lstrip())
    fim = ini + 1
    while fim < len(linhas):
        l = linhas[fim]
        if l.strip() and (len(l) - len(l.lstrip())) <= indent and not l.lstrip().startswith(("#", ")")):
            break
        fim += 1
    while linhas[fim - 1].strip() == "":
        fim -= 1
    trecho = linhas[ini:fim]
    return trecho[:max_linhas], ini + 1, ini + len(trecho[:max_linhas])


def trecho_regra(arquivo, id_regra):
    linhas = ler(arquivo)
    marca = next(i for i, l in enumerate(linhas) if f'"id": "{id_regra}"' in l)
    ini = marca - 1
    fim = next(i for i in range(marca, len(linhas)) if linhas[i] == "    },")
    trecho = linhas[ini:fim + 1]
    return trecho, ini + 1, fim + 1


def trecho_teste(arquivo, nome):
    linhas = ler(arquivo)
    ini = next(i for i, l in enumerate(linhas) if re.match(rf"\s*def {nome}\(", l))
    fim = ini + 1
    while fim < len(linhas) and not re.match(r"\s*def ", linhas[fim]) and not re.match(r"class ", linhas[fim]):
        fim += 1
    while linhas[fim - 1].strip() == "":
        fim -= 1
    return linhas[ini:fim], ini + 1, fim


def duracao(texto):
    palavras = len(texto.split())
    return max(DURACAO_MINIMA, round(palavras / PALAVRAS_POR_SEGUNDO + FOLGA, 1))


# ---------------------------------------------------------------- roteiro

NARRACAO = [
    ("Nicolas", "Oi, pessoal. Nosso projeto de Linguagens Formais e Autômatos é um sistema especialista para triagem de mensagens suspeitas: golpes que pedem senha ou Pix."),
    ("Nicolas", "Imagine uma mensagem dizendo que a conta vai ser bloqueada hoje e pedindo a senha. O sistema não sabe nada sobre ela. Então ele precisa perguntar."),
    ("Deivid", "Primeiro, a base de conhecimento. Ela guarda só dados: cada regra tem premissas, uma conclusão e uma fonte. Esta é a R1: se a mensagem pede senha e o contato não foi solicitado, é phishing."),
    ("Deivid", "Agora o sistema pergunta só o que a regra precisa. Aqui, duas respostas bastam. As outras três perguntas nem são feitas."),
    ("Deivid", "O motor avalia as premissas da esquerda para a direita. Se uma for falsa, ele para ali: a regra é falsa e nada mais é perguntado."),
    ("Deivid", "A inferência é para trás. Parte da ação recomendada, acha a regra que a conclui e busca os fatos que a sustentam. A ação exige phishing; phishing exige a R1 e os dois fatos dela."),
    ("Deivid", "Quando uma premissa é outra hipótese, o motor prova essa hipótese antes. Se o objetivo já está na cadeia, o ciclo para e o resultado é inconclusivo."),
    ("Lucas", "Agora, um caso sem resposta suficiente. Uma das respostas é interrogação. Desconhecido não vira não: a regra fica indeterminada e a ação fica inconclusiva."),
    ("Lucas", "A explicação mostra cada regra usada, o fato e o valor encontrado. Quem usa vê o caminho inteiro, e não só o resultado."),
    ("Lucas", "Os quinze testes automatizados cobrem isso: a resposta desconhecida, o ciclo, o fato repetido e a entrada inválida. Todos passam."),
    ("Lucas", "O sistema tem cinco regras SE-ENTÃO, cada uma com fonte. Faz inferência para trás e explica o caminho. É um protótipo didático: cobre os casos que as regras descrevem, e não todos os golpes possíveis."),
    ("Lucas", "Obrigado. Fontes: CERT.br, Febraban e Banco Central."),
]


def cena_codigo(arquivo, nome_ou_regra, tipo):
    if tipo == "regra":
        trecho, ini, fim = trecho_regra(arquivo, nome_ou_regra)
    elif tipo == "funcao":
        trecho, ini, fim = trecho_funcao(arquivo, nome_ou_regra)
    else:
        trecho, ini, fim = trecho_teste(arquivo, nome_ou_regra)
    return {"arquivo": arquivo, "ini": ini, "fim": fim, "linhas": trecho}


def visual_titulo():
    return '''<h1 class="rv" data-r="0">Triagem de mensagens suspeitas</h1>
        <div class="sub rv" data-r="1">Golpes digitais: o sistema pergunta, infere e explica</div>'''


def visual_mensagem():
    return '''<div class="bubble rv" data-r="0">Sua conta será bloqueada hoje. Confirme sua senha e o código que enviamos agora.</div>
        <div class="sub rv" data-r="1">O sistema não sabe nada ainda. Ele precisa perguntar.</div>'''


def visual_perguntas():
    linhas = [
        ("A mensagem pede senha, token ou código?", "sim"),
        ("Você não pediu este contato?", "sim"),
        ("Há link que não confere com o site oficial?", "não perguntado"),
        ("A mensagem exige ação imediata?", "não perguntado"),
        ("A mensagem pede transferência ou Pix?", "não perguntado"),
    ]
    corpo = ""
    for i, (q, r) in enumerate(linhas):
        classe = "sim" if r == "sim" else "off"
        corpo += f'<div class="row rv" data-r="{i}"><span>{html.escape(q)}</span><span class="badge {classe}">{r}</span></div>\n'
    return f'<h2 class="rv" data-r="0">Perguntas: só o que a regra precisa</h2>\n<div class="linhas">{corpo}</div>'


def visual_cadeia():
    # diagrama em fluxo normal (sem posição absoluta): sempre cabe na área útil
    return '''<div class="arvore">
          <div class="node objetivo rv" data-r="0">acao<small>nao_informar_dados</small></div>
          <div class="seta rv" data-r="1"></div>
          <div class="node regra rv" data-r="1">R4 · SE phishing = sim<small>ENTÃO acao</small></div>
          <div class="seta rv" data-r="2"></div>
          <div class="node objetivo rv" data-r="2">phishing<small>objetivo intermediário</small></div>
          <div class="seta rv" data-r="3"></div>
          <div class="node regra rv" data-r="3">R1 · SE senha = sim E nao_solicitado = sim<small>ENTÃO phishing</small></div>
          <div class="fatos">
            <div class="node fato rv" data-r="4">pede_senha_ou_codigo<small>sim</small></div>
            <div class="node fato rv" data-r="4">nao_solicitado<small>sim</small></div>
          </div>
        </div>'''


def visual_caso_b():
    return '''<div class="arvore">
          <div class="node objetivo indef rv" data-r="0">acao<small>inconclusiva</small></div>
          <div class="seta rv" data-r="1"></div>
          <div class="node regra indef rv" data-r="1">R1 · indeterminada<small>nao_solicitado = ?</small></div>
          <div class="seta rv" data-r="2"></div>
          <div class="node objetivo indef rv" data-r="2">phishing<small>inconclusiva</small></div>
          <div class="fatos">
            <div class="node fato rv" data-r="3">pede_senha_ou_codigo<small>sim</small></div>
            <div class="node fato indef rv" data-r="3">nao_solicitado<small>? desconhecido</small></div>
          </div>
        </div>'''


def visual_testes():
    itens = [
        "T1 ação confirmada perguntando só os fatos necessários",
        "T2 resposta '?' nunca vira 'não'",
        "T5 ciclo termina como inconclusivo",
        "T6 fato repetido é perguntado uma vez",
        "T7 fato falso refuta sem perguntar o resto",
        "Cobertura: R2, R4 e R5 usadas em testes",
        "Entrada inválida pede de novo",
        "RQ2 e RQ9 base separada, só biblioteca padrão",
    ]
    corpo = "".join(f'<div class="test rv" data-r="{i}">{html.escape(t)} · ok</div>' for i, t in enumerate(itens))
    return f'<h2 class="rv" data-r="0">15 testes automatizados</h2><div class="testes">{corpo}</div>'


def visual_fechamento():
    cartoes = [
        ("Regras", "5 regras SE-ENTÃO, cada uma com fonte citada", "var(--accent)"),
        ("Inferência", "Parte da ação e busca, para trás, só os fatos que a provam", "var(--sim)"),
        ("Explicação", "Mostra o rastro de cada regra e o fato que falta quando a resposta é '?'", "var(--duvida)"),
    ]
    corpo = "".join(
        f'<div class="cartao rv" data-r="{i}"><h2 style="color:{c}">{t}</h2><p>{html.escape(d)}</p></div>'
        for i, (t, d, c) in enumerate(cartoes)
    )
    return f'<div class="cartoes">{corpo}</div>'


def visual_fim():
    return '''<h1 class="rv" data-r="0" style="font-size:64px">Triagem de mensagens suspeitas</h1>
        <div class="sub rv" data-r="1">Protótipo didático de triagem de mensagens suspeitas.</div>
        <div class="sub rv" data-r="2" style="font-size:28px; margin-top:44px">Fontes: CERT.br · Febraban · Banco Central</div>'''


NARRACAO_DIR = pathlib.Path(__file__).resolve().parent.parent / "audio" / "out"


def duracao_da_fala(indice):
    """Duração real da narração gravada (audio/out/narracao.json), ou None se não existir."""
    import json
    arq = NARRACAO_DIR / "narracao.json"
    if not arq.exists():
        return None
    falas = json.loads(arq.read_text(encoding="utf-8"))["falas"]
    return falas[indice]["duracao"] if indice < len(falas) else None


def montar_cenas():
    cenas = []
    fonte = [
        ("visual", visual_titulo()),
        ("visual", visual_mensagem()),
        ("codigo", ("base.py", "R1", "regra")),
        ("visual", visual_perguntas()),
        ("codigo", ("motor.py", "_avaliar_regra", "funcao")),
        ("visual", visual_cadeia()),
        ("codigo", ("motor.py", "_provar", "funcao")),
        ("visual", visual_caso_b()),
        ("codigo", ("cli.py", "explicar", "funcao")),
        ("codigo", ("test_motor.py", "test_T2_resposta_desconhecida_nao_vira_nao", "teste")),
        ("visual", visual_fechamento()),
        ("visual", visual_fim()),
    ]
    for (locutor, texto), (tipo, dados) in zip(NARRACAO, fonte):
        if tipo == "visual":
            cena = {"tipo": "visual", "html": dados}
        else:
            arquivo, nome, modo = dados
            cena = {"tipo": "codigo", "codigo": cena_codigo(arquivo, nome, modo)}
        voz = duracao_da_fala(len(cenas))
        dur = max(DURACAO_MINIMA, round(voz + 0.8, 1)) if voz else duracao(texto)
        cena.update({"locutor": locutor, "texto": texto, "dur": dur, "voz": voz})
        cenas.append(cena)
    return cenas


def montar_html(cenas):
    inicio = 0.0
    secoes = []
    roteiro = []
    for i, c in enumerate(cenas):
        dur = c["dur"]
        if c["tipo"] == "visual":
            corpo = c["html"]
            cabecalho = ""
        else:
            cod = c["codigo"]
            linhas = "".join(
                f'<div class="cl" data-k="{k}"><span class="ln">{cod["ini"] + k}</span>{html.escape(l) or "&nbsp;"}</div>'
                for k, l in enumerate(cod["linhas"])
            )
            cabecalho = f'<div class="arq">{html.escape(cod["arquivo"])} · linhas {cod["ini"]}–{cod["fim"]}</div>'
            corpo = f'<div class="codigo" data-n="{len(cod["linhas"])}">{linhas}</div>'
        secoes.append(
            f'''      <section id="cena-{i}" class="clip cena" data-start="{inicio:.1f}" data-duration="{dur}" data-track-index="{i % 8}" data-n="{i}">
        {cabecalho}
        <div class="corpo">{corpo}</div>
        <div class="legenda" id="leg-{i}">{html.escape(c["texto"])}</div>
      </section>'''
        )
        roteiro.append((inicio, dur, c["locutor"], c["texto"], c.get("codigo")))
        inicio += dur
    total = round(inicio, 1)
    return total, secoes, roteiro


GSAP_SCRIPT = '''
      window.__timelines = window.__timelines || {};
      const tl = gsap.timeline({ paused: true });
      document.querySelectorAll("section.cena").forEach((sec) => {
        const ini = parseFloat(sec.dataset.start);
        const dur = parseFloat(sec.dataset.duration);
        const reveals = sec.querySelectorAll(".rv");
        const passo = Math.min(0.9, Math.max(0.25, (dur - 1.6) / Math.max(1, reveals.length)));
        reveals.forEach((el) => {
          const r = parseFloat(el.dataset.r || "0");
          tl.fromTo(el, { opacity: 0, y: 24 }, { opacity: 1, y: 0, duration: 0.5, ease: "power2.out" }, ini + 0.3 + r * passo);
        });
        const linhas = sec.querySelectorAll(".cl");
        if (linhas.length) {
          const pl = Math.min(0.55, Math.max(0.12, (dur - 1.6) / linhas.length));
          linhas.forEach((el) => {
            tl.fromTo(el, { opacity: 0.15 }, { opacity: 1, duration: 0.25 }, ini + 0.3 + parseFloat(el.dataset.k) * pl);
          });
        }
        tl.fromTo(sec.querySelector(".legenda"), { opacity: 0 }, { opacity: 1, duration: 0.4 }, ini + 0.1);
        tl.to(sec, { opacity: 1, duration: 0.01 }, ini);
      });
      window.__timelines["main"] = tl;
      tl.seek(0);
'''


def css():
    return '''
      :root {
        --ground: #0d1117; --panel: #161b22; --ink: #e6edf3; --muted: #8b949e;
        --sim: #3fb950; --nao: #f85149; --duvida: #d29922; --accent: #58a6ff;
        --font-display: "Helvetica Neue", Arial, sans-serif; --font-mono: "SF Mono", Menlo, monospace;
      }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1920px; height: 1080px; overflow: hidden; background: var(--ground); color: var(--ink); font-family: var(--font-display); }
      #root { position: relative; width: 1920px; height: 1080px; }
      .clip { position: absolute; inset: 0; }
      .cena { opacity: 1; }
      .corpo { position: absolute; top: 110px; left: 0; right: 0; height: 690px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; }
      h1 { font-size: 92px; font-weight: 700; letter-spacing: -0.03em; line-height: 1.05; }
      h2 { font-size: 60px; font-weight: 650; letter-spacing: -0.02em; }
      .sub { font-size: 36px; color: var(--muted); margin-top: 28px; }
      .bubble { width: 1080px; padding: 44px 52px; border-radius: 28px; background: #1f6feb22; border: 2px solid var(--accent); font-size: 44px; line-height: 1.35; text-align: left; }
      .linhas { display: flex; flex-direction: column; align-items: center; margin-top: 30px; }
      .row { display: flex; align-items: center; justify-content: space-between; width: 1300px; padding: 24px 34px; margin: 10px 0; background: var(--panel); border-radius: 18px; font-size: 38px; }
      .badge { font-family: var(--font-mono); font-size: 32px; font-weight: 700; padding: 8px 24px; border-radius: 12px; min-width: 150px; text-align: center; }
      .sim { background: var(--sim); color: #04260f; }
      .nao { background: var(--nao); color: #2d0503; }
      .off { background: #30363d; color: var(--muted); }
      .node { position: absolute; width: 440px; padding: 24px 28px; border-radius: 18px; background: var(--panel); border: 2px solid #30363d; font-size: 34px; text-align: center; }
      .node small { display: block; font-family: var(--font-mono); font-size: 24px; color: var(--muted); margin-top: 8px; }
      .node.fato { border-color: var(--accent); } .node.regra { border-color: #a371f7; } .node.objetivo { border-color: var(--sim); } .node.indef { border-color: var(--duvida); }
      svg.links { position: absolute; inset: 0; width: 1920px; height: 1080px; }
      svg.links line { stroke: #6e7681; stroke-width: 4; }
      .arq { position: absolute; top: 40px; left: 0; right: 0; text-align: center; font-family: var(--font-mono); font-size: 26px; color: var(--accent); }
      .codigo { width: 1760px; max-height: 640px; overflow: hidden; background: var(--panel); border-radius: 18px; padding: 26px 30px; font-family: var(--font-mono); font-size: 24px; line-height: 1.5; text-align: left; border: 2px solid #30363d; }
      .cl { white-space: pre-wrap; word-break: break-word; padding-left: 0; color: #c9d1d9; }
      .cl .ln { display: inline-block; width: 70px; color: #6e7681; }
      .testes { display: flex; flex-direction: column; align-items: flex-start; margin-top: 30px; }
      .test { font-family: var(--font-mono); font-size: 32px; margin: 8px 0; color: var(--sim); }
      .cartoes { display: flex; gap: 40px; }
      .arvore { display: flex; flex-direction: column; align-items: center; }
      .arvore .node { position: relative; width: 560px; padding: 14px 24px; font-size: 30px; }
      .arvore .node small { margin-top: 4px; font-size: 22px; }
      .seta { width: 4px; height: 18px; background: #6e7681; }
      .fatos { display: flex; gap: 60px; margin-top: 10px; }
      .fatos .node { width: 440px; padding: 14px 20px; font-size: 28px; }
      .cartao { width: 500px; height: 340px; padding: 40px; border-radius: 20px; background: var(--panel); text-align: left; display: flex; flex-direction: column; justify-content: center; }
      .cartao p { font-size: 34px; color: var(--muted); margin-top: 24px; line-height: 1.45; }
      .legenda { position: absolute; left: 150px; right: 150px; bottom: 50px; height: 170px; overflow: hidden; display: flex; align-items: center; justify-content: center; text-align: center; font-size: 34px; line-height: 1.4; color: var(--ink); background: rgba(13,17,23,0.92); border-radius: 18px; padding: 22px 36px; border: 1px solid #30363d; }
    '''


def trilha_sonora(roteiro, total):
    """Ambiente em toda a duração e um efeito no início de cada cena.

    Os arquivos vêm de audio/out (gerados por audio/sintese.py) e são copiados para
    video/assets pelo build.sh. Os tempos vêm do próprio roteiro, então o áudio segue o texto.
    """
    tags = [f'<audio id="ambiente" src="assets/ambiente-v2.wav" data-start="0" data-duration="{total}" '
            f'data-volume="0.35" data-fade-in="2" data-fade-out="3"></audio>']
    for i, (inicio, dur, _loc, _texto, cod) in enumerate(roteiro):
        voz = duracao_da_fala(i)
        if voz:  # o slot segue a duração real do arquivo de fala
            tags.append(f'<audio id="narracao-{i}" src="assets/narracao-{i + 1:02d}.wav" data-start="{inicio + 0.3:.1f}" '
                        f'data-duration="{voz:.2f}" data-volume="1"></audio>')
        efeito, duracao_efeito = ("clique-v2.wav", 0.12) if cod else ("whoosh-v2.wav", 1.4)
        tags.append(f'<audio id="efeito-{i}" src="assets/{efeito}" data-start="{inicio:.1f}" '
                    f'data-duration="{duracao_efeito:.2f}" data-volume="0.5"></audio>')
    return "\n".join(tags)


def main():
    cenas = montar_cenas()
    total, secoes, roteiro = montar_html(cenas)
    documento = f'''<!doctype html>
<html lang="pt-BR" data-resolution="landscape">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>{css()}</style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{total}" data-width="1920" data-height="1080">
{chr(10).join(secoes)}
{trilha_sonora(roteiro, total)}
    </div>
    <script>{GSAP_SCRIPT}</script>
  </body>
</html>
'''
    (pathlib.Path(__file__).parent / "index.html").write_text(documento, encoding="utf-8")

    linhas = ["# Roteiro de narração e tempos", "", f"Duração total: {total:.1f} s. Ritmo de referência: {PALAVRAS_POR_SEGUNDO} palavras por segundo, mais {FOLGA} s de folga por cena.", ""]
    linhas += ["| Início | Duração | Locutor | Texto narrado |", "|---|---|---|---|"]
    for inicio, dur, loc, texto, _ in roteiro:
        linhas.append(f"| {inicio:05.1f} s | {dur:.1f} s | {loc} | {texto} |")
    linhas += ["", "## Trechos de código mostrados", ""]
    for inicio, dur, loc, texto, cod in roteiro:
        if cod:
            linhas.append(f"### {inicio:05.1f} s · {cod['arquivo']} · linhas {cod['ini']}–{cod['fim']}")
            linhas.append("```python")
            linhas += [f"{cod['ini'] + k:>4}  {l}" for k, l in enumerate(cod["linhas"])]
            linhas.append("```")
            linhas.append("")
    (PROJETO / "roteiro-narracao.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print(f"total {total:.1f}s, cenas {len(cenas)}")


if __name__ == "__main__":
    main()
