# Glossário

Termos técnicos do projeto, num só sítio. Vai acrescentando à medida que leres. (O documento de arquitetura traz a sua própria cópia do essencial; este ficheiro é a lista-mestra que cresce.)

- **Agregador (Agregador Federado).** O coordenador central de uma sessão de FL: emite rondas, combina atualizações, publica o modelo final. Nunca vê dados em bruto.
- **Silo / Agente em modo silo.** O cliente de FL de um site que detém dados. Treina localmente, aplica a política, devolve apenas atualizações e métricas.
- **Ronda.** Um ciclo de distribuir-treinar-devolver-agregar. Uma sessão são muitas rondas.
- **Sessão.** Uma execução completa de treino federado, do modelo inicial ao modelo final publicado, feita de muitas rondas.
- **FedAvg.** Agregação de base: faz a média das atualizações dos sites, ponderada pela contagem de amostras.
- **FedProx / SCAFFOLD.** Estratégias de agregação que lidam melhor com dados não-IID do que o FedAvg (termo proximal; variáveis de controlo).
- **Privacidade diferencial (DP).** Uma garantia formal que limita o que um output revela sobre qualquer registo individual, via ruído calibrado. O limite é o orçamento de privacidade, épsilon.
- **Orçamento de privacidade (épsilon).** O "gasto" cumulativo de DP ao longo de uma sessão; quando se esgota, um site já não pode contribuir.
- **DP-SGD.** Descida de gradiente estocástica com privacidade diferencial: cortar os gradientes por exemplo, adicionar ruído. A forma padrão de treinar um modelo sob DP.
- **Agregação segura.** Um protocolo que deixa o Agregador aprender apenas a soma das atualizações, nunca uma atualização individual.
- **Inferência de pertença.** Um ataque que infere se um registo esteve no conjunto de treino de um modelo, a partir de acesso ao modelo.
- **Fuga por gradientes.** Um ataque que reconstrói inputs de treino a partir de gradientes partilhados.
- **Inversão de modelo.** Um ataque que reconstrói inputs representativos de uma classe a partir de um modelo.
- **Dados não-IID.** Dados distribuídos de forma desigual pelos sites; a dificuldade que define a FL real.
- **Partição de Dirichlet.** Uma forma padrão de sintetizar divisões não-IID entre clientes para experiências.
- **TRE (Trusted Research Environment).** Um ambiente de computação controlado e auditado onde os dados sensíveis ficam no sítio; costuma proibir ligações de entrada.
- **Five Safes.** Modelo de governação: dados, projetos, pessoas, ambientes e outputs seguros.
- **Model card.** Um documento curto que descreve o que um modelo é, como foi treinado, e o seu uso e limites previstos, publicado junto com o modelo.
- **Registry OCI / ORAS.** Um registry de contentores (e o ferramental para guardar nele artefactos arbitrários). O BioChef guarda aqui ferramentas, trainers e modelos.
- **Cosign / Sigstore.** Ferramental para assinar e verificar artefactos.
- **SBOM.** Software Bill of Materials: uma lista do que está dentro de um artefacto.
- **SLSA / proveniência.** Um registo de como um artefacto foi construído, para integridade da cadeia de abastecimento.
- **Digest.** Um hash de conteúdo que nomeia uma versão exata de um artefacto; fixar por digest torna "cada site correu o mesmo trainer" comprovável.
- **LS-AAI (LifeScience AAI / ELIXIR AAI).** O fornecedor de identidade OIDC para os utilizadores da UI federada.
- **OIDC.** OpenID Connect, o protocolo de autenticação que o LS-AAI fala.
- **GA4GH.** Global Alliance for Genomics and Health; define normas (DRS, htsget, refget) para acesso a dados controlados.
- **GDI / FEGA.** Infraestrutura europeia federada de dados genómicos (Genomic Data Infrastructure; Federated EGA).
- **WASM (WebAssembly).** Formato binário portável que deixa ferramentas nativas correr no browser; base da execução do lado do cliente do BioChef.
- **Snakemake.** O motor de workflows que o Agente BioChef existente usa como backend de execução (execução de workflows, não FL).
