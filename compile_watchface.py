import os
import sys
import io
import logging
import pathlib
import subprocess
import shutil
import psutil  # 需要安装: pip install psutil
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
        终极解决方案：专注于解决compile.exe的内存问题
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
        编译主流程
        :return: 成功返回True，失败返回False
        """
        try:
            # 1. 验证路径
            if not self._validate_paths():
                return False
                
            # 2. 准备输出文件名
            output_filename = self.project_path.stem + ".face"
            output_file = self.output_dir / output_filename
            
            # 3. 执行编译
            if not self._run_compile_command(output_filename):
                return False
                
            # 4. 处理输出
            return self._process_output(output_file)
            
        except Exception as e:
            logging.error(f"Compilation error: {str(e)}", exc_info=True)
            return False

    def _validate_paths(self):
        """验证所有必需路径"""
        # 验证项目文件
        if not self.project_path.exists():
            logging.error(f"Project file not found: {self.project_path}")
            return False
            
        # 验证编译工具（位于根目录）
        compile_tool = pathlib.Path.cwd() / "compile.exe"
        logging.info(f"Compiler tool path: {compile_tool}")
        
        if not compile_tool.exists():
            logging.error(f"Compiler tool not found: {compile_tool}")
            return False
        
        return True

    def _run_compile_command(self, output_filename):
        """执行编译命令 - 专注于解决内存问题"""
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
                str(self.project_path),
                "output",
                output_filename,
                "1461256429"
            ]
            
            logging.info(f"Executing command: {' '.join(cmd)}")
            
            # 增加虚拟内存（仅Windows）
            if os.name == 'nt':
                self._increase_virtual_memory()
            
            # 设置环境变量优化内存
            env = os.environ.copy()
            env["DOTNET_SYSTEM_GLOBALIZATION_INVARIANT"] = "1"
            env["COMPlus_gcServer"] = "1"  # 启用服务器GC
            
            # 使用subprocess执行命令
            result = subprocess.run(
                cmd,
                cwd=str(self.project_path.parent),  # 在项目目录下运行
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

    def _increase_virtual_memory(self):
        """增加虚拟内存（仅Windows）"""
        try:
            # 设置页面文件
            subprocess.run('wmic computersystem where name="%COMPUTERNAME%" set AutomaticManagedPagefile=True', shell=True)
            subprocess.run('wmic pagefileset create name="C:\\pagefile.sys"', shell=True)
            subprocess.run('wmic pagefileset where name="C:\\pagefile.sys" set InitialSize=4096,MaximumSize=8192', shell=True)
            logging.info("Increased virtual memory to 4-8GB")
        except Exception as e:
            logging.error(f"Failed to increase virtual memory: {str(e)}")

    def _process_output(self, output_file):
        """验证并处理输出文件"""
        # 编译工具在当前目录生成输出文件
        project_output_file = self.project_path.parent / "output" / output_file.name
        
        if not project_output_file.exists():
            logging.error(f"Output file not generated: {project_output_file}")
            return False
            
        try:
            # 移动文件到输出目录
            shutil.move(str(project_output_file), str(output_file))
            
            # 设置表盘ID
            binary = WatchfaceBinary(str(output_file))
            binary.setId("123456789")
            
            logging.info(f"Watch face file generated: {output_file}")
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
