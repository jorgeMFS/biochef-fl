# Comparação de frameworks de FL

Preenche isto à medida que testas cada framework (ver `fl-frameworks.md` para a grelha e para como correr um ensaio). O objetivo não é um resumo bibliográfico mas um veredito prático: cada linha deve ser sustentada por algo que correste mesmo ou leste na documentação, com a experiência registada em `experiments/`. Termina com uma recomendação.

## Pontuações

Pontua cada célula. Escala sugerida: ++ forte, + adequado, ~ parcial/incerto, - fraco/ausente. Acrescenta uma nota com a evidência.

| Critério | Flower | NVFlare | PySyft | OpenFL | Notas |
|---|---|---|---|---|---|
| **Implantabilidade em TRE** (só saída? pegada? amigável a contentores? sem portas de entrada?) | **+**: execução distribuída simples, cliente inicia ligação a `8080`; pegada leve. Evidência apenas local para a comparação, sem configuração de TRE final. | **~**: componentes do cliente podem comunicar por saída/loopback e o POC tem 8002/8003, mas há múltiplos processos, provisionamento e testes remotos/TRE pendentes. | **~** não testado nesta fase | **~** não testado nesta fase | o critério mais importante |
| **Privacidade diferencial** (incluída? que mecanismo?) | **~**: suporte depende de extensões/plugins da versão 1.7.0; não ativado nem medido neste teste | **+**: a versão 2.9.1 tem componentes/filtros de DP, mas não foram configurados nem foi testada contabilização epsilon | - não testado | - não testado | |
| **Agregação segura** (incluída? que protocolo? tratamento de quedas?) | **~**: a execução usada não ativa masking/secure aggregation; a semântica da versão precisa de teste dedicado | **~**: NVFlare disponibiliza opções como cifra homomórfica/agregação segura, mas não foram ativadas; falhas de participante e thresholds são por testar | - não testado | - não testado | |
| **Integração com o Agente BioChef** (o Agente consegue conduzi-lo? encaixe em Python?) | **+**: API Python, estratégia simples e poucos processos tornam a integração leve | **+**: API Python/FedJob forte, mas job, controlador, persistor e startup kits aumentam o encaixe | - não testado | - não testado | |
| **Encaixe com registry / artefactos assinados** (funciona com trainers e modelos obtidos por OCI?) | **~**: o modelo pode ser encapsulado pelo Agente, mas nenhum fluxo OCI foi testado | **~**: não foi testada integração OCI; o formato FedJob/persistor é adicional ao artefacto assinável | - não testado | - não testado | |
| **Encaixe com identidade / OIDC** (funciona com LS-AAI?) | **-**: não integrado nem testado neste protocolo | **-**: não integrado nem testado neste protocolo | - não testado | - não testado | ambos requerem trabalho explícito no Agente/Coordination Hub |
| **Modelos tabulares** (Random Forest, XGBoost) | **+**: frameworks/estratégias Python podem encapsular treino tabular, mas não foi testado nesta experiência | **+**: NVFlare anuncia suporte a modelos tabulares; não testado localmente | **~** continuidade do projeto anterior, não avaliado nesta matriz | **~** não testado nesta fase | o PySyft é a base atual do grupo (fed_rf) |
| **Modelos de gradientes / profundos** | **++**: LSTM executado localmente com equivalência numérica ao NVFlare | **++**: LSTM executado localmente com equivalência numérica ao Flower | - não testado | - não testado | |
| **Maturidade** (documentação, atividade da licença) | **+**: instalação simples, comunidade ativa e execução reproduzível | **+**: implementação de grau de produção, aprovisionamento completo e boa cobertura de privacidade; operação mais complexa | **~** não testado nesta fase | **~** não testado nesta fase | licença e suporte empresarial devem ser confirmados no final |

## Notas por framework

### Flower
- Experimentado: FedAvg local com LSTM e três clientes para Portugal, Macau e Guangdong; execução remota de três máquinas usada como referência. O treino chegou a reproduzir os números do NVFlare com diferença submilésimal na seed 1.
- Evidência / link da experiência: `experiments/02-nvflare-flower-comparison/`
- Limitações observadas: instabilidade de worker Ray numa execução local com seed 42; o problema não foi reproduzido nas execuções remotas Flower.

### NVFlare
- Experimentado: FedJob, persistor PyTorch, ScriptRunner externo e controller FedAvg local com três clientes.
- Evidência / link da experiência: `experiments/02-nvflare-flower-comparison/`
- Limitações observadas: ~5.9x mais tempo wall-clock que Flower nesta máquina; execução remota/TRE, secure aggregation e DP ainda não validados.

### PySyft
- Experimentado:
- Evidência / link da experiência:

### OpenFL
- Experimentado:
- Evidência / link da experiência:

## Recomendação

Indica a decisão e o raciocínio, julgado contra os critérios acima por ordem de prioridade (implantabilidade em TRE primeiro).

- **Decisão provisória:** manter Flower como candidato principal enquanto a integração e os testes TRE forem completados.
- **Porquê:** Flower atingiu equivalência numérica com NVFlare neste protocolo LSTM, teve menor custo de execução/código local e uma arquitetura mais simples para ligação cliente-servidor. NVFlare tem uma pegada operacional maior e ainda não foi validado numa execução remota ou num TRE. O suporte declarado de NVFlare a DP e agregação segura é uma vantagem, mas não foi ativado nesta experiência e, por isso, não pode justificar sozinho a decisão.
- **O que falta validar antes da decisão final:** fluxo remoto real de cada framework; endereço/porta e direção das ligações; execução com apenas ligações de saída; comportamento de TLS e certificados; secure aggregation com abandono de cliente; DP-SGD/filtros, clipping e epsilon; integração OCI; identidade LS-AAI; execução com modelos tabulares.
- **O que isto implica para a arquitetura:** preservar uma interface do Agente independente do framework e manter FedAvg, pesos, métricas, DP e agregação segura como componentes substituíveis. O Agente pode primeiro encapsular o caminho mais simples (Flower), mas a interface do executor deve continuar suficientemente abstrata para substituir NVFlare ou implementar o mínimo interno caso os testes de TRE bloqueiem ambos.
