# Semana 06 (2026-11-07 a 2026-11-13)

## Feito esta semana

- Terminei a sandbox do exemplo de previsão epidemiológica federada utilizando Flower.
- Organizei e registei o código e os resultados da experiência em experiments/.
- Apresentei os resultados da experiência com Flower na reunião de acompanhamento de quinta-feira.
- Contactei o João Marques relativamente ao acesso aos TREs, tendo recebido a indicação de que me será disponibilizado acesso em breve.
- Realizei a documentação das etapas realizadas e dos resultados obtidos.
- Comecei a explorar o NVFlare.

## Lido / aprendido

- Consolidei a compreensão do funcionamento da experiência de aprendizagem federada implementada com Flower.
- Analisei os resultados obtidos, incluindo o efeito do scaler e do otimizador e a importância de manter o estado do Adam entre rondas, aspetos relevantes a preservar para a tese.
- Clarifiquei os próximos objetivos do trabalho, passando da implementação inicial com Flower para a comparação entre Flower e NVFlare e o estudo da sua possível integração no BioChef.
- Comecei a aprofundar a compreensão do NVFlare, incluindo a sua arquitetura, os componentes e a forma de configurar e executar uma experiência de aprendizagem federada.

## Testado / experiências

- Concluí a implementação e os testes da sandbox Flower.
- Registei o código e os resultados em `experiments/`.
- Ainda não iniciei a montagem de um TRE.

## Bloqueado / questões para os orientadores

- Continuo à espera do acesso aos TREs, que será disponibilizado pelo João Marques.
- Como a prioridade desta semana foi concluir e apresentar a experiência com Flower, ainda não iniciei a implementação da experiência com NVFlare, ficando esse trabalho como uma das prioridades para a próxima semana.

## Plano para a próxima semana

- Replicar com NVFlare a experiência realizada com Flower, mantendo o mesmo modelo, os mesmos dados e o mesmo protocolo experimental, utilizando o scaler apenas nos dados de treino.
- Registar a nova experiência em `experiments/02`.
- Obter acesso aos TREs e preparar a execução das experiências nos ambientes correspondentes.
- Executar as versões Flower e NVFlare no TRE disponibilizado, mantendo cada região no respetivo ambiente.
- Começar a comparação entre Flower e NVFlare, considerando os requisitos de instalação, as ligações de rede, a visibilidade dos pesos dos clientes pelo servidor, o suporte para Secure Aggregation e Differential Privacy (DP), e a quantidade de código necessária.
- Analisar a arquitetura do BioChef através de docs/architecture.md do biochef-infra (PR #2) e das secções relevantes do spec do biochef-agent (PR #106), nomeadamente estudos, workflows e egress.
- Colocar o biochef-agent a correr localmente, seguindo o README, e executar um workflow de exemplo.
- Começar a estudar como integrar uma ronda de aprendizagem federada no fluxo do BioChef, identificando o processo de aprovação, os dados que saem de cada TRE e o local onde deverá ocorrer a agregação.
- Investigar possíveis abordagens para realizar a agregação sem expor os pesos individuais dos clientes, identificando duas ou três opções e respetivas vantagens e desvantagens.
