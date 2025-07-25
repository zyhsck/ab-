import os
import logging
import pathlib
import subprocess
from binary import WatchfaceBinary

class WatchfaceCompiler:
    def __init__(self, project_path, output_dir):
        """
        初始化编译器
        :param project_path: 项目文件路径(.fprj)
        :param output_dir: 输出目录路径
        """
        self.project_path = pathlib.Path(project_path).resolve()
        self.output_dir = pathlib.Path(output_dir).resolve()

    def compile(self):
        """
        将项目文件编译为表盘文件(.face)
        :return: 编译成功返回True，否则返回False
        """
        try:
            # 1. 验证输入路径
            if not self._validate_paths():
                return False

            # 2. 准备输出目录和文件名
            output_info_dir = self.output_dir / "output"
            output_info_dir.mkdir(parents=True, exist_ok=True)
            
            output_filename = self.project_path.stem + ".face"
            output_file = output_info_dir / output_filename

            # 3. 执行编译命令
            if not self._run_compile_command(output_filename):
                return False

            # 4. 验证输出并设置表盘ID
            return self._process_output(output_file)

        except Exception as e:
            logging.error(f"编译过程中发生未预期错误: {str(e)}", exc_info=True)
            return False

    def _validate_paths(self):
        """验证输入路径是否存在"""
        if not self.project_path.exists():
            logging.error(f"项目文件不存在: {self.project_path}")
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
            # 使用subprocess替代os.system更安全
            result = subprocess.run(
                cmd,
                cwd=self.output_dir,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            logging.debug(f"编译输出: {result.stdout}")
            return True
            
        except subprocess.CalledProcessError as e:
            logging.error(f"编译命令执行失败: {e.stderr}")
            return False

    def _process_output(self, output_file):
        """处理输出文件"""
        if not output_file.exists():
            logging.error(f"输出文件未生成: {output_file}")
            return False
            
        try:
            binary = WatchfaceBinary(str(output_file))
            binary.setId("122456789")
            logging.info(f"表盘文件生成成功: {output_file}")
            return True
        except Exception as e:
            logging.error(f"处理输出文件时出错: {str(e)}")
            return False


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # 示例用法
    compiler = WatchfaceCompiler(
        project_path="src/rw5/rw5.fprj",
        output_dir="output"
    )
    
    if compiler.compile():
        print("编译成功！")
    else:
        print("编译失败！")