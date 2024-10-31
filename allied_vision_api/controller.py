"""接收客户端发来的指令然后操控相机模块."""
import asyncio
import json
import logging
import threading

from socket_cyg.socket_server_asyncio import CygSocketServerAsyncio

from allied_vision_api.camera_api import CameraApi


class Controller:
    """Controller class."""
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s"
    logging.basicConfig(level=logging.INFO, encoding="UTF-8", format=LOG_FORMAT)

    def __init__(self):
        self._logger = logging.getLogger(f"{self.__module__}.{self.__class__.__name__}")

        self.camera_common = CameraApi()
        self.socket_server = CygSocketServerAsyncio()
        self.start_server_thread()

    def start_server_thread(self):
        """启动供下位机连接的socket服务, 指定处理客户端连接的处理器."""
        self.socket_server.operations_return_data = self.client_handler

        def _run_socket_server():
            asyncio.run(self.socket_server.run_socket_server())

        thread = threading.Thread(target=_run_socket_server, daemon=False)
        thread.start()

    def client_handler(self, data: bytes) -> str:
        """处理客户端发来的指令, 基本构想相机设置或者采集图片.

        Args:
            data:

        Returns:
            str: 回复信息.
        """
        data_dict = json.loads(data.decode(encoding="utf-8"))
        for command, info in data_dict.items():
            self._logger.info("%s 收到客户端指令: %s %s", "-" * 20, command, "-" * 20)
            self._logger.info("***指令包含的数据*** -> %s", info)
            if hasattr(self.camera_common, command):
                getattr(self.camera_common, command)(**info)
                self._logger.info("%s 指令执行结束 %s", "-" * 20, "-" * 20)
        return "@_@"
