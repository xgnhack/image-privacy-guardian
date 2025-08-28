# 🛡️ Image Privacy Guardian - 图像隐私守护者

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)

一个专业的图像隐私保护工具，专门用于自动监控文件夹并清理图像文件中的元数据、跟踪点和隐私信息，保护您的数字隐私安全。

## ✨ 核心特性

### 🎯 智能监控系统
- **实时文件夹监控**: 支持同时监控多个文件夹，自动检测新增或修改的图像文件
- **一键扫描功能**: 手动扫描指定文件夹，快速处理现有图像文件
- **定时自动扫描**: 可配置定时扫描间隔，自动化处理工作流程
- **异步处理架构**: 多线程处理，不阻塞用户界面，支持大批量文件处理

### 🔬 高级图像清理
- **两阶段清理过程**:
  1. **元数据清理**: 使用Pillow库移除EXIF、IPTC、XMP等元数据
  2. **高级清理**: 使用OpenCV移除图像中的跟踪点、水印和隐藏标记
- **智能颜色检测**: HSV颜色空间精确检测和移除特定颜色区域
- **可视化配置界面**: 实时预览清理效果，支持参数微调
- **颜色选择工具**: 点击图像直接选择目标颜色，简化配置过程

### 🛡️ 数据安全保障
- **自动备份系统**: 处理前自动备份原文件，支持按时间戳分类存储
- **智能失败处理**: 失败文件自动备份到错误目录，附带详细错误日志
- **文件完整性检查**: 基于哈希值的重复处理检测，避免重复操作
- **安全的文件操作**: 原地替换处理，保持文件路径和权限不变

### 📊 实时监控面板
- **处理统计**: 实时显示处理成功/失败数量和成功率
- **详细日志**: 完整的操作日志，支持清空和导出
- **进度显示**: 扫描和处理进度的实时反馈
- **状态指示**: 清晰的监控状态和错误提示

## 🖼️ 支持的图像格式

### ✅ 完全支持的格式
- **JPEG/JPG** - 最常用的照片格式，支持完整的元数据清理和高级清理
- **PNG** - 支持透明度的无损格式，完整功能支持
- **BMP** - Windows位图格式，完整功能支持
- **TIFF/TIF** - 专业图像格式，支持多层和高质量，完整功能支持
- **WebP** - Google开发的现代格式，支持透明度和高压缩比，完整功能支持
- **HEIF/HEIC** - 苹果现代格式，高效压缩，完整功能支持（需要pillow-heif库）

### ❌ 不支持的格式
- **GIF** - 动画格式，不适用于隐私清理
- **SVG** - 矢量格式，无像素级元数据
- **RAW** - 相机原始格式，需要专门处理
- **PSD** - Photoshop专有格式
- **AI/EPS** - Adobe矢量格式

## 🚀 快速开始

### 系统要求
- **操作系统**: Windows 7/8/10/11 (64位)
- **Python版本**: 3.7 或更高版本
- **内存**: 建议 4GB 以上
- **存储空间**: 至少 100MB 可用空间

### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/xgnhack/image-privacy-guardian.git
cd image-privacy-guardian
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **运行应用**
```bash
python main.py
```

### 快速启动脚本
双击运行 `start_guardian.bat` 文件即可快速启动应用。

## 📖 使用指南

### 1. 添加监控文件夹
1. 点击 "➕ 添加文件夹" 按钮
2. 选择要监控的文件夹
3. 文件夹会出现在监控列表中
4. 可以添加多个文件夹同时监控

### 2. 配置高级清理设置
1. 点击 "🔬 高级清理设置..." 按钮
2. 在配置对话框中：
   - 点击 "📂 加载测试图像..." 加载样本图像
   - 使用 "💧 从图像中选择颜色" 选择要清理的颜色
   - 调节HSV参数范围 (色调、饱和度、明度)
   - 配置滤波参数 (中值滤波、形态学操作)
   - 点击 "🔄 应用并预览" 实时查看清理效果
   - 点击 "💾 保存设置" 保存配置

### 3. 开始监控
1. 确保已添加文件夹并配置好清理设置
2. 点击 "🛡️ 开始监控" 按钮
3. 应用会实时监控文件夹中的图像文件变化
4. 新增或修改的图像文件会自动进行隐私清理

### 4. 手动扫描
1. 点击 "🔍 一键扫描" 按钮
2. 系统会扫描所有监控文件夹中的未处理文件
3. 扫描过程中可以点击 "⏹️ 停止扫描" 中断操作
4. 扫描完成后会显示处理结果统计

### 5. 定时扫描
1. 点击 "⏰ 定时扫描" 按钮启用自动扫描
2. 可以通过输入框设置扫描间隔 (分钟)
3. 系统会按设定间隔自动执行扫描任务

## 🏗️ 技术架构

### 核心组件
- **MainWindow** (`main.py`): 用户界面和应用控制中心
- **MonitoringManager** (`monitoring_manager.py`): 文件监控和处理引擎
- **ImageSanitizer** (`sanitizer_engine.py`): 图像清理核心算法
- **AdvancedSettingsDialog** (`advanced_settings_ui.py`): 高级配置界面

### 技术栈
- **UI框架**: PyQt5 - 跨平台GUI开发
- **文件监控**: Watchdog - 高效的文件系统事件监听
- **图像处理**: 
  - OpenCV - 计算机视觉和图像处理
  - Pillow (PIL) - 图像元数据处理
- **并发处理**: Python Threading + QThread
- **配置管理**: JSON + QSettings

### 关键特性
- **线程安全**: Qt信号槽机制确保UI线程安全
- **异步处理**: 后台处理不阻塞用户界面
- **资源控制**: 智能的处理间隔和资源管理
- **错误恢复**: 完善的异常处理和错误恢复机制

## 📁 项目结构

```
image-privacy-guardian/
├── main.py                     # 主应用程序入口
├── monitoring_manager.py       # 监控管理器
├── sanitizer_engine.py        # 图像清理引擎
├── advanced_settings_ui.py    # 高级设置界面
├── requirements.txt            # Python依赖包
├── start_guardian.bat         # Windows启动脚本
├── README.md                  # 项目说明文档
├── aegis_config/              # 配置文件目录
│   ├── app_config.json        # 应用程序配置
│   ├── advanced_config.json   # 高级清理参数
│   ├── backup_config.json     # 备份设置
│   ├── monitored_folders.json # 监控文件夹列表
│   └── ui_settings.json       # 界面设置
├── errorbak/                  # 错误文件备份目录
└── _AEGIS_BACKUP/            # 处理文件备份目录
```

## ⚙️ 配置说明

### 应用配置 (`app_config.json`)
```json
{
    "auto_start_monitoring": false,    // 启动时自动开始监控
    "minimize_to_tray": false,         // 最小化到系统托盘
    "auto_save_logs": true,            // 自动保存日志
    "backup_folder": "_AEGIS_BACKUP"   // 备份文件夹路径
}
```

### 高级清理配置 (`advanced_config.json`)
```json
{
    "target_color": [0, 255, 0],       // 目标颜色 (BGR)
    "hsv_lower": [35, 40, 40],         // HSV下限
    "hsv_upper": [85, 255, 255],       // HSV上限
    "median_blur": 5,                  // 中值滤波核大小
    "morph_kernel_size": 3,            // 形态学操作核大小
    "morph_iterations": 2              // 形态学操作迭代次数
}
```

## 🔧 故障排除

### 常见问题

**Q: 监控功能不工作？**
A: 检查文件夹路径是否正确，确保应用有读写权限，检查防火墙设置。

**Q: 清理效果不理想？**
A: 使用高级设置中的颜色选择工具重新配置目标颜色，调整HSV参数范围。

**Q: 处理速度较慢？**
A: 减少同时监控的文件夹数量，或在高级设置中调整处理间隔。

**Q: 文件处理失败？**
A: 检查 `errorbak` 目录中的错误日志，确认文件格式是否支持。

### 日志和调试
- 查看应用内实时日志了解处理状态
- 检查 `errorbak` 目录中的详细错误日志
- 使用高级设置对话框的预览功能调试参数
- 查看 `aegis_processed_files.json` 了解已处理文件记录

## 🤝 贡献指南

我们欢迎社区贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 开源许可

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 👥 开发团队

- **作者**: [xgnhack](https://github.com/xgnhack)
- **贡献者**: 
  - [Trae](https://github.com/trae) - AI开发助手
  - [Claude-4](https://www.anthropic.com/) - AI代码生成
  - [Gemini-2.5-pro](https://deepmind.google/technologies/gemini/) - AI技术支持

## 📞 联系我们

- **GitHub Issues**: [提交问题](https://github.com/xgnhack/image-privacy-guardian/issues)
- **Email**: 通过GitHub联系作者
- **文档**: [项目Wiki](https://github.com/xgnhack/image-privacy-guardian/wiki)

## 🔄 版本历史

### v1.0.0 (当前版本)
- ✅ 实时文件夹监控功能
- ✅ 智能图像清理算法
- ✅ 可视化配置界面
- ✅ 自动备份和错误处理
- ✅ 一键扫描和定时扫描
- ✅ 多线程异步处理

---

🛡️ **Image Privacy Guardian** - 守护您的数字隐私，让图像分享更安全！

*如果这个项目对您有帮助，请给我们一个 ⭐ Star！*