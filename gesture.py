import mediapipe as mp
import cv2
import time
import keyboard
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

prev_time = 0
cooldown = 1.5

# ── Windows Volume Control via pycaw ──────────────────────────────────────────

devices = AudioUtilities.GetSpeakers()
interface = devices._dev.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))

def volume_up():
    vol_range = volume.GetVolumeRange()
    current_db = volume.GetMasterVolumeLevel()
    new_db = min(current_db + (vol_range[1] - vol_range[0]) * 0.05, vol_range[1])
    volume.SetMasterVolumeLevel(new_db, None)

def volume_down():
    vol_range = volume.GetVolumeRange()
    current_db = volume.GetMasterVolumeLevel()
    new_db = max(current_db - (vol_range[1] - vol_range[0]) * 0.05, vol_range[0])
    volume.SetMasterVolumeLevel(new_db, None)

# ── Windows Spotify Control via keyboard media keys ───────────────────────────

def play_pause():
    keyboard.send('play/pause media')

def next_song():
    keyboard.send('next track')

def prev_song():
    keyboard.send('previous track')

# ── MediaPipe & OpenCV Setup ──────────────────────────────────────────────────

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# ── Camera Setup ──────────────────────────────────────────────────────────────
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cap.isOpened():
    print("❌ No camera found! Check your webcam connection.")
    exit()
time.sleep(2)  # Give camera time to warm up
print("✅ Camera ready!")

# ── Main Loop ─────────────────────────────────────────────────────────────────

while True:
    ret, img = cap.read()
    if not ret:
        print("⚠️  Camera not accessible. Exiting.")
        break

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    result = hands.process(img_rgb)
    img = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

    if result.multi_hand_landmarks:
        for hand_landmark in result.multi_hand_landmarks:

            lm_list = []
            for id, lm in enumerate(hand_landmark.landmark):
                h, w, _ = img.shape
                lm_list.append((id, int(lm.x * w), int(lm.y * h)))

            fingers = []

            if lm_list[4][1] > lm_list[3][1]:
                fingers.append(1)
            else:
                fingers.append(0)

            for tip_id in [8, 12, 16, 20]:
                if lm_list[tip_id][2] < lm_list[tip_id - 2][2]:
                    fingers.append(1)
                else:
                    fingers.append(0)

            print("Fingers:", fingers)

            current_time = time.time()

            if current_time - prev_time > cooldown:

                if fingers == [0, 0, 0, 0, 0]:
                    play_pause()
                    print("🎵 Play/Pause")
                    prev_time = current_time

                elif fingers == [0, 1, 0, 0, 0]:
                    next_song()
                    print("⏭️  Next Song")
                    prev_time = current_time

                elif fingers == [0, 1, 1, 0, 0]:
                    prev_song()
                    print("⏮️  Previous Song")
                    prev_time = current_time

                elif fingers == [1, 0, 0, 0, 0]:
                    volume_up()
                    print("🔊 Volume Up")
                    prev_time = current_time

                elif fingers == [0, 0, 0, 0, 1]:
                    volume_down()
                    print("🔉 Volume Down")
                    prev_time = current_time

            mp_drawing.draw_landmarks(
                img, hand_landmark, mp_hands.HAND_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(128, 128, 128), thickness=2, circle_radius=4),
                mp_drawing.DrawingSpec(color=(0, 0, 0), thickness=2, circle_radius=2)
            )

    img = cv2.flip(img, 1)
    cv2.imshow("Hands", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()