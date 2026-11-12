# Registo dos resultados da experiência com Flower

Este documento apresenta o objetivo, o protocolo, os resultados e as
limitações da experiência federada. A documentação geral do código e das
instruções de execução encontra-se em `README.md`.

## Questão

O estudo avalia o comportamento do F-LSTM federado na previsão de casos de
COVID-19 e compara o efeito da taxa de aprendizagem, do estado do otimizador
Adam e da política do scaler em Portugal, Guangdong e Macau.

## Montagem

- Framework: Flower 1.7.0.
- Modelo: LSTM em PyTorch.
- Otimizador: Adam.
- Treino: full-batch.
- Clientes federados: Portugal, Guangdong e Macau.
- Período dos dados: 2021-11-24 a 2023-01-08.
- Treino: até 2022-10-17.
- Teste: a partir de 2022-10-18.
- Média móvel: sete dias.
- Janela de entrada: sete dias.
- Rondas federadas: 200.
- Seeds: 1, 2 e 3 por configuração.

Foram concluídas 18 execuções, correspondentes a seis configurações e três
seeds:

1. A: `lr=0.01`, estado do Adam reiniciado, scaler ajustado à série completa.
2. B: `lr=0.003`, estado do Adam reiniciado, scaler ajustado à série completa.
3. C: `lr=0.003`, estado do Adam persistente, scaler ajustado à série
   completa.
4. D: configuração A com `--train-only-scaler`.
5. E: configuração B com `--train-only-scaler`.
6. F: configuração C com `--train-only-scaler`.

Os resultados brutos foram organizados por configuração e seed, com os
artefactos do servidor e dos clientes separados. Durante a análise foram
gerados CSVs de resumo e tabelas agregadas através de
`summarize_results.py` e `analyze_results.py`. Esses CSVs foram utilizados
para produzir os resultados abaixo, mas não fazem parte do registo
versionado, por serem derivados de dados reais.

## O que fiz

Para cada configuração:

1. foi iniciado o servidor Flower com `--paper`, 200 rondas e a configuração
   de taxa de aprendizagem, estado do Adam e scaler correspondente;
2. foram ligados três clientes, um por região, com a mesma configuração experimental e seeds derivadas da seed principal;
3. foram guardados os resultados do servidor e dos clientes separadamente;
4. foram calculadas as métricas globais e regionais para as 200 rondas;
5. foram comparados o resultado final, o melhor resultado observado e as
   curvas de training loss entre as três seeds.

Os CSVs de resumo foram gerados localmente com:

```bash
python summarize_results.py --output-dir processed_results raw_results/*/seed_*
python analyze_results.py processed_results --output-dir analysis_results
```

Os CSVs não fazem parte do registo versionado, mas foram utilizados para
produzir as tabelas e conclusões deste documento.

## Resultado

Os valores seguintes apresentam a média e o desvio-padrão entre as três seeds.
“Melhor RMSE” corresponde ao menor RMSE de teste observado ao longo das 200
rondas; “RMSE final” corresponde ao valor da ronda 200.

| Configuração | Ronda do melhor RMSE (média) | Melhor RMSE | RMSE final |
|---|---:|---:|---:|
| A | 70,7 | 354,33 ± 61,49 | 593,48 ± 386,62 |
| B | 120,0 | 192,18 ± 20,66 | 231,34 ± 5,03 |
| C | 200,0 | **112,15 ± 11,48** | **112,15 ± 11,48** |
| D | 20,7 | 454,81 ± 14,78 | 910,53 ± 210,38 |
| E | 86,3 | 412,99 ± 3,73 | 873,85 ± 55,02 |
| F | 184,3 | 429,87 ± 6,59 | 431,18 ± 6,72 |

A configuração C obteve o melhor resultado global na ronda 200. Entre as
configurações com scaler ajustado apenas ao treino, F foi a melhor, embora
tenha permanecido substancialmente abaixo de C.

### Métricas regionais finais do F-LSTM

A tabela seguinte apresenta o RMSE na ronda 200, como média ± desvio-padrão
das três seeds, para todas as configurações:

| Configuração | Portugal | Macau | Guangdong |
|---|---:|---:|---:|
| A | 1435,42 ± 1242,43 | 15,79 ± 2,51 | 329,24 ± 80,07 |
| B | 403,66 ± 4,18 | 14,07 ± 0,70 | 276,30 ± 18,58 |
| C | **157,41 ± 13,27** | **9,62 ± 0,65** | **169,41 ± 20,90** |
| D | 1611,66 ± 608,06 | 24,05 ± 2,00 | 1095,87 ± 21,34 |
| E | 1610,83 ± 169,30 | 11,76 ± 0,68 | 998,96 ± 6,69 |
| F | 170,23 ± 24,40 | 17,78 ± 0,39 | 1105,54 ± 14,83 |

As métricas regionais completas, incluindo MAE, SMAPE, nRMSE e nMAE, foram
calculadas durante a análise. 

Para a comparação entre modelos na configuração C, os resultados na ronda 200
foram:

| Região | Modelo | RMSE médio ± desvio-padrão | MAE médio ± desvio-padrão | SMAPE médio |
|---|---|---:|---:|---:|
| Portugal | LSTM | 2660,94 ± 1702,23 | 2649,81 ± 1709,75 | 63,56 |
| Portugal | C-LSTM | 563,46 ± 387,58 | 522,38 ± 406,54 | 31,01 |
| Portugal | FL-LSTM | **157,41 ± 13,27** | **112,01 ± 9,76** | **11,52** |
| Macau | LSTM | 14,30 ± 1,23 | 7,93 ± 0,63 | 54,41 |
| Macau | C-LSTM | 14,76 ± 0,44 | 8,96 ± 0,60 | 55,65 |
| Macau | FL-LSTM | **9,62 ± 0,65** | **5,32 ± 0,53** | **43,74** |
| Guangdong | LSTM | 987,21 ± 440,33 | 778,50 ± 374,69 | 63,37 |
| Guangdong | C-LSTM | 294,73 ± 10,29 | 236,48 ± 13,45 | 16,85 |
| Guangdong | FL-LSTM | **169,41 ± 20,90** | **126,15 ± 15,71** | **8,47** |

Esta comparação é apresentada para a ronda 200. A seleção de um modelo
anterior deve ser interpretada em conjunto com a análise da instabilidade
descrita na secção seguinte.

### Oscilações do training loss

O artigo descreve uma oscilação intensa depois da ronda 71. Nas execuções
realizadas, o padrão observado foi diferente: nas configurações A, B, D e E
as curvas apresentam oscilações aproximadamente periódicas, com picos
repetidos e amplitude variável. Não foi identificada uma única ronda de
instabilidade aplicável a todas as configurações, seeds e regiões.

As estimativas visuais do início das oscilações são:

| Configuração | Região | Início aproximado |
|---|---|---:|
| A | Guangdong e Macau | ronda 10 |
| A | Portugal | ronda 17 |
| B | Guangdong | possivelmente ronda 10 |
| B | Macau e Portugal | rondas 30--37 |
| C | Todas | não observado até à ronda 200 |
| D | Todas | ronda 10 |
| E | Todas | ronda 25 |
| F | Todas | não observado até à ronda 200 |

Estas rondas são estimativas obtidas por inspeção visual das curvas de
training loss para estas 3 seeds específicas. No entanto, não representam uma deteção automática nem devem ser tratadas
como valores exatos, pois os valores podem variar bastante entre as diferentes seeds. 

A configuração C e a configuração F não apresentaram
instabilidade clara até à ronda 200, o que é consistente com a persistência
do estado do otimizador Adam.

Numa execução exploratória anterior, com `lr=0.003`, estado do Adam reiniciado
e seed 42, a oscilação pareceu começar por volta da ronda 32. Essa execução
não pertence às 18 execuções finais e é mencionada apenas como observação
adicional.

Para comparação direta com o artigo, também foi realizada uma análise
secundária usando a regra fixa da ronda 71 e selecionando o menor training
loss até esse ponto. Essa análise não é usada para definir o resultado
principal desta experiência, uma vez que a inspeção das execuções finais
indica padrões de instabilidade diferentes.

## Conclusão

Dentro deste protocolo e desta versão dos dados, a configuração C apresentou
o melhor desempenho: `lr=0.003`, estado persistente do Adam e scaler ajustado à
série completa. O `lr=0.01` mostrou maior instabilidade e dependência da seed.
O scaler ajustado apenas aos dados de treino é metodologicamente adequado para
a tese, mas apresentou erros maiores, sobretudo em Guangdong, porque o surto
no período de teste está fora do intervalo observado no treino.

Os resultados reproduzem o protocolo implementado, mas não constituem uma
reprodução numérica exata do artigo. A série disponível para Guangdong tem
magnitude inferior à da Figura 4 do artigo e uma curva diferente no período
de teste. Os dados não foram multiplicados nem alterados para forçar
concordância.

Uma comparação numérica exata com a Tabela 3 e com as Figuras 4(a) e 4(b)
exigiria a versão original dos dados utilizada pelos autores, assim como a seed original e outras variáveis e detalhes não presentes no artigo original.
