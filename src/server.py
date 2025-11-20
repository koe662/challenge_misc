import sys
import time
import resource
from types import ModuleType
from io import StringIO
import ast

# ==================== 全局配置（严格锁定）====================
# 唯一允许的模块（解题必需）
ALLOWED_MODULES = {"sys", "importlib", "os"}
# 唯一允许访问的文件
ALLOWED_FILES = {"/flag.txt"}
# 重新导入os后，唯一允许的方法（解题必需）
ALLOWED_OS_METHODS = {"open", "read", "close", "O_RDONLY"}
# 执行限制
EXEC_TIMEOUT = 1.5  # 执行超时（留足解题时间）
MAX_OUTPUT_SIZE = 10240  # 最大输出10KB
MAX_MEMORY = 67108864  # 最大内存64MB

# 危险模块/方法/关键词（全面封堵）
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

# ==================== 1. 伪造初始OS模块（基础拦截）====================
class FakeOs:
    def __getattr__(self, name):
        raise AttributeError(f"❌ 伪造os模块无此属性：{name}（请删除sys.modules['os']后重新导入）")

# 初始篡改os模块缓存
sys.modules['os'] = FakeOs()

# ==================== 2. AST语义检测（精准封堵危险操作）====================
class DangerousCodeDetector(ast.NodeVisitor):
    """解析代码AST，精准检测非合法操作"""
    def __init__(self):
        self.has_dangerous = False
        self.dangerous_reason = ""

    def visit_Call(self, node):
        # 检测危险函数调用（如subprocess.run、os.system）
        func = node.func
        # 检测属性调用（如os.system、obj.method）
        if isinstance(func, ast.Attribute):
            # 禁止调用危险模块的方法（如subprocess.check_output）
            if isinstance(func.value, ast.Name) and func.value.id in DANGEROUS_MODULES:
                self.has_dangerous = True
                self.dangerous_reason = f"禁止调用危险模块方法：{func.value.id}.{func.attr}"
            # 禁止调用os的危险方法（即使通过反射）
            if isinstance(func.value, ast.Name) and func.value.id == "os" and func.attr in DANGEROUS_OS_METHODS:
                self.has_dangerous = True
                self.dangerous_reason = f"禁止调用os危险方法：os.{func.attr}"
            # 禁止调用sys的敏感属性（如sys.meta_path.append）
            if isinstance(func.value, ast.Name) and func.value.id == "sys" and func.attr in ["meta_path", "modules", "settrace"]:
                self.has_dangerous = True
                self.dangerous_reason = f"禁止操作sys敏感属性：sys.{func.attr}"
        # 检测内置函数调用（如getattr、setattr）
        if isinstance(func, ast.Name) and func.id in ["getattr", "setattr", "delattr", "eval", "exec"]:
            self.has_dangerous = True
            self.dangerous_reason = f"禁止使用危险内置函数：{func.id}"
        self.generic_visit(node)

    def visit_Str(self, node):
        # 检测敏感路径/关键词（如/proc、mount）
        for keyword in DANGEROUS_KEYWORDS:
            if keyword in node.s:
                self.has_dangerous = True
                self.dangerous_reason = f"禁止包含敏感关键词/路径：{keyword}"
        self.generic_visit(node)

    def visit_Dict(self, node):
        # 检测通过字典访问危险属性（如os.__dict__['system']）
        for key, value in zip(node.keys, node.values):
            if isinstance(key, ast.Str) and key.s in DANGEROUS_OS_METHODS:
                self.has_dangerous = True
                self.dangerous_reason = f"禁止访问os危险属性：os.__dict__['{key.s}']"
        self.generic_visit(node)

def check_dangerous_code(user_code):
    """检测用户代码是否包含危险操作"""
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

# ==================== 3. 加固sys.modules（仅允许删除os）====================
class RestrictedModulesDict:
    """包装sys.modules，仅允许删除'os'键"""
    def __init__(self, original_modules):
        self.original = original_modules

    def __delitem__(self, key):
        # 唯一允许删除的键：'os'
        if key != "os":
            raise KeyError(f"❌ 仅允许删除sys.modules['os']，禁止删除{key}")
        # 确保删除的是伪造os模块（防止重复删除）
        if key in self.original and isinstance(self.original[key], FakeOs):
            del self.original[key]
        else:
            raise KeyError("❌ 无需重复删除sys.modules['os']")

    def __setitem__(self, key, value):
        # 禁止添加任何模块到sys.modules
        raise ValueError("❌ 禁止修改sys.modules（添加模块）")

    def __getitem__(self, key):
        # 禁止访问危险模块的缓存
        if key in DANGEROUS_MODULES:
            raise KeyError(f"❌ 禁止访问危险模块：{key}")
        return self.original[key]

    def __getattr__(self, attr):
        # 禁止调用modules的危险方法（如clear、update）
        if attr in ["clear", "update", "pop", "popitem", "setdefault"]:
            raise AttributeError(f"❌ 禁止调用sys.modules.{attr}")
        return getattr(self.original, attr)

# ==================== 4. 加固sys模块（冻结核心属性）====================
class RestrictedSys:
    """包装sys模块，冻结核心属性，仅暴露安全功能"""
    def __init__(self, original_sys):
        self.original = original_sys
        # 冻结sys的核心属性，禁止修改
        self.frozen_attrs = ["meta_path", "modules", "settrace", "setprofile", "path"]

    def __getattr__(self, name):
        # 禁止访问敏感属性
        if name in ["socket", "fd", "fileno", "dup", "dup2", "call_tracing"]:
            raise AttributeError(f"❌ 禁止访问sys敏感属性：{name}")
        # 返回原始属性，modules返回加固后的版本
        attr = getattr(self.original, name)
        if name == "modules":
            return RestrictedModulesDict(attr)
        return attr

    def __setattr__(self, name, value):
        # 禁止修改冻结属性
        if name in self.frozen_attrs:
            raise AttributeError(f"❌ 禁止修改sys核心属性：{name}")
        if name == "original":
            super().__setattr__(name, value)
        else:
            raise AttributeError(f"❌ 禁止修改sys属性：{name}")

# 替换sys为加固版本
sys = RestrictedSys(sys)

# ==================== 5. 加固os模块（仅允许4个解题必需方法）====================
class SafeOs:
    """包装真实os模块，仅暴露解题必需的方法"""
    def __init__(self, original_os):
        self.original = original_os
        # 缓存允许的常量（O_RDONLY）
        self.O_RDONLY = original_os.O_RDONLY

    def __getattr__(self, name):
        # 仅允许访问白名单方法
        if name not in ALLOWED_OS_METHODS:
            raise AttributeError(f"❌ os模块仅允许使用：{ALLOWED_OS_METHODS}，禁止使用os.{name}")
        # 包装os.open，限制文件访问
        if name == "open":
            def restricted_open(path, flags, *args):
                # 解析真实路径，防止路径遍历
                real_path = self.original.path.realpath(path)
                if real_path not in ALLOWED_FILES:
                    raise PermissionError(f"❌ 仅允许访问文件：{ALLOWED_FILES}")
                # 仅允许读权限
                if flags != self.O_RDONLY:
                    raise PermissionError(f"❌ 仅允许读权限（O_RDONLY），禁止其他权限")
                return self.original.open(path, flags, *args)
            return restricted_open
        # 其他允许的方法直接返回（但限制参数/行为）
        method = getattr(self.original, name)
        if name == "read":
            def restricted_read(fd, size):
                # 限制读取大小（最多1KB，足够容纳flag）
                if size > 1024:
                    size = 1024
                return method(fd, size)
            return restricted_read
        return method

    # 禁止访问__dict__、__getattribute__等反射相关属性
    def __getattribute__(self, name):
        if name in ["__dict__", "__getattribute__", "__getattr__", "__class__"]:
            raise AttributeError(f"❌ 禁止访问os反射属性：{name}")
        return super().__getattribute__(name)

# ==================== 6. 模块导入拦截（仅允许白名单，os模块自动包装）====================
class RestrictedImporter:
    """拦截所有导入，仅允许白名单模块，os模块自动包装为SafeOs"""
    def __init__(self):
        self.original_import = __builtins__.__import__
        self.safe_modules = {}  # 缓存安全模块

    def intercept_import(self, name, globals=None, locals=None, fromlist=(), level=0):
        # 禁止导入危险模块
        if name in DANGEROUS_MODULES:
            raise ImportError(f"❌ 禁止导入危险模块：{name}")
        # 仅允许白名单模块
        if name not in ALLOWED_MODULES:
            raise ImportError(f"❌ 仅允许导入模块：{ALLOWED_MODULES}")
        # 导入os模块时，自动包装为SafeOs
        if name == "os":
            original_os = self.original_import(name, globals, locals, fromlist, level)
            safe_os = SafeOs(original_os)
            self.safe_modules["os"] = safe_os
            return safe_os
        # 导入其他白名单模块（sys已加固，importlib仅允许导入模块功能）
        if name in self.safe_modules:
            return self.safe_modules[name]
        mod = self.original_import(name, globals, locals, fromlist, level)
        # 加固importlib，仅允许导入白名单模块
        if name == "importlib":
            original_import_module = mod.import_module
            def restricted_import_module(module_name, package=None):
                return self.intercept_import(module_name)
            mod.import_module = restricted_import_module
        self.safe_modules[name] = mod
        return mod

# 替换内置__import__，拦截所有导入
importer = RestrictedImporter()
__builtins__.__import__ = importer.intercept_import

# ==================== 7. 资源限制（防DoS）====================
def set_resource_limits():
    """设置进程资源硬限制"""
    try:
        # CPU限制：软1秒，硬2秒
        resource.setrlimit(resource.RLIMIT_CPU, (1, 2))
        # 内存限制：软64MB，硬80MB
        resource.setrlimit(resource.RLIMIT_AS, (MAX_MEMORY, MAX_MEMORY + 16*1024*1024))
        # 禁止创建子进程
        resource.setrlimit(resource.RLIMIT_NPROC, (1, 1))
    except (AttributeError, resource.error):
        pass

# ==================== 8. 安全执行用户代码====================
def safe_execute(user_code):
    """全程监控用户代码，确保仅执行合法操作"""
    old_stdout = sys.original.stdout
    old_stderr = sys.original.stderr
    captured_out = StringIO()
    captured_err = StringIO()

    try:
        # 1. 检测危险代码（AST语义分析）
        check_dangerous_code(user_code)

        # 2. 捕获输出，限制大小
        sys.original.stdout = captured_out
        sys.original.stderr = captured_err

        # 3. 超时控制（同步执行，信号强制终止）
        import signal
        def timeout_handler(signum, frame):
            raise TimeoutError("执行超时")
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(EXEC_TIMEOUT))

        # 4. 受限命名空间：仅暴露加固后的sys和importlib
        safe_globals = {
            "__name__": "__main__",
            "sys": sys,
            "importlib": importer.safe_modules.get("importlib", __import__("importlib"))
        }

        # 5. 执行用户代码
        exec(user_code, safe_globals, {})

        # 6. 取消超时
        signal.alarm(0)

        # 7. 限制输出大小
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
        # 恢复stdout/stderr
        sys.original.stdout = old_stdout
        sys.original.stderr = old_stderr

# ==================== 主程序====================
if __name__ == "__main__":
    print("=" * 60)
    print("📌 PyJail Challenge：唯一绕过路径版")
    print("⚠️  规则：仅允许通过「删除os缓存+重新导入」解题")
    print("✅ 合法操作：del sys.modules['os'] → import os → 读取/flag.txt")
    print("❌ 禁止：反射、危险模块、系统命令、敏感路径访问")
    print("🎯 目标：读取 /flag.txt 并输出flag")
    print("=" * 60)

    # 初始化资源限制
    set_resource_limits()

    while True:
        try:
            user_input = input(">>> ")
            # 执行用户代码
            output, error = safe_execute(user_input)
            if output:
                print(f"✅ 输出：{output}")
            if error:
                print(f"❌ 错误：{error}")
        except KeyboardInterrupt:
            print("\n👋 退出挑战")
            sys.original.exit(0)
        except Exception as e:
            print(f"❌ 系统错误：{str(e)[:50]}")
