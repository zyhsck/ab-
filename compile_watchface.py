import os
import sys
import logging
import pathlib
import shutil
import subprocess
import re
from PIL import Image

# 强制UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 配置日志系统
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

class WatchfaceCompiler:
    def __init__(self, project_path, output_dir):
        try:
            self.project_path = pathlib.Path(project_path).resolve()
            self.final_output_dir = pathlib.Path(output_dir).resolve()
            self.temp_output_dir = self.project_path.parent / "output"
            self.final_output_dir.mkdir(parents=True, exist_ok=True)
            
            logging.info(f"Project path: {self.project_path}")
            logging.info(f"Final output directory: {self.final_output_dir}")
            
            # 动态获取预览图路径
            self.images_dir = self.project_path.parent / "images"
            self.pre_path = self.images_dir / "pre.png"
        except Exception as e:
            logging.error(f"Initialization failed: {str(e)}", exc_info=True)
            raise

    def compile(self):
        try:
            # 1. 首次编译尝试（捕获期望尺寸）
            output_filename = self.project_path.stem + ".face"
            success, error_output = self._run_compile_tool(output_filename)
            
            if not success:
                # 2. 从错误中解析期望尺寸
                expected_size = self._parse_expected_preview_size(error_output)
                if not expected_size:
                    logging.error("无法从错误信息中解析期望尺寸")
                    return False
                
                logging.info(f"解析到期望尺寸: {expected_size}")
                
                # 3. 调整预览图尺寸
                if not self._adjust_preview_size(expected_size):
                    logging.error("预览图尺寸调整失败")
                    return False
                
                # 4. 清理环境后重试编译
                logging.info("清理临时输出目录并重试编译...")
                if self.temp_output_dir.exists():
                    shutil.rmtree(self.temp_output_dir)
                
                success, _ = self._run_compile_tool(output_filename)
            
            if success:
                # 5. 移动输出文件
                final_output_file = self.final_output_dir / output_filename
                return self._move_output_file(output_filename, final_output_file)
            
            return False
            
        except Exception as e:
            logging.error(f"编译过程异常: {str(e)}", exc_info=True)
            return False

    def _parse_expected_preview_size(self, error_output):
        """从错误信息提取期望尺寸"""
        pattern = r'expected: (\d+)x(\d+)'
        match = re.search(pattern, error_output)
        if match:
            return (int(match.group(1)), int(match.group(2)))
        return None

    def _adjust_preview_size(self, expected_size):
        """精确调整预览图尺寸"""
        try:
            if not self.pre_path.exists():
                logging.error(f"预览图不存在: {self.pre_path}")
                return False
                
            with Image.open(self.pre_path) as img:
                current_size = img.size
                if current_size == expected_size:
                    logging.info("预览图尺寸已符合要求")
                    return True
                
                logging.info(f"调整预览图尺寸: {current_size} → {expected_size}")
                resized_img = img.resize(expected_size, Image.LANCZOS)
                
                # 原子操作保存文件
                temp_path = self.pre_path.with_suffix('.tmp.png')
                resized_img.save(temp_path, "PNG")
                os.replace(temp_path, self.pre_path)
                
                # 验证调整结果
                with Image.open(self.pre_path) as verified_img:
                    if verified_img.size == expected_size:
                        logging.info("尺寸验证成功")
                        return True
                    else:
                        logging.error(f"尺寸验证失败! 期望: {expected_size}, 实际: {verified_img.size}")
            return False
        except Exception as e:
            logging.error(f"调整预览图时出错: {str(e)}")
            return False

    def _run_compile_tool(self, output_filename):
        """执行编译命令"""
        try:
            compile_tool = pathlib.Path(__file__).parent / "compile.exe"
            if not compile_tool.exists():
                logging.error(f"编译器未找到: {compile_tool}")
                return False, ""
            
            cmd = [
                str(compile_tool),
                "-b",
                str(self.project_path),
                "output",
                output_filename,
                "1461256429"
            ]
            
            logging.info(f"执行命令: {' '.join(cmd)}")
            self.temp_output_dir.mkdir(parents=True, exist_ok=True)
            
            result = subprocess.run(
                cmd,
                cwd=str(self.project_path.parent),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                shell=True
            )
            
            output_text = result.stdout + "\n" + result.stderr
            logging.info(f"编译器输出:\n{output_text}")
            
            return result.returncode == 0, output_text
            
        except Exception as e:
            logging.error(f"命令执行异常: {str(e)}")
            return False, str(e)

    def _move_output_file(self, output_filename, final_output_file):
        """移动输出文件"""
        temp_output_file = self.temp_output_dir / output_filename
        
        if not temp_output_file.exists():
            logging.error(f"输出文件未生成: {temp_output_file}")
            return False
            
        try:
            shutil.move(str(temp_output_file), str(final_output_file))
            logging.info(f"文件已移动至: {final_output_file}")
            return True
        except Exception as e:
            logging.error(f"文件移动失败: {str(e)}")
            return False

if __name__ == "__main__":
    try:
        project_path = os.getenv("PROJECT_PATH", "project/fprj.fprj")
        output_dir = os.getenv("OUTPUT_DIR", "output")
        
        compiler = WatchfaceCompiler(project_path, output_dir)
        sys.exit(0 if compiler.compile() else 1)
    except Exception as e:
        print(f"程序异常: {str(e)}")
        sys.exit(1)
