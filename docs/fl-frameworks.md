# Frameworks de FL a avaliar

**Objetivo:** decidir se a camada de FL do BioChef deve encapsular um framework existente ou ser implementada de raiz no Agente. Para decidir, instala cada framework, corre um pequeno exemplo federado (por exemplo, um FedAvg de dois clientes sobre um conjunto de dados tabular pequeno), e pontua-o contra a grelha abaixo.

## Frameworks

- **Flower (flower.ai).** Agnóstico ao framework, primeiro em Python, com estratégias de agregação personalizadas fáceis de escrever, e comunidade grande. Forte candidato quando é preciso agregação personalizada. Começa pelo quickstart e por um FedAvg de dois clientes.
- **NVFlare (NVIDIA FLARE).** De grau de produção, usado em saúde, com aprovisionamento e um modelo de administração, e com privacidade diferencial e agregação segura já incluídas (incluindo cifra homomórfica). Mais pesado de operar. Experimenta um exemplo incluído mais o filtro de DP.
- **PySyft (OpenMined).** Centrado nos dados e orientado à governação; já usado no trabalho de FL anterior do grupo (Cotorobai). Útil para continuidade. Experimenta um exemplo de execução remota.
- **OpenFL (Intel).** Modelo agregador-colaborador dirigido a saúde e a cenários do tipo TRE. Experimenta o exemplo de PyTorch ou Keras.
- **FATE** (opcional). Industrial e muito pesado; regista-o por completude, mas é provavelmente demasiado pesado para um Agente leve de TRE.

## Grelha (pontua cada framework)

1. **Implantabilidade em TRE.** Consegue um site correr só de saída (consulta o agregador, sem portas de entrada)? Que pegada? É amigável a contentores? É o que mais importa para implantação real em TRE.
2. **Privacidade.** Tem privacidade diferencial incluída? Agregação segura? De que tipo?
3. **Integração com o BioChef.** Pode ser conduzido pelo Agente BioChef? Compatível com artefactos assinados no registry OCI? Funciona com LS-AAI / OIDC?
4. **Suporte a modelos.** Modelos tabulares (Random Forest, XGBoost) e modelos baseados em gradientes ou profundos?
5. **Maturidade.** Qualidade da documentação, atividade do projeto, e licença.

## Output

Uma tabela de comparação ao longo da grelha, mais uma recomendação clara (encapsular o framework X, ou construir de raiz) com o raciocínio. Isto alimenta diretamente o capítulo de arquitetura e o plano da tese, e é a primeira decisão de arquitetura real do trabalho.
