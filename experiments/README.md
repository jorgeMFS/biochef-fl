# Experiências

Uma pasta por experiência. Mantém leve mas reprodutível: qualquer pessoa (tu daqui a três meses, ou um orientador) devia conseguir ler a pasta e perceber o que fizeste, o que aconteceu, e o que significou.

## Convenção

Cria `experiments/NN-nome-curto/` (ex.: `01-flower-fedavg-dois-clientes/`) com um `notes.md` contendo:

- **Questão.** O que estás a tentar descobrir (ex.: "O Flower consegue correr um FedAvg de dois clientes sobre um conjunto de dados tabular pequeno, e quão difícil é a montagem?").
- **Montagem.** Framework e versão, conjunto de dados, como os dados foram divididos (ex.: alfa de Dirichlet), modelo, parâmetros principais. O suficiente para repetir.
- **O que fiz.** Comandos ou passos, em curto.
- **Resultado.** O que aconteceu: números, capturas de ecrã, erros. O resultado honesto, incluindo falhas.
- **Conclusão.** O que significa para a tese, e que linha do `docs/framework-comparison.md` sustenta.

Junta código e configs pequenos ao lado do `notes.md`. **Não** juntes conjuntos de dados, pesos de modelo, nem nada que contenha dados reais (ver o `.gitignore` do repositório).

## Índice

| # | Experiência | Questão | Estado |
|---|---|---|---|
| 01 | | | planeada |
