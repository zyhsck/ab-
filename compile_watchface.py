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
            
            # 检查最小长度（PNG文件头至少需要8字节）
            if len(base64_data) < 100:
                logging.error(f"Base64 data is too short: {len(base64_data)} characters")
                return False
                
            try:
                # 解码Base64数据
                bytes_data = base64.b64decode(base64_data)
            except Exception as e:
                logging.error(f"Failed to decode Base64 data: {str(e)}")
                return False
                
            # 记录解码后的字节长度
            logging.info(f"Decoded image size: {len(bytes_data)} bytes")
            
            # 检查最小文件大小（PNG文件头至少需要8字节）
            if len(bytes_data) < 8:
                logging.error(f"Decoded image is too small: {len(bytes_data)} bytes")
                return False
                
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
                # 尝试手动检测常见格式
                image_format = self._detect_image_format(bytes_data)
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

    def _detect_image_format(self, bytes_data):
        """
        手动检测图片格式
        :param bytes_data: 图片字节数据
        :return: 图片格式字符串（如'png', 'jpg'），如果无法检测返回None
        """
        # PNG文件头: 89 50 4E 47 0D 0A 1A 0A
        if len(bytes_data) >= 8 and bytes_data.startswith(b'\x89PNG\r\n\x1a\n'):
            return 'png'
            
        # JPEG文件头: FF D8 FF
        if len(bytes_data) >= 3 and bytes_data.startswith(b'\xFF\xD8\xFF'):
            return 'jpg'
            
        # GIF文件头: GIF87a or GIF89a
        if len(bytes_data) >= 6 and (bytes_data.startswith(b'GIF87a') or bytes_data.startswith(b'GIF89a')):
            return 'gif'
            
        return None

    # ... 其余代码保持不变 ...

def main():
    try:
        # 从环境变量获取路径
        project_path = os.getenv("PROJECT_PATH", "project/fprj.fprj")
        output_dir = os.getenv("OUTPUT_DIR", "output")
        image_base64 = os.getenv("IMAGE_BASE64", "")
        
        # 记录环境变量值
        logging.info(f"PROJECT_PATH: {project_path}")
        logging.info(f"OUTPUT_DIR: {output_dir}")
        logging.info(f"IMAGE_BASE64 length: {len(image_base64) if image_base64 else 'empty'}")
        
        compiler = WatchfaceCompiler(
            project_path=project_path,
            output_dir=output_dir
        )
        
        # 设置背景图片
        if image_base64:
            if not compiler.set_background_image(image_base64):
                logging.error("Failed to set background image")
                return 1
        else:
            logging.warning("No image data provided, using default image")
        
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
