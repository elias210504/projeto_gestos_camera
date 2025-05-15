import cv2
import mediapipe as mp
import math
import time
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from collections import deque

# Inicializar pycaw para controle de volume
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
volume_range = volume.GetVolumeRange()
min_vol = volume_range[0]
max_vol = volume_range[1]

# Inicialização MediaPipe
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.8, min_tracking_confidence=0.8)

# Captura de vídeo
cap = cv2.VideoCapture(0)

# Posição da barra de volume
volume_min_y = 150  # Ponto para volume mínimo (levemente mais alto)
volume_max_y = 350  # Ponto para volume máximo (levemente mais alto)
volume_bar_x = 50  # Posição horizontal da barra

# Variáveis de controle
gesture_start_time = None
show_volume_bar = False
volume_history = deque(maxlen=5)  # Histórico para suavizar o volume

def distancia(p1, p2):
    """Calcula a distância euclidiana entre dois pontos."""
    return math.hypot(p2.x - p1.x, p2.y - p1.y)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    # Verificar se há mãos detectadas
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            lm = hand_landmarks.landmark

            # Coordenadas do indicador e polegar
            thumb_tip = lm[4]
            index_tip = lm[8]

            # Converter coordenadas normalizadas para pixels
            thumb_x, thumb_y = int(thumb_tip.x * frame.shape[1]), int(thumb_tip.y * frame.shape[0])
            index_x, index_y = int(index_tip.x * frame.shape[1]), int(index_tip.y * frame.shape[0])

            # Verificar se o indicador e polegar estão juntos
            if distancia(thumb_tip, index_tip) < 0.05:
                if gesture_start_time is None:
                    gesture_start_time = time.time()  # Inicia o temporizador
                elif time.time() - gesture_start_time > 1.5:  # Verifica se o gesto foi mantido por 1,5 segundos
                    show_volume_bar = True
            else:
                gesture_start_time = None  # Reseta o temporizador se o gesto não for mantido

            # Controle de volume se a barra estiver visível
            if show_volume_bar:
                # Calcular a posição média entre o polegar e o indicador
                avg_y = (thumb_y + index_y) // 2

                # Restringir a posição dentro da barra de volume
                avg_y = max(volume_min_y, min(volume_max_y, avg_y))

                # Calcular o volume com base na posição
                normalized_volume = (avg_y - volume_min_y) / (volume_max_y - volume_min_y)
                volume_level = min_vol + (max_vol - min_vol) * (1 - normalized_volume)

                # Adicionar o volume ao histórico para suavização
                volume_history.append(volume_level)
                smoothed_volume = sum(volume_history) / len(volume_history)

                # Ajustar o volume suavizado
                volume.SetMasterVolumeLevel(smoothed_volume, None)

                # Desenhar o indicador de volume
                cv2.circle(frame, (volume_bar_x, avg_y), 10, (0, 255, 0), -1)

    else:
        show_volume_bar = False
        gesture_start_time = None

    # Desenhar a barra de volume apenas se estiver visível
    if show_volume_bar:
        # Parte externa da barra (borda arredondada e transparente)
        cv2.rectangle(frame, (volume_bar_x - 15, volume_min_y - 10), (volume_bar_x + 15, volume_max_y + 10), (255, 255, 255, 50), -1)  # Transparência simulada com cor mais clara
        cv2.rectangle(frame, (volume_bar_x - 15, volume_min_y - 10), (volume_bar_x + 15, volume_max_y + 10), (255, 255, 255), 2)  # Borda branca

        # Parte interna da barra (nível de volume)
        cv2.rectangle(frame, (volume_bar_x - 10, avg_y), (volume_bar_x + 10, volume_max_y), (255, 255, 255), -1)  # Preenchimento branco

        # Indicador de volume (círculo)
        cv2.circle(frame, (volume_bar_x, avg_y), 10, (0, 255, 0), -1)  # Indicador verde

    cv2.imshow("Controle por Gestos", frame)
    if cv2.waitKey(1) & 0xFF == 27:  # Pressione ESC para sair
        break

cap.release()
cv2.destroyAllWindows()
