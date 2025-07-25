import os
import logging
import pathlib
import subprocess
from binary import WatchfaceBinary

# 配置日志系统
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

class WatchfaceCompiler:
    def __init__(self, project_path, output_dir):
        """
        初始化编译器
        :param project_path: 项目文件路径(.fprj)
        :param output_dir: 输出目录路径
        """
        try:
            # 使用pathlib处理路径
            self.project_path = pathlib.Path(project_path).resolve()
            self.output_dir = pathlib.Path(output_dir).resolve()
            
            # 确保输出目录存在
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            logging.info(f"项目路径: {self.project_path}")
            logging.info(f"输出目录: {self.output_dir}")
        except Exception as e:
            logging.error(f"初始化失败: {str(e)}", exc_info=True)
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
            logging.error(f"编译过程异常: {str(e)}", exc_info=True)
            return False

    def _validate_paths(self):
        """验证所有必需路径"""
        if not self.project_path.exists():
            logging.error(f"项目文件不存在: {self.project_path}")
            return False
            
        # 编译工具路径 - 修改为相对路径
        compile_tool = "compile.exe"
        if not compile_tool.exists():
            logging.error(f"编译工具未找到: {compile_tool}")
            return False
            
        return True

    def _run_compile_command(self, output_filename):
        """执行编译命令"""
        # 编译工具路径
        compile_tool = "compile.exe"
        
        # 准备命令参数
        cmd = [
            str(compile_tool),
            "-b",
            str(self.project_path),
            "output",
            output_filename,
            "1461256429"
        ]
        
        try:
            logging.info(f"执行命令: {' '.join(cmd)}")
            
            # 使用subprocess执行命令
            result = subprocess.run(
                cmd,
                cwd=str(self.output_dir),
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            
            # 记录输出
            if result.stdout:
                logging.debug(f"编译输出:\n{result.stdout}")
            if result.stderr:
                logging.debug(f"编译错误:\n{result.stderr}")
                
            return True
            
        except subprocess.CalledProcessError as e:
            logging.error(f"编译失败（退出码 {e.returncode}）:\n{e.stderr}")
            return False
        except Exception as e:
            logging.error(f"命令执行异常: {str(e)}")
            return False

    def _process_output(self, output_file):
        """验证并处理输出文件"""
        if not output_file.exists():
            logging.error(f"输出文件未生成: {output_file}")
            return False
            
        try:
            # 设置表盘ID
            binary = WatchfaceBinary(str(output_file))
            binary.setId("123456789")
            
            logging.info(f"表盘文件生成成功: {output_file}")
            return True
        except Exception as e:
            logging.error(f"设置表盘ID失败: {str(e)}")
            return False


if __name__ == "__main__":
    try:
        # 使用固定路径
        compiler = WatchfaceCompiler(
            project_path="fprj.fprj",  # 固定文件名
            output_dir="output"         # 输出目录
        )
        
        if compiler.compile():
            print(" 编译成功")
        else:
            print(" 编译失败")
    except Exception as e:
        print(f" 程序异常: {str(e)}")