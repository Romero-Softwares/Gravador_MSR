import os
import threading
import time

import cv2
import numpy as np
import pyautogui
import sounddevice as sd
from moviepy import AudioFileClip, VideoFileClip
from scipy.io.wavfile import write


class RecorderEngine:
    def __init__(
        self,
        output_dir,
        video_temp,
        audio_temp,
        audio_rate,
        target_fps,
        status_callback=None,
        finished_callback=None,
    ):
        self.output_dir = output_dir
        self.video_temp = video_temp
        self.audio_temp = audio_temp
        self.audio_rate = audio_rate
        self.target_fps = target_fps
        self.status_callback = status_callback
        self.finished_callback = finished_callback

        self.recording = False
        self.camera_enabled = False
        self.capture_screen_enabled = True
        self.camera_overlay_position = None
        self.state_lock = threading.Lock()
        self.start_time_real = None
        self.stop_time_real = None
        self.video_thread = None
        self.audio_thread = None
        self.video_done_event = threading.Event()
        self.resolution = pyautogui.size()

    def set_output_dir(self, output_dir):
        self.output_dir = output_dir

    def set_capture_screen_enabled(self, enabled):
        with self.state_lock:
            self.capture_screen_enabled = enabled

        if self.recording:
            if enabled:
                self._set_status("Tela ativada durante a gravação.", "#3498db")
            else:
                self._set_status("Gravando somente a câmera em tela cheia.", "#9b59b6")

    def is_capture_screen_enabled(self):
        with self.state_lock:
            return self.capture_screen_enabled

    def start(self, camera_enabled=False, camera_overlay_position=None, capture_screen_enabled=True):
        self.recording = True
        self.camera_enabled = camera_enabled
        self.set_capture_screen_enabled(capture_screen_enabled)
        self.camera_overlay_position = camera_overlay_position
        self.start_time_real = time.perf_counter()
        self.stop_time_real = None
        self.video_done_event.clear()

        self.video_thread = threading.Thread(target=self._record_video, daemon=True)
        self.audio_thread = threading.Thread(target=self._record_audio, daemon=True)
        self.video_thread.start()
        self.audio_thread.start()

    def stop(self):
        if self.recording:
            self.stop_time_real = time.perf_counter()
        self.recording = False

    def _set_status(self, text, color=None):
        if self.status_callback:
            self.status_callback(text, color)

    def _finish(self, success, message, color=None):
        if self.finished_callback:
            self.finished_callback(success, message, color)

    def _record_video(self):
        frame_interval = 1.0 / self.target_fps
        codec = cv2.VideoWriter_fourcc(*"XVID")
        output = cv2.VideoWriter(self.video_temp, codec, self.target_fps, self.resolution)
        camera = self._open_camera() if self.camera_enabled else None
        frames_written = 0
        last_frame = None

        try:
            while self.recording:
                now = time.perf_counter()
                elapsed = max(0.0, now - self.start_time_real)
                expected_frames = int(elapsed / frame_interval) + 1

                if frames_written < expected_frames:
                    if self.is_capture_screen_enabled():
                        screenshot = pyautogui.screenshot()
                        frame = np.array(screenshot)
                        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

                        if camera:
                            self._draw_camera_overlay(frame, camera)

                        mouse_x, mouse_y = pyautogui.position()
                        cv2.circle(frame, (mouse_x, mouse_y), 6, (255, 255, 255), -1)
                        cv2.circle(frame, (mouse_x, mouse_y), 6, (0, 0, 0), 2)
                    else:
                        frame = self._get_camera_fullscreen_frame(camera)
                        if frame is None:
                            screenshot = pyautogui.screenshot()
                            frame = np.array(screenshot)
                            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                            self.set_capture_screen_enabled(True)

                    last_frame = frame
                    while frames_written < expected_frames:
                        output.write(last_frame)
                        frames_written += 1
                else:
                    time.sleep(0.001)

            final_time = self.stop_time_real or time.perf_counter()
            final_elapsed = max(0.0, final_time - self.start_time_real)
            final_expected_frames = max(frames_written, int(final_elapsed / frame_interval))

            if last_frame is not None:
                while frames_written < final_expected_frames:
                    output.write(last_frame)
                    frames_written += 1

        finally:
            if camera:
                camera.release()
            output.release()
            self.video_done_event.set()

    def _open_camera(self):
        camera_indices = [0, 1, 2, 3, 4, 5]
        backends = [cv2.CAP_DSHOW, cv2.CAP_ANY]

        for backend in backends:
            for index in camera_indices:
                camera = cv2.VideoCapture(index, backend)

                if not camera.isOpened():
                    camera.release()
                    continue

                success, _ = camera.read()
                if success:
                    self._set_status(
                        f"Câmera ativa: dispositivo {index}. Gravando tela, câmera e áudio...",
                        "#3498db",
                    )
                    return camera

                camera.release()

        self._set_status("Câmera não encontrada. Gravando tela e áudio.", "orange")
        return None

    def _get_camera_fullscreen_frame(self, camera):
        if not camera:
            return None

        success, camera_frame = camera.read()
        if not success:
            return None

        screen_width, screen_height = self.resolution
        camera_frame = cv2.flip(camera_frame, 1)
        return cv2.resize(camera_frame, (screen_width, screen_height))

    def _draw_camera_overlay(self, frame, camera):
        success, camera_frame = camera.read()
        if not success:
            return

        screen_width, screen_height = self.resolution
        overlay_width = max(220, int(screen_width * 0.18))
        overlay_height = int(overlay_width * 9 / 16)

        camera_frame = cv2.resize(camera_frame, (overlay_width, overlay_height))
        camera_frame = cv2.flip(camera_frame, 1)

        if self.camera_overlay_position:
            x1, y1 = self.camera_overlay_position
        else:
            margin = 24
            x1 = screen_width - overlay_width - margin
            y1 = screen_height - overlay_height - margin

        x1 = max(0, min(int(x1), screen_width - overlay_width))
        y1 = max(0, min(int(y1), screen_height - overlay_height))
        x2 = x1 + overlay_width
        y2 = y1 + overlay_height

        cv2.rectangle(frame, (x1 - 3, y1 - 3), (x2 + 3, y2 + 3), (255, 255, 255), 3)
        frame[y1:y2, x1:x2] = camera_frame

    def _record_audio(self):
        try:
            try:
                device_info = sd.query_devices(kind="input")
                self._set_status(f"Áudio: {device_info['name'][:35]}...", "blue")
            except Exception as error:
                print(f"Microfone indisponível: {error}")
                self._set_status("Microfone não encontrado. Gravando sem áudio.", "orange")
                while self.recording:
                    time.sleep(0.1)
                self.video_done_event.wait()
                self._merge_files(include_audio=False)
                return

            audio_data = sd.rec(
                int(3600 * self.audio_rate),
                samplerate=self.audio_rate,
                channels=1,
                device=None,
            )

            while self.recording:
                time.sleep(0.1)

            final_time = self.stop_time_real or time.perf_counter()
            duration = max(0.0, final_time - self.start_time_real)
            sd.stop()

            audio_final = audio_data[: int(duration * self.audio_rate)]
            write(self.audio_temp, self.audio_rate, audio_final)

            self.video_done_event.wait()
            self._merge_files(include_audio=True)

        except Exception as error:
            print(f"Erro no Microfone: {error}")
            self._set_status("Falha no microfone. Salvando vídeo sem áudio.", "orange")
            while self.recording:
                time.sleep(0.1)
            self.video_done_event.wait()
            self._merge_files(include_audio=False)

    def _merge_files(self, include_audio=True):
        file_name = f"gravacao_{int(time.time())}.mp4"
        final_path = os.path.join(self.output_dir, file_name)

        video_clip = None
        audio_clip = None
        final_clip = None

        try:
            if include_audio and os.path.exists(self.audio_temp):
                self._set_status("Sincronizando áudio/vídeo...", "yellow")
            else:
                self._set_status("Finalizando vídeo sem áudio...", "yellow")

            video_clip = VideoFileClip(self.video_temp).with_fps(self.target_fps)

            if include_audio and os.path.exists(self.audio_temp):
                audio_clip = AudioFileClip(self.audio_temp)
                synced_duration = min(video_clip.duration, audio_clip.duration)
                video_clip = video_clip.subclipped(0, synced_duration)
                audio_clip = audio_clip.subclipped(0, synced_duration)
                final_clip = video_clip.with_audio(audio_clip)
                final_clip = final_clip.with_duration(synced_duration)
            else:
                final_clip = video_clip

            final_clip.write_videofile(
                final_path,
                codec="libx264",
                audio_codec="aac" if include_audio and os.path.exists(self.audio_temp) else None,
                logger=None,
            )

            mensagem = "Vídeo salvo com sucesso!"
            if not include_audio:
                mensagem = "Vídeo salvo sem áudio."
            self._finish(True, mensagem, "#2ecc71")

        except Exception as error:
            print(f"Erro: {error}")
            self._finish(False, "Erro na finalização", "orange")

        finally:
            if final_clip:
                final_clip.close()
            if video_clip:
                video_clip.close()
            if audio_clip:
                audio_clip.close()

            self._cleanup_temp_files()

    def _cleanup_temp_files(self):
        if os.path.exists(self.video_temp):
            os.remove(self.video_temp)

        if os.path.exists(self.audio_temp):
            os.remove(self.audio_temp)
            
    def _os_temp_clean_file(self):
        if os.path_exists(self.file_temp) == "file_temp":
            clean.file.resource_file_temp
            return # for clean all file temp
