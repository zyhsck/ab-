import os
import mmap
import struct

class WatchfaceBinary:
    def __init__(self, path):
        self.path = path
        self.file_size = os.path.getsize(path)
        
    def setId(self, id):
        """
        设置表盘ID
        :param id: 9位ASCII字符的表盘ID
        """
        if len(id) != 9:
            raise ValueError("ID must be 9 characters long")
        
        # 以读写模式打开文件
        with open(self.path, "r+b") as f:
            # 创建内存映射
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_WRITE) as mm:
                # 尝试查找ID位置
                id_position = self._find_id_position(mm)
                
                if id_position is None:
                    # 如果找不到ID位置，尝试在文件末尾添加
                    self._append_id(mm, id)
                else:
                    # 确保位置有效
                    if id_position + 9 > len(mm):
                        raise ValueError(f"ID position {id_position} is beyond file size {len(mm)}")
                    
                    # 写入ID
                    mm[id_position:id_position+9] = id.encode('ascii')
    
    def _find_id_position(self, mm):
        """
        查找可能的ID位置
        :param mm: 内存映射对象
        :return: ID位置或None
        """
        # 尝试固定位置40（原始假设）
        if len(mm) >= 49:  # 40 + 9
            return 40
        
        # 尝试搜索特征字节 "ID:"
        signature = b"ID:"
        pos = mm.find(signature)
        if pos != -1 and pos + len(signature) + 9 <= len(mm):
            return pos + len(signature)
        
        # 尝试文件开头
        if len(mm) >= 9:
            return 0
        
        return None
    
    def _append_id(self, mm, id):
        """
        在文件末尾添加ID字段
        :param mm: 内存映射对象
        :param id: 9位ASCII字符的表盘ID
        """
        # 创建新的ID字段
        id_field = b"ID:" + id.encode('ascii')
        
        # 调整文件大小
        new_size = len(mm) + len(id_field)
        mm.resize(new_size)
        
        # 在文件末尾写入ID
        mm.seek(len(mm) - len(id_field))
        mm.write(id_field)
