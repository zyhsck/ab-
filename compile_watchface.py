import os
import sys
import io
import logging
import pathlib
import shutil
import subprocess
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
        except Exception as e:
            logging.error(f"Initialization failed: {str(e)}", exc_info=True)
            raise

    def compile(self):
        """
        编译主流程
        :return: 成功返回True，失败返回False
        """
        try:
            # 1. 验证项目文件
            if not self._validate_project_file():
                return False
                
            # 2. 准备输出文件名
            output_filename = self.project_path.stem + ".face"
            final_output_file = self.final_output_dir / output_filename
            
            # 3. 运行编译工具
            if not self._run_compile_tool(output_filename):
                return False
                
            # 4. 移动输出文件
            if not self._move_output_file(output_filename, final_output_file):
                return False
                
            # 5. 设置表盘ID
            return self._set_watchface_id(final_output_file)
            
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

    def _run_compile_tool(self, output_filename):
        """运行编译工具"""
        try:
            # 编译工具路径（相对于脚本位置）
            compile_tool = pathlib.Path(__file__).parent / "compile.exe"
            
            if not compile_tool.exists():
                logging.error(f"Compiler tool not found at: {compile_tool}")
                return False
            
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
            
            # 设置环境变量优化内存
            env = os.environ.copy()
            env["DOTNET_SYSTEM_GLOBALIZATION_INVARIANT"] = "1"
            env["COMPlus_gcServer"] = "1"  # 启用服务器GC
            env["COMPlus_gcConcurrent"] = "1"  # 启用并发GC
            
            # 使用subprocess执行命令
            result = subprocess.run(
                cmd,
                cwd=str(self.project_path.parent),
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
                
            return True
            
        except subprocess.CalledProcessError as e:
            logging.error(f"Compilation failed (exit code {e.returncode}):\n{e.stderr}")
            return False
        except Exception as e:
            logging.error(f"Command execution error: {str(e)}")
            return False

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


if __name__ == "__main__":
    try:
        # 从环境变量获取路径（GitHub Actions兼容）
        project_path = os.getenv("PROJECT_PATH", "project/fprj.fprj")
        output_dir = os.getenv("OUTPUT_DIR", "output")
        
        compiler = WatchfaceCompiler(
            project_path=project_path,
            output_dir=output_dir
        )
        
        if compiler.compile():
            print("Compile success")
            sys.exit(0)
        else:
            print("Compile failed")
            sys.exit(1)
    except Exception as e:
        print(f"Program error: {str(e)}")
        sys.exit(1)
