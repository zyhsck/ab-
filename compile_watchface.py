import os
import sys
import io
import logging
import pathlib
import shutil
import subprocess
import re
import base64
import time
import imghdr
from PIL import Image
from binary import WatchfaceBinary

# 强制UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 创建原始字节流处理器
class RawStreamHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record) + self.terminator
            self.stream.buffer.write(msg.encode('utf-8'))
            self.flush()
        except Exception:
            self.handleError(record)

# 配置日志系统
logger = logging.getLogger()
logger.setLevel(logging.INFO)

handler = RawStreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

class WatchfaceCompiler:
    def __init__(self, project_path, output_dir):
        """
        初始化编译器
        :param project_path: 项目文件路径(.fprj)
        :param output_dir: 最终输出目录路径
        """
        try:
            # 使用pathlib处理路径
            self.project_path = pathlib.Path(project_path).resolve()
            self.final_output_dir = pathlib.Path(output_dir).resolve()
            
            # 编译工具的输出目录（在项目目录下）
            self.temp_output_dir = self.project_path.parent / "output"
            
            # 确保所有目录存在
            self.final_output_dir.mkdir(parents=True, exist_ok=True)
            
            logging.info(f"Project path: {self.project_path}")
            logging.info(f"Final output directory: {self.final_output_dir}")
            logging.info(f"Temporary output directory: {self.temp_output_dir}")
            
            # 添加图片路径
            self.images_dir = self.project_path.parent / "images"
            self.pic_path = self.images_dir / "pic.png"
            self.pre_path = self.images_dir / "pre.png"
        except Exception as e:
            logging.error(f"Initialization failed: {str(e)}", exc_info=True)
            raise

    def set_background_image(self, base64_data):
        """
        设置背景图片
        :param base64_data: Base64编码的图片数据
        """
        try:
            # 检查Base64数据是否为空
            if not base64_data:
                logging.error("Base64 data is empty")
                return False
                
            # 记录Base64数据长度
            logging.info(f"Base64 data length: {len(base64_data)}")
            
            try:
                # 解码Base64数据
                bytes_data = base64.b64decode(base64_data)
            except Exception as e:
                logging.error(f"Failed to decode Base64 data: {str(e)}")
                return False
                
            # 记录解码后的字节长度
            logging.info(f"Decoded image size: {len(bytes_data)} bytes")
            
            # 确保图片目录存在
            self.images_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存到临时文件
            temp_path = self.pic_path.with_suffix('.tmp')
            with open(temp_path, "wb") as f:
                f.write(bytes_data)
            logging.info(f"Saved temporary image to: {temp_path}")
            
            # 检测图片格式
            image_format = imghdr.what(temp_path)
            if not image_format:
                logging.error("Unsupported image format")
                return False
                
            logging.info(f"Detected image format: {image_format}")
            
            # 重命名为正确格式
            temp_image_path = temp_path.with_suffix(f'.{image_format}')
            os.rename(temp_path, temp_image_path)
            logging.info(f"Renamed temporary image to: {temp_image_path}")
            
            # 验证图片完整性
            try:
                img = Image.open(temp_image_path)
                img.verify()  # 验证图片完整性
                img.close()
            except Exception as e:
                logging.error(f"Invalid image file: {str(e)}")
                return False
                
            # 转换为PNG格式
            img = Image.open(temp_image_path)
            img.save(self.pic_path, "PNG")
            logging.info(f"Converted image to PNG format: {self.pic_path}")
            
            # 复制为预览图
            shutil.copyfile(self.pic_path, self.pre_path)
            logging.info(f"Copied background image to preview image: {self.pre_path}")
            
            # 清理临时文件
            os.remove(temp_image_path)
            
            return True
        except Exception as e:
            logging.error(f"Failed to set background image: {str(e)}")
            return False

    # ... 其余代码保持不变 ...

def main():
    try:
        # 从环境变量获取路径
        project_path = os.getenv("PROJECT_PATH", "project/fprj.fprj")
        output_dir = os.getenv("OUTPUT_DIR", "output")
        image_base64 = os.getenv("IMAGE_BASE64", "")
        
        compiler = WatchfaceCompiler(
            project_path=project_path,
            output_dir=output_dir
        )
        
        # 设置背景图片
        if image_base64:
            if not compiler.set_background_image(image_base64):
                logging.error("Failed to set background image")
                return 1
        
        # 执行编译
        if compiler.compile():
            print("Compile success")
            return 0
        else:
            print("Compile failed")
            return 1
    except Exception as e:
        print(f"Program error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
