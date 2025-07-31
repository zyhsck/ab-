import os
import sys
import io
import logging
import pathlib
import shutil
import subprocess
import time
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
            
            # 添加预览图路径
            self.preview_path = self.project_path.parent / "images" / "pre.png"
        except Exception as e:
            logging.error(f"Initialization failed: {str(e)}", exc_info=True)
            raise

    # ... 其余代码保持不变 ...

def main():
    try:
        # 从环境变量获取路径
        project_path = os.getenv("PROJECT_PATH", "project/fprj.fprj")
        output_dir = os.getenv("OUTPUT_DIR", "output")
        
        compiler = WatchfaceCompiler(
            project_path=project_path,
            output_dir=output_dir
        )
        
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
