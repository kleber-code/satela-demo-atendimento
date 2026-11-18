from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Perfil(models.Model):
    PAPEIS = [("atendente", "Atendente"), ("supervisor", "Supervisor")]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil")
    nome = models.CharField(max_length=80)
    papel = models.CharField(max_length=12, choices=PAPEIS, default="atendente")
    cor = models.CharField(max_length=7, default="#1b7a55")

    def __str__(self):
        return self.nome

    @property
    def eh_supervisor(self):
        return self.papel == "supervisor" or self.user.is_superuser

    @property
    def iniciais(self):
        return "".join(p[0] for p in self.nome.split()[:2]).upper()


def perfil_de(user):
    p = getattr(user, "perfil", None) if user.is_authenticated else None
    if p is None and user.is_authenticated:
        p, _ = Perfil.objects.get_or_create(
            user=user,
            defaults={
                "nome": user.get_full_name() or user.username,
                "papel": "supervisor" if user.is_superuser else "atendente",
            },
        )
    return p


class Cliente(models.Model):
    nome = models.CharField(max_length=120)
    email = models.CharField(max_length=120, blank=True)
    telefone = models.CharField(max_length=30, blank=True)
    cor = models.CharField(max_length=7, default="#5b6b8c")

    def __str__(self):
        return self.nome

    @property
    def iniciais(self):
        return "".join(p[0] for p in self.nome.split()[:2]).upper() or "?"


class Etiqueta(models.Model):
    nome = models.CharField(max_length=40, unique=True)
    cor = models.CharField(max_length=7, default="#1b7a55")

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Conversa(models.Model):
    STATUS = [
        ("bot", "Com o bot"),
        ("aguardando", "Aguardando humano"),
        ("atendimento", "Em atendimento"),
        ("resolvida", "Resolvida"),
    ]
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="conversas")
    canal = models.CharField(max_length=20, default="web")
    status = models.CharField(max_length=12, choices=STATUS, default="bot", db_index=True)
    atribuido = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="conversas"
    )
    etiquetas = models.ManyToManyField(Etiqueta, blank=True, related_name="conversas")
    sessao_chave = models.CharField(max_length=64, blank=True, db_index=True)
    criada_em = models.DateTimeField(default=timezone.now)
    atualizada_em = models.DateTimeField(default=timezone.now, db_index=True)
    ultima_previa = models.CharField(max_length=140, blank=True)
    nao_lidas = models.PositiveIntegerField(default=0)
    aguardando_desde = models.DateTimeField(null=True, blank=True)
    primeira_resposta_em = models.DateTimeField(null=True, blank=True)
    primeira_resposta_humana_em = models.DateTimeField(null=True, blank=True)
    resolvida_em = models.DateTimeField(null=True, blank=True)
    resolvida_pelo_bot = models.BooleanField(default=False)
    bot_falhou = models.BooleanField(default=False, db_index=True)
    motivo_falha = models.CharField(max_length=30, blank=True)
    resumo_ia = models.TextField(blank=True)
    csat = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-atualizada_em"]

    @property
    def protocolo(self):
        return f"AT-{self.pk:05d}"

    def __str__(self):
        return f"{self.protocolo} {self.cliente}"

    @property
    def sla_estourado(self):
        from .servicos.horario import sla_minutos

        if self.status != "aguardando" or not self.aguardando_desde:
            return False
        return (timezone.now() - self.aguardando_desde).total_seconds() > sla_minutos() * 60


class Mensagem(models.Model):
    TIPOS = [
        ("cliente", "Cliente"),
        ("bot", "Bot"),
        ("atendente", "Atendente"),
        ("nota", "Nota interna"),
        ("sistema", "Sistema"),
        ("acao", "Ação da IA"),
    ]
    conversa = models.ForeignKey(Conversa, on_delete=models.CASCADE, related_name="mensagens")
    tipo = models.CharField(max_length=10, choices=TIPOS)
    usuario = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    texto = models.TextField()
    fontes = models.JSONField(default=list, blank=True)
    acao = models.JSONField(null=True, blank=True)
    fallback = models.BooleanField(default=False)
    criada_em = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["criada_em", "id"]

    def __str__(self):
        return f"{self.tipo}: {self.texto[:40]}"


class Artigo(models.Model):
    titulo = models.CharField(max_length=160)
    categoria = models.CharField(max_length=60, default="Geral")
    conteudo = models.TextField()
    palavras_chave = models.CharField(max_length=300, blank=True, help_text="Separadas por vírgula")
    ativo = models.BooleanField(default=True)
    citacoes = models.PositiveIntegerField(default=0)
    embedding = models.JSONField(null=True, blank=True)
    atualizado_em = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["categoria", "titulo"]

    def __str__(self):
        return self.titulo


class RespostaRapida(models.Model):
    atalho = models.CharField(max_length=30, unique=True, help_text="Ex.: /prazo")
    titulo = models.CharField(max_length=80)
    texto = models.TextField()

    class Meta:
        ordering = ["atalho"]

    def __str__(self):
        return self.atalho


class Pedido(models.Model):
    STATUS = [
        ("aguardando_pagamento", "Aguardando pagamento"),
        ("em_separacao", "Em separação"),
        ("enviado", "Enviado"),
        ("em_rota", "Em rota de entrega"),
        ("entregue", "Entregue"),
        ("cancelado", "Cancelado"),
    ]
    numero = models.CharField(max_length=20, unique=True)
    cliente_nome = models.CharField(max_length=120)
    itens = models.CharField(max_length=300)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=24, choices=STATUS)
    previsao_entrega = models.DateField(null=True, blank=True)
    rastreio = models.CharField(max_length=30, blank=True)
    atualizado_em = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-numero"]

    def __str__(self):
        return self.numero


class Agendamento(models.Model):
    TIPOS = [("retirada", "Retirada na loja"), ("visita_tecnica", "Visita técnica")]
    conversa = models.ForeignKey(Conversa, null=True, blank=True, on_delete=models.SET_NULL)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    data = models.DateField()
    periodo = models.CharField(max_length=10, default="manha")
    unidade = models.CharField(max_length=80, default="Loja Centro")
    referencia = models.CharField(max_length=120, blank=True)
    criado_em = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["data", "periodo"]


class Chamado(models.Model):
    PRIORIDADES = [("baixa", "Baixa"), ("normal", "Normal"), ("alta", "Alta")]
    conversa = models.ForeignKey(Conversa, null=True, blank=True, on_delete=models.SET_NULL)
    assunto = models.CharField(max_length=160)
    descricao = models.TextField(blank=True)
    prioridade = models.CharField(max_length=8, choices=PRIORIDADES, default="normal")
    status = models.CharField(max_length=12, default="aberto")
    criado_em = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-criado_em"]

    @property
    def protocolo(self):
        return f"CH-{self.pk:05d}"


class Configuracao(models.Model):
    nome_empresa = models.CharField(max_length=80, default="Aurora Casa & Tech")
    nome_bot = models.CharField(max_length=40, default="Aurora")
    instrucoes = models.TextField(
        default=(
            "Tom simpático, direto e profissional. Trate o cliente por você, use no máximo "
            "uma frase de abertura e vá direto à resposta. Quando citar prazos ou valores, "
            "use exatamente o que está nos artigos."
        )
    )
    bot_ativo = models.BooleanField(default=True)
    hora_inicio = models.PositiveSmallIntegerField(default=8)
    hora_fim = models.PositiveSmallIntegerField(default=18)
    dias_uteis = models.CharField(max_length=20, default="0,1,2,3,4,5", help_text="0=segunda ... 6=domingo")
    msg_fora_expediente = models.TextField(
        default="Nosso time humano está fora do expediente agora. Deixei sua conversa na fila e "
        "você será atendido assim que abrirmos."
    )
    msg_boas_vindas = models.TextField(
        default="Olá! Sou a Aurora, assistente virtual da Aurora Casa & Tech. Posso consultar pedido, "
        "tirar dúvidas, agendar retirada ou abrir um chamado. Como posso ajudar?"
    )
    sla_minutos = models.PositiveSmallIntegerField(default=5, help_text="Meta de 1ª resposta humana")

    @classmethod
    def carregar(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class EventoUso(models.Model):
    """Contador de uso (limites de taxa e teto de IA). Compartilhado entre workers via banco."""

    tipo = models.CharField(max_length=12)  # msg_ip, msg_sessao, ia
    chave = models.CharField(max_length=64, blank=True)
    criado_em = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [models.Index(fields=["tipo", "chave", "criado_em"])]
