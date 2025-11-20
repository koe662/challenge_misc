import sys
import time
import resource
import os as real_os  # 保存真实os模块引用（用于初始化flag）
from types import ModuleType
from io import StringIO
import ast
import socket
import os as sys_os  # 避免命名冲突

# ==================== GZCTF配置（适配平台）====================
FLAG_FILE = "/flag.txt"  # 兼容原有解题路径
LISTEN_PORT = 8080  # GZCTF默认映射端口
ALLOWED_MODULES = {"sys", "importlib", "os"}
ALLOWED_FILES = {FLAG_FILE}
ALLOWED_OS_METHODS = {"open", "read", "close", "O_RDONLY"}
EXEC_TIMEOUT = 1.5
MAX_OUTPUT_SIZE = 10240
MAX_MEMORY = 67108864  # 64MB

# 危险列表（全面封堵）
DANGEROUS_MODULES = {
    "subprocess", "ctypes", "ctypes.util", "socket", "select",
    "fcntl", "pty", "tty", "multiprocessing", "threading",
    "posix", "resource", "sysconfig", "distutils"
}
DANGEROUS_OS_METHODS = {
    "system", "popen", "popen2", "popen3", "popen4",
    "fork", "execv", "execve", "execvp", "execvpe",
    "mount", "umount", "umount2", "chroot", "unshare",
    "listdir", "scandir", "access", "stat", "lstat",
    "creat", "truncate", "ftruncate", "write", "remove",
    "rename", "chmod", "chown", "forkpty"
}
DANGEROUS_KEYWORDS = {
    "/proc", "/sys", "/dev", "/etc", "mount", "chroot",
    "unshare", "fork", "exec", "socket", "ctypes", "subprocess"
}

# ==================== 1. GZCTF Flag初始化（从环境变量注入）====================
def init_flag():
    """从GZCTF环境变量FLAG读取，写入/flag.txt"""
    flag = real_os.getenv("FLAG", "sdpcsec{pyth0n_j41l_br34k3r_[TEAM_HASH]}")  # 默认测试flag
    try:
        # 以只读模式创建/flag.txt（非root用户可写）
        with real_os.fdopen(real_os.open(FLAG_FILE, real_os.O_WRONLY | real_os.O_CREAT, 0o444), "w") as f:
            f.write(flag.strip())
        print(f"[INFO] Flag已注入：{FLAG_FILE}")
    except Exception as e:
        print(f"[ERROR] Flag注入失败：{str(e)}")
        sys.exit(1)

# 初始化Flag（仅在启动时执行一次）
init_flag()

# ==================== 2. 伪造初始OS模块====================
class FakeOs:
    def __getattr__(self, name):
        raise AttributeError(f"❌ 伪造os模块无此属性：{name}（请删除sys.modules['os']后重新导入）")

# 初始篡改os模块缓存
sys.modules['os'] = FakeOs()

# ==================== 3. AST语义检测====================
class DangerousCodeDetector(ast.NodeVisitor):
    def __init__(self):
        self.has_dangerous = False
        self.dangerous_reason = ""

    def visit_Call(self, node):
        func = node.func
        if isinstance(func, ast.Attribute):
            if isinstance(func.value, ast.Name) and func.value.id in DANGEROUS_MODULES:
                self.has_dangerous = True
                self.dangerous_reason = f"禁止调用危险模块方法：{func.value.id}.{func.attr}"
            if isinstance(func.value, ast.Name) and func.value.id == "os" and func.attr in DANGEROUS_OS_METHODS:
                self.has_dangerous = True
                self.dangerous_reason = f"禁止调用os危险方法：os.{func.attr}"
            if isinstance(func.value, ast.Name) and func.value.id == "sys" and func.attr in ["meta_path", "modules", "settrace"]:
                self.has_dangerous = True
                self.dangerous_reason = f"禁止操作sys敏感属性：sys.{func.attr}"
        if isinstance(func, ast.Name) and func.id in ["getattr", "setattr", "delattr", "eval", "exec"]:
            self.has_dangerous = True
            self.dangerous_reason = f"禁止使用危险内置函数：{func.id}"
        self.generic_visit(node)

    def visit_Str(self, node):
        for keyword in DANGEROUS_KEYWORDS:
            if keyword in node.s:
                self.has_dangerous = True
                self.dangerous_reason = f"禁止包含敏感关键词/路径：{keyword}"
        self.generic_visit(node)

    def visit_Dict(self, node):
        for key, value in zip(node.keys, node.values):
            if isinstance(key, ast.Str) and key.s in DANGEROUS_OS_METHODS:
                self.has_dangerous = True
                self.dangerous_reason = f"禁止访问os危险属性：os.__dict__['{key.s}']"
        self.generic_visit(node)

def check_dangerous_code(user_code):
    detector = DangerousCodeDetector()
    try:
        tree = ast.parse(user_code)
        detector.visit(tree)
        if detector.has_dangerous:
            raise ValueError(detector.dangerous_reason)
    except SyntaxError:
        raise ValueError("❌ 代码语法错误")
    except ValueError as e:
        raise e
    except Exception:
        raise ValueError("❌ 检测到未知危险操作")

# ==================== 4. 加固sys.modules====================
class RestrictedModulesDict:
    def __init__(self, original_modules):
        self.original = original_modules

    def __delitem__(self, key):
        if key != "os":
            raise KeyError(f"❌ 仅允许删除sys.modules['os']，禁止删除{key}")
        if key in self.original and isinstance(self.original[key], FakeOs):
            del self.original[key]
        else:
            raise KeyError("❌ 无需重复删除sys.modules['os']")

    def __setitem__(self, key, value):
        raise ValueError("❌ 禁止修改sys.modules（添加模块）")

    def __getitem__(self, key):
        if key in DANGEROUS_MODULES:
            raise KeyError(f"❌ 禁止访问危险模块：{key}")
        return self.original[key]

    def __getattr__(self, attr):
        if attr in ["clear", "update", "pop", "popitem", "setdefault"]:
            raise AttributeError(f"❌ 禁止调用sys.modules.{attr}")
        return getattr(self.original, attr)

# ==================== 5. 加固sys模块====================
class RestrictedSys:
    def __init__(self, original_sys):
        self.original = original_sys
        self.frozen_attrs = ["meta_path", "modules", "settrace", "setprofile", "path"]

    def __getattr__(self, name):
        if name in ["socket", "fd", "fileno", "dup", "dup2", "call_tracing"]:
            raise AttributeError(f"❌ 禁止访问sys敏感属性：{name}")
        attr = getattr(self.original, name)
        if name == "modules":
            return RestrictedModulesDict(attr)
        return attr

    def __setattr__(self, name, value):
        if name in self.frozen_attrs:
            raise AttributeError(f"❌ 禁止修改sys核心属性：{name}")
        if name == "original":
            super().__setattr__(name, value)
        else:
            raise AttributeError(f"❌ 禁止修改sys属性：{name}")

sys = RestrictedSys(sys)

# ==================== 6. 加固os模块====================
class SafeOs:
    def __init__(self, original_os):
        self.original = original_os
        self.O_RDONLY = original_os.O_RDONLY

    def __getattr__(self, name):
        if name not in ALLOWED_OS_METHODS:
            raise AttributeError(f"❌ os模块仅允许使用：{ALLOWED_OS_METHODS}，禁止使用os.{name}")
        if name == "open":
            def restricted_open(path, flags, *args):
                real_path = self.original.path.realpath(path)
                if real_path not in ALLOWED_FILES:
                    raise PermissionError(f"❌ 仅允许访问文件：{ALLOWED_FILES}")
                if flags != self.O_RDONLY:
                    raise PermissionError(f"❌ 仅允许读权限（O_RDONLY），禁止其他权限")
                return self.original.open(path, flags, *args)
            return restricted_open
        method = getattr(self.original, name)
        if name == "read":
            def restricted_read(fd, size):
                if size > 1024:
                    size = 1024
                return method(fd, size)
            return restricted_read
        return method

    def __getattribute__(self, name):
        if name in ["__dict__", "__getattribute__", "__getattr__", "__class__"]:
            raise AttributeError(f"❌ 禁止访问os反射属性：{name}")
        return super().__getattribute__(name)

# ==================== 7. 模块导入拦截====================
class RestrictedImporter:
    def __init__(self):
        self.original_import = __builtins__.__import__
        self.safe_modules = {}

    def intercept_import(self, name, globals=None, locals=None, fromlist=(), level=0):
        if name in DANGEROUS_MODULES:
            raise ImportError(f"❌ 禁止导入危险模块：{name}")
        if name not in ALLOWED_MODULES:
            raise ImportError(f"❌ 仅允许导入模块：{ALLOWED_MODULES}")
        if name == "os":
            original_os = self.original_import(name, globals, locals, fromlist, level)
            safe_os = SafeOs(original_os)
            self.safe_modules["os"] = safe_os
            return safe_os
        if name in self.safe_modules:
            return self.safe_modules[name]
        mod = self.original_import(name, globals, locals, fromlist, level)
        if name == "importlib":
            original_import_module = mod.import_module
            def restricted_import_module(module_name, package=None):
                return self.intercept_import(module_name)
            mod.import_module = restricted_import_module
        self.safe_modules[name] = mod
        return mod

importer = RestrictedImporter()
__builtins__.__import__ = importer.intercept_import

# ==================== 8. 资源限制====================
def set_resource_limits():
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (1, 2))
        resource.setrlimit(resource.RLIMIT_AS, (MAX_MEMORY, MAX_MEMORY + 16*1024*1024))
        resource.setrlimit(resource.RLIMIT_NPROC, (1, 1))
    except (AttributeError, resource.error):
        pass

# ==================== 9. 安全执行用户代码====================
def safe_execute(user_code):
    old_stdout = sys.original.stdout
    old_stderr = sys.original.stderr
    captured_out = StringIO()
    captured_err = StringIO()

    try:
        check_dangerous_code(user_code)
        sys.original.stdout = captured_out
        sys.original.stderr = captured_err

        import signal
        def timeout_handler(signum, frame):
            raise TimeoutError("执行超时")
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(EXEC_TIMEOUT))

        safe_globals = {
            "__name__": "__main__",
            "sys": sys,
            "importlib": importer.safe_modules.get("importlib", __import__("importlib"))
        }

        exec(user_code, safe_globals, {})
        signal.alarm(0)

        output = captured_out.getvalue()[:MAX_OUTPUT_SIZE].strip()
        error = captured_err.getvalue()[:MAX_OUTPUT_SIZE].strip()
        return output, error

    except TimeoutError:
        return "", "❌ 执行超时（超过1.5秒）"
    except ValueError as e:
        return "", str(e)
    except Exception as e:
        return "", f"❌ 执行失败：{str(e)[:50]}"
    finally:
        sys.original.stdout = old_stdout
        sys.original.stderr = old_stderr

# ==================== 10. GZCTF TCP服务（支持nc连接）====================
def run_gzctf_tcp_server():
    """适配GZCTF的TCP服务，监听8080端口"""
    host = '0.0.0.0'
    port = LISTEN_PORT
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((host, port))
        server_socket.listen(10)  # 支持多用户同时连接（GZCTF比赛场景）
        print(f"[INFO] GZCTF PyJail服务启动，监听 {host}:{port}")
        print(f"[INFO] 合法payload：del sys.modules['os'];import os;print(os.read(os.open('/flag.txt',os.O_RDONLY),1024).decode().strip())")
    except Exception as e:
        print(f"[ERROR] 服务启动失败：{str(e)}")
        sys.exit(1)

    while True:
        client_socket, addr = server_socket.accept()
        print(f"[INFO] 新连接：{addr}")
        welcome_msg = (
            "===== GZCTF PyJail Challenge =====\n"
            "规则：仅允许删除os缓存+重新导入解题\n"
            "目标：读取/flag.txt并输出flag\n"
            "输入payload（示例：del sys.modules['os'];import os;print(os.read(os.open('/flag.txt',os.O_RDONLY),1024).decode().strip())）\n"
            "==================================\n"
            ">>> "
        )
        try:
            client_socket.send(welcome_msg.encode("utf-8"))
            while True:
                user_input = client_socket.recv(4096).decode("utf-8", errors="ignore").strip()
                if not user_input:
                    break
                print(f"[INFO] 接收输入：{addr} -> {user_input[:50]}")
                output, error = safe_execute(user_input)
                if output:
                    response = f"✅ 输出：{output}\n>>> ".encode("utf-8")
                elif error:
                    response = f"❌ 错误：{error}\n>>> ".encode("utf-8")
                else:
                    response = ">>> ".encode("utf-8")
                client_socket.send(response)
        except Exception as e:
            error_msg = f"❌ 连接异常：{str(e)[:50]}\n".encode("utf-8")
            client_socket.send(error_msg)
        finally:
            client_socket.close()
            print(f"[INFO] 连接关闭：{addr}")

# ==================== 主程序====================
if __name__ == "__main__":
    set_resource_limits()
    run_gzctf_tcp_server()
