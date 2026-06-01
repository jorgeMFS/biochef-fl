# Lista de leitura

Agrupada por tema. Para as coisas que se *clicam para ver e correr* (a app ao vivo, os repositórios, os quickstarts dos frameworks, os portais de normas), ver `links.md`; este ficheiro são os artigos. Cada entrada dá a referência completa, um DOI ou link estável, e uma nota sobre o que retirar dela. Referências académicas verificadas por pesquisa web (junho de 2026).

## A. Fundamentos de federated learning

- **FedAvg.** McMahan, Moore, Ramage, Hampson, Agüera y Arcas (2017), "Communication-Efficient Learning of Deep Networks from Decentralized Data", AISTATS 2017, PMLR vol. 54, pp. 1273-1282. Link: https://proceedings.mlr.press/v54/mcmahan17a.html (arXiv: 1602.05629). O algoritmo fundador de FL e o problema dos dados não-IID. Lê primeiro este.
- **FedProx.** Li, Sahu, Zaheer, Sanjabi, Talwalkar, Smith (2020), "Federated Optimization in Heterogeneous Networks", MLSys 2020, vol. 2, pp. 429-450. Link: https://proceedings.mlsys.org/paper_files/paper/2020/hash/1f5fe83998a09396ebe6477d9475ba0c-Abstract.html (arXiv: 1812.06127). Lidar com sites que têm distribuições de dados diferentes (heterogeneidade estatística e de sistemas).
- **SCAFFOLD.** Karimireddy, Kale, Mohri, Reddi, Stich, Suresh (2020), "SCAFFOLD: Stochastic Controlled Averaging for Federated Learning", ICML 2020, PMLR vol. 119, pp. 5132-5143. Link: https://proceedings.mlr.press/v119/karimireddy20a.html (arXiv: 1910.06378). Variáveis de controlo para corrigir o desvio do cliente sob dados não-IID. O passo natural depois de FedAvg e FedProx.
- **Levantamento.** Kairouz, McMahan, et al. (2021), "Advances and Open Problems in Federated Learning", Foundations and Trends in Machine Learning, vol. 14, n.º 1-2, pp. 1-210. DOI: 10.1561/2200000083 (arXiv: 1912.04977). Usa-o como mapa da área, não como leitura de capa a capa.

## B. Privacidade em federated learning

- **DP-SGD.** Abadi, Chu, Goodfellow, McMahan, Mironov, Talwar, Zhang (2016), "Deep Learning with Differential Privacy", ACM CCS 2016, pp. 308-318. DOI: 10.1145/2976749.2978318 (arXiv: 1607.00133). O mecanismo que adiciona ruído calibrado durante o treino; percebe o orçamento de privacidade (épsilon).
- **Agregação segura.** Bonawitz, Ivanov, Kreuter, Marcedone, McMahan, Patel, Ramage, Segal, Seth (2017), "Practical Secure Aggregation for Privacy-Preserving Machine Learning", ACM CCS 2017, pp. 1175-1191. DOI: 10.1145/3133956.3133982 (IACR ePrint 2017/281). Deixa o agregador ver apenas a soma das atualizações, nunca a atualização individual de um site.
- **Inferência de pertença.** Shokri, Stronati, Song, Shmatikov (2017), "Membership Inference Attacks Against Machine Learning Models", IEEE Symposium on Security and Privacy (S&P) 2017, pp. 3-18. DOI: 10.1109/SP.2017.41. Mostra que um modelo treinado deixa fugir se um dado registo esteve no seu conjunto de treino.
- **Fuga por gradientes.** Zhu, Liu, Han (2019), "Deep Leakage from Gradients", NeurIPS 2019, pp. 14747-14756. Link: https://papers.nips.cc/paper/9617-deep-leakage-from-gradients (arXiv: 1906.08935). Mostra que gradientes partilhados podem reconstruir dados de treino. Em conjunto com a entrada anterior, é por isto que "os dados ficam locais" não basta, e o que motiva a camada de privacidade da tese.

## C. TRE e governação de dados

- **Five Safes.** Desai, Ritchie, Welpton (2016), "Five Safes: designing data access for research", Working Papers in Economics n.º 1601, University of the West of England, Bristol. Link: https://uwe-repository.worktribe.com/output/914745/ (EconPapers: RePEc:uwe:wpaper:20161601). O modelo de governação (dados, projetos, pessoas, ambientes, outputs seguros) por trás do acesso controlado a dados.
- **RGPD (dados genéticos).** Regulamento (UE) 2016/679 (RGPD), em particular o Artigo 9.º sobre categorias especiais de dados pessoais. Link: https://eur-lex.europa.eu/legal-content/PT/TXT/?uri=CELEX:32016R0679. A restrição legal por trás de tudo.
- **GA4GH Genomic Data Toolkit.** Panorâmicas de DRS, htsget e refget, as normas que o BioChef usa para aceder a dados controlados. Link: https://www.ga4gh.org/genomic-data-toolkit/ (página do DRS: https://www.ga4gh.org/product/data-repository-service-drs/).
- **GDI / 1+MG.** A Infraestrutura Europeia de Dados Genómicos e o quadro técnico 1+Million Genomes. Link: https://framework.onemilliongenomes.eu/. O contexto federado em que o BioChef encaixa.
- **FEGA (Federated EGA).** A rede federada do European Genome-phenome Archive. Link: https://ega-archive.org/. (O lado de Aveiro pode apontar-te diretamente para os recursos operacionais do FEGA-PT.)
- **Documentação do TRE do IST.** A recolher junto dos orientadores e do grupo da Ana Teresa. Perceber como o TRE deles concede acesso e o que se pode lá implantar.

## D. Específico do BioChef (o mais importante para esta tese)

- **Documento de arquitetura do BioChef** (o desenho federado). Documento interno. Define o Agente em modo silo, o Agregador Federado, trainers e modelos, políticas, e a aba federada. É o alvo que vais implementar. Lê-o com atenção.
- **Tese da plataforma BioChef.** Andrade (2026), "A web-based client-side plug-in platform for executing workflows", dissertação de mestrado, Universidade de Aveiro. A plataforma de execução de workflows existente (Agente, registry OCI, modelo de recipes e ferramentas, UI). Documento interno; o substrato que a camada de FL estende.
- **Artigo do BioChef.** Rosa, Andrade, Silva, Oliveira (2026), "BioChef: a client-side WebAssembly-based workflow builder for genomic data analysis", BMC Bioinformatics. Preprint verificado: DOI 10.21203/rs.3.rs-7697498/v1 (https://www.researchsquare.com/article/rs-7697498/v1). Nota: já publicado em BMC Bioinformatics (2026); copiar o DOI final do artigo BMC a partir da página da Springer (não resolveu na pesquisa à data de escrita).
- **Federated Random Forest (trabalho do grupo).** Cotorobai, Silva, Oliveira (2025), "A Federated Random Forest Solution for Secure Distributed Machine Learning", IEEE 38th International Symposium on Computer-Based Medical Systems (CBMS) 2025, pp. 769-774. DOI: 10.1109/CBMS65348.2025.00159 (arXiv: 2505.08085; código: https://github.com/ieeta-pt/fed_rf). O federated Random Forest do grupo, com PySyft; um candidato a trainer de referência. Uma extensão unificada de Random Forest e XGBoost (agregação no espaço de margem, SHAP distribuído) foi submetida à IEEE Access (confirmar estado e DOI).

## E. Normas e ferramental para a construção

- **OCI / ORAS** (guardar artefactos arbitrários num registry OCI): https://oras.land/. **Cosign / Sigstore** (assinatura): https://docs.sigstore.dev/. **SLSA** (níveis de proveniência): https://slsa.dev/. **CycloneDX** (formato de SBOM): https://cyclonedx.org/. Como o BioChef mantém ferramentas e modelos verificáveis.
- **LS-AAI (LifeScience AAI / ELIXIR AAI).** Autenticação baseada em OIDC usada pela UI e pelo Agregador. Ver https://elixir-europe.org/ (LifeScience Login).
