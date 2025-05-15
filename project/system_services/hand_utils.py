import mediapipe as mp

def inicializar_maos():
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    hands = mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.8,
        min_tracking_confidence=0.8
    )
    return hands, mp_hands, mp_drawing