# Links: coisas para ver, correr e ler

Um conjunto curado e verificado de links. A lista de leitura (`reading-list.md`) tem os artigos com DOI; este ficheiro é para as coisas que se clicam para *ver e correr*: a app ao vivo, os repositórios, os quickstarts dos frameworks, e os portais de normas. Links verificados em junho de 2026; se algum apodrecer, pesquisa pelo nome do projeto.

## Ver o BioChef a funcionar

- **Demo ao vivo (plataforma do lado do cliente):** https://ieeta-pt.github.io/Biochef. A plataforma WASM no browser do artigo publicado. Abre, constrói um pequeno workflow, e vê-o correr sem que nenhum dado saia da página.
- **Implantação de produção:** https://biochef.app
- **Código-fonte:** https://github.com/ieeta-pt/Biochef (frontend, registry, Agente, recipes).
- **Toolkit GTO** (o toolkit de genómica que o BioChef compila para WASM): https://github.com/cobilab/gto, documentação https://cobilab.github.io/gto/. É o que as ferramentas de exemplo na plataforma realmente são.

## O trabalho de FL do próprio grupo (a tua referência mais próxima)

- **fed_rf (federated Random Forest, PySyft):** https://github.com/ieeta-pt/fed_rf. Clona e corre isto cedo; é a coisa mais próxima do que vais construir, feita pelo mesmo grupo. Artigo: DOI 10.1109/CBMS65348.2025.00159 (arXiv: https://arxiv.org/abs/2505.08085).

## Frameworks de FL: ver e correr (para a decisão encapsular-vs-construir)

Instala cada um, corre um exemplo pequeno, e regista o resultado em `framework-comparison.md` e em `experiments/`.

- **Flower.** Documentação e tutoriais: https://flower.ai/docs/framework/. Os pontos de partida mais úteis para nós: quickstart de scikit-learn (https://flower.ai/docs/examples/quickstart-sklearn.html) e quickstart de XGBoost (https://flower.ai/docs/examples/xgboost-quickstart.html), porque o primeiro trainer de referência é baseado em árvores. Repositório: https://github.com/flwrlabs/flower.
- **NVFlare (NVIDIA FLARE).** Documentação: https://nvflare.readthedocs.io/. Panorâmica e catálogo de tutoriais: https://nvidia.github.io/NVFlare/. Repositório: https://github.com/NVIDIA/NVFlare. Nota para a espinha de privacidade: traz filtros de privacidade diferencial, agregação segura, cifra homomórfica, FedProx e SCAFFOLD, e suporta modelos de árvore (XGBoost, Random Forest), ver a documentação de privacidade em https://nvflare.readthedocs.io/en/main/example_applications_algorithms.html.
- **PySyft (OpenMined).** Repositório: https://github.com/OpenMined/PySyft. Projeto: https://openmined.org/. É a base sobre a qual o fed_rf está construído, logo a opção de continuidade ("computar sobre dados que não possuis e não consegues ver").
- **OpenFL (Intel / UPenn, securefederatedai).** Documentação: https://openfl.readthedocs.io/. O modelo agregador-colaborador do trabalho de segmentação federada de tumores (FeTS); de saúde e do tipo TRE por desenho.

## Ferramental de privacidade (a espinha de investigação)

- **Opacus (DP-SGD para PyTorch):** https://github.com/meta-pytorch/opacus, documentação https://opacus.ai/. Instancia um PrivacyEngine, passa-lhe o teu modelo/otimizador/dataloader, e treina sob privacidade diferencial seguindo o orçamento gasto (épsilon) em tempo real. É a ferramenta mais provável para a parte de DP.
- **Levantamento de frameworks de DP da OpenMined** (orientação): https://openmined.org/blog/a-survey-of-differential-privacy-frameworks/.

## Normas e governação (o contexto do BioChef)

- **GA4GH Genomic Data Toolkit** (DRS, htsget, refget): https://www.ga4gh.org/genomic-data-toolkit/. As normas que o BioChef usa para chegar a dados controlados.
- **GDI / quadro técnico 1+MG:** https://framework.onemilliongenomes.eu/. A infraestrutura europeia federada de dados genómicos em que o BioChef encaixa.
- **Federated EGA (FEGA):** https://ega-archive.org/. (Pergunta ao lado de Aveiro especificamente sobre o FEGA-PT.)
- **RGPD, Artigo 9.º** (categorias especiais de dados pessoais, a restrição legal): https://eur-lex.europa.eu/legal-content/PT/TXT/?uri=CELEX:32016R0679.

## Ferramental de cadeia de abastecimento / artefactos (como o BioChef mantém tudo verificável)

- **ORAS** (artefactos arbitrários num registry OCI): https://oras.land/.
- **Sigstore / Cosign** (assinar e verificar artefactos): https://docs.sigstore.dev/.
- **SLSA** (níveis de proveniência): https://slsa.dev/. **CycloneDX** (formato de SBOM): https://cyclonedx.org/.

## Blocos de construção da plataforma (já no BioChef)

- **biowasm** (compilar ferramentas de bioinformática para WASM): https://github.com/biowasm/biowasm. **aioli** (o runtime WASM que o BioChef usa): https://github.com/biowasm/aioli.
- **Snakemake** (o backend de workflows do Agente existente): https://snakemake.readthedocs.io/.
