"""异常类."""


class CameraBaseException(Exception):
    """Camera 异常基类."""


class CameraFindError(CameraBaseException):
    """未找到相机异常."""


class CameraConnectError(CameraBaseException):
    """Camera 连接时异常."""


class CameraFeatureSetError(CameraBaseException):
    """Camera 设置参数值时出现异常."""


class CameraVideoOpenError(CameraBaseException):
    """打开相机保存的视频异常."""


class CameraPhotoOpenError(CameraBaseException):
    """打开相机保存的图片异常."""
