from typing import Any

import numpy as np
from numpy.typing import NDArray

FloatAudioArray = NDArray[np.floating[Any]]
FeatureMatrix = NDArray[np.floating[Any]]
ModelInput = NDArray[np.float32]
PianoRoll = NDArray[np.uint8]
