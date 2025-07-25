import os
import sys
import io
import logging
import pathlib
import subprocess
import shutil
import json
import struct
import zlib
import xml.etree.ElementTree as ET
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
        终极解决方案：支持XML格式的.fprj文件
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
        编译主流程 - 支持XML格式
        :return: 成功返回True，失败返回False
        """
        try:
            # 1. 验证项目文件
            if not self._validate_project_file():
                return False
                
            # 2. 准备输出文件名
            output_filename = self.project_path.stem + ".face"
            output_file = self.output_dir / output_filename
            
            # 3. 解析.fprj文件并生成.face文件
            if not self._generate_face_file(output_file):
                return False
                
            # 4. 设置表盘ID
            return self._set_watchface_id(output_file)
            
        except Exception as e:
            logging.error(f"Compilation error: {str(e)}", exc_info=True)
            return False

    def _validate_project_file(self):
        """验证项目文件"""
        if not self.project_path.exists():
            logging.error(f"Project file not found: {self.project_path}")
            return False
            
        file_size = os.path.getsize(self.project_path)
        if file_size == 0:
            logging.error(f"Project file is empty: {self.project_path}")
            return False
            
        logging.info(f"Project file size: {file_size} bytes")
        return True

    def _generate_face_file(self, output_file):
        """解析XML格式的.fprj文件并生成.face文件"""
        try:
            # 读取文件内容
            with open(self.project_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 记录前100个字符用于调试
            sample = content[:100] if len(content) > 100 else content
            logging.info(f"FPRJ file sample: {sample}")
            
            # 尝试解析XML
            try:
                root = ET.fromstring(content)
            except ET.ParseError as e:
                logging.error(f"XML parse error: {str(e)}")
                return False
            
            # 提取必要信息
            watchface_name = root.attrib.get('name', 'MyWatchFace')
            components = []
            
            # 提取组件信息
            for component in root.findall('.//Component'):
                comp_type = component.attrib.get('type', '')
                comp_data = {}
                
                # 提取属性
                for key, value in component.attrib.items():
                    if key != 'type':
                        comp_data[key] = value
                
                # 提取子元素
                for child in component:
                    comp_data[child.tag] = child.text
                
                # 确保组件数据不为空
                if not comp_data:
                    logging.warning(f"Component {comp_type} has no data")
                
                components.append({
                    'type': comp_type,
                    'data': comp_data
                })
            
            logging.info(f"Watchface name: {watchface_name}")
            logging.info(f"Found {len(components)} components")
            
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
                for i, component in enumerate(components):
                    comp_type = component['type']
                    comp_data = component['data']
                    
                    logging.debug(f"Processing component {i+1}: {comp_type}")
                    
                    # 如果是图片组件，直接包含图片数据
                    if comp_type == 'Image':
                        image_path = self.project_path.parent / "images" / comp_data.get('src', 'pic.png')
                        if image_path.exists():
                            with open(image_path, 'rb') as img_file:
                                image_data = img_file.read()
                            
                            # 直接写入图片数据（不压缩）
                            f.write(struct.pack('<I', len(image_data)))
                            f.write(image_data)
                            logging.info(f"Included image: {image_path} ({len(image_data)} bytes)")
                            continue
                    
                    # 组件类型
                    type_bytes = comp_type.encode('utf-8')
                    f.write(struct.pack('<I', len(type_bytes)))
                    f.write(type_bytes)
                    
                    # 组件数据
                    try:
                        data_bytes = json.dumps(comp_data).encode('utf-8')
                        compressed = zlib.compress(data_bytes)
                        f.write(struct.pack('<I', len(compressed)))
                        f.write(compressed)
                        logging.debug(f"Component data size: {len(compressed)} bytes")
                    except Exception as e:
                        logging.error(f"Error processing component {i+1}: {str(e)}")
                        return False
            
            # 记录文件大小
            file_size = os.path.getsize(output_file)
            logging.info(f"Generated file size: {file_size} bytes")
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to generate face file: {str(e)}", exc_info=True)
            return False

    def _set_watchface_id(self, output_file):
        """设置表盘ID"""
        try:
            # 检查文件大小
            file_size = os.path.getsize(output_file)
            if file_size < 9:
                logging.error(f"File too small to set ID: {file_size} bytes")
                return False
                
            # 设置ID
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
