"""
监控管理器 - Aegis Folder Watch
负责文件夹监控、文件处理和失败处理的后端引擎
"""

import os
import sys
import time
import hashlib
import json
import shutil
import threading
import gc
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from sanitizer_engine import ImageSanitizer

try:
    import psutil
except ImportError:
    psutil = None


class MemoryMonitor:
    """内存监控和管理类"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.max_memory_mb = self.config.get('max_memory_usage_mb', 2048)
        self.cleanup_threshold_mb = self.config.get('cleanup_threshold_mb', 1536)
        self.gc_interval = self.config.get('gc_interval_seconds', 30)
        self.last_gc_time = time.time()
        
    def get_memory_usage_mb(self):
        """获取当前内存使用量（MB）"""
        if psutil:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        return 0
    
    def get_system_memory_percent(self):
        """获取系统内存使用百分比"""
        if psutil:
            return psutil.virtual_memory().percent
        return 0
    
    def should_cleanup(self):
        """检查是否需要清理内存"""
        current_memory = self.get_memory_usage_mb()
        return current_memory > self.cleanup_threshold_mb
    
    def force_garbage_collection(self):
        """强制垃圾回收"""
        current_time = time.time()
        if current_time - self.last_gc_time > self.gc_interval:
            gc.collect()
            self.last_gc_time = current_time
            return True
        return False
    
    def get_memory_stats(self):
        """获取内存统计信息"""
        return {
            'process_memory_mb': self.get_memory_usage_mb(),
            'system_memory_percent': self.get_system_memory_percent(),
            'max_memory_mb': self.max_memory_mb,
            'cleanup_threshold_mb': self.cleanup_threshold_mb
        }


class ImageFileHandler(FileSystemEventHandler):
    """图像文件事件处理器"""
    
    def __init__(self, monitoring_manager):
        super().__init__()
        self.monitoring_manager = monitoring_manager
        self.processing_delay = 1.0  # 文件稳定等待时间
        self.processed_in_session = set()  # 本次会话已处理的文件
    
    def on_created(self, event):
        """文件创建事件"""
        if not event.is_directory:
            self.handle_file_event(event.src_path, "创建")
    
    def on_modified(self, event):
        """文件修改事件"""
        if not event.is_directory:
            # 避免处理我们自己创建的临时文件
            if ".aegis_temp" in event.src_path or "_cleaned" in event.src_path:
                return
            self.handle_file_event(event.src_path, "修改")
    
    def handle_file_event(self, file_path, event_type):
        """处理文件事件"""
        try:
            # 检查文件扩展名
            if not self.monitoring_manager.is_image_file(file_path):
                return
            
            # 避免处理备份文件夹中的文件
            if self.monitoring_manager.backup_folder in file_path:
                return
            
            # 避免处理临时文件和已清理的文件
            file_name = os.path.basename(file_path)
            if ('_cleaned' in file_name or '_FAILED_' in file_name or 
                '_ERROR_' in file_name or file_name.startswith('~')):
                return
            
            # 过滤掉带时间戳的备份文件（防止处理已经备份的文件）
            if '_20' in file_name and ('_FAILED_' in file_name or len(file_name.split('_')) > 3):
                return
            
            # 避免重复处理同一文件
            if file_path in self.processed_in_session:
                return
            
            # 等待文件稳定
            self.wait_for_file_ready(file_path)
            
            # 再次检查文件是否存在
            if not os.path.exists(file_path):
                return
            
            # 检查文件是否已经被处理过
            if self.monitoring_manager.is_file_processed(file_path):
                return
            
            # 标记为本次会话已处理
            self.processed_in_session.add(file_path)
            
            # 提交处理任务
            self.monitoring_manager.submit_processing_task(file_path, event_type)
            
        except Exception as e:
            self.monitoring_manager.log_message.emit(
                f"❌ 处理文件事件失败: {file_path} - {str(e)}"
            )
    
    def wait_for_file_ready(self, file_path, max_wait=10):
        """等待文件准备就绪"""
        start_time = time.time()
        last_size = -1
        
        while time.time() - start_time < max_wait:
            try:
                if not os.path.exists(file_path):
                    time.sleep(0.1)
                    continue
                
                current_size = os.path.getsize(file_path)
                if current_size == last_size and current_size > 0:
                    # 文件大小稳定，尝试打开文件
                    try:
                        with open(file_path, 'rb') as f:
                            f.read(1)
                        break  # 文件可以正常访问
                    except:
                        pass  # 文件仍在写入中
                
                last_size = current_size
                time.sleep(self.processing_delay)
                
            except Exception:
                time.sleep(0.1)


class ProcessingWorker:
    """处理工作器 - 在单独线程中处理单个文件"""
    
    def __init__(self, file_path: str, event_type: str, monitoring_manager):
        self.file_path = file_path
        self.event_type = event_type
        self.monitoring_manager = monitoring_manager
        self.sanitizer = ImageSanitizer()
        
    def process_file(self):
        """处理文件"""
        start_time = time.time()  # 记录开始时间
        
        try:
            # 首先检查文件是否存在
            if not os.path.exists(self.file_path):
                return  # 静默跳过不存在的文件
            
            # 检查是否已处理过
            if self.monitoring_manager.is_file_processed(self.file_path):
                return  # 静默跳过已处理的文件
            
            # 再次检查文件是否存在（防止在检查过程中被删除）
            if not os.path.exists(self.file_path):
                return  # 静默跳过
            
            # 备份原文件
            backup_path = self.create_backup_path()
            
            # 记录开始处理
            self.monitoring_manager.log_message.emit(
                f"🔄 开始处理 ({self.event_type}): {os.path.basename(self.file_path)}"
            )
            
            # 执行清理（直接替换原文件）
            success = self.sanitizer.clean_image(
                input_path=self.file_path, 
                output_path=None, 
                remove_metadata=True, 
                advanced_cleaning=self.monitoring_manager.advanced_config.get('enabled', False),
                advanced_config=self.monitoring_manager.advanced_config
            )
            
            if success:
                # 成功处理
                processing_time = time.time() - start_time
                
                # 记录处理时间
                self.monitoring_manager.record_processing_time(processing_time)
                
                # 标记文件为已处理
                self.monitoring_manager.mark_file_processed(self.file_path)
                
                # 删除备份
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                    
                # 计算处理后文件的哈希值
                file_hash = self.monitoring_manager.calculate_file_hash(self.file_path)
                hash_display = file_hash[:8] + "..." if file_hash else "未知"
                
                self.monitoring_manager.log_message.emit(
                    f"✅ 处理成功: {os.path.basename(self.file_path)} (耗时: {processing_time:.2f}s)"
                )
                
                # 更新统计
                self.monitoring_manager.increment_success()
                    
            else:
                # 处理失败，恢复备份
                if os.path.exists(backup_path):
                    shutil.move(backup_path, self.file_path)
                raise Exception("图像清理过程失败")
                
        except FileNotFoundError:
            # 文件不存在错误，静默处理
            return
        except Exception as e:
            # 只有真正的处理错误才记录
            if "系统找不到指定的文件" not in str(e):
                self.handle_failure(str(e))
            
    def create_output_path(self):
        """创建输出路径"""
        file_dir = os.path.dirname(self.file_path)
        file_name = os.path.basename(self.file_path)
        name, ext = os.path.splitext(file_name)
        
        # 创建临时输出文件
        output_path = os.path.join(file_dir, f"{name}_cleaned{ext}")
        return output_path
        
    def create_backup_path(self):
        """创建备份路径"""
        # 检查原文件是否存在
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"原文件不存在: {self.file_path}")
        
        # 使用统一的备份路径创建方法
        backup_path = self.create_dated_backup_path(backup_type="processing")
        
        # 复制原文件到备份位置
        try:
            # 只有在需要复制文件时才创建目录
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            shutil.copy2(self.file_path, backup_path)
        except Exception as e:
            raise Exception(f"创建备份失败: {str(e)}")
        
        return backup_path
        
    def handle_failure(self, error_message):
        """处理失败情况 - 失败文件保留在监控文件夹中，同时复制到备份文件夹"""
        try:
            if os.path.exists(self.file_path):
                # 创建按日期分类的备份目录结构
                backup_path = self.create_dated_backup_path()
                
                # 只有在需要备份文件时才创建目录
                try:
                    # 确保备份目录存在
                    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                    
                    # 复制失败文件到备份目录（保留原文件在监控文件夹中）
                    shutil.copy2(self.file_path, backup_path)
                    
                    # 创建错误日志（放在同一目录）
                    file_name = os.path.basename(self.file_path)
                    name, ext = os.path.splitext(file_name)
                    error_log_path = os.path.join(os.path.dirname(backup_path), f"{name}_error_log.txt")
                    with open(error_log_path, 'w', encoding='utf-8') as f:
                        f.write(f"原始文件: {self.file_path}\n")
                        f.write(f"事件类型: {self.event_type}\n")
                        f.write(f"失败时间: {datetime.now().isoformat()}\n")
                        f.write(f"错误信息: {error_message}\n")
                        f.write(f"处理配置: {self.monitoring_manager.advanced_config}\n")
                        
                    self.monitoring_manager.log_message.emit(
                        f"❌ 处理失败: {os.path.basename(self.file_path)} - {error_message}"
                    )
                    self.monitoring_manager.log_message.emit(
                        f"📁 失败文件已备份到: {backup_path}（原文件保留在监控文件夹中）"
                    )
                    
                except Exception as backup_error:
                    # 如果备份失败，只记录错误，不创建空目录
                    self.monitoring_manager.log_message.emit(
                        f"❌ 处理失败: {os.path.basename(self.file_path)} - {error_message}"
                    )
                    self.monitoring_manager.log_message.emit(
                        f"💥 备份失败文件时出错: {str(backup_error)}"
                    )
            else:
                # 文件不存在，只记录错误，不创建任何目录
                self.monitoring_manager.log_message.emit(
                    f"⚠️ 处理失败但文件已不存在: {os.path.basename(self.file_path)} - {error_message}"
                )
            
        except Exception as general_error:
            self.monitoring_manager.log_message.emit(
                f"💥 处理失败情况时出错: {str(general_error)}"
            )
            
        finally:
            # 更新统计
            self.monitoring_manager.increment_failure()
    
    def create_dated_backup_path(self, backup_type="failed"):
        """创建按日期分类的备份路径，保持原有目录结构
        
        Args:
            backup_type: 备份类型，可以是 "failed"（失败）或 "processing"（处理中）
        """
        try:
            # 获取当前时间戳（精确到分钟）
            timestamp = datetime.now().strftime("%Y%m%d%H%M")
            
            # 计算相对于监控文件夹的路径
            relative_path = None
            monitored_folder_name = "unknown_source"
            
            for monitored_folder in self.monitoring_manager.monitored_folders:
                if self.file_path.startswith(monitored_folder):
                    # 获取相对路径
                    relative_path = os.path.relpath(self.file_path, monitored_folder)
                    # 获取监控文件夹的名称作为根目录
                    monitored_folder_name = os.path.basename(monitored_folder.rstrip(os.sep))
                    break
            
            if relative_path is None:
                # 如果无法确定相对路径，使用文件名
                relative_path = os.path.basename(self.file_path)
            
            # 构建备份路径：配置的备份文件夹/日期时间/监控文件夹名/相对路径
            backup_base = os.path.join(self.monitoring_manager.backup_folder, timestamp, monitored_folder_name)
            backup_path = os.path.join(backup_base, relative_path)
            
            # 如果文件已存在，添加序号
            if os.path.exists(backup_path):
                name, ext = os.path.splitext(backup_path)
                counter = 1
                while os.path.exists(f"{name}_{counter:03d}{ext}"):
                    counter += 1
                backup_path = f"{name}_{counter:03d}{ext}"
            
            return backup_path
            
        except Exception as e:
            # 如果创建路径失败，使用简单的备份路径
            timestamp = datetime.now().strftime("%Y%m%d%H%M")
            file_name = os.path.basename(self.file_path)
            return os.path.join(self.monitoring_manager.backup_folder, timestamp, "fallback", file_name)


class MonitoringManager(QObject):
    """监控管理器 - 后端引擎"""
    
    # 信号定义
    log_message = pyqtSignal(str)
    stats_updated = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, backup_folder=None):
        super().__init__()
        
        # 监控状态
        self.is_running = False
        self.observers = []
        
        # 加载性能配置
        self.performance_config = self.load_performance_config()
        
        # 配置
        self.config = {}
        self.advanced_config = {}  # 添加默认的advanced_config
        self.monitored_folders = []
        
        # 备份文件夹配置
        self.backup_folder = self.load_backup_config(backup_folder)
        
        # 统计信息
        self.stats = {
            'folders': 0,
            'processed': 0,
            'success': 0,
            'failed': 0,
            'memory_usage_mb': 0,
            'cpu_usage_percent': 0,
            'active_threads': 0
        }
        self.stats_lock = Lock()
        
        # 处理时间记录（用于计算处理速度和平均时间）
        self.processing_times = []  # 存储最近的处理时间
        self.processing_times_lock = Lock()
        self.max_processing_times = 100  # 最多保留100个处理时间记录
        self.start_time = time.time()  # 监控开始时间
        
        # 动态线程池管理
        thread_config = self.performance_config.get('thread_management', {})
        self.min_threads = thread_config.get('min_threads', 1)
        self.max_threads = thread_config.get('max_threads', 8)
        self.max_concurrent_threads = thread_config.get('default_threads', 3)
        self.cpu_threshold_increase = thread_config.get('cpu_threshold_increase', 50)
        self.cpu_threshold_decrease = thread_config.get('cpu_threshold_decrease', 80)
        self.adjustment_interval = thread_config.get('adjustment_interval_seconds', 10)
        self.last_adjustment_time = time.time()
        
        # 处理线程池
        self.processing_threads = []
        
        # 内存监控器
        memory_config = self.performance_config.get('memory_management', {})
        self.memory_monitor = MemoryMonitor(memory_config)
        
        # 已处理文件的哈希记录
        self.processed_files = {}  # {file_path: {'hash': hash_value, 'timestamp': timestamp}}
        self.processed_files_lock = Lock()
        self.log_file_path = "aegis_processed_files.json"
        self.max_processed_entries = memory_config.get('processed_files_max_entries', 10000)
        self.cleanup_threshold = memory_config.get('processed_files_cleanup_threshold', 8000)
        
        # 支持的图像格式
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp', '.heif', '.heic'}
        
        # 加载已处理文件记录
        self.load_processed_files()
        
        # 统计更新定时器
        stats_interval = self.performance_config.get('ui_performance', {}).get('stats_update_interval_ms', 1000)
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.emit_stats)
        self.stats_timer.start(stats_interval)  # 根据配置更新统计
        
        # 性能监控定时器
        self.performance_timer = QTimer()
        self.performance_timer.timeout.connect(self.adjust_thread_pool)
        self.performance_timer.start(self.adjustment_interval * 1000)  # 转换为毫秒
    
    def load_performance_config(self):
        """加载性能配置文件"""
        try:
            config_path = "performance_config.json"
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # 返回默认配置
                return {
                    "thread_management": {
                        "min_threads": 1,
                        "max_threads": 8,
                        "default_threads": 3,
                        "cpu_threshold_increase": 50,
                        "cpu_threshold_decrease": 80,
                        "adjustment_interval_seconds": 10
                    },
                    "memory_management": {
                        "max_memory_usage_mb": 2048,
                        "cleanup_threshold_mb": 1536,
                        "gc_interval_seconds": 30,
                        "processed_files_max_entries": 10000,
                        "processed_files_cleanup_threshold": 8000
                    },
                    "ui_performance": {
                        "stats_update_interval_ms": 1000
                    }
                }
        except Exception as e:
            self.log_message.emit(f"❌ 加载性能配置失败: {str(e)}")
            return {}
    
    def get_cpu_usage(self):
        """获取CPU使用率"""
        if psutil:
            return psutil.cpu_percent(interval=1)
        return 0
    
    def adjust_thread_pool(self):
        """动态调整线程池大小"""
        try:
            current_time = time.time()
            if current_time - self.last_adjustment_time < self.adjustment_interval:
                return
            
            # 获取系统资源使用情况
            cpu_usage = self.get_cpu_usage()
            memory_usage = self.memory_monitor.get_memory_usage_mb()
            current_threads = len([t for t in self.processing_threads if t.is_alive()])
            
            old_max = self.max_concurrent_threads
            
            # 根据CPU使用率调整线程数
            if cpu_usage < self.cpu_threshold_increase and current_threads >= self.max_concurrent_threads:
                # CPU使用率低且线程池满，可以增加线程
                if self.max_concurrent_threads < self.max_threads:
                    self.max_concurrent_threads = min(self.max_threads, self.max_concurrent_threads + 1)
            elif cpu_usage > self.cpu_threshold_decrease:
                # CPU使用率高，减少线程
                if self.max_concurrent_threads > self.min_threads:
                    self.max_concurrent_threads = max(self.min_threads, self.max_concurrent_threads - 1)
            
            # 根据内存使用情况调整
            if memory_usage > self.memory_monitor.cleanup_threshold_mb:
                # 内存使用过高，减少线程并清理
                if self.max_concurrent_threads > self.min_threads:
                    self.max_concurrent_threads = max(self.min_threads, self.max_concurrent_threads - 1)
                self.cleanup_memory()
            
            # 更新统计信息
            with self.stats_lock:
                self.stats['memory_usage_mb'] = memory_usage
                self.stats['cpu_usage_percent'] = cpu_usage
                self.stats['active_threads'] = current_threads
            
            if old_max != self.max_concurrent_threads:
                self.log_message.emit(f"🔧 线程池大小调整: {old_max} → {self.max_concurrent_threads} (CPU: {cpu_usage:.1f}%, 内存: {memory_usage:.1f}MB)")
            
            self.last_adjustment_time = current_time
            
        except Exception as e:
            self.log_message.emit(f"❌ 线程池调整失败: {str(e)}")
    
    def record_processing_time(self, processing_time):
        """记录处理时间"""
        try:
            with self.processing_times_lock:
                self.processing_times.append(processing_time)
                
                # 保持最多100个记录
                if len(self.processing_times) > self.max_processing_times:
                    self.processing_times = self.processing_times[-self.max_processing_times:]
                    
        except Exception as e:
            self.log_message.emit(f"❌ 记录处理时间失败: {str(e)}")
    
    def get_processing_speed(self):
        """计算处理速度（文件/分钟）"""
        try:
            current_time = time.time()
            elapsed_time = current_time - self.start_time
            
            if elapsed_time < 60:  # 少于1分钟
                return 0
            
            with self.stats_lock:
                processed_count = self.stats['processed']
                
            if processed_count == 0:
                return 0
                
            # 计算每分钟处理的文件数
            speed = (processed_count / elapsed_time) * 60
            return round(speed, 2)
            
        except Exception:
            return 0
    
    def get_average_processing_time(self):
        """计算平均处理时间"""
        try:
            with self.processing_times_lock:
                if not self.processing_times:
                    return 0
                    
                avg_time = sum(self.processing_times) / len(self.processing_times)
                return round(avg_time, 2)
                
        except Exception:
            return 0
    
    def cleanup_memory(self):
        """清理内存"""
        try:
            # 强制垃圾回收
            if self.memory_monitor.force_garbage_collection():
                self.log_message.emit("🧹 执行内存垃圾回收")
            
            # 清理已处理文件记录
            with self.processed_files_lock:
                if len(self.processed_files) > self.cleanup_threshold:
                    # 按时间戳排序，保留最新的记录
                    sorted_files = sorted(
                        self.processed_files.items(),
                        key=lambda x: x[1].get('timestamp', ''),
                        reverse=True
                    )
                    
                    # 保留最新的记录
                    keep_count = self.max_processed_entries // 2
                    self.processed_files = dict(sorted_files[:keep_count])
                    
                    self.log_message.emit(f"🧹 清理已处理文件记录: 保留 {keep_count} 条最新记录")
                    self.save_processed_files()
            
        except Exception as e:
            self.log_message.emit(f"❌ 内存清理失败: {str(e)}")
    
    def load_backup_config(self, backup_folder=None):
        """加载备份配置"""
        if backup_folder:
            return backup_folder
            
        try:
            # 尝试从配置文件加载
            config_path = os.path.join("aegis_config", "backup_config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    backup_config = json.load(f)
                    configured_folder = backup_config.get('backup_folder', 'errorbak')
                    
                    # 如果是相对路径，转换为绝对路径
                    if not os.path.isabs(configured_folder):
                        app_root = os.path.dirname(os.path.abspath(__file__))
                        return os.path.join(app_root, configured_folder)
                    else:
                        return configured_folder
        except Exception as e:
            print(f"加载备份配置失败: {e}")
        
        # 默认备份文件夹
        app_root = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(app_root, "errorbak")
        
    def start_monitoring(self, folders: List[str], config: dict):
        """开始监控"""
        try:
            self.monitored_folders = folders.copy()
            self.config = config.copy()
            self.advanced_config = config.copy()  # 添加advanced_config属性
            self.is_running = True
            
            # 更新统计
            self.stats['folders'] = len(folders)
            
            # 首次扫描所有文件夹中的图像文件
            self.log_message.emit("🔍 开始首次扫描现有文件...")
            self.initial_scan(folders)
            
            # 为每个文件夹创建观察者
            for folder in folders:
                if os.path.exists(folder):
                    observer = Observer()
                    event_handler = ImageFileHandler(self)
                    observer.schedule(event_handler, folder, recursive=True)
                    observer.start()
                    self.observers.append(observer)
                    
                    self.log_message.emit(f"👁️ 开始监控文件夹: {folder}")
                else:
                    self.log_message.emit(f"⚠️ 文件夹不存在: {folder}")
                    
            self.log_message.emit(f"🚀 监控管理器已启动，监控 {len(self.observers)} 个文件夹")
            
        except Exception as e:
            self.error_occurred.emit(f"启动监控失败: {str(e)}")
            
    def initial_scan(self, folders):
        """首次扫描文件夹中的所有图像文件"""
        for folder in folders:
            if not os.path.exists(folder):
                continue
                
            try:
                for root, dirs, files in os.walk(folder):
                    for file in files:
                        file_path = os.path.join(root, file)
                        
                        # 检查是否为图像文件
                        if self.is_image_file(file_path):
                            # 检查是否已处理过
                            if not self.is_file_processed(file_path):
                                self.log_message.emit(f"📁 发现新文件: {os.path.basename(file_path)}")
                                self.submit_processing_task(file_path, "首次扫描")
                            
            except Exception as e:
                self.log_message.emit(f"❌ 扫描文件夹失败 {folder}: {str(e)}")
            
    def stop_monitoring(self):
        """停止监控"""
        try:
            self.is_running = False
            
            # 停止所有观察者
            for observer in self.observers:
                observer.stop()
                observer.join()
                
            self.observers.clear()
            
            # 等待处理线程完成
            self.wait_for_processing_threads()
            
            self.log_message.emit("⏹️ 监控管理器已停止")
            
        except Exception as e:
            self.error_occurred.emit(f"停止监控失败: {str(e)}")
            
    def queue_file_for_processing(self, file_path: str, event_type: str):
        """将文件加入处理队列"""
        if not self.is_running:
            return
            
        try:
            # 清理已完成的线程
            self.cleanup_finished_threads()
            
            # 检查内存使用情况
            if self.memory_monitor.should_cleanup():
                self.cleanup_memory()
                # 如果内存仍然过高，暂停处理
                if self.memory_monitor.get_memory_usage_mb() > self.memory_monitor.max_memory_mb:
                    self.log_message.emit(f"⚠️ 内存使用过高，暂停处理: {os.path.basename(file_path)}")
                    return
            
            # 检查并发限制
            active_threads = len([t for t in self.processing_threads if t.is_alive()])
            if active_threads >= self.max_concurrent_threads:
                self.log_message.emit(f"⏳ 处理队列已满 ({active_threads}/{self.max_concurrent_threads})，等待处理: {os.path.basename(file_path)}")
                return
                
            # 创建处理工作器
            worker = ProcessingWorker(file_path, event_type, self)
            
            # 在新线程中执行
            thread = threading.Thread(target=worker.process_file, daemon=True)
            thread.start()
            
            self.processing_threads.append(thread)
            self.increment_processed()
            
        except Exception as e:
            self.log_message.emit(f"❌ 提交处理任务失败: {str(e)}")
    
    def submit_processing_task(self, file_path: str, event_type: str):
        """提交处理任务（兼容性方法）"""
        self.queue_file_for_processing(file_path, event_type)
            
    def cleanup_finished_threads(self):
        """清理已完成的线程"""
        self.processing_threads = [t for t in self.processing_threads if t.is_alive()]
        
    def wait_for_processing_threads(self, timeout=30):
        """等待处理线程完成"""
        start_time = time.time()
        
        while self.processing_threads and (time.time() - start_time) < timeout:
            self.cleanup_finished_threads()
            time.sleep(0.5)
            
        # 强制结束剩余线程（如果有的话）
        if self.processing_threads:
            self.log_message.emit(f"⚠️ {len(self.processing_threads)} 个处理线程未能及时完成")
            
    def update_config(self, new_config: dict):
        """更新配置"""
        self.config = new_config.copy()
        self.advanced_config = new_config.copy()  # 同时更新advanced_config
        self.log_message.emit("⚙️ 配置已更新")
        
    def increment_processed(self):
        """增加处理计数"""
        with self.stats_lock:
            self.stats['processed'] += 1
        
    def increment_success(self):
        """增加成功计数"""
        with self.stats_lock:
            self.stats['success'] += 1
        
    def increment_failure(self):
        """增加失败计数"""
        with self.stats_lock:
            self.stats['failed'] += 1
        
    def emit_stats(self):
        """发送统计信息更新信号"""
        with self.stats_lock:
            # 获取性能监控数据
            cpu_usage = self.get_cpu_usage()
            memory_stats = self.memory_monitor.get_memory_stats()
            active_threads = len([t for t in self.processing_threads if t.is_alive()])
            
            # 计算处理速度（文件/分钟）
            current_time = time.time()
            if hasattr(self, 'last_stats_time') and self.last_stats_time:
                time_diff = current_time - self.last_stats_time
                if time_diff > 0:
                    processed_diff = self.stats['processed'] - getattr(self, 'last_processed_count', 0)
                    processing_speed = (processed_diff / time_diff) * 60  # 转换为每分钟
                else:
                    processing_speed = 0
            else:
                processing_speed = 0
            
            # 更新记录
            self.last_stats_time = current_time
            self.last_processed_count = self.stats['processed']
            
            # 计算平均处理时间
            if hasattr(self, 'processing_times') and self.processing_times:
                avg_processing_time = sum(self.processing_times) / len(self.processing_times)
            else:
                avg_processing_time = 0
            
            # 确定当前状态
            if self.is_running:
                if active_threads > 0:
                    status = "处理中"
                else:
                    status = "监控中"
            else:
                status = "已停止"
            
            # 构建完整的统计信息
            enhanced_stats = self.stats.copy()
            enhanced_stats.update({
                'cpu_usage': cpu_usage,
                'memory_usage': memory_stats['process_memory_mb'],
                'active_threads': active_threads,
                'queue_length': len(self.processing_threads),
                'status': status,
                'processing_speed': processing_speed,
                'avg_processing_time': avg_processing_time
            })
            
            self.stats_updated.emit(enhanced_stats)
    
    def calculate_file_hash(self, file_path):
        """计算文件的MD5哈希值"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            self.log_message.emit(f"❌ 计算文件哈希失败: {file_path} - {str(e)}")
            return None
    
    def load_processed_files(self):
        """从文件加载已处理文件记录"""
        try:
            if os.path.exists(self.log_file_path):
                with open(self.log_file_path, 'r', encoding='utf-8') as f:
                    self.processed_files = json.load(f)
                self.log_message.emit(f"📖 已加载 {len(self.processed_files)} 条处理记录")
            else:
                self.processed_files = {}
                self.log_message.emit("📝 创建新的处理记录文件")
        except Exception as e:
            self.log_message.emit(f"❌ 加载处理记录失败: {str(e)}")
            self.processed_files = {}
    
    def save_processed_files(self):
        """保存已处理文件记录到文件"""
        try:
            with self.processed_files_lock:
                with open(self.log_file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.processed_files, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log_message.emit(f"❌ 保存处理记录失败: {str(e)}")
    
    def is_file_processed(self, file_path):
        """检查文件是否已经处理过（基于哈希值）"""
        try:
            if not os.path.exists(file_path):
                return True  # 文件不存在，认为已处理
            
            current_hash = self.calculate_file_hash(file_path)
            if not current_hash:
                return False  # 无法计算哈希，需要处理
            
            with self.processed_files_lock:
                if file_path in self.processed_files:
                    stored_hash = self.processed_files[file_path].get('hash')
                    return stored_hash == current_hash
                return False  # 文件未记录，需要处理
        except Exception as e:
            self.log_message.emit(f"❌ 检查文件处理状态失败: {file_path} - {str(e)}")
            return False
    
    def mark_file_processed(self, file_path):
        """标记文件为已处理"""
        try:
            file_hash = self.calculate_file_hash(file_path)
            if file_hash:
                with self.processed_files_lock:
                    self.processed_files[file_path] = {
                        'hash': file_hash,
                        'timestamp': datetime.now().isoformat()
                    }
                self.save_processed_files()
        except Exception as e:
            self.log_message.emit(f"❌ 标记文件处理状态失败: {file_path} - {str(e)}")
    
    def is_image_file(self, file_path):
        """检查文件是否为支持的图像格式"""
        if not Path(file_path).suffix.lower() in self.supported_formats:
            return False
            
        # 进一步检查文件名，排除备份文件
        filename = Path(file_path).name
        
        # 排除带时间戳的文件（通常是备份文件）
        import re
        timestamp_pattern = r'_\d{8}_\d{6}'
        if re.search(timestamp_pattern, filename):
            return False
            
        # 排除失败标记的文件
        if '_FAILED_' in filename:
            return False
            
        return True
        
    def get_monitoring_status(self) -> dict:
        """获取监控状态"""
        with self.stats_lock:
            return {
                'is_running': self.is_running,
                'monitored_folders': self.monitored_folders.copy(),
                'active_observers': len(self.observers),
                'processing_threads': len(self.processing_threads),
                'stats': self.stats.copy()
            }