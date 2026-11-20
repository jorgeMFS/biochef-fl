# Semana 07 (2026-11-14 a 2026-11-20)

## Feito esta semana

- Continuei a preparar a réplica da experiência federada com NVFlare, mantendo o modelo e o protocolo experimental definidos para a versão com Flower.
- Obtive acesso aos três TREs: `oscar`, `flare` e `ariel`.
- Comecei a ler a documentação da arquitetura do BioChef e os documentos associados ao projeto, nomeadamente o `docs/architecture.md` do `biochef-infra` e secções do specification do `biochef-agent`.

## Lido / aprendido

- Compreendi melhor os próximos passos necessários para comparar Flower e NVFlare de forma equivalente.
- Comecei a rever a arquitetura do BioChef e o fluxo previsto para workflows e estudos, embora ainda não tenha retirado conclusões definitivas.
- Identifiquei que o trabalho nesta fase deve separar a validação local da preparação e execução nos TREs.

## Testado / experiências

- A implementação da experiência com NVFlare encontra-se em progresso localmente.
- Ainda não existe uma execução comparável completa nem resultados finais da versão NVFlare.
- Ainda não registrei uma nova experiência em `experiments/`.
- Ainda não montei ou configurei manualmente um TRE, nem coloquei conjuntos de dados ou executei código nos ambientes `oscar`, `flare` e `ariel`. Apenas recebi acesso aos três TREs nesta semana e verifiquei o acesso e que conseguia ler os ficheiros lá presentes.
- Ainda não corri o `biochef-agent` localmente nem executei um workflow de exemplo.
- Ainda não investiguei de forma prática opções de agregação privada, Secure Aggregation ou Differential Privacy.

## Bloqueado / questões para os orientadores

- Ainda não existe um canal de comunicação definido entre os TREs e um orquestrador de aprendizagem federada para utilizar o NVFlare ou o Flower. A professora Ana Teresa deixou que eu testasse e experimentasse a melhor forma de estabelecer esta comunicação.
- O trabalho continua centrado em concluir e validar primeiro a experiência com NVFlare. Só depois dessa fase será avaliado, a pedido do João Marques, se vale a pena integrar o NVFlare e o Flower na mesma solução, pois ambos podem ser utilizados em conjunto.

## Plano para a próxima semana

- Concluir a implementação e os testes locais da experiência com NVFlare.
- Executar a experiência NVFlare localmente com o mesmo modelo, dados e protocolo da experiência Flower.
- Preparar e executar a experiência NVFlare nos TREs `oscar`, `flare` e `ariel`, mantendo cada região no respetivo ambiente e experimentando a melhor forma de comunicação com o orquestrador.
- Registar a experiência NVFlare em `experiments/` e comparar os resultados com Flower.
- Colocar o `biochef-agent` a correr localmente e executar um workflow de exemplo.
- Continuar a análise da arquitetura do BioChef, incluindo estudos, workflows e egress.
- Começar a estudar integração de uma ronda federada no fluxo do BioChef e opções para agregação que não exponham os pesos individuais dos clientes.
- Após concluir o plano anterior, avaliar se vale a pena combinar os dois frameworks para este caso de uso, caso haja tempo.