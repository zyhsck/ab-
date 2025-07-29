import os #line:1
import mmap #line:2
class WatchfaceBinary :#line:4
    def __init__ (OOOO0OO000O000OOO ,OOOOOOOO0OOOO0O00 ):#line:5
        OOOO0OO000O000OOO .path =OOOOOOOO0OOOO0O00 #line:6
        OOOO0OO000O000OOO .file_size =os .path .getsize (OOOOOOOO0OOOO0O00 )#line:7
    def setId (O0OOO00O0OO0OO000 ,O0OO0OO0O00OOO00O ):#line:9
        ""#line:10
        if len (O0OO0OO0O00OOO00O )!=9 :#line:11
            raise ValueError ("ID must be 9 characters long")#line:12
        with open (O0OOO00O0OO0OO000 .path ,"r+b")as OO00OOOOO0OO000OO :#line:15
            with mmap .mmap (OO00OOOOO0OO000OO .fileno (),0 ,access =mmap .ACCESS_WRITE )as O0000000OO00000OO :#line:17
                O0O00O0OO00O0OOO0 =O0OOO00O0OO0OO000 ._find_id_position (O0000000OO00000OO )#line:19
                if O0O00O0OO00O0OOO0 is None :#line:21
                    O0OOO00O0OO0OO000 ._append_id (O0000000OO00000OO ,O0OO0OO0O00OOO00O )#line:23
                else :#line:24
                    if O0O00O0OO00O0OOO0 +9 >len (O0000000OO00000OO ):#line:26
                        raise ValueError (f"ID position {O0O00O0OO00O0OOO0} is beyond file size {len(O0000000OO00000OO)}")#line:27
                    O0000000OO00000OO [O0O00O0OO00O0OOO0 :O0O00O0OO00O0OOO0 +9 ]=O0OO0OO0O00OOO00O .encode ('ascii')#line:30
    def _find_id_position (OOOOO0000O0OOO000 ,OO0O000O00OOO00O0 ):#line:32
        ""#line:33
        if len (OO0O000O00OOO00O0 )>=49 :#line:35
            return 40 #line:36
        O0OOOOO00OO000OO0 =b"ID:"#line:39
        O00000O0OO0O0O0OO =OO0O000O00OOO00O0 .find (O0OOOOO00OO000OO0 )#line:40
        if O00000O0OO0O0O0OO !=-1 and O00000O0OO0O0O0OO +len (O0OOOOO00OO000OO0 )+9 <=len (OO0O000O00OOO00O0 ):#line:41
            return O00000O0OO0O0O0OO +len (O0OOOOO00OO000OO0 )#line:42
        if len (OO0O000O00OOO00O0 )>=9 :#line:45
            return 0 #line:46
        return None #line:48
    def _append_id (OO0OO0000O0000000 ,OOOO0O0O000O000O0 ,OO00OO0O00OO00O00 ):#line:50
        ""#line:51
        O0O0O0OO00O0OOOO0 =b"ID:"+OO00OO0O00OO00O00 .encode ('ascii')#line:53
        O0OO0O0000OO00OO0 =len (OOOO0O0O000O000O0 )+len (O0O0O0OO00O0OOOO0 )#line:56
        OOOO0O0O000O000O0 .resize (O0OO0O0000OO00OO0 )#line:57
        OOOO0O0O000O000O0 .seek (len (OOOO0O0O000O000O0 )-len (O0O0O0OO00O0OOOO0 ))#line:60
        OOOO0O0O000O000O0 .write (O0O0O0OO00O0OOOO0 )#line:61
