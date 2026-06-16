# generate_vectors.py
import cv2
import numpy as np
import os

# ---------------- CONFIG ----------------
# CONFIG
MODEL_FILE = "openface.nn4.small2.v1.t7"

SKETCH_FOLDER = r"sketch\sketch2"


IMAGE_EXTS = (".jpg", ".jpeg", ".png")

# ----------------------------------------


def extract_embedding(net, detector, img):
    """Detects largest face and returns 128-D normalized embedding."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = detector.detectMultiScale(gray, 1.1, 5)

    if len(faces) == 0:
        return None

    (x, y, w, h) = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)[0]
    face_roi = img[y:y+h, x:x+w]

    try:
        face_roi = cv2.resize(face_roi, (96, 96))
    except:
        return None

    blob = cv2.dnn.blobFromImage(
        face_roi, 1.0 / 255, (96, 96),
        (0, 0, 0), swapRB=True, crop=False
    )

    net.setInput(blob)
    vec = net.forward().flatten()

    norm = np.linalg.norm(vec)
    if norm == 0:
        return None

    return vec / norm


def generate_vectors_for_folder():
    if not os.path.exists(MODEL_FILE):
        print("❌ Model file not found.")
        return

    if not os.path.isdir(SKETCH_FOLDER):
        print(f"❌ Sketch folder '{SKETCH_FOLDER}' not found.")
        return

    # Load model and detector once
    net = cv2.dnn.readNetFromTorch(MODEL_FILE)
    detector = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    embeddings = {}

    print("🔄 Processing sketches...\n")

    for fname in sorted(os.listdir(SKETCH_FOLDER)):
        if not fname.lower().endswith(IMAGE_EXTS):
            continue

        path = os.path.join(SKETCH_FOLDER, fname)
        img = cv2.imread(path)

        if img is None:
            print(f"⚠️ Could not read {fname}")
            continue

        vec = extract_embedding(net, detector, img)

        if vec is None:
            print(f"❌ No face / embedding for {fname}")
            continue

        key = os.path.splitext(fname)[0]
        embeddings[key] = vec

        print(f"✅ {fname} → embedding extracted")

    # -------- PRINT FOR COPY-PASTE (OPTIONAL) --------
    print("\n\n📋 COPY-PASTE READY DICTIONARY:\n")
    print("KNOWN_SKETCH_EMB = {")
    for k, v in embeddings.items():
        arr = ", ".join([f"{x:.6f}" for x in v])
        print(f'    "{k}": np.array([{arr}]),')
    print("}")

    # -------- SAVE TO FILE (RECOMMENDED) --------
    np.savez("sketch_embeddings.npz", **embeddings)
    print("\n💾 Saved embeddings to sketch_embeddings.npz")


if __name__ == "__main__":
    generate_vectors_for_folder()
