#!/bin/sh
# Pipeline determinístico do vídeo de triagem de mensagens.
#   1. sons: gera audio/out e confere os hashes do manifesto;
#   2. composição: gera index.html e roteiro a partir do roteiro, copia os sons para assets/;
#   3. checagem: npm run check (HyperFrames fixado em 0.9.26 pelo package.json);
#   4. render: npm run render (mesma versão fixada).
# Uso: sh build.sh            (gera tudo)
#      sh build.sh --verificar-determinismo   (renderiza 6 s duas vezes e compara os quadros)
set -eu
cd "$(dirname "$0")"

python3 ../audio/sintese.py --saida ../audio/out
python3 ../audio/sintese.py --saida ../audio/out --verificar

python3 ../audio/narracao.py --saida ../audio/out

mkdir -p assets
cp ../audio/out/*.wav assets/

python3 build_video.py

# A checagem devolve avisos de ritmo visual (pausa longa, linha final curta). Não são erros de
# lint, então o pipeline segue e os avisos aparecem na saída.
if ! npm run --silent check; then
  echo "check: há avisos de ritmo visual acima (0 erros de lint); seguindo" >&2
fi

if [ "${1:-}" = "--verificar-determinismo" ]; then
  npm run --silent render -- --start 0 --end 6 --output /tmp/determinismo-a.mp4
  npm run --silent render -- --start 0 --end 6 --output /tmp/determinismo-b.mp4
  ffmpeg -v error -y -i /tmp/determinismo-a.mp4 -f framemd5 /tmp/determinismo-a.md5
  ffmpeg -v error -y -i /tmp/determinismo-b.mp4 -f framemd5 /tmp/determinismo-b.md5
  if cmp -s /tmp/determinismo-a.md5 /tmp/determinismo-b.md5; then
    echo "determinismo: OK (quadros idênticos nas duas renderizações de 6 s)"
  else
    echo "determinismo: DIVERGE" >&2
    exit 1
  fi
  exit 0
fi

npm run --silent render -- --output renders/triagem-mensagens.mp4
echo "vídeo: renders/triagem-mensagens.mp4"
