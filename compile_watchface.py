import os
import sys
import logging
import pathlib
import subprocess
from binary import WatchfaceBinary

# 强制UTF-8编码输出
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf8', buffering=1)
logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)],
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class WatchfaceCompiler:
    def __init__(self, project_path, output_dir):
        """
        初始化编译器
        :param project_path: 项目文件路径(.fprj)
        :param output_dir: 输出目录路径
        """
        try:
            self.project_path = pathlib.Path(project_path).resolve()
            self.output_dir = pathlib.Path(output_dir).resolve()
        except Exception as e:
            logging.error(f"路径解析失败: {str(e)}")
            raise

    def compile(self):
        """
        编译主流程
        :return: 成功返回True，失败返回False
        """
        try:
            # 1. 路径验证
            if not self._validate_paths():
                return False

            # 2. 准备输出环境

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
            logging.error(f"项目文件不存在（绝对路径）：{self.project_path}")
            return False

        compile_tool = pathlib.Path("compile.exe").resolve()
        if not compile_tool.exists():
            logging.error(f"编译工具未找到: {compile_tool}")
            return False

        return True

    def _run_compile_command(self, output_filename):
        """执行编译命令"""
        compile_tool = pathlib.Path("compile.exe").resolve()
        cmd = [
            str(compile_tool),
            "-b",
            str(self.project_path),
            "output",
            output_filename,
            "1461256429"
        ]

        try:
            result = subprocess.run(
                cmd,
                cwd=self.output_dir,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            logging.debug(f"编译输出:\n{result.stdout}")
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"编译失败（退出码 {e.returncode}）:\n{e.stderr}")
            return False

    def _process_output(self, output_file):
        """验证并处理输出文件"""
        if not output_file.exists():
            logging.error(f"输出文件未生成: {output_file}")
            return False

        try:
            binary = WatchfaceBinary(str(output_file))
            binary.setId("122456789")
            logging.info(f"表盘文件生成成功: {output_file}")
            return True
        except Exception as e:
            logging.error(f"设置表盘ID失败: {str(e)}")
            return False


if __name__ == "__main__":
    # 示例用法（测试时建议使用绝对路径）
    compiler = WatchfaceCompiler(
        project_path=os.path.abspath("fprj.fprj"),
        output_dir=os.path.abspath("output")
    )
    
    if compiler.compile():
        print("✅ 编译成功")
    else:
        print("❌ 编译失败")