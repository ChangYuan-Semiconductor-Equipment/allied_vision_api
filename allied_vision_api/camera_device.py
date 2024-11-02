"""一个相机模块."""
from typing import Optional

from pymba import Vimba
from pymba.camera import Camera

from allied_vision_api.exception import CameraConnectError


class CameraDevice:
    """表示一个相机设备."""

    def __init__(self, vimba: Vimba, camera_id: str, camera_name: Optional[str] = None):
        """初始化 Camera 实例.

        Args:
            vimba (Vimba): Vimba 驱动的实例，用于管理相机.
            camera_id (str): 相机的唯一标识符.
            camera_name (Optional[str]): 相机的名称（默认为 None）。
        """
        self._camera_id = camera_id
        self._camera_name = camera_name
        self._camera_instance = self._get_camera_instance(vimba)
        self._is_open = False
        self._is_arm = False

    def __new__(cls, *args, **kwargs):
        """创建 Camera 实例前进行的操作.

        此方法执行以下步骤:
            1. 检查传入参数的数量是否为 2。
            2. 验证 camera_id 是否有效（非空且非 None）。
            3. 启动 Vimba 驱动。
            4. 检查是否可以找到指定的 camera_id。
            5. 在结束时关闭 Vimba 驱动。

        Args:
            vimba (Vimba): Vimba 驱动实例，用于相机管理。
            camera_id (str): 要连接的相机的唯一标识符。

        Raises:
            CameraConnectError:
                - 如果传入的参数数量不等于 2。
                - 如果 camera_id 是空字符串或 None。
                - 如果在当前 PC 上未发现指定的相机。
        """
        if len(args) != 2:
            raise CameraConnectError(f"连接相机必须要传入两个参数, vimba驱动实例和相机id, 你传入的参数是: {args}!")
        vimba, camera_id = args
        if camera_id == "" or camera_id is None:
            raise CameraConnectError("传入的相机id不能是空字符串和 None!")

        vimba.startup()
        if camera_id not in vimba.camera_ids():
            raise CameraConnectError(f"在此PC上未发现 {camera_id} 相机!")

        return super().__new__(cls)

    def _get_camera_instance(self, vimba: Vimba) -> Camera:
        """获取相机实例.

        Args:
            vimba: vimba 驱动实例.

        Returns:
            Camera: 相机实例对象.
        """
        vimba.startup()
        return vimba.camera(self._camera_id)

    @property
    def camera_id(self):
        """相机的id属性, id不能修改只能获取."""
        return self._camera_id

    @property
    def camera_name(self):
        """相机的name属性, 允许修改, 如果name为空默认name是id."""
        if self._camera_name is None:
            return self._camera_id
        return self._camera_name

    @camera_name.setter
    def camera_name(self, camera_name: str):
        """修改相机的name.

        Args:
            camera_name: 相机的名称
        """
        self._camera_name = camera_name

    @property
    def camera_instance(self):
        """相机的实例对象, 不能修改, 只能获取."""
        return self._camera_instance

    @property
    def is_open(self):
        """相机打开状态属性, 允许修改."""
        return self._is_open

    @is_open.setter
    def is_open(self, state: bool):
        """修改相机的的打开状态.

        Args:
            state: 相机的打开状态.
        """
        self._is_open = state

    @property
    def is_arm(self):
        """相机捕捉帧数据引擎状态, 允许修改."""
        return self._is_arm

    @is_arm.setter
    def is_arm(self, state: bool):
        """修改相机相机捕捉帧数据引擎状态.

        Args:
            state: 相机捕捉帧数据引擎状态.
        """
        self._is_arm = state
