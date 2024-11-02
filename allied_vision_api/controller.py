"""接收客户端发来的指令然后操控相机模块."""
import asyncio
import json
import threading

from socket_cyg.socket_server_asyncio import CygSocketServerAsyncio

from allied_vision_api.camera_api import CameraApi


class Controller:
    """Controller class."""

    def __init__(self, socket_ip="127.0.0.1", socket_port=8000):
        self.camera_api = CameraApi()
        self._logger = self.camera_api._logger
        self.socket_server = CygSocketServerAsyncio(socket_ip, socket_port)
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
            data: 收到的客户端数据.

        Returns:
            str: 回复信息.
        """
        if isinstance(data, str):
            data_dict = json.loads(data)
        else:
            data_dict = json.loads(data.decode(encoding="utf-8"))
        for command, info in data_dict.items():
            self._logger.info("%s 收到客户端指令: %s %s", "-" * 20, command, "-" * 20)
            self._logger.info("***指令包含的数据*** -> %s", info)
            if hasattr(self.camera_api, command):
                getattr(self.camera_api, command)(**info)
                self._logger.info("%s 指令执行结束 %s", "-" * 20, "-" * 20)
        return "@_@"
