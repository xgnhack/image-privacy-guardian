"""
Image Privacy Guardian - 主窗口
图像隐私守护者的主界面和控制中心
"""

import sys
import os
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QWidget, QListWidget, QPushButton, QTextEdit, QLabel,
                             QFileDialog, QMessageBox, QGroupBox, QSplitter,
                             QListWidgetItem, QFrame, QInputDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon

from advanced_settings_ui import AdvancedSettingsDialog
from monitoring_manager import MonitoringManager


class ScanWorker(QThread):
    """异步扫描工作线程"""
    progress_update = pyqtSignal(str)  # 进度更新信号
    file_found = pyqtSignal(str)  # 发现文件信号
    scan_finished = pyqtSignal(int)  # 扫描完成信号，参数为处理的文件数量
    error_occurred = pyqtSignal(str)  # 错误信号
    
    def __init__(self, monitored_folders, backup_folder):
        super().__init__()
        self.monitored_folders = monitored_folders
        self.backup_folder = backup_folder
        self.processed_count = 0
        self.should_stop = False
        
    def run(self):
        """执行扫描任务"""
        try:
            from monitoring_manager import MonitoringManager, ProcessingWorker
            
            # 创建临时的监控管理器
            temp_manager = MonitoringManager(backup_folder=self.backup_folder)
            
            self.processed_count = 0
            total_folders = len(self.monitored_folders)
            
            for i, folder in enumerate(self.monitored_folders):
                if self.should_stop:
                    break
                    
                if not os.path.exists(folder):
                    self.progress_update.emit(f"⚠️ 文件夹不存在: {folder}")
                    continue
                
                self.progress_update.emit(f"📂 扫描文件夹 ({i+1}/{total_folders}): {os.path.basename(folder)}")
                
                # 扫描文件夹
                folder_count = self.scan_folder_with_throttle(temp_manager, folder)
                self.processed_count += folder_count
                
                # 短暂休息，避免过度占用资源
                self.msleep(100)
            
            if not self.should_stop:
                self.scan_finished.emit(self.processed_count)
            
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def scan_folder_with_throttle(self, manager, folder_path):
        """带资源控制的文件夹扫描"""
        count = 0
        file_count = 0
        
        try:
            # 首先统计文件数量
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if manager.is_image_file(os.path.join(root, file)):
                        file_count += 1
            
            if file_count == 0:
                return 0
            
            # 处理文件
            processed = 0
            for root, dirs, files in os.walk(folder_path):
                if self.should_stop:
                    break
                    
                for file in files:
                    if self.should_stop:
                        break
                        
                    file_path = os.path.join(root, file)
                    
                    # 检查是否为图像文件
                    if manager.is_image_file(file_path):
                        processed += 1
                        
                        # 更新进度
                        if file_count > 0:
                            progress = int((processed / file_count) * 100)
                            self.progress_update.emit(f"  📄 检查文件 ({processed}/{file_count}, {progress}%): {os.path.basename(file_path)}")
                        
                        # 检查是否已处理过
                        if not manager.is_file_processed(file_path):
                            self.file_found.emit(f"🆕 发现未处理文件: {os.path.basename(file_path)}")
                            
                            # 处理文件
                            self.process_file_safely(manager, file_path)
                            count += 1
                            
                            # 每处理一个文件后休息，避免过度占用资源
                            self.msleep(200)
                        
                        # 每检查10个文件休息一下
                        if processed % 10 == 0:
                            self.msleep(50)
            
        except Exception as e:
            self.error_occurred.emit(f"扫描文件夹失败 {folder_path}: {str(e)}")
        
        return count
    
    def process_file_safely(self, manager, file_path):
        """安全地处理单个文件"""
        try:
            from monitoring_manager import ProcessingWorker
            
            # 创建处理工作器并直接执行
            worker = ProcessingWorker(file_path, "扫描发现", manager)
            worker.process_file()
            
            self.progress_update.emit(f"  ✅ 处理完成: {os.path.basename(file_path)}")
            
        except Exception as e:
            self.error_occurred.emit(f"处理文件失败 {os.path.basename(file_path)}: {str(e)}")
    
    def stop_scan(self):
        """停止扫描"""
        self.should_stop = True


class MainWindow(QMainWindow):
    """主窗口 - Image Privacy Guardian 的命令中心"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🛡️ Image Privacy Guardian - 图像隐私守护者")
        self.setGeometry(100, 100, 1000, 950)
        self.setMinimumSize(800, 950)
        
        # 监控的文件夹列表
        self.monitored_folders = []
        
        # 监控管理器
        self.monitoring_manager = None
        self.monitoring_thread = None
        
        # 初始化配置管理
        self.init_config_system()
        
        # 加载配置（不包括UI设置）
        self.load_basic_configs()
        
        # 监控状态
        self.is_monitoring = False
        
        # 定时扫描相关
        self.auto_scan_timer = QTimer()
        self.auto_scan_timer.timeout.connect(self.perform_auto_scan)
        self.auto_scan_interval = 300000  # 默认5分钟 (300秒 * 1000毫秒)
        self.is_auto_scanning = False
        
        # 存储标题标签的引用，用于字体自适应
        self.title_labels = []
        
        # 设置主窗口样式 - 采用简洁的蓝色配色方案
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
                color: #1e3a8a;
            }
            QLabel#title {
                font-size: 18px;
                font-weight: bold;
                color: #ffffff;
                background-color: #1e3a8a;
                padding: 15px;
                border-radius: 8px;
                margin: 5px;
            }
        """)
        
        self.setup_ui()
        self.setup_connections()
        
        # UI初始化完成后，加载完整配置
        self.load_all_configs()
        
    def setup_ui(self):
        """设置用户界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 标题区域
        title_container = QWidget()
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        # 标题
        title_label = QLabel("🛡️ Image Privacy Guardian - 图像隐私守护者")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin: 10px;")
        
        # 关于链接
        about_label = QLabel('<a href="#about" style="color: #3498db; text-decoration: none; font-size: 14px;">📖 关于</a>')
        about_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        about_label.setStyleSheet("margin: 10px; padding-right: 10px;")
        about_label.linkActivated.connect(self.show_about_dialog)
        
        title_layout.addWidget(title_label, 1)
        title_layout.addWidget(about_label, 0)
        main_layout.addWidget(title_container)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧控制面板
        control_panel = self.create_control_panel()
        control_panel.setMinimumWidth(350)
        splitter.addWidget(control_panel)
        
        # 右侧日志面板
        log_panel = self.create_log_panel()
        log_panel.setMinimumWidth(400)
        splitter.addWidget(log_panel)
        
        # 设置分割器比例
        splitter.setSizes([350, 450])
        
        # 状态栏
        self.statusBar().showMessage("就绪 - 请添加要监控的文件夹")
        
    def create_control_panel(self):
        """创建左侧控制面板"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        panel.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border: 1px solid #bfdbfe;
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout(panel)
        
        # 文件夹组
        folder_container = QFrame()
        folder_container.setFrameStyle(QFrame.StyledPanel)
        folder_container.setMinimumHeight(220)
        folder_main_layout = QVBoxLayout(folder_container)
        folder_main_layout.setContentsMargins(5, 5, 5, 5)
        folder_main_layout.setSpacing(5)
        
        # 自定义标题标签
        folder_title = QLabel("📁 监控文件夹")
        folder_title.setStyleSheet("""
            QLabel {
                background-color: #3498db;
                color: white;
                padding: 10px 15px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 16px;
                margin: 2px;
            }
        """)
        folder_title.setAlignment(Qt.AlignCenter)
        folder_main_layout.addWidget(folder_title)
        self.title_labels.append(folder_title)
        
        # 内容区域
        folder_group = QFrame()
        folder_layout = QVBoxLayout(folder_group)
        folder_layout.setContentsMargins(10, 10, 10, 10)
        
        # 文件夹列表
        self.folder_list = QListWidget()
        self.folder_list.setMinimumHeight(200)
        self.folder_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                background-color: #ffffff;
                selection-background-color: #3498db;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #ecf0f1;
            }
            QListWidget::item:hover {
                background-color: #ecf0f1;
            }
        """)
        folder_layout.addWidget(self.folder_list)
        
        # 文件夹操作按钮
        folder_btn_layout = QHBoxLayout()
        
        self.add_folder_btn = QPushButton("➕ 添加文件夹")
        self.add_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QPushButton:pressed {
                background-color: #1d4ed8;
            }
            QPushButton:disabled {
                background-color: #e5e7eb;
                color: #9ca3af;
            }
        """)
        
        self.remove_folder_btn = QPushButton("➖ 移除文件夹")
        self.remove_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #64748b;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #475569;
            }
            QPushButton:pressed {
                background-color: #334155;
            }
            QPushButton:disabled {
                background-color: #e5e7eb;
                color: #9ca3af;
            }
        """)
        self.remove_folder_btn.setEnabled(False)
        
        folder_btn_layout.addWidget(self.add_folder_btn)
        folder_btn_layout.addWidget(self.remove_folder_btn)
        folder_layout.addLayout(folder_btn_layout)
        
        # 备份文件夹设置按钮
        self.backup_folder_btn = QPushButton("📁 设置备份文件夹...")
        self.backup_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #64748b;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #475569;
            }
            QPushButton:pressed {
                background-color: #334155;
            }
        """)
        folder_layout.addWidget(self.backup_folder_btn)
        
        folder_main_layout.addWidget(folder_group)
        layout.addWidget(folder_container)
        
        # 控制组
        control_container = QFrame()
        control_container.setFrameStyle(QFrame.StyledPanel)
        control_container.setMinimumHeight(220)
        control_main_layout = QVBoxLayout(control_container)
        control_main_layout.setContentsMargins(8, 8, 8, 8)
        control_main_layout.setSpacing(8)
        
        # 自定义标题标签
        control_title = QLabel("🎛️ 监控控制")
        control_title.setStyleSheet("""
            QLabel {
                background-color: #1e3a8a;
                color: white;
                padding: 12px 16px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 16px;
                margin: 2px;
            }
        """)
        control_title.setAlignment(Qt.AlignCenter)
        control_main_layout.addWidget(control_title)
        self.title_labels.append(control_title)
        
        # 内容区域
        control_group = QFrame()
        control_layout = QVBoxLayout(control_group)
        control_layout.setContentsMargins(15, 15, 15, 15)
        control_layout.setSpacing(6)
        
        # 主控制按钮
        self.main_control_btn = QPushButton("🛡️ 开始监控")
        self.main_control_btn.setMinimumHeight(45)
        self.main_control_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                padding: 12px 16px;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QPushButton:pressed {
                background-color: #1d4ed8;
            }
            QPushButton:disabled {
                background-color: #e5e7eb;
                color: #9ca3af;
            }
        """)
        self.main_control_btn.setEnabled(False)
        control_layout.addWidget(self.main_control_btn)
        
        # 扫描功能按钮 - 水平布局
        scan_layout = QHBoxLayout()
        scan_layout.setSpacing(15)  # 设置按钮间距为15px
        
        self.manual_scan_btn = QPushButton("🔍 一键扫描")
        self.manual_scan_btn.setMinimumHeight(45)
        self.manual_scan_btn.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: white;
                border: none;
                padding: 12px 16px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #047857;
            }
            QPushButton:pressed {
                background-color: #065f46;
            }
            QPushButton:disabled {
                background-color: #e5e7eb;
                color: #9ca3af;
            }
        """)
        self.manual_scan_btn.setToolTip("立即扫描所有监控文件夹中的未处理文件")
        
        self.auto_scan_btn = QPushButton("⏰ 定时扫描")
        self.auto_scan_btn.setMinimumHeight(45)
        self.auto_scan_btn.setStyleSheet("""
            QPushButton {
                background-color: #7c3aed;
                color: white;
                border: none;
                padding: 12px 16px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #6d28d9;
            }
            QPushButton:pressed {
                background-color: #5b21b6;
            }
            QPushButton:disabled {
                background-color: #e5e7eb;
                color: #9ca3af;
            }
        """)
        self.auto_scan_btn.setToolTip("开启/关闭定时扫描功能")
        self.auto_scan_btn.setCheckable(True)
        
        # 添加按钮到水平布局，各占一半宽度
        scan_layout.addWidget(self.manual_scan_btn)
        scan_layout.addWidget(self.auto_scan_btn)
        
        # 将水平布局添加到主布局
        control_layout.addLayout(scan_layout)
        
        # 高级设置按钮
        self.advanced_settings_btn = QPushButton("🔬 高级清理设置...")
        self.advanced_settings_btn.setMinimumHeight(45)
        self.advanced_settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #64748b;
                color: white;
                border: none;
                padding: 12px 16px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #475569;
            }
            QPushButton:pressed {
                background-color: #334155;
            }
        """)
        control_layout.addWidget(self.advanced_settings_btn)
        
        control_main_layout.addWidget(control_group)
        layout.addWidget(control_container)
        
        # 统计信息组
        stats_container = QFrame()
        stats_container.setFrameStyle(QFrame.StyledPanel)
        stats_container.setMinimumHeight(140)
        stats_main_layout = QVBoxLayout(stats_container)
        stats_main_layout.setContentsMargins(5, 5, 5, 5)
        stats_main_layout.setSpacing(5)
        
        # 自定义标题标签
        stats_title = QLabel("📊 监控统计")
        stats_title.setStyleSheet("""
            QLabel {
                background-color: #1e3a8a;
                color: white;
                padding: 10px 15px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 16px;
                margin: 2px;
            }
        """)
        stats_title.setAlignment(Qt.AlignCenter)
        stats_main_layout.addWidget(stats_title)
        self.title_labels.append(stats_title)
        
        # 内容区域
        stats_group = QFrame()
        stats_layout = QVBoxLayout(stats_group)
        stats_layout.setContentsMargins(10, 10, 10, 10)
        
        self.stats_label = QLabel("监控文件夹: 0\n处理文件: 0\n成功: 0\n失败: 0")
        self.stats_label.setStyleSheet("""
            QLabel {
                background-color: #f1f5f9;
                border: 1px solid #bfdbfe;
                border-radius: 4px;
                padding: 10px;
                font-family: 'Consolas', 'Monaco', monospace;
                color: #1e3a8a;
            }
        """)
        stats_layout.addWidget(self.stats_label)
        
        stats_main_layout.addWidget(stats_group)
        layout.addWidget(stats_container)
        
        layout.addStretch()
        
        return panel
        
    def create_log_panel(self):
        """创建右侧日志面板"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout(panel)
        
        # 日志组
        log_container = QFrame()
        log_container.setFrameStyle(QFrame.StyledPanel)
        log_container.setMinimumHeight(420)
        log_main_layout = QVBoxLayout(log_container)
        log_main_layout.setContentsMargins(5, 5, 5, 5)
        log_main_layout.setSpacing(5)
        
        # 自定义标题标签
        log_title = QLabel("📝 实时日志")
        log_title.setStyleSheet("""
            QLabel {
                background-color: #1e3a8a;
                color: white;
                padding: 10px 15px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 16px;
                margin: 2px;
            }
        """)
        log_title.setAlignment(Qt.AlignCenter)
        log_main_layout.addWidget(log_title)
        self.title_labels.append(log_title)
        
        # 内容区域
        log_group = QFrame()
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(10, 10, 10, 10)
        
        # 日志文本区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #f1f5f9;
                color: #1e3a8a;
                border: 1px solid #bfdbfe;
                border-radius: 5px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10pt;
            }
        """)
        log_layout.addWidget(self.log_text)
        
        # 日志控制按钮
        log_btn_layout = QHBoxLayout()
        
        self.clear_log_btn = QPushButton("🗑️ 清空日志")
        self.clear_log_btn.setStyleSheet("""
            QPushButton {
                background-color: #64748b;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #475569;
            }
        """)
        
        self.save_log_btn = QPushButton("💾 保存日志")
        self.save_log_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        
        log_btn_layout.addWidget(self.clear_log_btn)
        log_btn_layout.addWidget(self.save_log_btn)
        log_btn_layout.addStretch()
        
        log_layout.addLayout(log_btn_layout)
        
        log_main_layout.addWidget(log_group)
        layout.addWidget(log_container)
        
        return panel
    

        
    def setup_connections(self):
        """设置信号连接"""
        # 文件夹管理
        self.add_folder_btn.clicked.connect(self.add_folder)
        self.remove_folder_btn.clicked.connect(self.remove_folder)
        self.folder_list.itemSelectionChanged.connect(self.on_folder_selection_changed)
        
        # 监控控制
        self.main_control_btn.clicked.connect(self.toggle_monitoring)
        self.manual_scan_btn.clicked.connect(self.handle_manual_scan_click)
        self.auto_scan_btn.clicked.connect(self.toggle_auto_scan)
        self.advanced_settings_btn.clicked.connect(self.open_advanced_settings)
        self.backup_folder_btn.clicked.connect(self.set_backup_folder)
        
        # 日志控制
        self.clear_log_btn.clicked.connect(self.clear_log)
        self.save_log_btn.clicked.connect(self.save_log)
        
    def add_folder(self):
        """添加监控文件夹"""
        folder_path = QFileDialog.getExistingDirectory(
            self, "选择要监控的文件夹", ""
        )
        
        if folder_path and folder_path not in self.monitored_folders:
            self.monitored_folders.append(folder_path)
            
            # 添加到列表显示
            item = QListWidgetItem(f"📁 {folder_path}")
            self.folder_list.addItem(item)
            
            # 保存配置
            self.save_config('folders', self.monitored_folders)
            
            # 更新UI状态
            self.update_ui_state()
            self.log_message(f"✅ 已添加监控文件夹: {folder_path}")
            
        elif folder_path in self.monitored_folders:
            QMessageBox.information(self, "提示", "该文件夹已在监控列表中")
            
    def remove_folder(self):
        """移除监控文件夹"""
        current_row = self.folder_list.currentRow()
        if current_row >= 0 and current_row < len(self.monitored_folders):
            folder_path = self.monitored_folders[current_row]
            
            # 从列表中移除
            self.monitored_folders.pop(current_row)
            self.folder_list.takeItem(current_row)
            
            # 保存配置
            self.save_config('folders', self.monitored_folders)
            
            # 更新UI状态
            self.update_ui_state()
            self.log_message(f"❌ 已移除监控文件夹: {folder_path}")
        else:
            self.log_message("⚠️ 请先选择要移除的文件夹")
            
    def on_folder_selection_changed(self):
        """文件夹选择变化"""
        has_selection = self.folder_list.currentRow() >= 0
        self.remove_folder_btn.setEnabled(has_selection and not self.is_monitoring)
        
    def toggle_monitoring(self):
        """切换监控状态"""
        if not self.is_monitoring:
            self.start_monitoring()
        else:
            self.stop_monitoring()
            
    def start_monitoring(self):
        """开始监控"""
        if not self.monitored_folders:
            QMessageBox.warning(self, "警告", "请先添加要监控的文件夹")
            return
            
        try:
            # 创建监控线程
            self.monitoring_thread = QThread()
            self.monitoring_manager = MonitoringManager(backup_folder=self.backup_folder)
            self.monitoring_manager.moveToThread(self.monitoring_thread)
            
            # 连接信号
            self.monitoring_manager.log_message.connect(self.log_message)
            self.monitoring_manager.stats_updated.connect(self.update_stats)
            self.monitoring_manager.error_occurred.connect(self.on_monitoring_error)
            
            # 启动监控
            self.monitoring_thread.started.connect(
                lambda: self.monitoring_manager.start_monitoring(
                    self.monitored_folders, self.advanced_config
                )
            )
            
            self.monitoring_thread.start()
            
            # 更新UI状态
            self.is_monitoring = True
            self.main_control_btn.setText("🛑 停止监控")
            self.main_control_btn.setStyleSheet("""
                QPushButton {
                    background-color: #6c757d;
                    color: white;
                    border: none;
                    padding: 12px;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #5a6268;
                }
                QPushButton:pressed {
                    background-color: #495057;
                }
            """)
            
            # 禁用文件夹操作
            self.add_folder_btn.setEnabled(False)
            self.remove_folder_btn.setEnabled(False)
            
            self.statusBar().showMessage("🛡️ 监控中...")
            self.log_message("🚀 监控已启动")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动监控失败: {str(e)}")
            
    def stop_monitoring(self):
        """停止监控"""
        try:
            if self.monitoring_manager:
                self.monitoring_manager.stop_monitoring()
                
            if self.monitoring_thread:
                self.monitoring_thread.quit()
                self.monitoring_thread.wait()
                
            # 更新UI状态
            self.is_monitoring = False
            self.main_control_btn.setText("🛡️ 开始监控")
            self.main_control_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2c3e50;
                    color: white;
                    border: none;
                    padding: 12px;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #34495e;
                }
                QPushButton:pressed {
                    background-color: #1a252f;
                }
            """)
            
            # 启用文件夹操作
            self.add_folder_btn.setEnabled(True)
            self.remove_folder_btn.setEnabled(self.folder_list.currentRow() >= 0)
            
            # 停止定时扫描
            if self.is_auto_scanning:
                self.stop_auto_scan()
            
            self.statusBar().showMessage("就绪")
            self.log_message("⏹️ 监控已停止")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"停止监控失败: {str(e)}")
            
    def open_advanced_settings(self):
        """打开高级设置对话框"""
        dialog = AdvancedSettingsDialog(self)
        
        # 加载当前配置到对话框
        dialog.load_settings(self.advanced_config)
        
        if dialog.exec_() == dialog.Accepted:
            # 获取新的配置
            self.advanced_config = dialog.get_current_config()
            
            # 保存配置
            self.save_config('advanced', self.advanced_config)
            
            self.log_message("⚙️ 高级设置已更新")
            
            # 如果正在监控，更新配置
            if self.is_monitoring and self.monitoring_manager:
                self.monitoring_manager.update_config(self.advanced_config)
                
    def set_backup_folder(self):
        """设置备份文件夹"""
        current_backup = getattr(self, 'backup_folder', os.path.join(os.getcwd(), '_AEGIS_BACKUP'))
        
        folder = QFileDialog.getExistingDirectory(
            self, "选择备份文件夹", current_backup
        )
        
        if folder:
            self.backup_folder = folder
            self.log_message(f"📁 备份文件夹已设置为: {folder}")
            
            # 保存配置
            backup_config = {
                'backup_folder': folder,
                'auto_cleanup': getattr(self, 'auto_cleanup', False),
                'max_backup_days': getattr(self, 'max_backup_days', 30)
            }
            self.save_config('backup', backup_config)
                
            # 如果正在监控，更新监控管理器的备份路径
            if self.is_monitoring and self.monitoring_manager:
                self.monitoring_manager.backup_folder = folder
                
    def update_ui_state(self):
        """更新UI状态"""
        has_folders = len(self.monitored_folders) > 0
        self.main_control_btn.setEnabled(has_folders and not self.is_monitoring)
        
        # 更新统计
        self.update_stats({
            'folders': len(self.monitored_folders),
            'processed': 0,
            'success': 0,
            'failed': 0
        })
        
    def update_stats(self, stats):
        """更新统计信息"""
        self.stats_label.setText(
            f"监控文件夹: {stats.get('folders', 0)}\n"
            f"处理文件: {stats.get('processed', 0)}\n"
            f"成功: {stats.get('success', 0)}\n"
            f"失败: {stats.get('failed', 0)}"
        )
        
    def log_message(self, message):
        """添加日志消息"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        self.log_text.append(formatted_message)
        
        # 自动滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.End)
        self.log_text.setTextCursor(cursor)
        
    def on_monitoring_error(self, error_message):
        """处理监控错误"""
        self.log_message(f"❌ 错误: {error_message}")
        QMessageBox.warning(self, "监控错误", error_message)
        
    def clear_log(self):
        """清空日志"""
        self.log_text.clear()
        self.log_message("📝 日志已清空")
        
    def save_log(self):
        """保存日志"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存日志", "aegis_log.txt", "文本文件 (*.txt)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                self.log_message(f"💾 日志已保存到: {file_path}")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"保存日志失败: {str(e)}")
                

        
    def init_config_system(self):
        """初始化配置管理系统"""
        # 创建配置文件夹
        self.config_dir = os.path.join(os.getcwd(), 'aegis_config')
        os.makedirs(self.config_dir, exist_ok=True)
        
        # 配置文件路径
        self.config_files = {
            'app': os.path.join(self.config_dir, 'app_config.json'),
            'advanced': os.path.join(self.config_dir, 'advanced_config.json'),
            'backup': os.path.join(self.config_dir, 'backup_config.json'),
            'folders': os.path.join(self.config_dir, 'monitored_folders.json'),
            'ui': os.path.join(self.config_dir, 'ui_settings.json')
        }
        
    def load_basic_configs(self):
        """加载基础配置（不包括UI设置）"""
        # 加载应用配置
        self.app_config = self.load_config('app', {
            'auto_start_monitoring': False,
            'minimize_to_tray': False,
            'auto_save_logs': True,
            'log_level': 'INFO'
        })
        
        # 加载高级设置配置
        self.advanced_config = self.load_config('advanced', {
            'enabled': True,
            'hue_center': 120,
            'hue_tolerance': 10,
            'min_saturation': 50,
            'min_value': 50,
            'median_blur_kernel': 5,
            'morphology_iterations': 2
        })
        
        # 加载备份配置
        backup_config = self.load_config('backup', {
            'backup_folder': os.path.join(os.getcwd(), '_AEGIS_BACKUP'),
            'auto_cleanup': False,
            'max_backup_days': 30
        })
        self.backup_folder = backup_config['backup_folder']
        
        # 加载监控文件夹列表
        self.monitored_folders = self.load_config('folders', [])
        
    def load_all_configs(self):
        """加载所有配置（包括UI设置）"""
        # 先加载基础配置
        self.load_basic_configs()
        
        # 加载UI设置
        self.ui_settings = self.load_config('ui', {
            'window_geometry': None,
            'splitter_sizes': [350, 450],
            'theme': 'blue'
        })
        
        # 应用UI设置（包括加载监控文件夹到UI）
        self.apply_ui_settings()
        
        # 更新UI状态
        self.update_ui_state()
        
    def load_config(self, config_type, default_value):
        """加载指定类型的配置"""
        config_file = self.config_files.get(config_type)
        if not config_file:
            return default_value
            
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # 如果配置文件不存在，创建默认配置
                self.save_config(config_type, default_value)
                return default_value
        except Exception as e:
            self.log_message(f"⚠️ 加载配置失败 ({config_type}): {str(e)}")
            return default_value
            
    def save_config(self, config_type, config_data):
        """保存指定类型的配置"""
        config_file = self.config_files.get(config_type)
        if not config_file:
            return False
            
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            self.log_message(f"⚠️ 保存配置失败 ({config_type}): {str(e)}")
            return False
            
    def save_all_configs(self):
        """保存所有配置"""
        # 保存应用配置
        self.save_config('app', self.app_config)
        
        # 保存高级设置配置
        self.save_config('advanced', self.advanced_config)
        
        # 保存备份配置
        backup_config = {
            'backup_folder': self.backup_folder,
            'auto_cleanup': getattr(self, 'auto_cleanup', False),
            'max_backup_days': getattr(self, 'max_backup_days', 30)
        }
        self.save_config('backup', backup_config)
        
        # 保存监控文件夹列表
        self.save_config('folders', self.monitored_folders)
        
        # 保存UI设置
        self.save_ui_settings()
        
    def apply_ui_settings(self):
        """应用UI设置"""
        # 恢复窗口几何信息
        if self.ui_settings.get('window_geometry'):
            try:
                geometry = self.ui_settings['window_geometry']
                self.setGeometry(geometry['x'], geometry['y'], geometry['width'], geometry['height'])
            except:
                pass
                
        # 恢复监控文件夹列表显示（只有在UI已初始化时才执行）
        if hasattr(self, 'folder_list') and self.monitored_folders:
            # 清空现有列表，避免重复
            self.folder_list.clear()
            
            # 先过滤出存在的文件夹
            valid_folders = []
            for folder in self.monitored_folders:
                if os.path.exists(folder):
                    valid_folders.append(folder)
                    item = QListWidgetItem(f"📁 {folder}")
                    self.folder_list.addItem(item)
                else:
                    self.log_message(f"⚠️ 文件夹不存在，已自动移除: {folder}")
            
            # 更新监控文件夹列表（只保留存在的文件夹）
            if len(valid_folders) != len(self.monitored_folders):
                self.monitored_folders = valid_folders
                self.save_config('folders', self.monitored_folders)
                
    def save_ui_settings(self):
        """保存UI设置"""
        # 保存窗口几何信息
        geometry = self.geometry()
        self.ui_settings['window_geometry'] = {
            'x': geometry.x(),
            'y': geometry.y(),
            'width': geometry.width(),
            'height': geometry.height()
        }
        
        self.save_config('ui', self.ui_settings)
        
    def perform_manual_scan(self):
        """执行手动扫描"""
        if not self.monitored_folders:
            QMessageBox.warning(self, "警告", "请先添加要监控的文件夹")
            return
        
        # 检查是否已经在扫描中
        if hasattr(self, 'scan_worker') and self.scan_worker and self.scan_worker.isRunning():
            QMessageBox.information(self, "提示", "扫描正在进行中，请稍候...")
            return
            
        self.log_message("🔍 开始手动扫描所有监控文件夹...")
        self.manual_scan_btn.setEnabled(True)
        self.manual_scan_btn.setText("⏹️ 停止扫描")
        self.manual_scan_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc2626;
                color: white;
                border: none;
                padding: 12px 16px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #b91c1c;
            }
            QPushButton:pressed {
                background-color: #991b1b;
            }
        """)
        
        # 创建并启动扫描工作线程
        self.scan_worker = ScanWorker(self.monitored_folders, self.backup_folder)
        self.scan_worker.progress_update.connect(self.on_scan_progress)
        self.scan_worker.file_found.connect(self.on_scan_file_found)
        self.scan_worker.scan_finished.connect(self.on_scan_finished)
        self.scan_worker.error_occurred.connect(self.on_scan_error)
        self.scan_worker.start()
    
    def handle_manual_scan_click(self):
        """处理一键扫描按钮点击事件"""
        # 检查是否正在扫描
        if hasattr(self, 'scan_worker') and self.scan_worker and self.scan_worker.isRunning():
            # 正在扫描，执行停止操作
            self.scan_worker.stop_scan()
            self.manual_scan_btn.setText("🔄 停止中...")
            self.manual_scan_btn.setEnabled(False)
            self.log_message("⏹️ 正在停止扫描...")
        else:
            # 没有在扫描，执行开始扫描
            self.perform_manual_scan()
    
    def scan_folder_for_unprocessed_files(self, manager, folder_path):
        """扫描文件夹中的未处理文件"""
        count = 0
        try:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # 检查是否为图像文件
                    if manager.is_image_file(file_path):
                        # 检查是否已处理过
                        if not manager.is_file_processed(file_path):
                            self.log_message(f"🆕 发现未处理文件: {os.path.basename(file_path)}")
                            # 直接处理文件，不依赖监控状态
                            self.process_single_file(manager, file_path, "扫描发现")
                            count += 1
        except Exception as e:
            self.log_message(f"❌ 扫描文件夹失败 {folder_path}: {str(e)}")
        
        return count
    
    def process_single_file(self, manager, file_path, event_type):
        """直接处理单个文件（不依赖监控状态）"""
        try:
            # 导入ProcessingWorker
            from monitoring_manager import ProcessingWorker
            
            # 创建处理工作器并直接执行
            worker = ProcessingWorker(file_path, event_type, manager)
            worker.process_file()
            
            self.log_message(f"✅ 处理完成: {os.path.basename(file_path)}")
            
        except Exception as e:
            self.log_message(f"❌ 处理文件失败 {os.path.basename(file_path)}: {str(e)}")
    
    def toggle_auto_scan(self):
        """切换定时扫描状态"""
        if not self.is_auto_scanning:
            self.start_auto_scan()
        else:
            self.stop_auto_scan()
    
    def start_auto_scan(self):
        """开始定时扫描"""
        if not self.monitored_folders:
            QMessageBox.warning(self, "警告", "请先添加要监控的文件夹")
            self.auto_scan_btn.setChecked(False)
            return
        
        # 询问扫描间隔
        interval_minutes, ok = QInputDialog.getInt(
            self, "设置扫描间隔", 
            "请输入定时扫描间隔（分钟）:", 
            5, 1, 60, 1
        )
        
        if not ok:
            self.auto_scan_btn.setChecked(False)
            return
        
        self.auto_scan_interval = interval_minutes * 60 * 1000  # 转换为毫秒
        self.auto_scan_timer.start(self.auto_scan_interval)
        self.is_auto_scanning = True
        
        self.auto_scan_btn.setText("⏰ 停止定时")
        self.auto_scan_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc2626;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #b91c1c;
            }
            QPushButton:pressed {
                background-color: #991b1b;
            }
        """)
        
        self.log_message(f"⏰ 定时扫描已启动，间隔: {interval_minutes} 分钟")
    
    def stop_auto_scan(self):
        """停止定时扫描"""
        self.auto_scan_timer.stop()
        self.is_auto_scanning = False
        
        self.auto_scan_btn.setText("⏰ 定时扫描")
        self.auto_scan_btn.setStyleSheet("""
            QPushButton {
                background-color: #7c3aed;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #6d28d9;
            }
            QPushButton:pressed {
                background-color: #5b21b6;
            }
        """)
        
        self.log_message("⏰ 定时扫描已停止")
    
    def perform_auto_scan(self):
        """执行自动定时扫描"""
        if not self.monitored_folders:
            self.log_message("⚠️ 没有监控文件夹，跳过定时扫描")
            return
        
        self.log_message("⏰ 执行定时扫描...")
        
        try:
            # 创建临时的监控管理器进行扫描
            temp_manager = MonitoringManager(backup_folder=self.backup_folder)
            temp_manager.log_message.connect(self.log_message)
            
            scan_count = 0
            for folder in self.monitored_folders:
                if os.path.exists(folder):
                    folder_count = self.scan_folder_for_unprocessed_files(temp_manager, folder)
                    scan_count += folder_count
            
            if scan_count > 0:
                self.log_message(f"⏰ 定时扫描完成，处理了 {scan_count} 个文件")
            else:
                self.log_message("⏰ 定时扫描完成，没有发现新文件")
                
        except Exception as e:
            self.log_message(f"❌ 定时扫描失败: {str(e)}")
    
    def on_scan_progress(self, message):
        """扫描进度更新回调"""
        self.log_message(message)
    
    def on_scan_file_found(self, message):
        """发现文件回调"""
        self.log_message(message)
    
    def on_scan_finished(self, processed_count):
        """扫描完成回调"""
        self.manual_scan_btn.setEnabled(True)
        self.manual_scan_btn.setText("🔍 一键扫描")
        self.manual_scan_btn.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: white;
                border: none;
                padding: 12px 16px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #047857;
            }
            QPushButton:pressed {
                background-color: #065f46;
            }
            QPushButton:disabled {
                background-color: #e5e7eb;
                color: #9ca3af;
            }
        """)
        
        if processed_count > 0:
            self.log_message(f"✅ 手动扫描完成！共处理了 {processed_count} 个未处理文件")
            QMessageBox.information(self, "扫描完成", f"扫描完成！\n共处理了 {processed_count} 个未处理文件")
        else:
            self.log_message("✅ 手动扫描完成，没有发现未处理文件")
            QMessageBox.information(self, "扫描完成", "扫描完成！\n没有发现未处理文件")
    
    def on_scan_error(self, error_message):
        """扫描错误回调"""
        self.manual_scan_btn.setEnabled(True)
        self.manual_scan_btn.setText("🔍 一键扫描")
        self.manual_scan_btn.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: white;
                border: none;
                padding: 12px 16px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #047857;
            }
            QPushButton:pressed {
                background-color: #065f46;
            }
            QPushButton:disabled {
                background-color: #e5e7eb;
                color: #9ca3af;
            }
        """)
        
        self.log_message(f"❌ 扫描过程中发生错误: {error_message}")
        QMessageBox.critical(self, "扫描错误", f"扫描过程中发生错误:\n{error_message}")
    
    def show_about_dialog(self):
        """显示关于对话框"""
        try:
            # 读取README.md文件内容
            readme_path = os.path.join(os.path.dirname(__file__), "README.md")
            if os.path.exists(readme_path):
                with open(readme_path, 'r', encoding='utf-8') as f:
                    readme_content = f.read()
            else:
                readme_content = "README.md 文件未找到"
            
            # 创建关于对话框
            about_dialog = QMessageBox(self)
            about_dialog.setWindowTitle("关于 Image Privacy Guardian")
            about_dialog.setIcon(QMessageBox.Information)
            
            # 设置详细文本为README内容
            about_dialog.setDetailedText(readme_content)
            
            # 设置主要文本
            about_dialog.setText("""
🛡️ Image Privacy Guardian - 图像隐私守护者

版本: 1.0.0
作者: Image Privacy Guardian Team

这是一个专业的图像隐私保护工具，能够自动检测和清理图像中的隐私信息。

支持格式: JPEG/JPG, PNG, BMP, TIFF/TIF, WebP, HEIF/HEIC

点击"Show Details..."查看完整说明文档
            """)
            
            # 设置对话框样式
            about_dialog.setStyleSheet("""
                QMessageBox {
                    background-color: #f8f9fa;
                }
                QMessageBox QLabel {
                    color: #2c3e50;
                    font-size: 12px;
                }
            """)
            
            about_dialog.exec_()
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法显示关于信息: {str(e)}")
        
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 停止扫描线程
        if hasattr(self, 'scan_worker') and self.scan_worker and self.scan_worker.isRunning():
            self.scan_worker.stop_scan()
            self.scan_worker.wait(3000)  # 等待最多3秒
        
        # 停止定时扫描
        if self.is_auto_scanning:
            self.stop_auto_scan()
        
        # 保存所有配置
        self.save_all_configs()
        
        if self.is_monitoring:
            reply = QMessageBox.question(
                self, "确认退出", 
                "监控正在运行中，确定要退出吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.stop_monitoring()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("Image Privacy Guardian")
    app.setApplicationVersion("1.0")
    
    # 设置应用图标（如果有的话）
    # app.setWindowIcon(QIcon("icon.png"))
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()