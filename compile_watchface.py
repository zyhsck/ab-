import os
import logging
import pathlib
from binary import WatchfaceBinary

class WatchfaceCompiler:
    def __init__(self, project_path, output_dir):
        self.project_path = str(pathlib.Path(project_path).resolve())
        self.output_dir = str(pathlib.Path(output_dir).resolve())

    def compile(self):
        """
        将项目文件编译为表盘文件（.bin）
        :return: 编译成功返回 True，否则返回 False
        """
        try:
            # 1. 检查项目文件是否存在
            if not os.path.exists(self.project_path):
                logging.error(f"项目文件 {self.project_path} 不存在！")
                return False

            # 2. 调用编译工具（使用绝对路径更安全）
            compile_tool = str(pathlib.Path("compile.exe").resolve())
            if not os.path.exists(compile_tool):
                logging.error(f"编译工具未找到：{compile_tool}")
                return False

            # 3. 确保输出目录存在
            output_info_dir = pathlib.Path(self.output_dir) / "output"
            output_info_dir.mkdir(parents=True, exist_ok=True)

            # 4. 执行编译命令（安全处理路径）
            output_filename = pathlib.Path(self.project_path).stem + ".face"
            output_file = output_info_dir / output_filename
            
            cmd = f'"{compile_tool}" -b "{self.project_path}" output "{output_filename}" 1461256429'
            if os.system(cmd) != 0:
                raise RuntimeError("编译命令执行失败")

            # 5. 验证输出文件
            if not output_file.exists():
                logging.error("编译失败，未生成输出文件！")
                return False

            # 6. 设置表盘 ID
            binary = WatchfaceBinary(str(output_file))
            binary.setId("122456789")

            logging.info(f"表盘文件已生成：{output_file}")
            return True

        except Exception as e:
            logging.error(f"编译错误：{str(e)}", exc_info=True)
            return False