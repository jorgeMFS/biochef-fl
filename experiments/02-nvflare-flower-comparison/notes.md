# Registo da comparação Flower/NVFlare

Este documento complementa `table.md` e `README.md`.

## Questão

O NVFlare consegue reproduzir o mesmo FedAvg do LSTM configurado no Flower,
com o mesmo modelo, dados, scaler, seed e protocolo de treino, e quais são as
diferenças práticas relevantes para o BioChef?

## Montagem

- Sistema: WSL2 Ubuntu 22.04.5 LTS, CPU AMD Ryzen 5 5600U, 16 GB RAM.
- Python: 3.10.12.
- Flower: 1.7.0.
- NVFlare: 2.9.1.
- PyTorch: 2.14.1.
- Modelo: LSTM com 64 unidades ocultas, 2 camadas, dropout 0.
- Dados: Portugal, Macau e Guangdong.
- Protocolo: 200 rondas, 1 época local por ronda, Adam com
  `lr=0.003`, FedAvg ponderado pelo número de exemplos.
- Seed principal: 1.
- Período: 2021-11-24 a 2023-01-08.
- Split: treino até 2022-10-17; teste a partir de 2022-10-18.
- Média móvel: janela 7; Portugal usa duas suavizações.
- Window: 7.
- Scalers: ajustados apenas na divisão de treino de cada região.

Os scripts `flower_main.py` e `nvflare_main.py` implementam o mesmo protocolo
de forma independente. Para cada métrica de teste, a seleção da melhor ronda
é apenas descritiva.

## O que fiz

1. Executei uma comparação local primária de 200 rondas com seed 1 no Flower.
2. Executei uma comparação local primária equivalente no NVFlare.
3. Registei o melhor RMSE, MAE e SMAPE de teste e os valores da ronda 200.
4. Medi tempo real, tempo de utilizador e tempo de sistema.
5. Registei o tamanho de código dos scripts após formatação com Black.
6. Observei processos e sockets locais com `ss -tnlp`.
7. Mantive execuções remotas de referência do Flower e uma execução adicional
   com seed 42 como contexto de estabilidade.

## Resultados

Na seed 1, ambos os frameworks atingiram a melhor RMSE de teste na ronda 164.
A diferença entre o melhor RMSE foi inferior a 0.00007% relativamente ao
Flower. Na ronda 200, a diferença foi inferior a 0.00009%. Os resultados
detalhados estão em `table.md`.

O Flower terminou em aproximadamente 148 segundos. O NVFlare terminou em
aproximadamente 874 segundos. O maior custo observado no NVFlare não foi
explicado por profiling; hipóteses consistentes com a arquitetura incluem
processos externos, troca de tarefas, serialização e persistência.

### Estabilidade

Na seed 42, o NVFlare concluiu as 200 rondas. Uma execução local do Flower
sofreu instabilidade de um worker Ray por volta da ronda 108 e terminou sem
produção comparável à execução principal. Execuções remotas de Flower em três
máquinas concluíram ambas as seeds limpas. Isto indica que o problema local
da seed 42 foi mais provavelmente um artefacto de worker/sandbox do que uma
diferença do FedAvg, mas a causa não foi isolada.

### Rede

Na observação local:

- Flower: ligador do servidor em `*:8080`; os clientes iniciam uma ligação
  TCP de saída para o servidor.
- NVFlare POC/simulador: servidor em `8002`; componentes locais do cliente
  usam também loopback para comunicação entre processos.
- A submissão POC de trabalho requer configuração/administração NVFlare e
  certificados gerados pelo aprovisionamento.

Sem teste entre três máquinas ou dentro de um TRE real, não é possível
garantir que a implantação suporta apenas egressos do silo.

### Pesos e privacidade

Nesta configuração simples, o servidor executa FedAvg em texto simples:

- o servidor recebe atualizações individuais de parâmetros dos clientes;
- o servidor pode agregá-las para produzir o modelo global;
- não há clipping DP, ruído DP, secure aggregation ou thresholding ativado.

Os dois frameworks oferecem componentes de privacidade noutros modos:

- Flower expõe extensões e plugins de secure aggregation/DP, mas o mecanismo e o custo operacional dependem da versão e da estratégia escolhida. Na versão 1.7.0, embora mecanismos como Differential Privacy e Secure Aggregation já fossem concebíveis por meio de implementações customizadas ou experimentais, optei por não ativá-los nesta experiência para manter a comparação direta com o NVFlare. Em versões posteriores do Flower, o suporte nativo para Differential Privacy e Secure Aggregation foi aprimorado, permitindo uma integração mais direta e eficiente desses recursos.
- NVFlare fornece componentes de filtros DP e cifra homomórfica/agregação segura em alguns modos de implantação. Estes componentes não foram ativados nesta experiência.

Nenhum framework foi avaliado com:

- abandono de cliente sob secure aggregation;
- threshold mínimo de participantes;
- orçamento epsilon;
- auditoria formal de fuga;
- TLS customizado ou integração com identidade.

## Conclusão preliminar

Os dois frameworks são numérica e algoritmicamente equivalentes neste
experimento. O NVFlare produziu a mesma solução com mais código local e
maior custo de execução, mas tem uma pegada operacional mais pesada e
componentes de privacidade/provisionamento mais integrados.

O Flower é mais simples de integrar e de executar localmente, mas a robustez
de uma execução distribuída depende da infraestrutura/worker. O NVFlare
necessita de validação remota antes de ser escolhido para TRE.

Ainda não existe uma recomendação final de encapsulamento. Esta decisão exige
validar no TRE: alcance de portas, apenas saída, secure aggregation,
differential privacy, integração OIDC/registry e operação com artefactos
assinados.
