from .base import Canal, EntradaMensagem


class CanalWeb(Canal):
    """Widget /demo/: o navegador envia por POST e busca respostas por polling curto."""

    slug = "web"
    nome = "Chat do site"
    usa_polling = True

    def receber(self, payload):
        return EntradaMensagem(
            canal=self.slug,
            identificador=payload.get("sessao", ""),
            texto=(payload.get("texto") or "").strip(),
            nome=payload.get("nome", ""),
        )

    def enviar(self, conversa, mensagem):
        # Nada a fazer: o widget lê as mensagens novas via /demo/api/mensagens/.
        return None
