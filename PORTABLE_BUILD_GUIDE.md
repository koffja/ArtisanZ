# Artisan Windows 便携版打包指南

## 概述

本指南说明如何创建Artisan的Windows便携版（绿色版），可在任何Windows 11 x64电脑上直接运行，无需安装任何依赖。

---

## 快速开始

### 方法一：使用打包脚本（推荐）

1. **运行打包脚本**
   ```cmd
   build-win-portable.bat
   ```

2. **打包完成后**
   - 输出目录：`src\dist\artisan\`
   - 整个文件夹可直接复制使用

### 方法二：手动打包

1. **进入src目录**
   ```cmd
   cd src
   ```

2. **运行PyInstaller**
   ```cmd
   python -m PyInstaller artisan-win.spec --clean --noconfirm
   ```

3. **打包完成后**
   - 输出目录：`dist\artisan\`
   - 整个文件夹可直接复制使用

---

## 打包内容说明

### 核心文件
```
artisan/
├── artisan.exe              # 主程序可执行文件
├── _internal/               # 程序依赖文件
│   ├── PyQt6/              # Qt框架
│   ├── matplotlib/         # 绘图库
│   ├── scipy/              # 科学计算库
│   ├── numpy/              # 数值计算库
│   └── ...                 # 其他依赖
├── translations/           # 语言翻译文件
├── includes/               # 资源文件（字体、图标等）
├── Machines/               # 机器配置文件
├── Themes/                 # 主题文件
├── Icons/                  # 图标资源
├── *.dll                   # VC++运行时DLL（绿色版关键）
└── README.txt              # 说明文档
```

### 关键DLL说明

便携版自动包含以下运行时DLL：

| DLL文件 | 用途 |
|---------|------|
| msvcp140*.dll | Microsoft C++标准库 |
| vcruntime140*.dll | Microsoft C++运行时 |
| ucrtbase.dll | 通用C运行时 |
| api-ms-win-crt-*.dll | UCRT组件 |

---

## 部署说明

### 在目标电脑上使用

1. **复制整个文件夹**
   ```
   将整个 artisan/ 文件夹复制到目标电脑的任意位置
   例如：C:\Program Files\Artisan\
   或：D:\Tools\Artisan\
   或：桌面\Artisan\
   ```

2. **直接运行**
   ```
   双击 artisan.exe 启动程序
   无需安装任何依赖
   无需管理员权限
   ```

### 系统要求

- **操作系统**: Windows 11 (x64)
- **内存**: 建议4GB以上
- **磁盘空间**: 约500MB
- **权限**: 无需管理员权限

---

## 验证清单

### 打包后验证

在开发电脑上：

- [ ] 运行 `artisan.exe` 成功启动
- [ ] 检查 `_internal/` 目录包含所有依赖
- [ ] 检查根目录包含VC++ DLL文件
- [ ] 检查 `translations/` 目录包含翻译文件
- [ ] 检查 `includes/` 目录包含资源文件

### 跨电脑测试

在全新的Windows 11电脑上（无Python环境）：

- [ ] 直接运行 `artisan.exe` 成功
- [ ] 界面显示正常（无乱码）
- [ ] 绘图功能正常
- [ ] 设备连接功能正常
- [ ] 保存/加载配置文件正常

---

## 故障排除

### 问题：启动时提示缺少DLL

**原因**：打包时系统DLL未正确复制

**解决方案**：
```cmd
# 1. 手动复制系统DLL
copy C:\Windows\System32\msvcp140.dll dist\artisan\
copy C:\Windows\System32\vcruntime140.dll dist\artisan\
copy C:\Windows\System32\ucrtbase.dll dist\artisan\

# 2. 或安装VC++ Redistributable（如果提供了安装包）
dist\artisan\vc_redist.x64.exe
```

### 问题：运行时崩溃

**原因**：可能是hidden imports缺失

**解决方案**：
```cmd
# 1. 查看PyInstaller警告
python -m PyInstaller artisan-win.spec --debug=all

# 2. 根据警告添加hidden imports到spec文件
```

### 问题：界面显示异常

**原因**：字体或Qt插件缺失

**解决方案**：
```cmd
# 检查includes/目录包含所有字体文件
检查_internal/PyQt6/Qt6/plugins/目录包含所需插件
```

### 问题：程序体积过大

**原因**：包含了不必要的文件

**解决方案**：
```cmd
# 使用UPX压缩（需要安装UPX）
# 编辑spec文件，设置：
# upx=True
```

---

## 高级配置

### 自定义图标

编辑 `artisan-win.spec`：
```python
icon='artisan.ico',  # 修改为你的图标文件
```

### 添加启动画面

编辑 `artisan-win.spec`：
```python
exe = EXE(...,
          splash='splash.png',  # 添加启动画面
          ...)
```

### 减小体积

1. **排除不需要的模块**
   ```python
   excludes=['tkinter', 'test', 'unittest', ...]
   ```

2. **启用UPX压缩**
   ```python
   upx=True,
   upx_exclude=[],
   ```

3. **删除不必要的翻译文件**
   ```python
   # spec文件中已包含清理逻辑
   ```

---

## 分发建议

### 创建压缩包

```cmd
# 使用7-Zip创建自解压包
7z a -sfx artisan.7z artisan\

# 或使用标准zip
powershell Compress-Archive -Path artisan\ -DestinationPath artisan.zip
```

### 创建安装程序（可选）

如果需要提供安装程序，可以使用：
- **NSIS**: 轻量级安装程序制作工具
- **Inno Setup**: 功能强大的安装程序制作工具
- **WiX Toolset**: Windows Installer XML工具集

---

## 版本信息

- **适用版本**: Artisan (基于PyQt6)
- **目标平台**: Windows 11 x64
- **Python版本**: 3.12+
- **PyInstaller版本**: 6.17.0

---

## 更新日志

### 2025-12-25
- 改进spec文件，添加更多hidden imports
- 自动复制VC++ Runtime DLLs
- 添加UCRT DLLs支持
- 改进错误处理和日志输出

---

## 技术支持

如遇到问题，请提供以下信息：

1. 错误截图
2. Windows版本（`winver`）
3. 打包日志
4. 运行时日志（如果有的话）

---

## 许可证

本打包配置遵循Artisan项目的GNU General Public License。

---

**提示**：首次在目标电脑运行时，Windows Defender可能会弹出警告，这是正常的安全提示。选择"允许"或"更多信息"->"仍要运行"即可。
