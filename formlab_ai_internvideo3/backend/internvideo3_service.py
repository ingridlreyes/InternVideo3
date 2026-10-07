from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

MODEL_ID = os.getenv("FORMLAB_INTERNVIDEO3_MODEL", "yanziang/InternVideo3-8B-Instruct")
ENABLE = os.getenv("FORMLAB_ENABLE_INTERNVIDEO3", "0").lower() in {"1","true","yes","on"}

class InternVideo3Service:
    def __init__(self) -> None:
        self.model = None
        self.processor = None
        self.torch = None
        self.error: Optional[str] = None

    @property
    def ready(self) -> bool:
        return self.model is not None and self.processor is not None

    def load(self) -> None:
        if self.ready or not ENABLE:
            return
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoProcessor
            self.torch = torch

            kwargs = {
                "device_map": "auto",
                "trust_remote_code": True,
            }
            if torch.cuda.is_available():
                kwargs["dtype"] = torch.bfloat16
                kwargs["attn_implementation"] = "sdpa"
            elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
                kwargs["dtype"] = torch.float16
            else:
                kwargs["dtype"] = torch.float32

            self.model = AutoModelForCausalLM.from_pretrained(MODEL_ID, **kwargs)
            self.processor = AutoProcessor.from_pretrained(MODEL_ID, trust_remote_code=True)
        except Exception as exc:
            self.error = f"{type(exc).__name__}: {exc}"
            self.model = None
            self.processor = None

    def analyze(
        self,
        video_path: str,
        exercise: str,
        biomechanics: dict,
        user_question: str = "",
    ) -> str:
        if not self.ready:
            self.load()
        if not self.ready:
            raise RuntimeError(self.error or "InternVideo3 is not enabled/loaded.")

        criteria_map = {
            "squat": {
                "reference": "ALEX-GYM-1",
                "criteria": [
                    "feet flat",
                    "simultaneous hip/knee bend",
                    "backward hip movement",
                    "neutral lower back",
                    "hips below knees",
                    "feet angled about 30 degrees",
                ],
            },
            "lunge": {
                "reference": "ALEX-GYM-1",
                "criteria": [
                    "shoulder-width heels",
                    "forward gaze",
                    "90-degree knee bend",
                    "natural arm movement",
                    "aligned feet",
                    "straight back",
                    "back knee positioning",
                ],
            },
            "single_leg_rdl": {
                "reference": "ALEX-GYM-1",
                "criteria": [
                    "balance maintenance",
                    "back alignment",
                    "full leg extension",
                    "controlled reversal",
                    "support knee angle",
                ],
            },
            "conventional_deadlift": {
                "reference": "Pose-only experimental rubric; NOT an ALEX-GYM-1 labeled exercise",
                "criteria": [
                    "hip-hinge pattern consistency",
                    "knee/hip coordination",
                    "trunk-orientation consistency",
                    "hip extension at lockout",
                    "left/right symmetry",
                    "bar path only if clearly visible; otherwise unable_to_assess",
                ],
            },
        }
        exercise_spec = criteria_map[exercise]
        criteria = exercise_spec["criteria"]
        criteria_reference = exercise_spec["reference"]

        system_text = """You are the deep-video evidence layer of FormLab AI, a research prototype for exercise technique analysis.
Use ONLY evidence visible in the supplied video and the measured browser biomechanics supplied by the user.
Do not invent angles, repetitions, pain, diagnoses, injury probabilities, body composition, or medical conclusions.
If a criterion cannot be assessed from the camera angle, occlusion, clothing, equipment, or image quality, explicitly say unable_to_assess.
Separate direct visual observations from interpretations. When possible, give timestamps.
Do not tell the user that a movement is medically safe or unsafe.
Focus on training-form observations and within-set consistency."""

        question = user_question.strip() or "Assess the exercise execution and identify the clearest observable technique patterns and within-set drift."
        prompt = f"""{system_text}

Exercise: {exercise}
Exercise-criteria reference: {criteria_reference}
Criteria:
{json.dumps(criteria, ensure_ascii=False)}

Browser-derived biomechanics summary:
{json.dumps(biomechanics, ensure_ascii=False, indent=2)}

User question:
{question}

Return a concise structured report with:
1. exercise_observed
2. observable_criteria: each item must include criterion, status (supported / attention / unable_to_assess), evidence, and timestamp_s if available
3. repetition_or_phase_patterns
4. technique_drift
5. measurement_limitations
6. short_coach_explanation

Never fabricate a numeric measurement that is not present in the browser summary."""

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "video",
                        "video": video_path,
                        "fps": 4,
                        "min_pixels": 128 * 2 * 32 * 32,
                        "max_pixels": 256 * 2 * 32 * 32,
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ]

        inputs = self.processor.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            fps=4,
            return_tensors="pt",
        ).to(self.model.device)

        with self.torch.inference_mode():
            output = self.model.generate(
                **inputs,
                max_new_tokens=1400,
                do_sample=False,
                use_cache=True,
            )
        generated_ids = [o[len(i):] for i, o in zip(inputs.input_ids, output)]
        return self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

service = InternVideo3Service()
