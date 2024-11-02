"""Allied vision API."""
import datetime
import logging
import os
import sys
import threading
import time
from ctypes import ArgumentError
from logging.handlers import TimedRotatingFileHandler
from typing import Optional, Callable, Union, Dict

import cv2
from pymba import Vimba, VimbaException
from pymba.camera import Camera, SINGLE_FRAME, CONTINUOUS

from allied_vision_api.camera_device import CameraDevice
from allied_vision_api.camera_feature_command import CameraFeatureCommand
from allied_vision_api.exception import CameraFeatureSetError


# pylint: disable=C0301, disable=R0917, disable=R0913, disable=R0904
class CameraApi:
    """Allied vision api.

    相机三大组件:
        - vimba: 控制相机的驱动, 操作相机的一切前提是 vimba驱动已打开.
        - open_camera: 表示程序和相机建立了连接, 可以通过代码操作相机, 而不是打开了相机正在捕捉数据.
        - arm_camera: 表示打开了相机的捕捉数据引擎, 相机真正在捕捉数据.

    获取相机参数值前提条件:
        - is_vimba_open = True: vimba驱动已打开.
        - is_open = True: 程序已和相机建立连接.
        - is_arm = True or False: 相机捕捉帧数据引擎打开或关闭不影响获取参数值.

    设置相机参数值前提条件:
        - is_vimba_open = True: vimba驱动已打开.
        - is_open = True: 程序已和相机建立连接.
        - is_arm = False: 相机捕捉帧数据引擎必须关闭.

    拍照前提条件:
        - is_vimba_open = True: vimba驱动已打开.
        - is_open = True: 程序已和相机建立连接.
        - is_arm = True: 相机捕捉帧数据引擎已打开.
    """

    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s"

    def __init__(self):
        self._logger = logging.getLogger(f"{self.__module__}.{self.__class__.__name__}")
        self._file_handler = None
        self._set_log()

        self._vimba = Vimba()
        self._is_vimba_open = False
        self._cameras_instance = self._get_all_camera_instance()

    @property
    def logger(self):
        """CameraApi 的日志器."""
        return self._logger

    @property
    def file_handler(self):
        """保存日志的日志器."""
        if self._file_handler is None:
            log_dir = f"{os.getcwd()}/log"
            os.makedirs(log_dir, exist_ok=True)
            file_name = f"{log_dir}/{datetime.datetime.now().strftime('%Y-%m-%d')}_{os.path.basename(os.getcwd())}.log"
            self._file_handler = TimedRotatingFileHandler(
                file_name, when="D", interval=1, backupCount=10, encoding="UTF-8"
            )
        return self._file_handler

    @property
    def vimba(self):
        """vimba驱动实例."""
        return self._vimba

    @property
    def is_vimba_open(self):
        """vimba驱动状态."""
        return self._is_vimba_open

    @is_vimba_open.setter
    def is_vimba_open(self, state: bool):
        """设置vimba驱动状态.

        Args:
            state: vimba驱动状态
        """
        self._is_vimba_open = state

    @property
    def cameras_instance(self) -> dict:
        """获取当前PC连接的所有相机实例对象.

        Returns:
            dict: 当前PC连接的所有相机实例对象
        """
        return self._cameras_instance

    @staticmethod
    def get_expect_timestamp(timestamp: Union[str, int, float]) -> str:
        """根据传进来的时间戳得到处理后的时间戳字符串.

        Args:
            timestamp: 传进来的时间戳.

        Returns:
            str: 期待的时间戳.
        """
        integer_decimal_list = str(timestamp).split(".")
        if len(integer_decimal_list) == 1:
            return f"{integer_decimal_list[0]:>08}.{'0' * 8}"
        return f"{integer_decimal_list[0]:>08}.{integer_decimal_list[1]:>08}"

    def _get_all_camera_instance(self) -> Dict[str, CameraDevice]:
        """获取所有的相机对象."""
        self.open_vimba()
        cameras_object = {}
        for camera_id in self._vimba.camera_ids():
            cameras_object.update({camera_id: CameraDevice(self._vimba, camera_id)})
        return cameras_object

    def _set_log(self):
        """设置日志."""
        self.file_handler.setFormatter(logging.Formatter(self.LOG_FORMAT))
        self.file_handler.setLevel(logging.INFO)
        self._logger.addHandler(self.file_handler)
        if sys.version_info.minor == 11:
            logging.basicConfig(level=logging.INFO, encoding="UTF-8", format=self.LOG_FORMAT)
        else:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(self.LOG_FORMAT))
            console_handler.setLevel(logging.INFO)
            self._logger.addHandler(console_handler)
            self._logger.setLevel(logging.INFO)

    def open_vimba(self):
        """判断是否已经实例化了vimba的 C API."""
        if not self._is_vimba_open:
            self._vimba.startup()
            self._is_vimba_open = True
            self._logger.info("*** vimba 驱动已打开 ***")

    def open_camera(self, id_or_name: str):
        """打开指定相机.

        Args:
            id_or_name: 相机id或name.
        """
        camera_id = self.get_camera_id_with_name(id_or_name)
        self.open_vimba()
        if not self.get_camera_open_state(camera_id):
            self.get_camera_instance(camera_id).open()
            self.cameras_instance[camera_id].is_open = True
            self._logger.info("*** 相机已打开 ***")

    def close_vimba(self) -> None:
        """相机操作结束后需要关闭vimba"""
        if self._is_vimba_open:
            self._vimba.shutdown()
            self._is_vimba_open = False
            self._logger.info("*** vimba 驱动已关闭 ***")

    def close_camera(self, id_or_name: str):
        """关闭相机.

        Args:
            id_or_name: 相机id或name.
        """
        camera_id = self.get_camera_id_with_name(id_or_name)
        if self.get_camera_open_state(camera_id):
            self.get_camera_instance(camera_id).close()
            self.cameras_instance[camera_id].is_open = False
            self._logger.info("*** 相机已关闭 ***")

    def arm_camera(self, id_or_name: str, mode=SINGLE_FRAME, call_back=None):
        """打开相机引擎.

        Args:
            id_or_name: 相机id或name.
            mode: 引擎模式, 默认是 SINGLE_FRAME 模式.
            call_back: 每个帧准备就绪时调用的函数引用
        """
        camera_id = self.get_camera_id_with_name(id_or_name)
        self.open_camera(camera_id)
        if not self.get_camera_arm_state(camera_id):
            self.get_camera_instance(camera_id).arm(mode, callback=call_back)
            self.cameras_instance[camera_id].is_arm = True
            self._logger.info("*** 相机捕捉引擎已打开 ***")

    def disarm_camera(self, id_or_name: str):
        """关闭指定相机的引擎.

        Args:
            id_or_name: 相机id或name.
        """
        camera_id = self.get_camera_id_with_name(id_or_name)
        if self.get_camera_arm_state(camera_id):
            self.get_camera_instance(camera_id).disarm()
            self.cameras_instance[camera_id].is_arm = False
            self._logger.info("*** 相机捕捉引擎已关闭 ***")

    def get_camera_ids(self) -> list:
        """获取所有相机的id.

        Returns:
            list: 所有已连接的相机列表
        """
        return list(self.cameras_instance.keys())

    def get_camera_id_name_map(self) -> Dict[str, str]:
        """获取相机名称和id的对应关系.

        returns:
            Dict[str, str]: 返回相机的当前对应关系, key是相机id, value是相机name.
        """
        return {camera_id: camera_instance.camera_name for camera_id, camera_instance in self.cameras_instance.items()}

    def get_camera_name(self, id_or_name: str) -> str:
        """获取相机的名称.

        Args:
            id_or_name: 相机的id或name.

        Returns:
            str: 相机对应的名称.
        """
        id_name_map = self.get_camera_id_name_map()
        return id_name_map[id_or_name] if id_or_name in id_name_map else id_or_name

    def get_camera_arm_state(self, id_or_name: str) -> bool:
        """获取相机的arm状态.

        Args:
            id_or_name: 相机id或name.

        Returns:
            bool: True -> 已打开, False -> 已关闭.
        """
        return self.cameras_instance[self.get_camera_id_with_name(id_or_name)].is_arm

    def get_camera_open_state(self, id_or_name: str) -> bool:
        """获取相机的打开状态.

        Args:
            id_or_name: 相机id或name.

        Returns:
            bool: True -> 已打开, False -> 已关闭.
        """
        return self.cameras_instance[self.get_camera_id_with_name(id_or_name)].is_open

    def get_camera_id_with_name(self, camera_name: str) -> Optional[str]:
        """根据相机名称获取相机id.

        Returns:
            Optional[str]: 返回相机id或None.
        """
        if camera_name in self.cameras_instance:
            return camera_name
        for _camera_id, camera_instance in self.cameras_instance.items():
            if camera_name == camera_instance.camera_name:
                return _camera_id
        return None

    def get_camera_instance(self, id_or_name: str) -> Optional[Camera]:
        """根据相机id获取相机的实例对象.

        Args:
            id_or_name: 相机id或name.

        Returns:
            Optional[Camera]: 返回相机实例或者None.
        """
        if id_or_name:
            return self.cameras_instance[self.get_camera_id_with_name(id_or_name)].camera_instance
        return None

    def get_feature_value(self, camera_id, feature_name: str) -> Union[str, int, float]:
        """获取当前参数, 前提是相机已打开, 相机已打开代表程序连接了相机而不是相机处于捕捉数据状态.

        Args:
            camera_id: 相机id.
            feature_name: 参数选项的名称.

        Returns:
            Union[tuple, list]: 返回参数可选值的范围.
        """
        feature_instance = self.get_camera_instance(camera_id).feature(feature_name)
        self.open_camera(camera_id)
        return feature_instance.value

    def get_feature_range(self, camera_id, feature_name: str) -> Union[tuple, list]:
        """获取参数值的范围.

        Args:
            camera_id: 相机id.
            feature_name: 参数选项的名称.

        Returns:
            Union[tuple, list]: 返回参数可选值的范围.
        """
        feature_instance = self.get_camera_instance(camera_id).feature(feature_name)
        self.open_camera(camera_id)
        return feature_instance.range

    def set_feature_value(self, id_or_name: str, feature_name: str = None, value: Union[int, float, str] = None):
        """设置指定相机的参数值, 设置前提要打开相机.

        Args:
            id_or_name: 相机id或name.
            feature_name: 要设定的参数名称.
            value: 设定值.

        Raises:
            CameraFeatureSetError: 当设置的值类型不正确, 值超出允许范围时抛出异常.
        """
        if not self.get_camera_open_state(id_or_name):
            self.open_camera(id_or_name)

        self.disarm_camera(id_or_name)
        feature = self.get_camera_instance(id_or_name).feature(feature_name)
        self._logger.info("*** 当前 %s 值 *** -> %s", feature_name, feature.value)
        try:
            feature.value = value
        except VimbaException as e:
            self._logger.error("*** 设置参数 %s = %s 失败 *** -> 当前值 %s ", feature_name, value, feature.value)
            self._logger.error("*** 失败原因 *** -> 超出允许设置范围 %s", feature.range)
            raise CameraFeatureSetError(f"超出允许设置范围 {feature.range}") from e
        except ArgumentError as e:
            type_ = type(feature.value)
            self._logger.error("*** 设置参数 %s = %s 失败 *** -> 当前值 %s ", feature_name, value, feature.value)
            self._logger.error("*** 失败原因 *** -> 设置的值类型 %s 不正确, 正确类型是 %s", type(value), type_)
            raise CameraFeatureSetError(f"设置的值类型不正确, 正确类型是 {type(feature.value)}") from e

        self._logger.info("*** 设置成功 *** -> 设置后 %s 值是 %s", feature_name, feature.value)

    def set_one_quarter(self, id_or_name: str):
        """设置相机捕捉区域为中间四分之一.

        Args:
            id_or_name: 相机id或name.
        """
        _feature_values = {
            CameraFeatureCommand.Width.value: 2664,
            CameraFeatureCommand.Height.value: 2304,
            CameraFeatureCommand.OffsetY.value: 1152,
            CameraFeatureCommand.OffsetX.value: 1344
        }
        self.set_multiple_feature(id_or_name, _feature_values)

    def set_one_sixteenth(self, id_or_name: str):
        """设置相机捕捉区域为中间十六分之一.

        Args:
            id_or_name: 相机id或name.
        """
        _feature_values = {
            CameraFeatureCommand.Width.value: 1336,
            CameraFeatureCommand.Height.value: 1152,
            CameraFeatureCommand.OffsetY.value: 1728,
            CameraFeatureCommand.OffsetX.value: 2000
        }
        self.set_multiple_feature(id_or_name, _feature_values)

    def set_multiple_feature(self, id_or_name: str, feature_name_values: Dict[str, Union[str, int, float]]):
        """设置多个参数.

        Args:
            id_or_name: 相机id或name.
            feature_name_values: 要设置的参数字典.
        """
        for feature_name, set_value in feature_name_values.items():
            self.set_feature_value(id_or_name, feature_name, set_value)

    def set_full(self, id_or_name: str):
        """设置相机捕捉区域为全部区域.

        Args:
            id_or_name: 相机id或name.
        """
        max_width = self.get_feature_value(id_or_name, CameraFeatureCommand.WidthMax.value)
        max_height = self.get_feature_value(id_or_name, CameraFeatureCommand.HeightMax.value)
        _feature_values = {
            CameraFeatureCommand.Width.value: max_width,
            CameraFeatureCommand.Height.value: max_height,
            CameraFeatureCommand.OffsetY.value: 0,
            CameraFeatureCommand.OffsetX.value: 0,
            CameraFeatureCommand.BinningHorizontal.value: 1,
            CameraFeatureCommand.BinningVertical.value: 1
        }
        self.set_multiple_feature(id_or_name, _feature_values)

    def set_camera_id_name_map(self, id_name_map: Dict[str, str]) -> None:
        """设置每个相机的名称, 和相机id一一对应.

        Args:
            id_name_map: 相机id和name的对应关系.
        """
        for camera_id, camera_name, in id_name_map.items():
            if camera_id in self.cameras_instance:
                self.cameras_instance[camera_id].camera_name = camera_name

    def acquire_one(self, id_or_name: str, project_name: str = "", timestamp: Union[int, float, str] = "",
                    camera_close: bool = False, vimba_close: bool = False, save_dir: str = None):
        """采集一张照片, 前提是打开vimba驱动, 打开相机, 打开相机engineer (arm).

        Args:
            id_or_name: 相机id或name.
            project_name: 所属项目.
            timestamp: 传进来的时间戳.
            camera_close: 是否关闭相机.
            vimba_close: 是否关闭vimba.
            save_dir: 指定图片保存目录.
        """
        self.open_vimba()
        self.open_camera(id_or_name)
        self.arm_camera(id_or_name)
        camera_instance = self.get_camera_instance(id_or_name)
        self._logger.info("*** 开始捕捉帧数据 ***")
        frame = camera_instance.acquire_frame()
        self._logger.info("*** 结束捕捉帧数据 ***")

        self.save_photo_local(frame, project_name, self.get_expect_timestamp(timestamp), id_or_name, save_dir=save_dir)

        if camera_close:
            self.disarm_camera(id_or_name)
            self.close_camera(id_or_name)
        if vimba_close:
            self.close_vimba()

    def acquire_continue(self, id_or_name: str, project_name="", timestamp="", acquire_one=False, interval=100,
                         continue_time=5, camera_close=False, vimba_close=False, save_dir=None):
        """指定间隔时间, 连续采集图片.

        Args:
            id_or_name: 相机id或name.
            project_name: 项目名称.
            timestamp: 传进来的时间戳.
            acquire_one: 是否只拍一个照片.
            interval: 间隔时间, 单位是毫秒.
            continue_time: 持续时间, 单位是秒.
            camera_close: 是否关闭相机.
            vimba_close: 是否关闭vimba.
            save_dir: 指定图片保存目录.
        """
        timestamp = self.get_expect_timestamp(timestamp)
        if acquire_one:
            self.acquire_one(
                id_or_name, project_name, timestamp,
                camera_close=camera_close, vimba_close=vimba_close, save_dir=save_dir
            )
            return
        self.open_vimba()
        self.open_camera(id_or_name)
        self.arm_camera(
            id_or_name, CONTINUOUS, self.generate_save_photo_func(
                id_or_name, project_name, timestamp, interval, save_dir
            )
        )
        camera_instance = self.get_camera_instance(id_or_name)
        camera_instance.start_frame_acquisition()
        time.sleep(continue_time)
        camera_instance.stop_frame_acquisition()

        if camera_close:
            self.disarm_camera(id_or_name)
            self.close_camera(id_or_name)
        if vimba_close:
            self.close_vimba()

    def save_photo_local(self, frame, project_name: str, timestamp: str, id_or_name: str, save_dir=None):
        """将采集的图片保存在本地.

        Args:
            frame: 采集到的图像帧数据.
            project_name: 项目名称, example: seethru or display.
            timestamp: 传进来的时间戳.
            id_or_name: 相机id或name.
            save_dir: 指定图片保存目录.
        """
        camera_name = self.get_camera_name(id_or_name)
        exposure_time = f"{int(self.get_feature_value(id_or_name, CameraFeatureCommand.ExposureTime.value)):>08}"

        def _save_photo_local():
            _frame_id = f"{frame.data.frameID:>04}"
            _file_name = f"{project_name}.{camera_name}.{exposure_time}.{timestamp}.{_frame_id}.png"
            if save_dir:
                os.makedirs(save_dir, exist_ok=True)
                file_path = os.path.join(save_dir, _file_name)
            else:
                file_path = _file_name
            cv2.imwrite(file_path, frame.buffer_data_numpy())  # pylint: disable=E1101

        threading.Thread(target=_save_photo_local, daemon=False).start()

    def generate_save_photo_func(
            self, camera_id, project_name: str, timestamp: str, interval: int, save_dir=None
    ) -> Callable:
        """生成保存图片的函数.

        Args:
            camera_id: 相机id.
            project_name: 项目名称.
            timestamp: 传进来的时间戳.
            interval: 间隔时间.
            save_dir: 指定图片保存目录.

        Returns:
            Callable: 保存图片的函数.
        """
        exposure_time = f"{int(self.get_feature_value(camera_id, CameraFeatureCommand.ExposureTime.value)):>08}"

        def _save_photo_handler(_frame):
            """保存图片.

            Args:
                _frame: 捕捉到的帧数据.
            """
            _frame_id = f"{_frame.data.frameID:>04}"

            def _save_photo():
                _image = _frame.buffer_data_numpy()
                if save_dir:
                    os.makedirs(save_dir, exist_ok=True)
                    file_path = os.path.join(save_dir, f"{project_name}.{camera_id}.{exposure_time}.{_frame_id}.png")
                else:
                    file_path = f"{project_name}.{camera_id}.{timestamp}.{exposure_time}.{_frame_id}.png"
                cv2.imwrite(file_path, _image)  # pylint: disable=E1101

            cv2.waitKey(interval)  # pylint: disable=E1101
            threading.Thread(target=_save_photo, daemon=False).start()

        return _save_photo_handler
