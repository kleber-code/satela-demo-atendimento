from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class EntradaMensagem:
    """Mensagem de cliente já normalizada, independente do canal de origem."""

    canal: str
    identificador: str  # sessão web, telefone WhatsApp etc.: chave estável do contato
    texto: str
    nome: str = ""
    meta: dict = field(default_factory=dict)


class Canal(ABC):
    slug = ""
    nome = ""
    # True quando o cliente precisa buscar respostas (polling); False quando empurramos (webhook de saída)
    usa_polling = False

    @abstractmethod
    def receber(self, payload) -> EntradaMensagem:
        """Converte o payload bruto do canal (formulário web, webhook) em EntradaMensagem."""

    @abstractmethod
    def enviar(self, conversa, mensagem) -> None:
        """Entrega ao cliente uma mensagem de saída (bot ou atendente). Canal web: no-op."""

    def verificar_assinatura(self, request) -> bool:
        """Valida a autenticidade do webhook de entrada (HMAC etc.). Web: sempre True."""
        return True
