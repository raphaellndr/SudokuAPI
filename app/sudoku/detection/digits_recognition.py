from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort
from cv2.typing import MatLike


def detect_digits(digits: list[MatLike]) -> list[int]:
    """Detects digits in the boxes using the trained ONNX model.

    Args:
        digits (list[MatLike]): list of digit images.

    Returns:
        list[int]: list of detected digits as integers.
    """
    model_path = Path(__file__).parent / "digits_classifier_model.onnx"
    ort_session = ort.InferenceSession(model_path)

    predicted_digits = []
    for image in digits:
        img = np.asarray(image)
        img = cv2.resize(img, (28, 28))

        # Convert to grayscale if the image has multiple channels
        if len(img.shape) == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Normalize
        img = img / 255.0

        # Reshape for model input: (1, 28, 28, 1) - grayscale
        img = img.reshape(1, 28, 28, 1).astype(np.float32)

        # Perform prediction with ONNX Runtime
        ort_inputs = {ort_session.get_inputs()[0].name: img}
        ort_outs = ort_session.run(None, ort_inputs)

        prediction = ort_outs[0]
        class_index = np.argmax(prediction, axis=-1)
        probability_value = np.amax(prediction, axis=-1)

        if probability_value > 0.8:
            predicted_digits.append(int(class_index[0]))
        else:
            predicted_digits.append(0)

    return predicted_digits


__all__ = ["detect_digits"]
