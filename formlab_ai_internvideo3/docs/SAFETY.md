# Safety & Product Boundary

FormLab AI analyzes exercise movement. It is not a medical diagnostic system.

## Allowed product behavior

- report joint angles derived from pose landmarks;
- count and segment repetitions;
- compare repetitions within the same session;
- describe visible movement patterns;
- explain which visual evidence triggered an attention flag;
- state when a criterion cannot be reliably assessed.

## Explicitly excluded

- diagnosis of musculoskeletal injury;
- claim that a movement is medically safe;
- injury-risk percentage;
- rehabilitation prescriptions;
- interpretation of pain as a specific condition;
- nutrition or weight-loss prescriptions in this MVP.

## Pain handling

If the user reports severe or persistent pain, acute swelling, loss of strength, numbness/tingling, or major functional limitation, a form-analysis system should not attempt to "fix" the problem through angle coaching alone.

## Human factors

Body proportions differ. FormLab therefore avoids assuming one universal appearance for a technically acceptable movement and gives priority to:

- measured geometry;
- within-person consistency;
- explicit exercise criteria;
- camera/view limitations.
