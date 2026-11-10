"""Spec do vídeo de triagem de mensagens, para o template showcode."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build_video as bv  # cenas visuais já prontas no projeto

PROJETO = str(pathlib.Path(__file__).resolve().parent.parent)

CODIGO = {
    2: {"arquivo": "base.py", "tipo": "regra", "nome": "R1"},
    4: {"arquivo": "motor.py", "tipo": "funcao", "nome": "_avaliar_regra"},
    6: {"arquivo": "motor.py", "tipo": "funcao", "nome": "_provar"},
    8: {"arquivo": "cli.py", "tipo": "funcao", "nome": "explicar"},
    9: {"arquivo": "test_motor.py", "tipo": "teste", "nome": "test_T2_resposta_desconhecida_nao_vira_nao"},
}
VISUAIS = {
    1: bv.visual_mensagem(), 3: bv.visual_perguntas(), 5: bv.visual_cadeia(),
    7: bv.visual_caso_b(), 10: bv.visual_testes(), 11: bv.visual_fechamento(), 12: bv.visual_fim(),
}

SPEC = {
    "projeto": PROJETO,
    "transparente": False,
    "cenas": [],
}
for i, (locutor, texto) in enumerate(bv.NARRACAO):
    n = i + 1
    cena = {"locutor": locutor, "texto": texto}
    if n in CODIGO:
        cena["codigo"] = CODIGO[n]
    else:
        cena["html"] = VISUAIS.get(n, bv.visual_titulo())
    SPEC["cenas"].append(cena)
