# AppData迁移工具

![Windows](https://img.shields.io/badge/Platform-Windows-blue)
![Python](https://img.shields.io/badge/Python-3.7%2B-green)

## 功能特性

✅ 自动化迁移用户AppData目录
✅ 自动处理文件占用问题
✅ 创建符号链接保持兼容性
✅ 管理员权限自动提权
✅ 支持Local/LocalLow/Roaming目录

## 环境要求
- Windows 10/11

## 快速开始
1. 下载右侧的最新release可执行文件
2. 双击运行

## 源码构建要求
- Python 3.7+
- Poetry 1.2+

## 源码运行
```powershell
# 克隆仓库
git clone https://github.com/huwei901108/AppDataMove.git
```
（或者，在国内可使用gitee仓库：
```powershell
git clone https://gitee.com/huwei818/AppDataMove.git
```
）
```powershell
# 安装依赖
cd AppDataMove
poetry install

# 运行程序
./run.bat
```

## 编译独立程序

```powershell
./build.bat
# 生成的可执行文件在dist目录
```

## 使用说明

1. 运行程序后会提示输入要迁移的AppData路径
2. 程序会自动验证路径格式：
   - 必须匹配 `C:\Users\<用户名>\AppData\<Local|LocalLow|Roaming>\<子目录>`
3. 确认后程序将：
   - 自动关闭占用文件的进程
   - 迁移数据到D盘对应位置
   - 创建符号链接保持程序兼容性

⚠️ 注意：
- 需要以管理员权限运行
- 迁移前请关闭相关应用程序
- 建议先备份重要数据

## 技术实现

- 使用Windows API检测管理员权限
- 集成Sysinternals工具处理文件占用
- 采用shutil进行可靠文件操作
- 通过符号链接保持系统兼容

## 许可协议

[MIT License](LICENSE)