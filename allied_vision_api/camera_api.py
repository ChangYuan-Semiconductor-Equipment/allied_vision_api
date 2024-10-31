"""Allied vision API."""
import datetime
import logging
import os
import sys
import threading
import time
from logging.handlers import TimedRotatingFileHandler
from typing import Optional, Callable, Union

import cv2
from pymba import Vimba
from pymba.camera import Camera, SINGLE_FRAME, CONTINUOUS

from allied_vision_api.camera_feature_command import CameraFeatureCommand


# pylint: disable=C0301, disable=R0917, disable=R0913, disable=R0904
class CameraApi:
    """Allied vision api."""

    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s"

    def __init__(self):
        self.logger = logging.getLogger(f"{self.__module__}.{self.__class__.__name__}")
        self._file_handler = None
        self.set_log()

        self.vimba = Vimba()
        self.is_vimba_open = False
        self.cameras_instance = self.get_all_camera_instance()

    @property
    def file_handler(self):
        """保存日志的日志器."""
        if self._file_handler is None:
            log_dir = f"{os.getcwd()}/log"
            os.makedirs(log_dir, exist_ok=True)
            file_name = f"{log_dir}/{datetime.datetime.now().strftime('%Y-%m-%d')}"
            self._file_handler = TimedRotatingFileHandler(
                file_name, when="D", interval=1, backupCount=10, encoding="UTF-8"
            )
        return self._file_handler

    def set_log(self):
        """设置日志."""
        self.file_handler.setFormatter(logging.Formatter(self.LOG_FORMAT))
        self.file_handler.setLevel(logging.INFO)
        self.logger.addHandler(self.file_handler)
        if sys.version_info.minor == 11:
            logging.basicConfig(level=logging.INFO, encoding="UTF-8", format=self.LOG_FORMAT)
        else:
            self.logger.setLevel(logging.INFO)

    def open_vimba(self):
        """判断是否已经实例化了vimba的 C API."""
        if not self.is_vimba_open:
            self.vimba.startup()
            self.is_vimba_open = True
            self.logger.info("*** vimba 驱动已打开 ***")

    def close_vimba(self) -> None:
        """相机操作结束后需要关闭vimba"""
        if self.is_vimba_open:
            self.vimba.shutdown()
            self.is_vimba_open = False
            self.logger.info("*** vimba 驱动已关闭 ***")

    def open_camera(self, camera_id=None):
        """打开指定相机.

        Args:
            camera_id: 相机id.
        """
        self.open_vimba()
        if not self.cameras_instance[camera_id]["is_open"]:
            self.get_camera_instance(camera_id).open()
            self.cameras_instance[camera_id]["is_open"] = True
            self.logger.info("*** 相机已打开 ***")

    def close_camera(self, camera_id=None):
        """关闭相机.

        Args:
            camera_id: 相机id.
        """
        if self.cameras_instance[camera_id]["is_open"]:
            self.get_camera_instance(camera_id).close()
            self.cameras_instance[camera_id]["is_open"] = False
            self.logger.info("*** 相机已关闭 ***")

    def arm_camera(self, camera_id=None, mode=SINGLE_FRAME, call_back=None):
        """打开相机引擎.

        Args:
            camera_id: 相机id.
            mode: 引擎模式, 默认是 SINGLE_FRAME 模式.
            call_back: 每个帧准备就绪时调用的函数引用
        """
        self.open_camera(camera_id)
        if not self.cameras_instance[camera_id]["is_arm"]:
            self.get_camera_instance(camera_id).arm(mode, callback=call_back)
            self.cameras_instance[camera_id]["is_arm"] = True
            self.logger.info("*** 相机捕捉引擎已打开 ***")

    def disarm_camera(self, camera_id=None):
        """关闭指定相机的引擎.

        Args:
            camera_id: 相机id.
        """
        if self.get_camera_arm_state(camera_id):
            self.get_camera_instance(camera_id).disarm()
            self.cameras_instance[camera_id]["is_arm"] = False
            self.logger.info("*** 相机捕捉引擎已关闭 ***")

    def get_camera_arm_state(self, camera_id=None) -> bool:
        """获取相机的arm状态.

        Args:
            camera_id: 相机id.

        Returns:
            bool: True -> 已打开, False -> 已关闭.
        """
        return self.cameras_instance[camera_id]["is_arm"]

    def get_camera_open_state(self, camera_id=None) -> bool:
        """获取相机的打开状态.

        Args:
            camera_id: 相机id.

        Returns:
            bool: True -> 已打开, False -> 已关闭.
        """
        return self.cameras_instance[camera_id]["is_open"]

    def get_camera_instance(self, camera_id=None) -> Optional[Camera]:
        """根据相机id获取相机的实例对象.

        Args:
            camera_id: 相机id.

        Returns:
            Optional[Camera]: 返回相机实例或者None.
        """
        if camera_id:
            return self.cameras_instance[camera_id]["instance"]
        return None

    def get_all_camera_instance(self) -> dict:
        """获取所有的相机对象."""
        self.open_vimba()
        cameras_object = {}
        for camera_id in self.vimba.camera_ids():
            cameras_object.update({
                camera_id: {
                    "instance": self.vimba.camera(camera_id),
                    "is_open": False,
                    "is_arm": False
                }
            })
        return cameras_object

    def get_feature_value(self, camera_id, feature_name: str) -> Union[str, int, float]:
        """获取当前参数.

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

    def set_feature_value(self, camera_id: str = None, feature_name: str = None, value: Union[int, float, str] = None):
        """设置指定相机的参数值, 设置前提要打开相机.

        Args:
            camera_id: 相机id.
            feature_name: 要设定的参数名称.
            value: 设定值.
        """
        if not self.get_camera_open_state(camera_id):
            self.open_camera(camera_id)

        self.disarm_camera(camera_id)
        feature = self.get_camera_instance(camera_id).feature(feature_name)
        self.logger.info("***当前 %s 值*** -> %s", feature_name, feature.value)
        feature.value = value
        self.logger.info("***设置后 %s 值*** -> %s", feature_name, feature.value)

    def set_one_quarter(self, camera_id: str):
        """设置相机捕捉区域为中间四分之一.

        Args:
            camera_id: 相机id.
        """
        self.set_feature_value(camera_id, CameraFeatureCommand.Width.value, 2664)
        self.set_feature_value(camera_id, CameraFeatureCommand.Height.value, 2304)
        self.set_feature_value(camera_id, CameraFeatureCommand.OffsetY.value, 1152)
        self.set_feature_value(camera_id, CameraFeatureCommand.OffsetX.value, 1344)

    def set_one_sixteenth(self, camera_id: str):
        """设置相机捕捉区域为中间十六分之一.

        Args:
            camera_id: 相机id.
        """
        self.set_feature_value(camera_id, CameraFeatureCommand.Width.value, 1336)
        self.set_feature_value(camera_id, CameraFeatureCommand.Height.value, 1152)
        self.set_feature_value(camera_id, CameraFeatureCommand.OffsetY.value, 1728)
        self.set_feature_value(camera_id, CameraFeatureCommand.OffsetX.value, 2000)

    def set_full(self, camera_id: str):
        """设置相机捕捉区域为全部区域.

        Args:
            camera_id: 相机id.
        """
        max_width = self.get_feature_value(camera_id, CameraFeatureCommand.WidthMax.value)
        max_height = self.get_feature_value(camera_id, CameraFeatureCommand.HeightMax.value)
        self.set_feature_value(camera_id, CameraFeatureCommand.Width.value, max_width)
        self.set_feature_value(camera_id, CameraFeatureCommand.Height.value, max_height)
        self.set_feature_value(camera_id, CameraFeatureCommand.OffsetY.value, 0)
        self.set_feature_value(camera_id, CameraFeatureCommand.OffsetX.value, 0)

    def acquire_one(self, camera_id=None, project_name="", camera_close=False, vimba_close=False, save_dir=None):
        """采集一张照片, 前提是打开vimba驱动, 打开相机, 打开相机engineer (arm).

        Args:
            camera_id: 相机id.
            project_name: 所属项目.
            camera_close: 是否关闭相机.
            vimba_close: 是否关闭vimba.
            save_dir: 指定图片保存目录.
        """
        self.open_vimba()
        self.open_camera(camera_id)
        self.arm_camera(camera_id)
        camera_instance = self.get_camera_instance(camera_id)
        self.logger.info("*** 开始捕捉帧数据 ***")
        frame = camera_instance.acquire_frame()
        self.logger.info("*** 结束捕捉帧数据 ***")

        self.save_photo_local(frame, project_name, camera_id, save_dir=save_dir)

        if camera_close:
            self.disarm_camera(camera_id)
            self.close_camera(camera_id)
        if vimba_close:
            self.close_vimba()

    def acquire_continue(self, camera_id=None,  project_name="", acquire_one=False, interval=100,
                         continue_time=5, camera_close=False, vimba_close=False, save_dir=None):
        """指定间隔时间, 连续采集图片.

        Args:
            camera_id: 相机id.
            project_name: 项目名称.
            acquire_one: 是否只拍一个照片.
            interval: 间隔时间, 单位是毫秒.
            continue_time: 持续时间, 单位是秒.
            camera_close: 是否关闭相机.
            vimba_close: 是否关闭vimba.
            save_dir: 指定图片保存目录.
        """
        if acquire_one:
            self.acquire_one(
                camera_id, project_name, camera_close=camera_close, vimba_close=vimba_close, save_dir=save_dir
            )
            return
        self.open_vimba()
        self.open_camera(camera_id)
        self.arm_camera(camera_id, CONTINUOUS, self.generate_save_photo_func(camera_id, project_name, interval, save_dir))
        camera_instance = self.get_camera_instance(camera_id)
        camera_instance.start_frame_acquisition()
        time.sleep(continue_time)
        camera_instance.stop_frame_acquisition()

        if camera_close:
            self.disarm_camera(camera_id)
            self.close_camera(camera_id)
        if vimba_close:
            self.close_vimba()

    def save_photo_local(self, frame, project_name: str, camera_id: str, save_dir=None):
        """将采集的图片保存在本地.

        Args:
            frame: 采集到的图像帧数据.
            project_name: 项目名称, example: seethru or display.
            camera_id: 相机id.
            save_dir: 指定图片保存目录.
        """
        exposure_time = f"{int(self.get_feature_value(camera_id, CameraFeatureCommand.ExposureTime.value)):08}"
        def _save_photo_local():
            _frame_id = f"{frame.data.frameID:04}"
            _image = frame.buffer_data_numpy()
            if save_dir:
                os.makedirs(save_dir, exist_ok=True)
                file_path = os.path.join(save_dir, f"{project_name}.{camera_id}.{exposure_time}.{_frame_id}.png")
            else:
                file_path = f"{project_name}.{camera_id}.{exposure_time}.{_frame_id}.png"
            cv2.imwrite(file_path, _image)  # pylint: disable=E1101
        threading.Thread(target=_save_photo_local, daemon=False).start()

    def generate_save_photo_func(self, camera_id, project_name: str, interval: int, save_dir=None) -> Callable:
        """生成保存图片的函数.

        Args:
            camera_id: 相机id.
            project_name: 项目名称.
            interval: 间隔时间.
            save_dir: 指定图片保存目录.

        Returns:
            Callable: 保存图片的函数.
        """
        exposure_time = f"{int(self.get_feature_value(camera_id, CameraFeatureCommand.ExposureTime.value)):08}"

        def _save_photo_handler(_frame):
            """保存图片.

            Args:
                _frame: 捕捉到的帧数据.
            """
            _frame_id = f"{_frame.data.frameID:04}"

            def _save_photo():
                _image = _frame.buffer_data_numpy()
                if save_dir:
                    os.makedirs(save_dir, exist_ok=True)
                    file_path = os.path.join(save_dir, f"{project_name}.{camera_id}.{exposure_time}.{_frame_id}.png")
                else:
                    file_path = f"{project_name}.{camera_id}.{exposure_time}.{_frame_id}.png"
                cv2.imwrite(file_path, _image)  # pylint: disable=E1101

            cv2.waitKey(interval)  # pylint: disable=E1101
            threading.Thread(target=_save_photo, daemon=False).start()

        return _save_photo_handler
