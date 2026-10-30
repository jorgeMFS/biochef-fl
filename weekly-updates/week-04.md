# Semana 04 (2026-10-24 a 2026-10-30)

## Feito esta semana

- Corri o exemplo distribuído nas três máquinas: `pearl`, `yellow` e `gold`.
- Verifiquei que a comunicação entre os clientes e o servidor Flower funcionou corretamente.
- Obtive resultados do treino distribuído e apresentei alguns deles na reunião com os orientadores.
- Comparei os resultados obtidos com os resultados apresentados no artigo.

## Lido / aprendido

- Compreendi melhor o funcionamento prático de uma experiência federada com vários clientes e um servidor de agregação.
- Percebi as diferenças entre a execução local e a execução distribuída nas três máquinas.
- Ganhei experiência com a configuração e execução do Flower nas máquinas destinadas à experiência.

## Testado / experiências

- Executei com sucesso o exemplo de previsão epidemiológica federada nas três máquinas.
- Confirmei o funcionamento da comunicação entre os clientes e o servidor Flower.
- Comparei os resultados da experiência com os resultados descritos no artigo.
- Ainda não registei formalmente a experiência em `experiments/`, pois estou a aguardar uma resposta sobre uma dúvida relacionada com possíveis alterações à sandbox.

## Bloqueado / questões para os orientadores

- Aguardo a resposta da profª Ana Teresa sobre uma dúvida relacionada com a previsão dos dados de Macau. Atualmente, o código utiliza a agregação global de pesos no FedAvg para prever os dados de Macau usando os das duas outras regiões. Enviei um email a questionar se devo manter este procedimento ou realizar um cenário mais explícito de validação cruzada: treinar o modelo apenas com os dados de Portugal e Guangdong e avaliá-lo exclusivamente nos dados de Macau, pois foi o que me levou a entender na reunião de quinta-feira.

## Plano para a próxima semana

- Esclarecer com a professora se é necessário alterar a sandbox e aplicar as alterações, se for caso disso.
- Aprofundar a comparação entre os resultados obtidos e os resultados do artigo.
- Montar um dos TREs para preparar a fase seguinte das experiências e colocar os datasets nos três TREs.
- Começar a explorar o NVFlare e, se houver tempo, iniciar uma implementação ou um primeiro teste.
- Registar a experiência atual e os seus resultados em `experiments/` e colocar neste repositório o código e instruções da sandbox com o Flower.
