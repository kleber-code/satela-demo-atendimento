"""Dados fictícios da loja Aurora Casa & Tech. Nenhum dado pessoal real."""
from decimal import Decimal

ETIQUETAS = [
    ("Urgente", "#c0392b"), ("Entrega", "#3b6ea8"), ("Pagamento", "#8a7a1b"), ("Troca/devolução", "#a8613b"),
    ("Defeito", "#a83b6e"), ("Elogio", "#1b7a55"), ("Agendamento", "#7a4aa8"), ("Cancelamento", "#5b6b8c"),
]

NOMES = [
    "Ana Beatriz Souza", "Carlos Eduardo Lima", "Juliana Prado", "Marcos Vinícius Rocha", "Fernanda Castro",
    "Rodrigo Nogueira", "Patrícia Mendes", "Lucas Ferraz", "Aline Barbosa", "Thiago Monteiro",
    "Camila Azevedo", "Bruno Carvalho", "Larissa Teixeira", "Gustavo Pires", "Renata Siqueira",
    "Felipe Duarte", "Vanessa Moura", "Eduardo Ribeiro", "Débora Cardoso", "Henrique Batista",
    "Natália Freitas", "Paulo Sérgio Dias", "Tatiane Lopes", "Leonardo Campos", "Bianca Moreira",
    "Ricardo Fonseca", "Simone Araújo", "Vitor Hugo Martins", "Priscila Gomes", "André Luiz Barros",
    "Mariana Coelho", "Sérgio Tavares", "Isabela Cunha", "Wagner Pacheco", "Cláudia Rezende",
    "Otávio Brandão", "Luana Vasconcelos", "Diogo Salgado", "Helena Magalhães", "Rafael Quintanilha",
]

# numero, cliente, itens, valor, status, dias até a previsão, rastreio
PEDIDOS = [
    ("AUR-10421", "Ana Beatriz Souza", "Air Fryer Digital 5L", Decimal("389.90"), "em_rota", 1, "AN482910377BR"),
    ("AUR-10422", "Carlos Eduardo Lima", "Smart TV 50\" 4K", Decimal("2299.00"), "enviado", 3, "AN482910412BR"),
    ("AUR-10423", "Juliana Prado", "Cafeteira Expresso + 2 xícaras", Decimal("459.00"), "em_separacao", 4, ""),
    ("AUR-10424", "Marcos Vinícius Rocha", "Fone Bluetooth ANC", Decimal("299.90"), "entregue", -2, "AN482909881BR"),
    ("AUR-10425", "Fernanda Castro", "Aspirador Robô Slim", Decimal("1199.00"), "aguardando_pagamento", 7, ""),
    ("AUR-10426", "Rodrigo Nogueira", "Notebook 15\" 16GB/512GB", Decimal("3899.00"), "enviado", 5, "AN482910655BR"),
    ("AUR-10427", "Patrícia Mendes", "Jogo de panelas antiaderente", Decimal("279.90"), "cancelado", 0, ""),
    ("AUR-10428", "Lucas Ferraz", "Ventilador de coluna 40cm", Decimal("219.90"), "em_rota", 0, "AN482910701BR"),
    ("AUR-10429", "Aline Barbosa", "Micro-ondas 30L inox", Decimal("649.00"), "entregue", -5, "AN482909410BR"),
    ("AUR-10430", "Thiago Monteiro", "Monitor 27\" 144Hz", Decimal("1549.00"), "em_separacao", 2, ""),
    ("AUR-10431", "Camila Azevedo", "Geladeira Frost Free 400L", Decimal("3799.00"), "enviado", -3, "AN482908230BR"),
]

RESPOSTAS_RAPIDAS = [
    ("/ola", "Saudação", "Olá! Aqui é da equipe Aurora Casa & Tech. Vou te ajudar com isso agora mesmo."),
    ("/aguarde", "Pedir um instante", "Só um instante enquanto verifico isso no sistema, já te respondo."),
    ("/prazo", "Prazos de entrega", "Nossos prazos: capitais de 2 a 5 dias úteis e interior de 5 a 10 dias úteis, contados após a confirmação do pagamento."),
    ("/troca", "Troca e devolução", "Você pode pedir troca ou devolução em até 7 dias corridos após receber o produto, e ele deve estar sem uso e na embalagem original. Posso abrir o pedido para você agora."),
    ("/nf", "Nota fiscal", "A nota fiscal é enviada por e-mail em até 24h após o faturamento e fica disponível em Meus Pedidos."),
    ("/desculpa", "Pedido de desculpas", "Sinto muito pelo transtorno. Vou priorizar o seu caso e te mantenho informado(a) a cada passo."),
    ("/fecho", "Encerramento", "Ficou mais alguma dúvida? Se estiver tudo certo, vou encerrar por aqui. Obrigado por falar com a Aurora!"),
    ("/pix", "Estorno via Pix", "O estorno de pagamentos via Pix cai na mesma conta em até 2 dias úteis após a aprovação do cancelamento."),
]

# titulo, categoria, palavras-chave, conteudo
ARTIGOS = [
    ("Prazos e frete de entrega", "Entrega", "prazo, entrega, frete, demora, chega, dias, correios, transportadora, grátis",
     "O prazo de entrega é contado a partir da confirmação do pagamento.\nCapitais e regiões metropolitanas: de 2 a 5 dias úteis. Interior: de 5 a 10 dias úteis. Produtos grandes (geladeiras, fogões, TVs acima de 55 polegadas) podem levar até 12 dias úteis.\nO frete é grátis para compras acima de R$ 299 nas regiões Sul e Sudeste. Nas demais regiões, o frete grátis começa em R$ 499.\nO valor e o prazo exatos aparecem no carrinho, ao informar o CEP."),
    ("Como rastrear meu pedido", "Entrega", "rastrear, rastreio, rastreamento, codigo, onde esta, acompanhar, status pedido",
     "Assim que o pedido é despachado, enviamos o código de rastreio por e-mail e ele aparece em Meus Pedidos.\nPara acompanhar, informe o código no site da transportadora ou peça ao assistente virtual: basta informar o número do pedido (formato AUR-12345).\nO código só fica ativo na transportadora até 24h após o despacho."),
    ("Pedido atrasado", "Entrega", "atraso, atrasado, nao chegou, passou do prazo, demora, atrasada",
     "Se o prazo informado passou, abrimos uma investigação junto à transportadora em até 1 dia útil.\nPedidos atrasados têm prioridade e o cliente pode optar por aguardar, trocar o endereço de entrega (se ainda não saiu para rota) ou cancelar com estorno integral.\nNesses casos o atendimento é feito por um atendente humano."),
    ("Troca e devolução", "Trocas e devoluções", "troca, trocar, devolucao, devolver, arrependimento, voltar produto, reembolso",
     "Compras online têm direito de arrependimento: 7 dias corridos após o recebimento, com produto sem uso, na embalagem original e com nota fiscal.\nPara solicitar, abra a solicitação em Meus Pedidos ou fale com o atendimento. Enviamos um código de postagem gratuito.\nA devolução do valor é feita na mesma forma de pagamento em até 10 dias úteis após recebermos o produto."),
    ("Produto com defeito e garantia", "Garantia", "defeito, quebrou, garantia, nao funciona, pifou, assistencia, estragou, danificado",
     "Todos os produtos têm 12 meses de garantia contra defeitos de fabricação (já incluída a garantia legal de 90 dias).\nSe o produto apresentar defeito: 1) guarde a embalagem e a nota fiscal; 2) abra um chamado informando o problema e, se possível, fotos ou vídeo; 3) nossa equipe retorna em até 2 dias úteis com a solução: troca, conserto ou reembolso.\nProduto que chegou danificado deve ser avisado em até 7 dias corridos."),
    ("Formas de pagamento e parcelamento", "Pagamento", "pagamento, pagar, pix, cartao, parcelar, parcelamento, boleto, juros, desconto, parcelas",
     "Aceitamos Pix (5% de desconto à vista), cartão de crédito em até 10x sem juros para compras acima de R$ 300 (abaixo disso, até 3x sem juros) e boleto bancário.\nO Pix e o cartão têm aprovação imediata; o boleto vence em 3 dias úteis e leva até 2 dias úteis para compensar."),
    ("Segunda via de boleto", "Pagamento", "boleto, segunda via, vencido, venceu, codigo de barras, 2a via",
     "A segunda via do boleto fica disponível em Meus Pedidos > Pagamento enquanto o pedido estiver aguardando pagamento.\nBoletos vencidos não podem ser pagos; nesse caso o pedido é cancelado automaticamente após 3 dias do vencimento e você pode refazer a compra ou pagar por Pix."),
    ("Nota fiscal", "Fiscal", "nota fiscal, nf, nfe, danfe, xml, cnpj, comprovante",
     "A nota fiscal eletrônica é enviada por e-mail em até 24h após o faturamento e também fica em Meus Pedidos > Nota fiscal.\nPara emitir com CNPJ, informe o documento antes do pagamento: não é possível alterar o CPF/CNPJ da nota depois do faturamento."),
    ("Retirada na loja", "Loja física", "retirada, retirar, loja, buscar, endereco, centro, retire, agendar retirada, pegar",
     "Você pode retirar o pedido na Loja Centro (Rua das Acácias, 100 - endereço fictício), de segunda a sábado, das 9h às 18h.\nA retirada fica disponível 2 horas após a confirmação do pagamento para itens em estoque na loja. Leve documento com foto e o número do pedido.\nO assistente virtual pode agendar o dia e o período da retirada."),
    ("Instalação e visita técnica", "Serviços", "instalacao, instalar, visita tecnica, tecnico, montagem, suporte de tv, ar condicionado",
     "Oferecemos visita técnica para instalação de TVs com suporte de parede, ar-condicionado e montagem de móveis.\nValor: R$ 120 por visita, agendada com no mínimo 2 dias úteis de antecedência, em períodos de manhã ou tarde, de segunda a sábado.\nO assistente virtual pode agendar a visita."),
    ("Cancelamento de pedido", "Pedidos", "cancelar, cancelamento, desistir, estorno, estornar, nao quero mais",
     "Antes do envio: o cancelamento é imediato e o estorno é feito em até 2 dias úteis (Pix) ou na fatura do cartão em até 2 ciclos.\nDepois do envio: recuse a entrega ou solicite devolução ao receber, dentro de 7 dias corridos.\nO cancelamento é concluído por um atendente humano para garantir o estorno correto."),
    ("Alterar endereço de entrega", "Pedidos", "alterar endereco, mudar endereco, trocar endereco, cep errado, endereco errado",
     "O endereço só pode ser alterado enquanto o pedido estiver em separação (antes do despacho). Depois disso, a transportadora não consegue redirecionar a carga.\nSolicite ao atendimento informando o número do pedido e o novo endereço completo."),
    ("Conta, senha e cadastro", "Conta", "senha, login, conta, cadastro, esqueci, redefinir, email, acessar",
     "Para redefinir a senha, use \"Esqueci minha senha\" na tela de login: enviamos um link válido por 30 minutos para o seu e-mail.\nDados cadastrais podem ser editados em Minha Conta. A Aurora nunca pede senha, código de verificação ou dados de cartão por mensagem."),
    ("Horário de atendimento", "Atendimento", "horario, atendimento, funciona, aberto, fechado, expediente, sabado, domingo, falar",
     "O assistente virtual atende 24 horas, todos os dias.\nO atendimento humano funciona de segunda a sábado, das 8h às 18h (horário de Brasília). Fora desse horário, sua conversa entra na fila e é respondida assim que abrirmos."),
    ("Estorno e reembolso", "Pagamento", "estorno, reembolso, devolver dinheiro, dinheiro de volta, reembolsar, prazo estorno",
     "Pix: o estorno cai em até 2 dias úteis após a aprovação. Cartão de crédito: aparece em até 2 faturas, conforme o fechamento do seu cartão. Boleto: devolvemos por Pix ou transferência para conta de mesma titularidade em até 5 dias úteis."),
]

# ------------------------------------------------------------------ cenários de conversa
# Turnos: ("b", texto, [fontes]) bot | ("ia_acao", nome, args) | ("bp",) resposta de pedido |
#         ("transf", resumo, motivo, categoria) | ("h", texto) atendente | ("n", texto) nota | ("c", texto) cliente
CENARIOS = [
    {
        "qtd": 4, "janela": "hist", "status": "resolvida", "etiquetas": ["Entrega"], "csat": [7, 3, 0, 0, 1],
        "abre": ["Oi, boa tarde! Queria saber onde está meu pedido {pedido}", "Bom dia, como acompanho o pedido {pedido}?", "pedido {pedido} ja chegou? to esperando"],
        "turnos": [
            ("ia_acao", "consultar_pedido", {"numero": "{pedido}"}),
            ("bp",),
            ("c", "Perfeito, era só isso. Muito obrigado!"),
            ("b", "Por nada, {nome}! Fico feliz em ajudar. Se precisar de algo mais, é só chamar.", []),
        ],
    },
    {
        "qtd": 3, "janela": "hist", "status": "resolvida", "etiquetas": ["Entrega"], "csat": [6, 4, 1, 0, 1],
        "abre": ["Quanto tempo demora a entrega para Campinas?", "qual o prazo de entrega? e o frete é grátis?", "Boa noite, vocês entregam em quanto tempo no interior?"],
        "turnos": [
            ("b", "Capitais e regiões metropolitanas levam de 2 a 5 dias úteis; no interior, de 5 a 10 dias úteis, contados a partir da confirmação do pagamento. O frete é grátis acima de R$ 299 nas regiões Sul e Sudeste. O valor exato aparece no carrinho ao informar o CEP.", ["Prazos e frete de entrega"]),
            ("c", "Entendi, obrigada!"),
            ("b", "Disponha! Se precisar de mais alguma coisa, estou por aqui.", []),
        ],
    },
    {
        "qtd": 3, "janela": "hist", "status": "resolvida", "etiquetas": ["Troca/devolução"], "csat": [5, 4, 2, 0, 1],
        "abre": ["Comprei uma cafeteira e não gostei, dá pra devolver?", "Quero devolver um produto que comprei semana passada, como faço?", "qual o prazo pra troca? errei a voltagem"],
        "turnos": [
            ("b", "Dá sim! Compras online têm 7 dias corridos de arrependimento após o recebimento, com o produto sem uso e na embalagem original. Você abre a solicitação em Meus Pedidos e enviamos um código de postagem gratuito. O reembolso sai na mesma forma de pagamento em até 10 dias úteis depois que recebermos o produto.", ["Troca e devolução"]),
            ("c", "Ótimo, vou fazer isso agora. Valeu!"),
            ("b", "Por nada! Boa sorte com a troca e conte comigo.", []),
        ],
    },
    {
        "qtd": 3, "janela": "hist", "status": "resolvida", "etiquetas": ["Pagamento"], "csat": [5, 3, 1, 0, 2],
        "abre": ["Dá pra parcelar em 10x sem juros?", "meu boleto venceu, consigo gerar outro?", "Tem desconto no pix?"],
        "turnos": [
            ("b", "Aceitamos Pix com 5% de desconto à vista, cartão em até 10x sem juros para compras acima de R$ 300 (abaixo disso, até 3x) e boleto com vencimento em 3 dias úteis. Se o boleto venceu, a segunda via fica em Meus Pedidos > Pagamento enquanto o pedido estiver aguardando pagamento.", ["Formas de pagamento e parcelamento", "Segunda via de boleto"]),
            ("c", "Beleza, entendi. Obrigado"),
            ("b", "De nada! Qualquer dúvida é só chamar.", []),
        ],
    },
    {
        "qtd": 1, "janela": "hist", "status": "resolvida", "etiquetas": [], "csat": [4, 4, 0, 0, 2],
        "abre": ["Preciso da nota fiscal do pedido {pedido}", "Onde baixo a NF? preciso pra empresa"],
        "turnos": [
            ("b", "A nota fiscal eletrônica é enviada por e-mail em até 24h após o faturamento e também fica disponível em Meus Pedidos > Nota fiscal. Se precisar dela com CNPJ, o documento deve ser informado antes do pagamento.", ["Nota fiscal"]),
            ("c", "Achei aqui, obrigado!"),
            ("b", "Que bom! Por nada.", []),
        ],
    },
    {
        "qtd": 3, "janela": "hist", "status": "resolvida", "etiquetas": ["Agendamento"], "csat": [8, 2, 0, 0, 1],
        "abre": ["Quero retirar meu pedido na loja, como funciona?", "posso buscar na loja? queria agendar", "Boa tarde, dá pra retirar o pedido {pedido} na loja essa semana?"],
        "turnos": [
            ("b", "Pode sim! A retirada é na Loja Centro, de segunda a sábado, das 9h às 18h, e fica disponível 2 horas após a confirmação do pagamento. Qual dia e período (manhã ou tarde) prefere?", ["Retirada na loja"]),
            ("c", "Pode ser daqui a alguns dias, de manhã mesmo"),
            ("ia_acao", "agendar", {"tipo": "retirada", "periodo": "manha", "referencia": "{pedido}"}),
            ("b", "Pronto, {nome}! Sua retirada está agendada na Loja Centro, de manhã. Leve documento com foto e o número do pedido. Algo mais?", ["Retirada na loja"]),
            ("c", "Não, tá ótimo. Obrigada!"),
            ("b", "Por nada! Até lá.", []),
        ],
    },
    {
        "qtd": 3, "janela": "recente", "status": "atendimento", "agente": "rafael", "etiquetas": ["Defeito", "Urgente"],
        "abre": ["Meu ar condicionado chegou e não liga, já tentei de tudo", "A air fryer que comprei parou de funcionar com 10 dias de uso", "O fone veio com um lado sem som"],
        "turnos": [
            ("b", "Sinto muito pelo transtorno, {nome}. Todos os produtos têm 12 meses de garantia contra defeito de fabricação. Posso abrir um chamado para o time de suporte agora. Consegue me dizer o que acontece ao ligar?", ["Produto com defeito e garantia"]),
            ("c", "Liga a luz e logo desliga, sai um barulho estranho. Quero trocar por outro novo."),
            ("ia_acao", "abrir_chamado", {"assunto": "Produto não funciona ao ligar (defeito)", "descricao": "Cliente relata que o produto liga e desliga em seguida, com ruído. Quer troca.", "prioridade": "alta"}),
            ("transf", "Cliente relata defeito de fabricação em produto recém-recebido (liga e desliga com ruído). Chamado de prioridade alta já aberto. Cliente quer troca por produto novo.", "Troca por defeito exige análise humana.", "nao_soube"),
            ("h", "Oi, {nome}! Aqui é o Rafael, da Aurora. Li o resumo do seu caso e já estou com o chamado em mãos. Pode me mandar uma foto ou vídeo do produto ligando?"),
            ("c", "Mando já, um minuto"),
            ("n", "Cliente dentro da garantia (12 meses). Pedir foto/vídeo e liberar troca se confirmado."),
        ],
    },
    {
        "qtd": 1, "janela": "hist", "status": "resolvida", "agente": "camila", "etiquetas": ["Defeito"], "csat": [4, 4, 1, 1, 0],
        "abre": ["O micro-ondas que comprei não esquenta, ligo e só gira o prato"],
        "turnos": [
            ("b", "Poxa, sinto muito. Pelo que descreve pode ser defeito de fabricação, coberto pela garantia de 12 meses. Vou abrir um chamado e já passo para um atendente.", ["Produto com defeito e garantia"]),
            ("ia_acao", "abrir_chamado", {"assunto": "Micro-ondas não aquece", "descricao": "Cliente informa que o micro-ondas liga e gira o prato mas não aquece.", "prioridade": "normal"}),
            ("transf", "Micro-ondas não aquece, dentro da garantia. Chamado aberto.", "Defeito exige análise humana.", "nao_soube"),
            ("h", "Olá! Aqui é a Camila. Vou providenciar a troca do micro-ondas. Te enviei um código de postagem gratuito por e-mail."),
            ("c", "Recebi, muito obrigado pela rapidez!"),
            ("h", "Imagina! Assim que o produto chegar ao nosso centro, enviamos o novo. Ficou mais alguma dúvida?"),
            ("c", "Não, só isso!"),
        ],
    },
    {
        "qtd": 3, "janela": "recente", "status": "aguardando", "etiquetas": ["Urgente", "Entrega"],
        "abre": ["VOCÊS ESTÃO DE BRINCADEIRA? meu pedido AUR-10431 já passou do prazo faz 3 dias!!", "Pedido AUR-10431 atrasado de novo. Isso é um absurdo, já é a segunda vez", "Minha geladeira era pra ter chegado e nada. Pedido AUR-10431. Quero uma solução hoje"],
        "turnos": [
            ("ia_acao", "consultar_pedido", {"numero": "AUR-10431"}),
            ("b", "Entendo a sua frustração e peço desculpas, {nome}. Seu pedido AUR-10431 consta como enviado, com previsão vencida em 3 dias. Pedidos atrasados têm prioridade e eu não consigo resolver isso sozinho, então vou passar para um atendente humano agora.", ["Pedido atrasado"]),
            ("transf", "Cliente irritado: pedido AUR-10431 (geladeira) enviado com 3 dias de atraso. Quer solução hoje; já consultamos o status, sem novidades de rastreio.", "Cliente insatisfeito com atraso; prioridade.", "nao_soube"),
            ("c", "Alguém vai me responder ou não?"),
        ],
    },
    {
        "qtd": 3, "janela": "hist", "status": "resolvida", "agente": "diego", "etiquetas": ["Cancelamento", "Pagamento"], "csat": [3, 4, 3, 1, 1],
        "abre": ["Quero cancelar o pedido {pedido}, fiz sem querer", "preciso cancelar a compra de ontem", "Como faço pra cancelar e receber o dinheiro de volta?"],
        "turnos": [
            ("b", "Antes do envio o cancelamento é imediato e o estorno sai em até 2 dias úteis no Pix ou em até 2 faturas no cartão. Para concluir o cancelamento preciso transferir você para um atendente humano, ok?", ["Cancelamento de pedido"]),
            ("c", "Pode ser"),
            ("transf", "Cliente quer cancelar pedido feito por engano. Orientado sobre prazos de estorno; cancelamento depende de atendente.", "Cancelamento deve ser concluído por humano.", "nao_soube"),
            ("h", "Olá, {nome}! Aqui é o Diego. Já cancelei o pedido e o estorno foi solicitado. Use /pix para ver o prazo: até 2 dias úteis."),
            ("c", "Perfeito, obrigada pela agilidade"),
            ("h", "Disponha! Qualquer coisa estamos à disposição."),
        ],
    },
    {
        "qtd": 3, "janela": "recente", "status": "aguardando", "etiquetas": ["Pagamento"],
        "abre": ["Tem cupom de primeira compra? Vi um anúncio de 15% off", "Vocês têm algum cupom de desconto? Recebi um código no Instagram", "O cupom BEMVINDO15 não está funcionando"],
        "turnos": [
            ("b", "Não encontrei informações sobre cupons e campanhas na minha base e prefiro não te passar nada errado. Vou chamar um atendente humano para te ajudar.", []),
            ("transf", "Cliente pergunta sobre cupom de primeira compra / código de campanha. Base de conhecimento não tem artigo sobre cupons.", "Sem artigo sobre cupons e promoções.", "nao_soube"),
        ],
    },
    {
        "qtd": 2, "janela": "hist", "status": "atendimento", "agente": "marina", "etiquetas": [],
        "abre": ["Vocês têm o fogão de indução da marca Zênite em estoque na loja de Recife?", "Dá pra comprar 30 liquidificadores pra minha empresa com CNPJ? Tem desconto atacado?"],
        "turnos": [
            ("b", "Essa informação não está na minha base e não quero te passar algo incorreto. Vou transferir para um atendente humano.", []),
            ("transf", "Pergunta comercial fora do escopo da base (estoque específico / compra em volume com CNPJ).", "Fora do escopo do bot.", "nao_soube"),
            ("h", "Olá! Aqui é a Marina, supervisora do atendimento. Vou verificar isso com o time comercial e já te retorno."),
            ("n", "Encaminhar ao comercial B2B. Cliente aguardando retorno ainda hoje."),
        ],
    },
    {
        "qtd": 3, "janela": "hist", "status": "resolvida", "etiquetas": ["Agendamento"], "csat": [7, 2, 1, 0, 1],
        "abre": ["Preciso instalar uma TV de parede, vocês fazem?", "Vocês fazem instalação de ar-condicionado?"],
        "turnos": [
            ("b", "Fazemos sim! A visita técnica custa R$ 120, deve ser agendada com 2 dias úteis de antecedência e acontece de manhã ou à tarde, de segunda a sábado. Quer agendar? Qual período prefere?", ["Instalação e visita técnica"]),
            ("c", "Quero sim, de tarde"),
            ("ia_acao", "agendar", {"tipo": "visita_tecnica", "periodo": "tarde", "referencia": "Instalação"}),
            ("b", "Agendado, {nome}! Nosso técnico vai até você à tarde na data confirmada. Algo mais em que eu possa ajudar?", ["Instalação e visita técnica"]),
            ("c", "Era só isso, valeu"),
            ("b", "Por nada! Até logo.", []),
        ],
    },
    {
        "qtd": 2, "janela": "recente", "status": "atendimento", "agente": "camila", "etiquetas": ["Pagamento"],
        "abre": ["Quero falar com um atendente, por favor", "Me passa para uma pessoa de verdade? a cobrança no meu cartão veio duplicada"],
        "turnos": [
            ("b", "Claro! Vou te passar para uma pessoa da nossa equipe.", []),
            ("transf", "Cliente pediu atendimento humano; relata possível cobrança duplicada no cartão.", "Cliente pediu atendimento humano.", "pediu_humano"),
            ("h", "Oi, {nome}, tudo bem? Aqui é a Camila. Vou verificar a cobrança agora, me confirma os 4 últimos dígitos do cartão (não envie o número completo)."),
            ("c", "Os 4 últimos são 0000"),
        ],
    },
    {
        "qtd": 3, "janela": "recente", "status": "bot", "etiquetas": [],
        "abre": ["Oi!", "Bom dia", "Olá, tudo bem?"],
        "turnos": [
            ("b", "Olá! Sou a Aurora, assistente virtual da Aurora Casa & Tech. Posso consultar pedido, tirar dúvidas, agendar retirada ou abrir um chamado. Como posso ajudar?", []),
            ("c", "Qual o horário de atendimento de vocês?"),
            ("b", "O assistente virtual atende 24 horas, todos os dias. O atendimento humano funciona de segunda a sábado, das 8h às 18h (horário de Brasília). Fora desse horário sua conversa entra na fila e é respondida assim que abrirmos.", ["Horário de atendimento"]),
        ],
    },
]
