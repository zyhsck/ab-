import os
import sys
import io
import logging
import pathlib
import shutil
import subprocess
import re
import base64
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
            # 解码Base64数据
            bytes_data = base64.b64decode(base64_data)
            
            # 确保图片目录存在
            self.images_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存背景图
            with open(self.pic_path, "wb") as f:
                f.write(bytes_data)
            logging.info(f"Saved background image to: {self.pic_path}")
            
            # 复制为预览图（不调整大小）
            shutil.copyfile(self.pic_path, self.pre_path)
            logging.info(f"Copied background image to preview image: {self.pre_path}")
            
            return True
        except Exception as e:
            logging.error(f"Failed to set background image: {str(e)}")
            return False

    def compile(self):
        """
        编译主流程（带重试）
        :return: 成功返回True，失败返回False
        """
        try:
            # 1. 验证项目文件
            if not self._validate_project_file():
                return False
                
            # 2. 准备输出文件名
            output_filename = self.project_path.stem + ".face"
            final_output_file = self.final_output_dir / output_filename
            
            # 3. 首次编译尝试
            success, error_output = self._run_compile_tool(output_filename)
            if not success:
                # 检查错误日志，如果是预览图尺寸问题，尝试调整并重试
                logging.warning("First compilation failed. Attempting to fix preview and retry...")
                
                # 解析错误日志，获取期望的预览图尺寸
                expected_size = self._parse_expected_preview_size(error_output)
                if expected_size:
                    logging.info(f"Expected preview size: {expected_size}")
                    
                    # 尝试调整预览图尺寸
                    if self._adjust_preview_size(expected_size):
                        logging.info("Preview image resized. Retrying compilation...")
                        
                        # 关键修复：删除临时输出目录，确保重新编译
                        if self.temp_output_dir.exists():
                            shutil.rmtree(self.temp_output_dir)
                            logging.info(f"Deleted temporary output directory: {self.temp_output_dir}")
                        
                        # 重试编译
                        success, _ = self._run_compile_tool(output_filename)
                    else:
                        logging.error("Failed to resize preview image.")
                        return False
                else:
                    logging.error("Could not parse expected preview size from errors.")
                    return False
                
            if not success:
                return False
                
            # 4. 移动输出文件
            if not self._move_output_file(output_filename, final_output_file):
                return False
                
            # 5. 设置表盘ID
            return self._set_watchface_id(final_output_file)
            
        except Exception as e:
            logging.error(f"Compilation error: {str(e)}", exc_info=True)
            return False

    def _parse_expected_preview_size(self, error_output):
        """
        从错误信息中解析期望的预览图尺寸
        :param error_output: 错误输出内容
        :return: (width, height) 元组，如果解析失败返回None
        """
        # 错误信息格式： "Error: Preview has wrong size: ... expected: ..."
        pattern = r'expected: (\d+)x(\d+)'
        match = re.search(pattern, error_output)
        if match:
            return (int(match.group(1)), int(match.group(2)))
        return None

    def _adjust_preview_size(self, expected_size):
        """
        调整预览图尺寸
        :param expected_size: 期望尺寸 (width, height)
        :return: 成功返回True，失败返回False
        """
        try:
            # 检查预览图是否存在
            if not self.pre_path.exists():
                logging.error(f"Preview image not found: {self.pre_path}")
                return False
                
            # 打开并调整图片
            img = Image.open(self.pre_path)
            
            # 检查当前尺寸
            current_size = img.size
            if current_size == expected_size:
                logging.info("Preview already has correct size")
                return True
                
            logging.info(f"Resizing preview from {current_size} to {expected_size}")
            
            # 调整尺寸
            img = img.resize(expected_size, Image.LANCZOS)
            
            # 保存到临时文件
            temp_path = self.pre_path.with_suffix('.tmp.png')
            img.save(temp_path, "PNG")
            
            # 原子替换原文件
            os.replace(temp_path, self.pre_path)
            
            # 验证调整后的尺寸
            img_after = Image.open(self.pre_path)
            if img_after.size == expected_size:
                logging.info(f"Verified preview size: {img_after.size}")
                return True
            else:
                logging.error(f"Resize failed! Expected: {expected_size}, Actual: {img_after.size}")
                return False
        except Exception as e:
            logging.error(f"Failed to resize preview image: {str(e)}")
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

    def _run_compile_tool(self, output_filename):
        """运行编译工具"""
        try:
            # 编译工具路径（相对于脚本位置）
            compile_tool = pathlib.Path(__file__).parent / "compile.exe"
            
            if not compile_tool.exists():
                logging.error(f"Compiler tool not found at: {compile_tool}")
                return False, ""
            
            # 准备命令参数
            cmd = [
                str(compile_tool),
                "-b",
                str(self.project_path),
                "output",  # 编译工具会在项目目录下创建output子目录
                output_filename,
                "1461256429"
            ]
            
            logging.info(f"Executing command: {' '.join(cmd)}")
            
            # 确保临时输出目录存在
            self.temp_output_dir.mkdir(parents=True, exist_ok=True)
            logging.info(f"Created temporary output directory: {self.temp_output_dir}")
            
            # 使用subprocess执行命令
            result = subprocess.run(
                cmd,
                cwd=str(self.project_path.parent),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                shell=True
            )
            
            # 记录输出
            output_text = result.stdout + "\n" + result.stderr
            logging.info(f"Compiler output:\n{output_text}")
                
            # 检查返回码
            if result.returncode != 0:
                logging.error(f"Compilation failed with exit code {result.returncode}")
                return False, output_text
                
            return True, output_text
            
        except Exception as e:
            logging.error(f"Command execution error: {str(e)}")
            return False, str(e)

    def _move_output_file(self, output_filename, final_output_file):
        """移动输出文件到最终目录"""
        # 编译工具生成的临时输出文件路径
        temp_output_file = self.temp_output_dir / output_filename
        
        if not temp_output_file.exists():
            logging.error(f"Output file not generated: {temp_output_file}")
            return False
            
        try:
            # 移动文件到最终输出目录
            shutil.move(str(temp_output_file), str(final_output_file))
            logging.info(f"Moved output file to: {final_output_file}")
            return True
        except Exception as e:
            logging.error(f"Failed to move output file: {str(e)}")
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
