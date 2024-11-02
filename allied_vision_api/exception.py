"""异常类."""


class CameraBaseException(Exception):
    """Camera 异常基类."""


class CameraFindError(CameraBaseException):
    """未找到相机异常."""


class CameraConnectError(CameraBaseException):
    """Camera 连接时异常."""


class CameraFeatureSetError(CameraBaseException):
    """Camera 设置参数值时出现异常."""


class CameraRunTimeError(CameraBaseException):
    """Camera 运行时异常."""
