# Comparação de frameworks de FL

Preenche isto à medida que testas cada framework (ver `fl-frameworks.md` para a grelha e para como correr um ensaio). O objetivo não é um resumo bibliográfico mas um veredito prático: cada linha deve ser sustentada por algo que correste mesmo ou leste na documentação, com a experiência registada em `experiments/`. Termina com uma recomendação.

## Pontuações

Pontua cada célula. Escala sugerida: ++ forte, + adequado, ~ parcial/incerto, - fraco/ausente. Acrescenta uma nota com a evidência.

| Critério | Flower | NVFlare | PySyft | OpenFL | Notas |
|---|---|---|---|---|---|
| **Implantabilidade em TRE** (só saída? pegada? amigável a contentores? sem portas de entrada?) | | | | | o critério mais importante |
| **Privacidade diferencial** (incluída? que mecanismo?) | | | | | |
| **Agregação segura** (incluída? que protocolo? tratamento de quedas?) | | | | | |
| **Integração com o Agente BioChef** (o Agente consegue conduzi-lo? encaixe em Python?) | | | | | |
| **Encaixe com registry / artefactos assinados** (funciona com trainers e modelos obtidos por OCI?) | | | | | |
| **Encaixe com identidade / OIDC** (funciona com LS-AAI?) | | | | | |
| **Modelos tabulares** (Random Forest, XGBoost) | | | | | o PySyft é a base atual do grupo (fed_rf) |
| **Modelos de gradientes / profundos** | | | | | |
| **Maturidade** (documentação, atividade, licença) | | | | | |

## Notas por framework

### Flower
- Experimentado: (que exemplo, o que funcionou, o que não funcionou)
- Evidência / link da experiência:

### NVFlare
- Experimentado:
- Evidência / link da experiência:

### PySyft
- Experimentado:
- Evidência / link da experiência:

### OpenFL
- Experimentado:
- Evidência / link da experiência:

## Recomendação

Indica a decisão e o raciocínio, julgado contra os critérios acima por ordem de prioridade (implantabilidade em TRE primeiro).

- **Decisão:** encapsular [framework X] / construir de raiz no Agente.
- **Porquê:**
- **O que isto implica para a arquitetura:** (ex.: o quão modular tem de ser a estratégia do Agregador; de onde vêm a DP e a agregação segura; o que o Agente tem de encapsular ou implementar.)
