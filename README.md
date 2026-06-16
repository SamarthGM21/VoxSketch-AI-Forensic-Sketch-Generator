# VoxSketch: AI Forensic Sketch Generator

> **"Where Voice Meets Vision"**
> An advanced AI-powered forensic sketch generator and database matcher designed to turn verbal witness descriptions into composite sketches and search them against a criminal mugshot database.

---

## 🌟 Key Features

* **🎙️ Voice-to-Sketch Interface:** Real-time speech-to-text transcription via the Web Speech API right in the browser.
* **🧠 Semantic Phrase Matching:** Powered by the SentenceTransformers (`all-MiniLM-L6-v2`) model, matching witness descriptions (e.g. *"long wavy hair"*, *"broad chin"*) to specific sketch components using cosine similarity.
* **🎨 Dynamic Canvas Studio:** Multi-layer sketch composition tool built with Pillow (PIL) and interactive Javascript. Supports dragging, resizing, opacity, and layer ordering.
* **🔎 Forensic Database Matcher:** Deep learning-based facial similarity matching utilizing the Google **FaceNet** / **OpenFace** neural network to identify matching suspect mugshots.
* **⚡ One-Click Startup:** Interactive batch startup script to launch all microservices in separate windows simultaneously.

---

## ⚙️ Tech Stack & Libraries

* **Frontend:** HTML5, Tailwind CSS, Web Speech API, Vanilla Javascript.
* **Backend Framework:** Python Flask.
* **Natural Language Processing:** PyTorch, SentenceTransformers (`all-MiniLM-L6-v2`).
* **Computer Vision:** OpenCV (`cv2`), OpenFace (`openface.nn4.small2.v1.t7`).
* **Image Processing:** Pillow (PIL).

---

## 📂 Project Structure

```text
voxsketch-final-project/
├── run.bat                         # One-click startup script
├── README.md                       # Project documentation
└── voxsketch-final-project/        # Source Directory
    ├── trail/                      # Static landing hub & canvas studio (Port 8002)
    ├── generate-sketch/            # Voice-to-Sketch Flask server (Port 5000)
    └── databasematch/              # Suspect database matcher Flask server (Port 5001)
```

---

## 🚀 Installation & Setup

### Prerequisites
* Python 3.8+ (Python 3.10 recommended)
* Git

### 1. Install Dependencies
Run the following command in your terminal to install the required Python packages globally or in your virtual environment:

```bash
pip install flask sentence-transformers torch numpy opencv-python pillow
```

### 2. Start the Application
To run all three project services simultaneously:

1. Open the project root folder.
2. Double-click the **`run.bat`** file.
3. Once all terminals load, open your web browser and navigate to:
   👉 **[http://localhost:8002](http://localhost:8002)**

---

## 💡 How It Works (Forensic Matcher Pipeline)

1. **Detection:** The Matcher runs a Haar Cascade face detector to crop the suspect's face.
2. **Feature Extraction:** Crops sub-regions representing the eyes, nose, mouth, and hair.
3. **Deep Matching:** Feeds crops into the OpenFace neural net to extract a 128-D vector.
4. **Cosine Similarity:** Performs weighted comparisons to output a confidence match level against pre-indexed suspect mugshots.
