import cv2
import time
from collections import deque

from distancia import distancia
from volume_control import inicializar_volume
from hand_utils import inicializar_maos

# Inicializar pycaw para controle de volume
volume, min_vol, max_vol = inicializar_volume()

# Inicialização MediaPipe
hands, mp_hands, mp_drawing = inicializar_maos()

# Captura de vídeo
cap = cv2.VideoCapture(0)

# Posição da barra de volume
volume_min_y = 150
volume_max_y = 350
volume_bar_x = 50

# Variáveis de controle
gesture_start_time = None
show_volume_bar = False
volume_history = deque(maxlen=5)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            lm = hand_landmarks.landmark

            thumb_tip = lm[4]
            index_tip = lm[8]

            thumb_x, thumb_y = int(thumb_tip.x * frame.shape[1]), int(thumb_tip.y * frame.shape[0])
            index_x, index_y = int(index_tip.x * frame.shape[1]), int(index_tip.y * frame.shape[0])

            if distancia(thumb_tip, index_tip) < 0.05:
                if gesture_start_time is None:
                    gesture_start_time = time.time()
                elif time.time() - gesture_start_time > 1.5:
                    show_volume_bar = True
            else:
                gesture_start_time = None

            if show_volume_bar:
                avg_y = (thumb_y + index_y) // 2
                avg_y = max(volume_min_y, min(volume_max_y, avg_y))
                normalized_volume = (avg_y - volume_min_y) / (volume_max_y - volume_min_y)
                volume_level = min_vol + (max_vol - min_vol) * (1 - normalized_volume)
                volume_history.append(volume_level)
                smoothed_volume = sum(volume_history) / len(volume_history)
                volume.SetMasterVolumeLevel(smoothed_volume, None)
                cv2.circle(frame, (volume_bar_x, avg_y), 10, (0, 255, 0), -1)
    else:
        show_volume_bar = False
        gesture_start_time = None

    if show_volume_bar:
        cv2.rectangle(frame, (volume_bar_x - 15, volume_min_y - 10), (volume_bar_x + 15, volume_max_y + 10), (255, 255, 255, 50), -1)
        cv2.rectangle(frame, (volume_bar_x - 15, volume_min_y - 10), (volume_bar_x + 15, volume_max_y + 10), (255, 255, 255), 2)
        cv2.rectangle(frame, (volume_bar_x - 10, avg_y), (volume_bar_x + 10, volume_max_y), (255, 255, 255), -1)
        cv2.circle(frame, (volume_bar_x, avg_y), 10, (0, 255, 0), -1)

    cv2.imshow("Controle por Gestos", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()