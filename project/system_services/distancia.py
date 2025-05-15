import math

def distancia(p1, p2):
    """Calcula a distância euclidiana entre dois pontos."""
    return math.hypot(p2.x - p1.x, p2.y - p1.y)