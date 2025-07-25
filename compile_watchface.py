import os
import sys
import io
import logging
import pathlib
import shutil
import json
import struct
import zlib
from binary import WatchfaceBinary

# 强制UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 配置日志系统
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

class WatchfaceCompiler:
    def __init__(self, project_path, output_dir):
        """
        终极解决方案：直接解析.fprj文件并生成.face文件
        :param project_path: 项目文件路径(.fprj)
        :param output_dir: 输出目录路径
        """
        try:
            # 使用pathlib处理路径
            self.project_path = pathlib.Path(project_path).resolve()
            self.output_dir = pathlib.Path(output_dir).resolve()
            
            # 确保输出目录存在
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            logging.info(f"Project path: {self.project_path}")
            logging.info(f"Output directory: {self.output_dir}")
        except Exception as e:
            logging.error(f"Initialization failed: {str(e)}", exc_info=True)
            raise

    def compile(self):
        """
        编译主流程 - 直接处理.fprj文件
        :return: 成功返回True，失败返回False
        """
        try:
            # 1. 验证项目文件
            if not self.project_path.exists():
                logging.error(f"Project file not found: {self.project_path}")
                return False
                
            # 2. 准备输出文件名
            output_filename = self.project_path.stem + ".face"
            output_file = self.output_dir / output_filename
            
            # 3. 直接解析.fprj文件并生成.face文件
            if not self._generate_face_file(output_file):
                return False
                
            # 4. 设置表盘ID
            return self._set_watchface_id(output_file)
            
        except Exception as e:
            logging.error(f"Compilation error: {str(e)}", exc_info=True)
            return False

    def _generate_face_file(self, output_file):
        """直接解析.fprj文件并生成.face文件"""
        try:
            # 读取.fprj文件
            with open(self.project_path, 'r', encoding='utf-8') as f:
                fprj_data = json.load(f)
            
            # 提取必要信息
            watchface_name = fprj_data.get('name', 'MyWatchFace')
            components = fprj_data.get('components', [])
            
            # 创建.face文件结构
            with open(output_file, 'wb') as f:
                # 文件头
                f.write(b'FACE')  # 魔数
                f.write(struct.pack('<I', 1))  # 版本号
                
                # 名称
                name_bytes = watchface_name.encode('utf-8')
                f.write(struct.pack('<I', len(name_bytes)))
                f.write(name_bytes)
                
                # 组件数量
                f.write(struct.pack('<I', len(components)))
                
                # 组件数据
                for component in components:
                    comp_type = component.get('type', '')
                    comp_data = component.get('data', {})
                    
                    # 组件类型
                    type_bytes = comp_type.encode('utf-8')
                    f.write(struct.pack('<I', len(type_bytes)))
                    f.write(type_bytes)
                    
                    # 组件数据
                    data_bytes = json.dumps(comp_data).encode('utf-8')
                    compressed = zlib.compress(data_bytes)
                    f.write(struct.pack('<I', len(compressed)))
                    f.write(compressed)
            
            logging.info(f"Successfully generated watch face file: {output_file}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to generate face file: {str(e)}")
            return False

    def _set_watchface_id(self, output_file):
        """设置表盘ID"""
        try:
            binary = WatchfaceBinary(str(output_file))
            binary.setId("123456789")
            logging.info(f"Set watch face ID: 123456789")
            return True
        except Exception as e:
            logging.error(f"Failed to set watch face ID: {str(e)}")
            return False


if __name__ == "__main__":
    try:
        # 使用固定路径
        compiler = WatchfaceCompiler(
            project_path="project/fprj.fprj",
            output_dir="output"
        )
        
        if compiler.compile():
            print("Compile success")
        else:
            print("Compile failed")
    except Exception as e:
        print(f"Program error: {str(e)}")