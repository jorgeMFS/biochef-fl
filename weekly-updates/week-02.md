# Semana 02 (2026-10-10 a 2026-10-16)

## Feito esta semana

- Terminei a leitura do artigo FedAvg.
- Li os READMEs do `Biochef` (editor) e do `biochef-agent`, e o guia de instalação do editor, para perceber como os componentes se ligam.
- Recebi o artigo, a sandbox (dados e código Flower) e as instruções para as próximas experiências.
- Comecei a ler o artigo enviado (previsão epidemiológica federada com Flower e LSTM).

## Lido / aprendido

- FedAvg: cada cliente treina localmente a partir do mesmo modelo global e o servidor faz a média ponderada pelo número de exemplos. Mais computação local (`E` maior, `B` menor) reduz as rondas de comunicação, mas os ganhos diminuem com dados non-IID.
- Componentes do BioChef: o editor (workflows e WebAssembly), o agente (executa workflows via Snakemake) e os repositórios de receitas e hub. O roadmap do agente aponta para um modo silo, com política de privacidade e orçamento.
- Noções básicas de privacidade diferencial: orçamento `ε` e `δ`, limitação (clipping) mais ruído, DP-SGD.
- Artigo enviado: LSTM de 2 camadas, FedAvg com Flower, três clientes e um servidor de agregação, comparação entre treino local, centralizado e federado.

## Testado / experiências

- Ainda não instalei o Flower nem corri o exemplo. A tarefa foi recebida esta semana e arranca na próxima.

## Bloqueado / questões para os orientadores

- Setup do BioChef: que componentes devo levantar primeiro? É preciso acesso ao registry ou existe uma instância de desenvolvimento? Basta seguir os READMEs do editor e do agente, ou há passos adicionais? Qual é a ordem de instalação dos componentes?

## Plano para a próxima semana

- Ler com atenção as instruções da sandbox e o artigo enviado (métodos, hardware e resultados).
- Correr o exemplo localmente com os dados da sandbox, antes de passar para as três máquinas.
- Instalar o Flower nas três máquinas e correr o exemplo, depois de confirmar o acesso e as regras de instalação.

- Se houver tempo:
    - Configurar o BioChef localmente e levantar o editor e o agente, para perceber como funcionam.
    - Ler a introdução à privacidade diferencial e o artigo de agregação segura (lista de leitura, secção B).
    - Instalar o fed_rf e o NVFlare localmente, e correr os quickstarts de cada um (ver `docs/links.md`).