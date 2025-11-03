import threading
import queue
import tkinter as tk
from tkinter import scrolledtext
import logging

# 非阻塞弹窗类 - 用于TSRL推理展示
class NonBlockingInferenceWindow:
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        self.root = None
        self.text_area = None
        self.window_thread = None
        self.update_queue = queue.Queue()
        self.is_running = False
        
    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance
    
    def _create_window(self, title: str):
        """在新线程中创建窗口"""
        try:
            # 创建主窗口
            self.root = tk.Tk()
            self.root.title(title)
            self.root.geometry("600x400")
            self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
            
            # 创建滚动文本框
            self.text_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, width=70, height=25)
            self.text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
            
            # 添加关闭按钮
            close_button = tk.Button(self.root, text="关闭", command=self._on_closing)
            close_button.pack(pady=5)
            
            # 启动更新循环
            self.root.after(100, self._process_updates)
            
            # 运行窗口
            self.is_running = True
            self.root.mainloop()
        except Exception as e:
            logging.error(f"Error creating inference display window: {e}")
    
    def _on_closing(self):
        """窗口关闭事件处理"""
        self.is_running = False
        if self.root:
            self.root.destroy()
        self.root = None
        self.text_area = None
    
    def _process_updates(self):
        """处理更新队列"""
        try:
            while not self.update_queue.empty():
                content = self.update_queue.get_nowait()
                if self.text_area:
                    self.text_area.configure(state='normal')
                    self.text_area.delete(1.0, tk.END)
                    self.text_area.insert(tk.INSERT, content)
                    self.text_area.configure(state='disabled')
                    self.text_area.see(tk.END)
        except queue.Empty:
            pass
        except Exception as e:
            logging.error(f"Error processing updates: {e}")
        
        # 继续更新循环
        if self.root and self.is_running:
            self.root.after(100, self._process_updates)
    
    def show_window(self, title: str):
        """显示窗口"""
        if not self.is_running:
            self.window_thread = threading.Thread(target=self._create_window, args=(title,), daemon=True)
            self.window_thread.start()
    
    def update_content(self, content: str):
        """更新窗口内容"""
        if self.is_running:
            self.update_queue.put(content)
    
    def is_window_running(self):
        """检查窗口是否正在运行"""
        return self.is_running


# 非阻塞弹窗类 - 用于Vehicle通信展示
class NonBlockingVehicleDisplayWindow:
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        self.root = None
        self.text_area = None
        self.window_thread = None
        self.update_queue = queue.Queue()
        self.is_running = False
        
    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance
    
    def _create_window(self, title: str):
        """在新线程中创建窗口"""
        try:
            # 创建主窗口
            self.root = tk.Tk()
            self.root.title(title)
            self.root.geometry("600x400")
            self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
            
            # 创建滚动文本框
            self.text_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, width=70, height=25)
            self.text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
            
            # 添加关闭按钮
            close_button = tk.Button(self.root, text="关闭", command=self._on_closing)
            close_button.pack(pady=5)
            
            # 启动更新循环
            self.root.after(100, self._process_updates)
            
            # 运行窗口
            self.is_running = True
            self.root.mainloop()
        except Exception as e:
            logging.error(f"Error creating vehicle display window: {e}")
    
    def _on_closing(self):
        """窗口关闭事件处理"""
        self.is_running = False
        if self.root:
            self.root.destroy()
        self.root = None
        self.text_area = None
    
    def _process_updates(self):
        """处理更新队列"""
        try:
            while not self.update_queue.empty():
                content = self.update_queue.get_nowait()
                if self.text_area:
                    self.text_area.configure(state='normal')
                    self.text_area.delete(1.0, tk.END)
                    self.text_area.insert(tk.INSERT, content)
                    self.text_area.configure(state='disabled')
                    self.text_area.see(tk.END)
        except queue.Empty:
            pass
        except Exception as e:
            logging.error(f"Error processing updates: {e}")
        
        # 继续更新循环
        if self.root and self.is_running:
            self.root.after(100, self._process_updates)
    
    def show_window(self, title: str):
        """显示窗口"""
        if not self.is_running:
            self.window_thread = threading.Thread(target=self._create_window, args=(title,), daemon=True)
            self.window_thread.start()
    
    def update_content(self, content: str):
        """更新窗口内容"""
        if self.is_running:
            self.update_queue.put(content)
    
    def is_window_running(self):
        """检查窗口是否正在运行"""
        return self.is_running