import os
import sys
import io
import logging
import pathlib
import shutil
import json
import struct
import zlib
import chardet  # 需要安装: pip install chardet
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
            if not self._validate_project_file():
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
        """直接解析.fprj文件并生成.face文件"""
        try:
            # 读取文件二进制内容
            with open(self.project_path, 'rb') as f:
                raw_data = f.read()
                
            # 检测编码
            detection = chardet.detect(raw_data)
            encoding = detection['encoding'] or 'utf-8'
            confidence = detection['confidence']
            
            logging.info(f"Detected encoding: {encoding} (confidence: {confidence})")
            
            # 尝试解码内容
            try:
                content = raw_data.decode(encoding)
            except UnicodeDecodeError as e:
                logging.error(f"Failed to decode file: {str(e)}")
                # 尝试其他常见编码
                for alt_encoding in ['utf-8', 'latin-1', 'cp1252']:
                    try:
                        content = raw_data.decode(alt_encoding)
                        logging.info(f"Successfully decoded with {alt_encoding}")
                        break
                    except:
                        continue
                else:
                    logging.error("Failed to decode file with any encoding")
                    return False
            
            # 记录前100个字符用于调试
            sample = content[:100] if len(content) > 100 else content
            logging.info(f"FPRJ file sample: {sample}")
            
            # 尝试解析JSON
            try:
                fprj_data = json.loads(content)
            except json.JSONDecodeError as e:
                # 输出更详细的错误信息
                logging.error(f"JSON decode error: {str(e)}")
                logging.error(f"Error at line {e.lineno}, column {e.colno}: {e.msg}")
                
                # 输出错误位置附近的文本
                start = max(0, e.pos - 20)
                end = min(len(content), e.pos + 20)
                context = content[start:end]
                logging.error(f"Error context: ...{context}...")
                return False
            except Exception as e:
                logging.error(f"Unexpected error parsing JSON: {str(e)}")
                return False
        
            # 提取必要信息
            watchface_name = fprj_data.get('name', 'MyWatchFace')
            components = fprj_data.get('components', [])
            
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
                    comp_type = component.get('type', '')
                    comp_data = component.get('data', {})
                    
                    logging.debug(f"Processing component {i+1}: {comp_type}")
                    
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
                    except Exception as e:
                        logging.error(f"Error processing component {i+1}: {str(e)}")
                        return False
            
            logging.info(f"Successfully generated watch face file: {output_file}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to generate face file: {str(e)}", exc_info=True)
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