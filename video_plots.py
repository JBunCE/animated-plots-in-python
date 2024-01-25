import vlc
import queue
import threading
import numpy as np
import customtkinter as ctk
import matplotlib.pyplot as plt

from matplotlib.animation import FuncAnimation
from moviepy.editor import concatenate_videoclips, VideoFileClip
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from sympy import symbols, lambdify

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

class MainWindowG(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Graficación")
        self.geometry("1366x768")

        self.protocol("WM_DELETE_WINDOW", self.destroy_program)

        self.options_frame = ctk.CTkFrame(self)
        self.options_frame.pack(side="left", fill="y", expand=False, padx=10, pady=10)

        self.chart_frame = ctk.CTkFrame(self)
        self.chart_frame.pack(side="top", fill="both", expand=True, padx=10, pady=10)

        self.charts_controls_frame = ctk.CTkFrame(self)
        self.charts_controls_frame.pack(side="top", fill="x", expand=False, padx=10, pady=10)

        self.next_chart_button = ctk.CTkButton(self.charts_controls_frame, text="Reset video", command=self.reset_video)
        self.next_chart_button.pack(side="right", fill="x", expand=False, padx=10, pady=10)

        self.progress_bar = ctk.CTkProgressBar(self.charts_controls_frame)
        self.progress_bar.set(0)


        self.functions_entries = []
        for i in range(5):
            label = ctk.CTkLabel(self.options_frame, text=f"Function {i}")
            label.pack(side="top", fill="x", expand=False, padx=10, pady=5)

            self.functions_entries.append(ctk.CTkEntry(self.options_frame))
            self.functions_entries[i].pack(side="top", fill="x", expand=False, padx=10, pady=2)

        self.function_range_a_label = ctk.CTkLabel(self.options_frame, text="Rango a")
        self.function_range_a_label.pack(side="top", fill="x", expand=False, padx=10, pady=5)
        self.function_range_a_entry = ctk.CTkEntry(self.options_frame)
        self.function_range_a_entry.pack(side="top", fill="x", expand=False, padx=10, pady=5)

        self.function_range_b_label = ctk.CTkLabel(self.options_frame, text="Rango b")
        self.function_range_b_label.pack(side="top", fill="x", expand=False, padx=10, pady=5)
        self.function_range_b_entry = ctk.CTkEntry(self.options_frame)
        self.function_range_b_entry.pack(side="top", fill="x", expand=False, padx=10, pady=5)

        self.init_button = ctk.CTkButton(self.options_frame, text="Graficar", command=self.init_graph)
        self.init_button.pack(side="top", fill="x", expand=False, padx=10, pady=10)

        self.x_symbol = symbols("x")
        self.plot_index = 0
        self.video_index = 0
        self.frame_index = []

        self.video_instance = vlc.Instance()
        self.media_player = self.video_instance.media_player_new()

        self.canvas = ctk.CTkCanvas(self.chart_frame, bg="black")
        self.canvas.pack(expand=True, fill="both")

        win_id = self.canvas.winfo_id()
        self.media_player.set_hwnd(win_id)

        self.queue = queue.Queue()

        self.vide_thread_flag = True
        self.video_thread = threading.Thread(target=self.play_video)
        self.video_thread.start()

    def destroy_program(self):
        self.vide_thread_flag = False
        self.destroy()

    def calculate_indexes(self):
        a = float(self.function_range_a_entry.get())
        b = float(self.function_range_b_entry.get())

        self.y = []
        self.x = np.linspace(a, b, 1000)
        self.frame_index = range(1, len(self.x) + 1, 15)
        for i in range(len(self.functions_entries)):
            if self.functions_entries[i].get() != "":
                f = lambdify(self.x_symbol, self.functions_entries[i].get())
                self.y.append(f(self.x))

    def init_graph(self):
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=10, pady=10)

        plot_thread = threading.Thread(target=self.create_plot)
        plot_thread.start()
        
        # self.unir_videos()

    def create_plot(self):
        self.calculate_indexes()
        for i in range(len(self.y)):
            
            self.plot_index = i
            fig, self.ax = plt.subplots()

            self.animation = FuncAnimation(fig, self.update, range(len(self.frame_index)), interval=0, cache_frame_data=False, repeat=False)

            self.animation.save(f"plot_{self.plot_index}.mp4", writer="ffmpeg", fps=15, dpi=100)
            plt.close(fig)

            self.progress_bar.set(float(f"0.{i + 1}") / float(f"0.{len(self.y)}"))
        self.unir_videos()
        self.queue.put("reset")

    def update(self, frame):
        self.ax.clear()
        self.ax.plot(self.x[:self.frame_index[frame]], self.y[self.plot_index][:self.frame_index[frame]])

        self.ax.set_xlim([1.1*np.min(self.x),1.1*np.max(self.x)])
        self.ax.set_ylim([1.1*np.min(self.y[self.plot_index]),1.1*np.max(self.y[self.plot_index])])

    def play_video(self):
        while self.vide_thread_flag:
            command = self.queue.get()
            if command == "reset":
                self.media = self.video_instance.media_new("final.mp4")
                self.media_player.set_media(self.media)
                self.media_player.play()

    def reset_video(self):
        self.video_index += 1
        if self.video_index < len(self.functions_entries):
            self.video_index = 0
        self.queue.put("reset")

    def unir_videos(self):
        clips = []
        for i in range(len(self.functions_entries)):
            clips.append(VideoFileClip(f"plot_{i}.mp4"))
        
        final_clip = concatenate_videoclips(clips)
        final_clip.write_videofile("final.mp4")

if __name__ == "__main__":
    window = MainWindowG()
    window.mainloop()