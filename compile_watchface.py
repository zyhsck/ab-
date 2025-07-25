import os
import sys
import io
import logging
import pathlib
import shutil
import subprocess
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
        终极解决方案：模拟原始编译工具的行为
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
        编译主流程 - 模拟原始编译工具
        :return: 成功返回True，失败返回False
        """
        try:
            # 1. 验证项目文件
            if not self._validate_project_file():
                return False
                
            # 2. 准备输出文件名
            output_filename = self.project_path.stem + ".face"
            output_file = self.output_dir / output_filename
            
            # 3. 直接复制项目结构
            if not self._copy_project_structure():
                return False
                
            # 4. 运行原始编译工具
            if not self._run_original_compiler(output_filename):
                return False
                
            # 5. 移动输出文件
            if not self._move_output_file(output_file):
                return False
                
            # 6. 设置表盘ID
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

    def _copy_project_structure(self):
        """复制整个项目结构到临时目录"""
        try:
            # 创建临时工作目录
            self.work_dir = pathlib.Path("work")
            if self.work_dir.exists():
                shutil.rmtree(self.work_dir)
            self.work_dir.mkdir(parents=True, exist_ok=True)
            
            # 复制项目目录下的所有内容到work_dir
            project_parent = self.project_path.parent
            for item in os.listdir(project_parent):
                src = project_parent / item
                dst = self.work_dir / item
                if src.is_dir():
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)
            
            logging.info(f"Copied project contents to work directory: {self.work_dir}")
            return True
        except Exception as e:
            logging.error(f"Failed to copy project structure: {str(e)}")
            return False

    def _run_original_compiler(self, output_filename):
        """运行原始编译工具"""
        try:
            # 编译工具路径（根目录）
            compile_tool = pathlib.Path.cwd() / "compile.exe"
            
            if not compile_tool.exists():
                logging.error("Compiler tool not found")
                return False
            
            # 准备命令参数
            cmd = [
                str(compile_tool),
                "-b",
                str(self.work_dir / self.project_path.name),
                "output",
                output_filename,
                "1461256429"
            ]
            
            logging.info(f"Executing command: {' '.join(cmd)}")
            
            # 创建输出目录
            output_dir = self.work_dir / "output"
            output_dir.mkdir(parents=True, exist_ok=True)
            logging.info(f"Created output directory: {output_dir}")
            
            # 设置环境变量优化内存
            env = os.environ.copy()
            env["DOTNET_SYSTEM_GLOBALIZATION_INVARIANT"] = "1"
            env["COMPlus_gcServer"] = "1"  # 启用服务器GC
            env["COMPlus_gcConcurrent"] = "1"  # 启用并发GC
            
            # 使用subprocess执行命令
            result = subprocess.run(
                cmd,
                cwd=str(self.work_dir),
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                shell=True,
                env=env
            )
            
            # 记录输出
            if result.stdout:
                logging.info(f"Compiler output:\n{result.stdout}")
            if result.stderr:
                logging.warning(f"Compiler warnings:\n{result.stderr}")
                
            # 检查输出文件是否生成
            work_output_file = self.work_dir / "output" / output_filename
            if work_output_file.exists():
                logging.info(f"Output file generated: {work_output_file}")
                return True
            else:
                logging.error(f"Output file not generated: {work_output_file}")
                # 列出工作目录内容
                logging.error("Contents of work directory:")
                for p in self.work_dir.glob('**/*'):
                    logging.error(f"  {p}")
                return False
                
        except subprocess.CalledProcessError as e:
            logging.error(f"Compilation failed (exit code {e.returncode}):\n{e.stderr}")
            return False
        except Exception as e:
            logging.error(f"Command execution error: {str(e)}")
            return False

    def _move_output_file(self, output_file):
        """移动输出文件到目标目录"""
        # 编译工具在工作目录生成输出文件
        work_output_file = self.work_dir / "output" / output_file.name
        
        if not work_output_file.exists():
            logging.error(f"Output file not generated: {work_output_file}")
            # 检查可能的其他位置
            alt_path = self.work_dir / output_file.name
            if alt_path.exists():
                logging.info(f"Found output file in alternative location: {alt_path}")
                shutil.move(str(alt_path), str(output_file))
                return True
            else:
                return False
            
        try:
            # 移动文件到输出目录
            shutil.move(str(work_output_file), str(output_file))
            logging.info(f"Moved output file to: {output_file}")
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
