from enum import Enum

class CameraFeatureCommand(Enum):

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