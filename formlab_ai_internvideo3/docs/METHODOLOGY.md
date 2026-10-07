# FormLab AI — Methodology

## 1. Objective

Convert an exercise video into a traceable set of movement observations and explanations without conflating:

- pixels,
- measured pose,
- deterministic calculations,
- and generative model interpretation.

## 2. Primary research dataset: ALEX-GYM-1

ALEX-GYM-1 was selected over a generic exercise-classification dataset because it contains **criterion-specific exercise-quality annotations**.

The published dataset contains 670 videos from 45 participants:

- 295 squats;
- 106 lunges;
- 269 single-leg Romanian deadlifts.

It provides synchronized frontal/lateral views and 33-pose-landmark data.

The paper defines six squat criteria, seven lunge criteria and five single-leg RDL criteria.

FormLab does not claim to have trained on the full dataset inside this deliverable because the original author-hosted media and weights are not copied into the project. Instead:

- the published criteria are used as the evidence rubric;
- the project includes a dataset adapter;
- the web layer is independently executable with a pretrained pose estimator;
- the deep-video layer is independently executable with InternVideo3.

## 3. Fast pose layer

MediaPipe Pose Landmarker runs in the browser in VIDEO mode.

For each processed frame:

1. detect the person's pose;
2. retain normalized landmarks for drawing;
3. use world landmarks for 3D angle calculation where available;
4. derive joint and trunk metrics.

The basic joint-angle calculation is:

\[
\theta = \arccos \frac{(A-B)\cdot(C-B)}
{\|A-B\|\|C-B\|}
\]

where B is the joint of interest.

Examples:

- knee: hip → knee → ankle;
- hip: shoulder → hip → knee;
- elbow: shoulder → elbow → wrist.

Trunk lean is calculated as the angle between the shoulder-to-hip vector and the vertical axis.

## 4. Repetition segmentation

The MVP uses transparent state-machine thresholds solely to segment motion into repetitions.

These thresholds are **engine rules**, not claims that a certain angle is universally "correct."

Current rules:

- squat/lunge: enter down phase when the primary knee angle is below 115°, complete when it returns above 155°;
- single-leg RDL: enter down phase when mean hip angle is below 120°, complete when it returns above 155°;
- conventional deadlift: enter active hinge phase when mean hip angle is below 125°, complete when it returns above 155°.

Rep segmentation can later be replaced with an ALEX-GYM-1-trained temporal model.

## 5. Technique attention logic

The fast layer avoids a universal "good/bad form" score.

It highlights:

- poor pose visibility;
- large left/right knee-angle differences;
- trunk-lean drift relative to the user's first complete repetitions;
- whether the screen-space hip landmark passed below the knee landmark during a squat.

The last measurement is explicitly camera-dependent.

## 6. InternVideo3 deep layer

InternVideo3-8B-Instruct is used for temporal/contextual interpretation.

Input:

- original uploaded video;
- exercise identity;
- deterministic biomechanics summary;
- ALEX-GYM-1 criteria;
- optional user question.

The model prompt requires:

- no invented numeric measurements;
- no diagnosis;
- no injury-probability claims;
- timestamps when supported;
- `unable_to_assess` for visually unsupported criteria.

InternVideo3 is therefore not the source of joint-angle measurements. It is the layer that explains longer-range patterns and contextual criteria.

## 7. Why multimodal

ALEX-GYM-1 itself reports complementary strengths between pose and visual streams. FormLab mirrors that design principle:

- explicit geometry → pose engine;
- holistic/temporal context → video model.

This is preferable to asking a single LLM to infer all kinematics from pixels.

## 8. Provenance

Every result belongs to one of three classes:

### OBSERVED

Direct output of pose detection from the actual user video.

### DERIVED

Deterministic calculations using observed pose landmarks.

### MODEL

InternVideo3-generated interpretation.

The UI never labels MODEL output as a measured angle.

## 9. Known limitations

- single-camera depth ambiguity;
- occlusion by barbells, racks or clothing;
- camera-height and camera-angle effects;
- MediaPipe world landmarks are model estimates, not optical motion-capture ground truth;
- rep thresholds are MVP segmentation rules;
- deep video interpretation may be wrong and must remain evidence-grounded;
- ALEX-GYM-1 views and participant distribution may not represent every real gym setting.

## 10. Future validation

A portfolio-to-research upgrade should:

1. download the full ALEX-GYM-1 processed data;
2. reproduce the author split or preferably create participant-level splits;
3. compare MediaPipe-derived criteria with dataset labels;
4. measure per-criterion precision/recall/F1;
5. calibrate rep segmentation from observed training data;
6. evaluate across camera viewpoints;
7. compare InternVideo3 criterion descriptions against expert annotations.


## Conventional deadlift extension

ALEX-GYM-1's published third exercise is the **single-leg Romanian deadlift**, not the conventional bilateral deadlift.

For that reason conventional deadlift is implemented as a separate experimental mode. Its numerical outputs come from the same observed MediaPipe landmarks and deterministic kinematics as the other modes, but no ALEX-GYM-1 label performance is attributed to it.

The thresholds used to segment repetitions are state-machine rules, not universal prescriptions of correct technique.
