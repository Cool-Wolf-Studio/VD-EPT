import pickle

class Tools:
    def __init__(self):
        pass

    def Error(self, error, num, value):
        r = '\033[91m'; y = '\033[93m'; s = '\033[0m'
        print(f"{r}{error}{s}[{y}{num}{s}]: {value}")

    def to_bytes(self, value: str) -> bytes:
        value = str(value)
        return value.encode('utf-16', errors="replace")
    
    def re_text(self, value: bytes) -> str:
        return value.decode('utf-16', errors="ignore")
    
    def split_text(self, value: str) -> list:
        s = []
        for i in range(0, len(value), 100):
            s.append(value[i:i+100])
        return s
    
    def next_free(self, value, index: dict) -> str:
        c = int(value[1:3])
        t = int(value[4:])
        t += 1
        if t > 255: c += 1; t = 0
        if c > 10: self.Error("StorageError", 100, "空间不足!"); return 100
        e = f'T{str(c).zfill(2)}x{str(t).zfill(3)}'
        Value = []
        for v in index.values():
            if isinstance(v, list): Value.extend(v)
            else: Value.append(v)
        if e in Value: self.next_free(e, index)
        else: return e

class Mian:
    def __init__(self, name="LING011-1MB", mode=None):
        self.size = 1*1024*1024; self.label = ("EPT/VD", "LING011", "1.62x", self.size); self.name = name
        self.clusters = {f"C{c:02d}t{t:03d}": None for c in range(11) for t in range(256)}; self.index = {0:(self.label)}
        self.tools = Tools()
        self.part = self.PART(self.size, self.tools)
        if mode is True: self._self_check()
        elif mode is None: self._format()

    def part_size_statistic(self, part):
        if part not in self.part.space.keys(): self.tools.Error('StorageError', 92, '没有这个分区'); return 92
        allsize = (self.part.space[part]['size']) * 1024 #KB->B
        used = 0
        files = []
        for file in self.index.keys():
            if isinstance(self.index[file][0], tuple):
                if self.index[file][0][2] == part:
                    used += self.index[file][0][1]
                    files.append(file)
            else:
                if self.index[file][1] == part:
                    used += self.index[file][0][1]
                    files.append(file)
        if allsize < used: self.tools.Error('StorageError', 100, '空间不足'); return 100
        free = allsize - used
        print(f"分区'{part}'的使用情况: {used}/{allsize}B, 剩余空间: {free}B")
        print(f"分区'{part}'中的文件/文件夹: {files}")
        return (used, allsize, free)
    
    def allpart_size_statistic(self):
        allsize = self.size * 1024
        used = 0
        files = []
        for file in self.index.keys():
            if isinstance(self.index[file][0], tuple) and file != 0:
                used += self.index[file][0][1]
                files.append(file)
            elif file != 0:
                used += self.index[file][0][1]
                files.append(file)
        if allsize < used: self.tools.Error('StorageError', 100, '空间不足'); return 100
        free = allsize - used
        print(f"VD的使用情况: {used}/{allsize}B, 剩余空间: {free}B")
        print(f"VD中的文件/文件夹: {files}")
        return (used, allsize, free)

    def _self_check(self):
        with open('clusters.ovd', 'rb') as c, open('index.ovd', 'rb') as i, open('partinfo.ovd', 'rb') as p:
            self.clusters = eval(self.tools.re_text(c.read()))
            self.index = eval(self.tools.re_text(i.read()))
            self.part = pickle.load(p)
        self.allpart_size_statistic()
        print('self-check over')
        return 0

    def _format(self):
        with open('clusters.ovd', 'wb') as c, open('index.ovd', 'wb') as i, open('partinfo.ovd', 'wb') as p:
            c.write(self.tools.to_bytes(self.clusters))
            i.write(self.tools.to_bytes(self.index))
            pickle.dump(self.part, p)
        print('format VD. ok')
        return 0
    
    def storage(self):
        with open('clusters.ovd', 'wb') as c, open('index.ovd', 'wb') as i:
            c.write(self.tools.to_bytes(self.clusters))
            i.write(self.tools.to_bytes(self.index))
        return 0

    class PART:
        def __init__(self, size: int, tool: Tools):
            self.size = size
            self.used = 0
            self.space = {0:("EPT/VD", "LING011", self.size), 'main':{"type": "ept", "size": self.size}}
            self.tools = tool

        def allocate(self, name, size: int=1):
            if size < 1: self.tools.Error('StorageError', 110, '无效或过小的空间大小(<1)'); return 110
            if name in self.space.keys(): self.tools.Error('StorageError', 110, '分区名无效或已存在'); return 110
            if (self.used + size) > self.size: self.tools.Error('StorageError', 100, '空间不足'); return 100
            elif (self.used + size) == self.size:
                self.tools.Error('StorageWarning', 109, '这将导致VD中没有任何剩余空间, 想要继续吗(Y,n)'); a = input()
                if a == 'y' or a == 'yes' or a == 'Y': del a
                else: del a; return 109
            size = size * 1024
            self.used += size
            self.space.setdefault(name, {'type': 'ept', 'size': size})
            return 0
        
        def free(self, name):
            if name not in self.space.keys: self.tools.Error('StorageError', 92, '没有这个分区'); return 92
            elif name == 0: self.tools.Error('StorageError', 92, '想删除元信息'); return 92
            self.used -= self.space[name]['size']
            self.space.pop(name)
            return 0

        def changeSize(self, name, size):
            if name not in self.space.keys: self.tools.Error('StorageError', 92, '没有这个分区'); return 92
            elif name == 0: self.tools.Error('StorageError', 92, '想修改元信息'); return 92
            size = size * 1024
            self.used = (self.used - self.space[name]["size"] + size)
            self.space[name]['size'] = size
            return 0
        
        def rename(self, name, new):
            if name not in self.space.keys: self.tools.Error('StorageError', 92, '没有这个分区'); return 92
            elif name == 0: self.tools.Error('StorageError', 92, '想重命名元信息'); return 92
            self.space[new] = self.space.pop(name)
            return 0
        
        def info(self, name):
            if name not in self.space.keys: self.tools.Error('StorageError', 92, '没有这个分区'); return 92
            return self.space[name]
    
    def add_f(self, file, parent=None, value=None, part="main"):
        if file in self.index.keys() and parent == self.index[file][0][0]: self.tools.Error('StorageError', 92, '想创建一个重复的文件'); return 92
        if file[0] == '/' or file[-1] == '/': self.tools.Error('StorageError', 110, '文件名称不合法'); return 110
        if value is None:
            self.index.setdefault(file, ((parent, 0, part), None))
            self.storage()
            print(f"创建文件'{file}'成功")
            return 0
        Value = []
        for i in range(11 * 256):
            key = f"C{str(i//256).zfill(2)}t{str(i%256).zfill(3)}"
            for v in self.index.values():
                if isinstance(v, list) or isinstance(v, tuple): Value.extend(v)
                else: Value.append(v)
            if key not in Value:
                print(key)
                if len(value) < 100:
                    self.index.setdefault(file, ((parent, len(key), part), [key]))
                    self.clusters[key] = value
                else:
                    indexes = []
                    indexes.append(key)
                    values = self.tools.split_text(value)
                    self.clusters[key] = values[0]
                    key = self.tools.next_free(key, self.index)
                    self.index.setdefault(file, ((parent, len(value), part), indexes))
                    for i in range(int(len(value)/100)):
                        indexes.append(key)
                        values = self.tools.split_text(value)
                        self.clusters[key] = value[i]
                        key = self.tools.next_free(key, self.index)
                    self.index.setdefault(file, ((parent, len(value), part), indexes))
                self.storage()
                print(f"创建文件'{file}'成功")
                return 0
        self.tools.Error('StorageError', 100, '您的虚拟磁盘设备已经满了!(FULL)')
        return 100

    def set_p(self, name, parent=None, part="main"):
        if name in self.index.keys() and parent == self.index[name][0]: self.tools.Error('StorageError', 92, '想创建一个重复的文件夹'); return 92
        if name[0] == '/' or name[-1] != '/': self.tools.Error('StorageError', 110, '文件夹名称不合法'); return 110
        self.index.setdefault(name, (parent, part))
        self.storage()
        print(f"创建文件'{name}'成功")
        return 0
    
    def find(self, name: str) -> list:
        found = []
        for file in self.index.keys():
            if name == str(file):
                print('FILE: ', file)
                found.append(file)
            elif name == str(file)[:-1]:
                print('PATH: ', file)
                found.append(file)
        return found
    
    def delete(self, name: str, delc=True):
        if name not in self.index.keys(): self.tools.Error('StorageError', 92, '没有这个文件或文件夹'); return 92
        if isinstance(self.index[name][0], tuple):
            if self.index[name][1] is not None:
                self.clusters.pop(name)
                print(f"删除文件'{name}'成功")
            if delc == True:
                self.clusters.update({key: None for key in self.index[name][1]})
                self.index.pop(name)
            else:
                self.index.pop(name)
            print(f"删除文件'{name}'成功")
        else:
            self.index.pop(name)
            print(f"删除文件夹'{name}'成功")
        self.storage()
        return 0
    
    def change_f(self, name: str, value: str):
        if name not in self.index.keys(): self.tools.Error('StorageError', 92, '没有这个文件'); return 92
        self.clusters.update({key: None for key in self.index[name][1]})
        Value = []
        for i in range(11 * 256):
            key = f"C{str(i//256).zfill(2)}t{str(i%256).zfill(3)}"
            for v in self.index.values():
                if isinstance(v, list) or isinstance(v, tuple): Value.extend(v)
                else: Value.append(v)
            if key not in Value:
                print(key)
                if value > 100:
                    indexes = []
                    indexes.append(key)
                    values = self.tools.split_text(value)
                    self.clusters[key] = values[0]
                    key = self.tools.next_free(key, self.index)
                    self.index[name] = (self.index[name][0], indexes)
                    for i in range(int(len(value)/100)):
                        indexes.append(key)
                        values = self.tools.split_text(value)
                        self.clusters[key] = value[i]
                        key = self.tools.next_free(key, self.index)
                    self.index[name] = (self.index[name][0], indexes)
                else:
                    self.index[name] = (self.index[name][0], [key])
                    self.clusters[key] = value
                self.storage()
                print(f"修改文件'{name}'成功")
                return 0
        self.tools.Error('StorageError', 100, '您的虚拟磁盘设备已经满了!(FULL)')
        return 100
    
    def move_f(self, name: str, parent: str):
        if name not in self.index.keys(): self.tools.Error('StorageError', 92, '没有这个文件'); return 92
        if parent not in self.index.keys(): self.tools.Error('StorageError', 92, '没有这个文件夹'); return 92
        self.index[name] = ((parent, len(self.index[name][0][1])), self.index[name][1])
        self.storage()
        print(f"修改文件路径'{name}'到'{parent}'成功")
        return 0
    
    def move_p(self, name: str, parent: str):
        if name not in self.index.keys(): self.tools.Error('StorageError', 92, '没有这个文件夹'); return 92
        self.index[name] = (parent, 'PATH')
        self.storage()
        print(f"修改文件夹路径'{name}'到'{parent}'成功")
        return 0
    
    def query(self, name: str):
        if name not in self.index.keys(): self.tools.Error('StorageError', 92, '没有这个文件或文件夹'); return 92
        if isinstance(self.index[name][0], tuple):
            print(f"文件'{name}'的元信息: {self.clusters[name]}")
        else:
            print(f"文件夹'{name}'的元信息: {self.index[name][1]}")
        return 0
    
    def read(self, name: str):
        if name not in self.index.keys(): self.tools.Error('StorageError', 92, '没有这个文件'); return 92
        if not isinstance(self.index[name][0], tuple): self.tools.Error('StorageError', 92, '不是文件'); return 0
        if self.index[name][1] is None:
            print(f"文件'{name}'的内容: {self.clusters[name]}")
        else:
            values = ''
            for key in self.index[name][1]:
                values += self.clusters[key]
            print(f"文件'{name}'的内容: {values}")
        return 0
    
    def p_list(self, name: str):
        if name not in self.index.keys(): self.tools.Error('StorageError', 92, '没有这个文件夹'); return 92
        if isinstance(self.index[name][0], tuple): self.tools.Error('StorageError', 92, '不是文件夹'); return 0
        files = []
        for file in self.index.keys():
            if name.count('/') == file.count('/'):
                files.append(file)
        print(f"文件夹'{name}'中的文件/文件夹: {files}")
        return 0
    
    def rename(self, name: str, new: str):
        if name not in self.index.keys(): self.tools.Error('StorageError', 92, '没有这个文件或文件夹'); return 92
        self.index[new] = self.index.pop(name)
        self.storage()
        print(f"重命名'{name}'为'{new}'成功")
        return 0
    
    def watch_label(self):
        print(f"VD的标签: {self.label}")
        return 0
    
    def part_info(self):
        print(f"VD的分区信息: {self.part.space}")
        return 0
    
    def p_allocate(self, name, part="main"):
        if name not in self.index.keys(): self.tools.Error('StorageError', 92, '没有这个文件夹'); return 92
        if part not in self.part.space.keys(): self.tools.Error('StorageError', 92, '没有这个分区'); return 92
        self.index[name] = (self.index[name][0], part)
        return 0

    def query_p(self, name):
        if name not in self.index.keys(): self.tools.Error('StorageError', 92, '没有这个文件夹'); return 92
        if not isinstance(self.index[name][0], tuple): self.tools.Error('StorageError', 92, '不是文件夹'); return 0
        if self.index[name][1] == 'main': print(f"文件夹'{name}'的分区: 主分区")
        else: print(f"文件夹'{name}'的分区: {self.index[name][1]}")
        return 0
    
    def f_allocate(self, file, part="main"):
        if file not in self.index.keys(): self.tools.Error('StorageError', 92, '没有这个文件'); return 92
        if part not in self.part.space.keys(): self.tools.Error('StorageError', 92, '没有这个分区'); return 92
        self.index[file] = ((None, self.index[file][0][1], part), self.index[file][1])
        return 0
    
    def part_size(self, part):
        if part not in self.part.space.keys(): self.tools.Error('StorageError', 92, '没有这个分区'); return 92
        size = self.part.space[part]['size']
        if size < 1024: print(f"分区'{part}'的大小: {size}KB")
        if size > 1024 and size < 1024*1024: print(f"分区'{part}'的大小: {size/1024}MB")
        if size > 1024*1024: print(f"分区'{part}'的大小: {size/1024/1024}GB")
        else: self.tools.Error('StorageError', 100, '无效的分区大小'); return 100
        return 0

vd = Mian(mode=None) #None是格式化，Ture是读盘
vd.watch_label()