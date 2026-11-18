from .base import Canal


class CanalWhatsApp(Canal):
    """Esqueleto do canal WhatsApp via Hub da Satela. NÃO implementado nesta vitrine.

    Contrato esperado (ver README, seção "Plugando o WhatsApp"):
      * um endpoint de webhook recebe o evento do Hub -> verificar_assinatura() -> receber()
        -> servicos.atendimento.processar_entrada();
      * enviar() chama a API de envio do Hub quando o bot ou um atendente responde.
    """

    slug = "whatsapp"
    nome = "WhatsApp"
    usa_polling = False

    def receber(self, payload):
        raise NotImplementedError("Canal WhatsApp não implementado nesta demonstração.")

    def enviar(self, conversa, mensagem):
        raise NotImplementedError("Canal WhatsApp não implementado nesta demonstração.")

    def verificar_assinatura(self, request):
        return False
