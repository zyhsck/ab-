import os #line:1
import sys #line:2
import io #line:3
import logging #line:4
import pathlib #line:5
import shutil #line:6
import subprocess #line:7
from binary import WatchfaceBinary #line:8
sys .stdout =io .TextIOWrapper (sys .stdout .buffer ,encoding ='utf-8',errors ='replace')#line:11
sys .stderr =io .TextIOWrapper (sys .stderr .buffer ,encoding ='utf-8',errors ='replace')#line:12
logging .basicConfig (level =logging .INFO ,format ='%(asctime)s - %(levelname)s - %(message)s',handlers =[logging .StreamHandler (sys .stdout )])#line:19
class WatchfaceCompiler :#line:21
    def __init__ (O0O00OOOOOOO000O0 ,OOOOO000OO0OOOO00 ,O0OO0000O00OO0O0O ):#line:22
        ""#line:27
        try :#line:28
            O0O00OOOOOOO000O0 .project_path =pathlib .Path (OOOOO000OO0OOOO00 ).resolve ()#line:30
            O0O00OOOOOOO000O0 .final_output_dir =pathlib .Path (O0OO0000O00OO0O0O ).resolve ()#line:31
            O0O00OOOOOOO000O0 .temp_output_dir =O0O00OOOOOOO000O0 .project_path .parent /"output"#line:34
            O0O00OOOOOOO000O0 .final_output_dir .mkdir (parents =True ,exist_ok =True )#line:37
            logging .info (f"Project path: {O0O00OOOOOOO000O0.project_path}")#line:39
            logging .info (f"Final output directory: {O0O00OOOOOOO000O0.final_output_dir}")#line:40
            logging .info (f"Temporary output directory: {O0O00OOOOOOO000O0.temp_output_dir}")#line:41
        except Exception as O00000OOOOO000OOO :#line:42
            logging .error (f"Initialization failed: {str(O00000OOOOO000OOO)}",exc_info =True )#line:43
            raise #line:44
    def compile (O00O0O0000OOOOO0O ):#line:46
        ""#line:50
        try :#line:51
            if not O00O0O0000OOOOO0O ._validate_project_file ():#line:53
                return False #line:54
            OOO00O000O0OOO0OO =O00O0O0000OOOOO0O .project_path .stem +".face"#line:57
            OOO0OO00O00000O0O =O00O0O0000OOOOO0O .final_output_dir /OOO00O000O0OOO0OO #line:58
            if not O00O0O0000OOOOO0O ._run_compile_tool (OOO00O000O0OOO0OO ):#line:61
                return False #line:62
            if not O00O0O0000OOOOO0O ._move_output_file (OOO00O000O0OOO0OO ,OOO0OO00O00000O0O ):#line:65
                return False #line:66
            return O00O0O0000OOOOO0O ._set_watchface_id (OOO0OO00O00000O0O )#line:69
        except Exception as O0OOOOOO0OO0O0OO0 :#line:71
            logging .error (f"Compilation error: {str(O0OOOOOO0OO0O0OO0)}",exc_info =True )#line:72
            return False #line:73
    def _validate_project_file (O0OOO0O00000000OO ):#line:75
        ""#line:76
        if not O0OOO0O00000000OO .project_path .exists ():#line:77
            logging .error (f"Project file not found: {O0OOO0O00000000OO.project_path}")#line:78
            return False #line:79
        O0O00OO0OOO00O0OO =os .path .getsize (O0OOO0O00000000OO .project_path )#line:81
        if O0O00OO0OOO00O0OO ==0 :#line:82
            logging .error (f"Project file is empty: {O0OOO0O00000000OO.project_path}")#line:83
            return False #line:84
        logging .info (f"Project file size: {O0O00OO0OOO00O0OO} bytes")#line:86
        return True #line:87
    def _run_compile_tool (O0OOOOO0O0000OO00 ,O0O00OO00O00OO0O0 ):#line:89
        ""#line:90
        try :#line:91
            OO00OOOOO000OOO00 =pathlib .Path (__file__ ).parent /"compile.exe"#line:93
            if not OO00OOOOO000OOO00 .exists ():#line:95
                logging .error (f"Compiler tool not found at: {OO00OOOOO000OOO00}")#line:96
                return False #line:97
            O0O0OOOO00000OOOO =[str (OO00OOOOO000OOO00 ),"-b",str (O0OOOOO0O0000OO00 .project_path ),"output",O0O00OO00O00OO0O0 ,"1461256429"]#line:107
            logging .info (f"Executing command: {' '.join(O0O0OOOO00000OOOO)}")#line:109
            O0OOOOO0O0000OO00 .temp_output_dir .mkdir (parents =True ,exist_ok =True )#line:112
            logging .info (f"Created temporary output directory: {O0OOOOO0O0000OO00.temp_output_dir}")#line:113
            O0O0O000O0O0O000O =os .environ .copy ()#line:116
            O0O0O000O0O0O000O ["DOTNET_SYSTEM_GLOBALIZATION_INVARIANT"]="1"#line:117
            O0O0O000O0O0O000O ["COMPlus_gcServer"]="1"#line:118
            O0O0O000O0O0O000O ["COMPlus_gcConcurrent"]="1"#line:119
            OOOOO00000O0O0OO0 =subprocess .run (O0O0OOOO00000OOOO ,cwd =str (O0OOOOO0O0000OO00 .project_path .parent ),check =True ,stdout =subprocess .PIPE ,stderr =subprocess .PIPE ,text =True ,encoding ='utf-8',shell =True ,env =O0O0O000O0O0O000O )#line:132
            if OOOOO00000O0O0OO0 .stdout :#line:135
                logging .info (f"Compiler output:\n{OOOOO00000O0O0OO0.stdout}")#line:136
            if OOOOO00000O0O0OO0 .stderr :#line:137
                logging .warning (f"Compiler warnings:\n{OOOOO00000O0O0OO0.stderr}")#line:138
            return True #line:140
        except subprocess .CalledProcessError as OO00OO0OOO000OO0O :#line:142
            logging .error (f"Compilation failed (exit code {OO00OO0OOO000OO0O.returncode}):\n{OO00OO0OOO000OO0O.stderr}")#line:143
            return False #line:144
        except Exception as OO00OO0OOO000OO0O :#line:145
            logging .error (f"Command execution error: {str(OO00OO0OOO000OO0O)}")#line:146
            return False #line:147
    def _move_output_file (OO0O000OO00O0OO00 ,OOOOOOO00O0O00000 ,OO0OO0OO0O0O0OOO0 ):#line:149
        ""#line:150
        O0O0O000O00000O00 =OO0O000OO00O0OO00 .temp_output_dir /OOOOOOO00O0O00000 #line:152
        if not O0O0O000O00000O00 .exists ():#line:154
            logging .error (f"Output file not generated: {O0O0O000O00000O00}")#line:155
            return False #line:156
        try :#line:158
            shutil .move (str (O0O0O000O00000O00 ),str (OO0OO0OO0O0O0OOO0 ))#line:160
            logging .info (f"Moved output file to: {OO0OO0OO0O0O0OOO0}")#line:161
            return True #line:162
        except Exception as O0O0O00O000OOOOOO :#line:163
            logging .error (f"Failed to move output file: {str(O0O0O00O000OOOOOO)}")#line:164
            return False #line:165
    def _set_watchface_id (OO0O00O0O000O0O0O ,OO0O0O00O0OO000OO ):#line:167
        ""#line:168
        try :#line:169
            O0OO0000OO00O00OO =os .path .getsize (OO0O0O00O0OO000OO )#line:171
            if O0OO0000OO00O00OO <9 :#line:172
                logging .error (f"File too small to set ID: {O0OO0000OO00O00OO} bytes")#line:173
                return False #line:174
            O0O0OO0O0000OO00O =WatchfaceBinary (str (OO0O0O00O0OO000OO ))#line:177
            O0O0OO0O0000OO00O .setId ("123456789")#line:178
            logging .info (f"Set watch face ID: 123456789")#line:179
            return True #line:180
        except Exception as OOO00O0OO0O00O000 :#line:181
            logging .error (f"Failed to set watch face ID: {str(OOO00O0OO0O00O000)}")#line:182
            return False #line:183
if __name__ =="__main__":#line:186
    try :#line:187
        project_path =os .getenv ("PROJECT_PATH","project/fprj.fprj")#line:189
        output_dir =os .getenv ("OUTPUT_DIR","output")#line:190
        compiler =WatchfaceCompiler (project_path =project_path ,output_dir =output_dir )#line:195
        if compiler .compile ():#line:197
            print ("Compile success")#line:198
            sys .exit (0 )#line:199
        else :#line:200
            print ("Compile failed")#line:201
            sys .exit (1 )#line:202
    except Exception as e :#line:203
        print (f"Program error: {str(e)}")#line:204
        sys .exit (1 )#line:205
