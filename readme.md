===============================
  STUDIO MODDER SUITE v1.0
===============================
Desenvolvido por: Dimitrius Caio Vespasiano


Este e um conjunto de ferramentas para ajudar a automatizar tarefas
chatas de modding, como copiar ou renomear muitos arquivos de uma so vez.

O programa tem duas ferramentas principais:
1. Copiador com Sequencia
2. Renomeador em Lote


---------------------------------
1. COPIADOR COM SEQUENCIA
---------------------------------
Use esta aba para selecionar UM arquivo "molde" e criar VÁRIAS cópias
dele com nomes em sequencia (ex: criar 100 arquivos configurados
a partir de um).

COMO USAR:
1.  Em "1. Arquivos e Quantidade", selecione o "Arquivo de base"
    (o molde) e a "Pasta de exportacao" (onde as copias irao).

2.  Defina a "Quantidade de arquivos a gerar".
    Lembrando que o arquivo base ja e uma dessas copias, portanto
    se quiser gerar 35 arquivos, coloque 36 na quantidade, e
    apague o arquivo base, caso queira.

3.  Em "2. Configuração do Nome", crie os blocos do nome.
    -   Digite um ou diversos prefixo prontos (ex: "shape_",
        "arquivo_" "skin_"), clique em "Adicionar" para adicionar
        um por um na lista de blocos.
    -   Ative a sequencia "Numerica", escolha um formato (ex: "00")
        e clique em "Adicionar/Atualizar Bloco". Caso queira, pode
        adicionar uma sequencia alfabetica tambem.
        Obs: Caso nao adicione nenhuma sequencia, o proprio
        Windows adicionara, entao nao fara sentido voce nao utilizar!

4.  Em "Montagem", de um duplo-clique nos blocos da lista
    "Blocos disponiveis" para montar o nome final
    (ex: "minha_skin_" e "[00]").
    Obs: voce pode arrastar e organizar a ordem dos prefixos e
    sequencias adicionados na lista de Montagem, quem vem antes,
    quem vem depois. Ajuste a ordem ao gosto.

5.  O "Preview do Nome" mostrara como o primeiro arquivo ficara
    (ex: "shape_arquivo_skin_00.dds").
    Caso queira, pode limitar a quantidade de caracteres, por
    exemplo limitar a 12 caracteres, e automaticamente o programa
    engolira letras para preservar a sequencia, experimente
    limitar e observar no Preview.

6.  (OPCIONAL) Editando o Conteudo Interno (A Magica da Sincronizacao)

    Este e o recurso mais poderoso da aba "Copiador" e funciona APENAS
    para arquivos de texto (.txt, .sii, .tobj, .ini, etc.).

    OBJETIVO:
    Fazer com que um pedaco do texto *dentro* do arquivo mude
    junto com o nome do arquivo.

    EXEMPLO DE USO:
    Voce esta copiando um arquivo "skin_00.tobj". Dentro dele,
    existe uma linha de texto que aponta para uma textura:
    Value: "/caminho/textura/skin_00.dds"

    Voce quer que, ao gerar o arquivo "skin_01.tobj", essa linha
    mude automaticamente para:
    Value: "/caminho/textura/skin_01.dds"

    COMO FAZER ISSO (PASSO A PASSO):

    a.  Ative o Editor:
        Marque a caixa "Ativar configuracao de conteudo de texto
        interno". O conteudo do seu arquivo base aparecera no editor.

    b.  Selecione o Alvo:
        No editor, encontre e selecione (pinte) com o mouse o
        pedaco de texto exato que voce quer que mude.
        * No nosso exemplo, voce selecionaria apenas o "00"
          (a parte que precisa mudar).

    c.  Configure o Bloco:
        Clique com o botao direito no texto que voce selecionou.
        Um menu aparecera. Escolha "Configurar blocos de sequencia".

    d.  Monte a Sequencia Interna:
        Uma nova janela (o "Montador de Sequencia") vai aparecer.
        Nela, voce vera os mesmos "Blocos disponiveis" (prefixos
        e sequencias) que voce criou na tela principal.
        
        IMPORTANTE: Voce *nao* esta criando uma nova sequencia.
        Voce esta dizendo ao programa *como* ele deve usar a
        sequencia principal *naquele pedaco de texto*.

        Monte a sequencia que voce precisa. Por exemplo, se o nome
        do seu arquivo e "skin_[00]" e o texto interno tambem
        precisa ser "00", basta dar um duplo-clique no bloco
        "[00]" na janela do montador.

    e.  Conclua:
        Clique em "Concluir". O texto que voce selecionou (ex: "00")
        sera substituido por um BLOCO ESCURO no editor, mostrando
        o preview (ex: 00).
        * Este bloco agora esta SINCRONIZADO com a sequencia principal!

    f.  Gere os Arquivos:
        Agora, quando voce clicar em "Gerar Arquivos":
        * Arquivo 1: Nome = skin_00.tobj | Conteudo = ...skin_00.dds
        * Arquivo 2: Nome = skin_01.tobj | Conteudo = ...skin_01.dds
        * Arquivo 3: Nome = skin_02.tobj | Conteudo = ...skin_02.dds
        * ...e assim por diante.

    PARA EDITAR OU REMOVER:
    Se voce errar, basta clicar com o botao direito no bloco escuro
    dentro do editor para "Editar configuracao" ou "Remover
    configuracao" (o que restaura o texto original).

7.  Clique em "Gerar Arquivos".


---------------------------------
2. RENOMEADOR EM LOTE
---------------------------------
Use esta aba para pegar VÁRIOS arquivos ja existentes (ex: arquivos
com nomes baguncados) e renomea-los todos de uma vez para um novo
padrao limpo.

COMO USAR:
1.  Em "1. Seleção de Arquivos", clique em "Selecionar Multiplos
    Arquivos" e escolha todos os arquivos que quer renomear.

2.  Os arquivos aparecerão na tabela em "2. Arquivos Importados".

3.  Em "3. Configuração do Nome", crie os blocos de nome (prefixos
    e sequencias), exatamente como na (COPIADOR COM SEQUENCIA).

4.  Adicione os blocos na "Montagem".

5.  (O MAIS IMPORTANTE) Observe a coluna "Novo Nome (Preview)" na
    tabela. Ela mostrara EM TEMPO REAL como cada arquivo sera
    renomeado.

6.  Quando o preview estiver perfeito, clique em "4. Exportação" >
    "Renomear Arquivos".


---------------------------------
NOTA IMPORTANTE SOBRE ARQUIVOS
---------------------------------
Este programa e seguro para QUALQUER TIPO DE ARQUIVO.

-   ARQUIVOS BINARIOS (.dds, .png, .zip, .scs, etc.):
    O programa ira COPIAR o arquivo perfeitamente, sem
    corrompe-lo. A edicao de conteudo interno sera
    (corretamente) desativada para esses arquivos.

-   ARQUIVOS DE TEXTO (.txt, .sii, .sui, .tobj, .ini, etc.):
    O programa permite a edicao interna e ira preservar 100%
    da sua indentacao (espacos e tabs) original.

-   IMPORTANTE SOBRE ARQUIVOS CRIPTOGRAFADOS (COMO .TOBJ):
    Este programa NAO CRIPTOGRAFA arquivos .tobj para o jogo.
    Ele tambem NAO LE arquivos .tobj que ja estao criptografados.
    
    O objetivo desta ferramenta e facilitar o trabalho com os
    arquivos de texto LEGIVEIS (descriptografados). Tentar
    editar um arquivo ja criptografado como se fosse texto
    ira corrompe-lo.