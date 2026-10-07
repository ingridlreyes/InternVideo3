# FormLab AI — InternVideo3 Exercise Intelligence

FormLab AI is an interactive research prototype for exercise-technique analysis.

It combines:

1. **Real-time pose measurement in the browser**
   - MediaPipe Pose Landmarker
   - 33 pose landmarks
   - world-landmark joint angles
   - rep segmentation
   - within-session drift and symmetry checks

2. **Deep video reasoning**
   - InternVideo3-8B-Instruct
   - long-horizon video understanding
   - temporal evidence + natural-language explanation
   - no fabricated deep-analysis output when the backend is unavailable

3. **Exercise-quality research reference**
   - ALEX-GYM-1
   - 670 videos
   - squat, lunge, single-leg Romanian deadlift
   - criterion-specific biomechanical annotations

4. **Conventional deadlift mode**
   - real pose/angle analysis from the uploaded video
   - rep segmentation and within-session drift
   - explicitly marked experimental because ALEX-GYM-1 does not provide conventional-deadlift labels

## Quick start — browser analysis

From the project root:

```bash
python serve.py
```

Open:

```text
http://127.0.0.1:8000/FormLab_AI.html
```

Why localhost instead of double-clicking the HTML?

- webcam access is reliably available on localhost;
- browser module loading is more consistent;
- the page can connect to the optional backend on port 8001.

The first pose-model load requires internet access because the page uses the official MediaPipe Tasks Vision browser package and model asset.

## What works without InternVideo3

The browser layer is independently functional.

Upload a video or enable the camera. It calculates:

- mean knee angle;
- mean hip angle;
- mean elbow angle;
- trunk-lean proxy;
- left/right knee-angle difference;
- pose visibility;
- repetition timing;
- minimum joint angles per rep;
- within-session technique drift signals.

The video itself is not uploaded anywhere by the browser pose layer.

## Deep analysis with InternVideo3

InternVideo3 is intentionally separated from the fast pose path because an 8B long-video model is much heavier than a real-time pose estimator.

Create a Python environment with a compatible GPU stack, then:

```bash
pip install -r backend/requirements.txt
export FORMLAB_ENABLE_INTERNVIDEO3=1
uvicorn backend.app:app --host 127.0.0.1 --port 8001
```

The page will detect the backend automatically.

The backend uses:

```text
yanziang/InternVideo3-8B-Instruct
```

and follows the official video inference pattern with video sampling at 4 FPS.

### Hardware note

The real-time browser path is lightweight compared with InternVideo3. The deep model should be treated as a GPU workload. A cloud GPU is the practical option if a local machine does not have enough unified/VRAM memory.

## Dataset choice

The primary exercise-quality dataset is **ALEX-GYM-1** because its target matches the product better than generic action-recognition datasets.

Published composition:

- 295 squat videos;
- 106 lunge videos;
- 269 single-leg Romanian deadlift videos;
- 45 participants;
- frontal + lateral views;
- 33 pose landmarks;
- 5–7 explicit biomechanical criteria per exercise.

The authors report the following multimodal results:

| Exercise | Hamming loss | F1 |
|---|---:|---:|
| Squat | 0.0259 | 0.9706 |
| Single-leg RDL | 0.0488 | 0.9347 |
| Lunge | 0.0756 | 0.9097 |

These are **published ALEX-GYM-1 results**, not results from a FormLab user video.

The original ALEX-GYM-1 media and weights are not redistributed in this ZIP. The source manifest points to the authors' repository/data links.

## Validate a local ALEX-GYM-1 download

After downloading the authors' processed dataset:

```bash
python scripts/alexgym1_adapter.py \
  --data-dir /path/to/ALEX-GYM-1 \
  --output data/alex_gym_1_local_summary.json
```

The adapter checks:

- required Excel/JSON files;
- metadata vs pose-row counts;
- rating columns;
- observed criterion prevalence.

It stops on mismatches instead of filling missing values.

## Why not use InternVideo3 for every frame?

Because that would be inefficient and would make numeric biomechanics less transparent.

Architecture:

```text
              UPLOADED / LIVE VIDEO
                       |
              ---------------------
              |                   |
              v                   v
      MediaPipe Pose        InternVideo3
      low-latency           deep temporal reasoning
              |                   |
      33 landmarks                |
              |                   |
      deterministic angles         |
      + rep segmentation           |
              |                   |
              ------ evidence -----
                       |
                       v
              FormLab explanation
```

The pose engine is the **measurement layer**.
InternVideo3 is the **context/reasoning layer**.

## Evidence labels

- `OBSERVED`: pose landmarks detected from frames.
- `DERIVED`: angles, timing, symmetry, repetition summaries.
- `MODEL`: InternVideo3 interpretation.

No fake pose values or sample user results are included in the UI.

## Technique scope

The browser path is intentionally conservative.

For example, ALEX-GYM-1 labels **neutral lower back** for squat, but MediaPipe does not provide individual lumbar vertebral landmarks. FormLab therefore marks that criterion as view/model-dependent rather than pretending to directly measure lumbar neutrality.

Likewise, a monocular camera cannot robustly establish every foot-contact or foot-angle criterion from every viewpoint.

## Safety boundary

This is not a medical device.

FormLab does **not**:

- diagnose injuries;
- estimate injury probability;
- prescribe treatment;
- infer medical conditions from posture;
- certify that an exercise is medically safe.

It can describe measured motion and point out visible/within-session technique changes.

## Project structure

```text
formlab_ai_internvideo3/
├── FormLab_AI.html
├── serve.py
├── backend/
│   ├── app.py
│   ├── internvideo3_service.py
│   └── requirements.txt
├── scripts/
│   └── alexgym1_adapter.py
├── data/
│   └── alex_gym_1_manifest.json
├── metadata/
│   ├── source_manifest.json
│   └── build_validation.json
├── docs/
│   ├── ARCHITECTURE.mmd
│   ├── METHODOLOGY.md
│   └── SAFETY.md
└── web/
    └── index.html
```

## Public sources

- ALEX-GYM-1 repository:
  https://github.com/AhmedYasserrr/ALEX-GYM-1
- ALEX-GYM-1 paper:
  https://www.scitepress.org/Papers/2025/136694/136694.pdf
- InternVideo3:
  https://github.com/OpenGVLab/InternVideo/tree/main/InternVideo3
- MediaPipe Pose Landmarker:
  https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker/web_js


## Conventional deadlift

FormLab now includes a `conventional_deadlift` mode.

This mode uses real MediaPipe pose observations and deterministic angle calculations. It is **not presented as an ALEX-GYM-1-trained exercise**, because the ALEX-GYM-1 paper specifies *single-leg Romanian deadlifts* for its 269 deadlift videos.

The conventional-deadlift mode therefore focuses on:

- hip-hinge trajectory;
- knee/hip coordination;
- trunk-orientation consistency;
- lockout return;
- left/right angular symmetry;
- rep-to-rep drift.

Bar path is not numerically measured by the pose engine because the barbell is not a human landmark. It is left to a future barbell detector or to evidence-grounded deep-video interpretation when visibly supported.
