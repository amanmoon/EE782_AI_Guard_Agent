# AI Guard Agent

**Authors:** V Sathvik (22B3946), Aman Moon (22B1216)
**Date:** November 27, 2025

## Abstract
This system details the architecture and implementation of an AI Guard Agent. The system integrates Automatic Speech Recognition (ASR), Facial Recognition, and Large Language Models (LLM) to create an interactive security monitor. The application operates via a multi-threaded Python backend, utilizing OpenAI's Whisper for audio transcription, Google's Gemma for conversational intelligence, and dlib-based models for biometric verification.

## 1. Introduction
The AI Guard Agent is a desktop-based security application designed to monitor an environment through audio-visual inputs. The system operates in two distinct states: a passive listening mode and an active "Guard Mode".

* **Activation:** Upon activation via specific voice commands, the system employs computer vision to verify the identity of individuals in the frame.
* **Response:** Unverified individuals trigger a defensive persona in the conversational agent, while verified users are greeted normally.
* **Performance:** The implementation relies heavily on local inference using CUDA-accelerated PyTorch models to ensure low-latency performance.

## 2. System Architecture
The backend logic is implemented in Python, structured around concurrent execution to handle blocking I/O operations (audio recording and video capture) without freezing the main application loop. Inter-process communication and UI updates are managed via the **Eel library**, bridging the Python backend with the frontend interface.

The architecture consists of three primary worker threads:
1.  **Audio Processor:** Handles raw PCM data capture, Voice Activity Detection (VAD), and Fast Fourier Transform (FFT) for visualization.
2.  **Vision Engine:** Performs face detection and embedding comparison against a trusted database.
3.  **Inference Engine:** Manages the LLM context and text-to-speech (TTS) synthesis.

## 3. Audio Subsystem Implementation
The audio processing logic prioritizes real-time visualization and command latency.

### 3.1 Signal Processing and Visualization
The `RealTime AudioProcessor` captures audio at a sample rate of 16kHz. To drive the user interface visualization, raw audio chunks are decomposed into frequency bins ranging from 50Hz to 16kHz using Fast Fourier Transform (FFT).

The magnitude is calculated as:
$$M_{band}=\frac{1}{N}\sum_{f=f_{min}}^{f_{max}}|FFT(x)|$$

To map these magnitudes to a visual scale, a logarithmic transformation is applied to approximate human loudness perception:
`log_magnitudes = np.log1p(band_magnitudes)`

### 3.2 Voice Activity Detection (VAD)
To prevent processing ambient silence, the system implements dynamic VAD. A `calibrate` method samples ambient noise to establish a baseline amplitude. The silence threshold is set dynamically:

$$T_{silence} = \max(100, A_{ambient\_max} \times 1.2)$$

Transmission to the recognition queue occurs only when the amplitude exceeds $T_{silence}$ for a sustained duration.

### 3.3 Command Recognition
The system utilizes fuzzy string matching (fuzzywuzzy and jellyfish libraries) to handle variations in spoken commands. The matching algorithm combines token set ratio and phonetic matching (Metaphone algorithm).

$$combined\_score = (text\_score \times 0.4) + (phonetic\_score \times 0.6)$$

A strict threshold of 85% confidence is required to toggle the guard mode state.

## 4. Computer Vision Module
Facial recognition operates on a strict producer-consumer model within a daemon thread to maintain video feed fluidity.

* **Enrollment:** The system utilizes the dlib HOG (Histogram of Oriented Gradients) face detector to generate 128-dimensional encodings for trusted faces.
* **Verification:** The system calculates the Euclidean distance between the live face encoding ($E_{live}$) and trusted encodings ($E_{trusted}$). Verification is confirmed if:
    $$||E_{live}-E_{trusted}|| < 0.6$$

To prevent false negatives from motion blur, the system implements temporal smoothing, waiting for a 10-second confirmation window before flagging a user as unauthorized.

## 5. Generative AI Integration
The conversational core is powered by Google's Gemma model (`google/gemma-3n-E4b-it`). To accommodate consumer hardware, the model is loaded with `torch.bfloat16` precision on CUDA devices to reduce VRAM usage.

### Context-Aware Prompt Engineering
The behavioral logic is controlled via dynamic prompt injection based on verification status:
1.  **Verified State:** Instructions to behave as a helpful assistant.
2.  **Unverified State (Guard Mode):** strictly engineered for security:
    > "Instructions: You are a guard AI. An unverified user is trying to talk to you. Politely but firmly, tell them to please kindly leave the room."

## 6. Integration and Control Flow
The application flow follows a strict state machine:
1.  **Idle:** Listens for "Activate" keyword.
2.  **Active (Guard Mode):**
    * Vision thread updates `is_verified` flag.
    * Audio thread captures input.
    * Whisper transcribes input.
    * Gemma generates response based on context.
    * Response is synthesized via `pyttsx3`.

---
