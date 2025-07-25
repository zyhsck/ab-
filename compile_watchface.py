import os
import logging
from binary import WatchfaceBinary

class WatchfaceCompiler:
    def __init__(self, project_path, output_dir):
        self.project_path = project_path
        self.output_dir = output_dir

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

            # 2. 调用编译工具（示例路径，需根据实际项目调整）
            compile_tool = os.path.join("compile.exe")  # 修正为正确的相对路径
            if not os.path.exists(compile_tool):
                logging.error("编译工具未找到！")
                return False

            # 3. 确保输出目录存在
            output_info_dir = os.path.join(self.output_dir, "output")
            os.makedirs(output_info_dir, exist_ok=True)

            # 4. 执行编译命令
            output_filename = os.path.splitext(os.path.basename(self.project_path))[0] + ".face"
            output_file = os.path.join(self.output_dir, "output", output_filename)
            cmd = f"{compile_tool} -b {self.project_path.replace('/', '\\')} output {output_filename} 1461256429"
            os.system(cmd)

            # 4. 验证输出文件
            if not os.path.exists(output_file):
                logging.error("编译失败，未生成输出文件！")
                return False

            # 5. 可选：设置表盘 ID（如果设备支持）
            binary = WatchfaceBinary(output_file)
            binary.setId("123456789")  # 替换为实际表盘 ID

            logging.info(f"表盘文件已生成：{output_file}")
            return True

        except Exception as e:
            logging.error(f"编译过程中发生错误：{e}")
            return False


if __name__ == "__main__":
    # 示例用法
    compiler = WatchfaceCompiler(
        project_path="src/rw5/rw5.fprj",  # 替换为实际项目文件路径
        output_dir="output"  # 替换为输出目录
    )
    if compiler.compile():
        print("编译成功！")
    else:
        print("编译失败！")