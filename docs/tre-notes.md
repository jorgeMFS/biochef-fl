# Notas sobre TRE (geral + IST)

O que é um Trusted Research Environment, porque molda o desenho de FL, e as especificidades do **TRE do IST** onde vais implantar. A parte geral podes preencher a partir da lista de leitura; a parte específica do IST vem dos orientadores e do grupo da Ana Teresa. Trata a secção do IST como a fonte autoritativa assim que estiver preenchida, sobrepõe-se a pressupostos gerais.

## 1. TRE em geral

- **Definição.** Um ambiente de computação controlado e auditado onde os dados sensíveis ficam dentro de uma fronteira segura e os investigadores autorizados têm acesso restrito sob regras de governação.
- **Five Safes.** O modelo de governação: dados seguros, projetos seguros, pessoas seguras, ambientes seguros, outputs seguros. (Ver lista de leitura.) Anota a que "safe" serve cada parte do teu desenho.
- **Porque molda o desenho de FL.** Os TRE costumam não permitir **ligações de entrada na rede**. Essa única restrição é a razão por que o Agente em modo silo tem de ser **só de saída** (consulta o Agregador; o Agregador nunca entra dentro). Anota, à medida que as conheceres, todas as outras restrições que toquem o desenho (restrições de saída, verificação de outputs, o que se pode instalar, se contentores são permitidos).

## 2. O TRE do IST (a recolher junto dos orientadores)

Preenche cada item; deixa um "desconhecido / pendente" datado se ainda não tiveres a informação.

- **O que é e quem o gere.**
- **Como um investigador obtém acesso** (o procedimento, quem aprova, quanto tempo demora). Está no caminho crítico, começa cedo.
- **O que se pode implantar lá dentro.** Contentores? Serviços de longa duração? Um Agente que faz polling? Rede de saída sequer, e para onde?
- **Regras de rede.** Entrada proibida (assume que sim, confirma)? Lista de permissões de saída? O endpoint do Agregador precisa de ser alcançável de dentro?
- **Dados disponíveis para a tese.** Que conjuntos de dados, sob que condições, e qual é o caminho para os obter. Se os dados genómicos forem lentos, é por isto que existe a alternativa sintética.
- **Controlos de output / divulgação.** Que verificações se aplicam antes de algo sair do ambiente. Isto mapeia diretamente na política do silo e na maquinaria de privacidade.

## 3. Implicações para o desenho (manter atualizado)

À medida que as especificidades do IST chegam, anota aqui o que forçam no desenho. Forma de exemplo:
- "O IST proíbe entrada, logo o silo faz polling, confirmado."
- "Lista de permissões de saída, logo os endpoints do Agregador e do registry têm de estar na lista; documentar os hosts."
- "As verificações de output exigem X, logo a política do silo tem de aplicar X antes de enviar atualizações."
