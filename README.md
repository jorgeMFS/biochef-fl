# BioChef: Federated Learning (pré-tese de mestrado)

Núcleo de trabalho da pré-tese de mestrado sobre a camada de federated learning (FL) do BioChef.
Reúne o que ler, o que testar, a arquitetura alvo, e o registo de progresso semanal.

**Aluno:** Rafael Chuva, MEIC-A, Instituto Superior Técnico
**Orientadores:** Ana Teresa Freitas (IST / INESC-ID), Jorge Miguel Silva (U. Aveiro / IEETA)

## O projeto num parágrafo

O BioChef é uma plataforma para analisar dados sensíveis (genómicos e de saúde) mantendo esses dados sob o controlo da instituição que os detém. A parte de execução de workflows já existe: as ferramentas correm no browser (WebAssembly) ou num Agente local, e os dados nunca têm de se mover. A **camada de federated learning** (treinar modelos entre vários sites que detêm dados, sem centralizar os dados) está desenhada na arquitetura mas **ainda não implementada**. Construir essa camada é o objeto desta dissertação.

## Objetivo da fase de pré-tese

Perceber o terreno, depois propor a abordagem. Em concreto:

1. Aprender os fundamentos de federated learning e de Trusted Research Environments (TRE).
2. Perceber a arquitetura do BioChef e a plataforma existente (lê `docs/architecture.md` de fio a pavio).
3. Instalar e testar os principais frameworks de FL (Flower, NVFlare, e outros) e decidir se a camada de FL deve encapsular um deles ou ser construída de raiz. Regista a comparação em `docs/framework-comparison.md`.
4. Estudar a arquitetura alvo de FL e, onde for útil, prototipar pequenas peças (regista experiências em `experiments/`).
5. Produzir a pré-tese escrita: um estado da arte, uma abordagem proposta, e um plano de trabalho.

## Mapa do repositório

| Caminho | O que é |
|---|---|
| `docs/architecture.md` | **Começa aqui.** A arquitetura autónoma: o sistema inteiro, depois a camada de FL, depois os componentes que vais construir. Lê de início ao fim. |
| `docs/reading-list.md` | Artigos e documentos a ler, cada um com DOI/link e o que retirar dele. |
| `docs/links.md` | **Coisas para ver e correr:** a app BioChef ao vivo, os repositórios, os quickstarts dos frameworks de FL, o ferramental de privacidade, os portais de normas. |
| `docs/fl-frameworks.md` | Os frameworks de FL a instalar e testar, e a grelha para os comparar. |
| `docs/framework-comparison.md` | A tabela de comparação que preenches à medida que testas cada framework, terminando na recomendação encapsular-vs-construir. |
| `docs/tre-notes.md` | O que aprenderes sobre TRE em geral e sobre o **TRE do IST** em específico (acesso, restrições de implantação). Recolhe junto dos orientadores. |
| `docs/glossary.md` | Termos técnicos, num só sítio. Vai acrescentando. |
| `experiments/` | Uma pasta por experiência (corridas de FedAvg de brincar, ensaios de frameworks). Ver `experiments/README.md`. |
| `weekly-updates/` | Um ficheiro por semana. Copia `TEMPLATE.md` para `week-NN.md` toda as sextas. |

## Atualizações semanais

Toda as sextas, copia `weekly-updates/TEMPLATE.md` para `weekly-updates/week-NN.md` e preenche: o que fizeste, o que leste ou aprendeste, o que testaste, o que está bloqueado, e o plano para a semana seguinte. O `week-01.md` já está começado como exemplo. É assim que os orientadores acompanham o progresso entre reuniões.

## Primeiras semanas sugeridas

- **Semanas 1-2:** Ler `docs/architecture.md` de fio a pavio (está escrito para se ler de uma assentada). Ler o artigo do FedAvg e uma introdução curta à privacidade diferencial, a partir de `docs/reading-list.md`. Montar este repositório e escrever o `week-01.md`.
- **Semanas 3-4:** Conceitos de TRE (Five Safes, dados de categoria especial no RGPD) e as especificidades do TRE do IST; começar o `docs/tre-notes.md`. Ler por alto a agregação segura.
- **Semanas 5+:** Instalar o Flower e o NVFlare, correr um exemplo de FedAvg de dois clientes sobre um conjunto de dados tabular pequeno (registar em `experiments/`), e começar a preencher o `docs/framework-comparison.md`.
