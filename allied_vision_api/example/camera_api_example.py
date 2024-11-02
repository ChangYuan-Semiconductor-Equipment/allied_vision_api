"""camera_api_example."""
from allied_vision_api.camera_api import CameraApi


if __name__ == '__main__':
    camera_api = CameraApi()

    """
    拍一张照片:
    
        Args:
            id_or_name: 支持相机的别名和相机id.
            project_name: 所属项目, 不传默认项目名称为空, 保存的图片没有项目名称.
            camera_close: 是否关闭相机, 默认不关闭, 传入True, 拍完照会关闭相机.
            vimba_close: 是否关闭vimba, 默认不关闭, 传入True, 拍完照会关闭vimba驱动.
            save_dir: 指定图片保存目录, 不传照片保存在执行入口同级目录下.
    """
    camera_api.acquire_one(id_or_name="相机的名称或id", project_name="项目名称", save_dir="照片保存到的目录")
