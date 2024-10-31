"""枚举相机可操作的参数."""
from enum import Enum


# pylint: disable=C0103
class CameraFeatureCommand(Enum):
    """枚举相机可操作的参数 class"""

    # 曝光
    ExposureActiveMode = "ExposureActiveMode"
    ExposureAuto = "ExposureAuto"
    ExposureAutoMax = "ExposureAutoMax"
    ExposureAutoMin = "ExposureAutoMin"
    ExposureMode = "ExposureMode"
    ExposureTime = "ExposureTime"

    # gain
    Gain = "Gain"
    GainAuto = "GainAuto"
    GainAutoMax = "GainAutoMax"
    GainAutoMin = "GainAutoMin"
    GainSelector = "GainSelector"

    # ROI
    Height = "Height"
    HeightMax = "HeightMax"
    OffsetY = "OffsetY"
    Width = "Width"
    WidthMax = "WidthMax"
    OffsetX = "OffsetX"

    # binning
    BinningHorizontal = "BinningHorizontal"
    BinningVertical = "BinningVertical"

    # Rate of Capture
    AcquisitionFrameRate = "AcquisitionFrameRate"
