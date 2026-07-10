import unicodedata


def normalizar_busca(texto):
    if not texto:
        return ''
    sem_acento = unicodedata.normalize('NFKD', texto)
    sem_acento = ''.join(c for c in sem_acento if not unicodedata.combining(c))
    return sem_acento.lower()
