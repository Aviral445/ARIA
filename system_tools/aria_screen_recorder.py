"""
system_tools/aria_screen_recorder.py — Autonomous Screen & Audio Recording, Visual Frame Analysis,
and Intelligent Meeting Notes Engine for Aria AI.

Enables Aria to:
1. Record user screen & Google Meets with background threading (MSS + OpenCV + PyAudio/SoundDevice).
2. Attach to Windows desktop station (winsta0\\default) for 100% reliable screen capture.
3. Simultaneously capture meeting audio into high-fidelity 16kHz WAV format.
4. Extract key presentation slides & visual frames at key points during the meeting.
5. Transcribe spoken audio using Whisper / Gemini speech recognition.
6. Multimodally analyze screen visuals + audio transcript to generate structured, comprehensive "Perfect Meeting Notes".
7. Auto-save notes to Desktop / Documents and open them for immediate review.
"""

import os
import sys
import time
import json
import threading
import datetime
import re
import io
from typing import Dict, Any, List, Optional, Tuple

import numpy as np

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure root paths are accessible
try:
    from core.paths import ROOT_DIR, DATA_DIR, RECORDINGS_DIR
except ImportError:
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(ROOT_DIR, "data")
    RECORDINGS_DIR = os.path.join(DATA_DIR, "recordings")

os.makedirs(RECORDINGS_DIR, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# 1. WINDOWS DESKTOP STATION ATTACH HELPER
# ─────────────────────────────────────────────────────────────────────────────
def ensure_desktop_attached():
    """Attaches current thread to winsta0\\default to guarantee screen capture in background."""
    if sys.platform == "win32":
        try:
            import ctypes
            u32 = ctypes.windll.user32
            hwinsta = u32.OpenWindowStationW("winsta0", False, 0x0000037F)
            if hwinsta:
                u32.SetProcessWindowStation(hwinsta)
            hdesk = u32.OpenDesktopW("default", 0, False, 0x000001FF)
            if hdesk:
                u32.SetThreadDesktop(hdesk)
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# 2. SCREEN & AUDIO RECORDER CONTROLLER
# ─────────────────────────────────────────────────────────────────────────────
class AriaScreenRecorder:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self.is_recording: bool = False
        self.current_session: Optional[Dict[str, Any]] = None
        self.stop_event = threading.Event()
        self.video_thread: Optional[threading.Thread] = None
        self.audio_thread: Optional[threading.Thread] = None
        self.last_completed_session: Optional[Dict[str, Any]] = None
        self._initialized = True

    def get_status(self) -> Dict[str, Any]:
        """Returns the current recording status."""
        if not self.is_recording or not self.current_session:
            last = self.last_completed_session.get("session_id", "None") if self.last_completed_session else "None"
            return {
                "recording": False,
                "status": "IDLE",
                "message": "Aria is not currently recording.",
                "last_session": last
            }

        elapsed = time.time() - self.current_session.get("start_epoch", time.time())
        mins = int(elapsed // 60)
        secs = int(elapsed % 60)
        return {
            "recording": True,
            "status": "RECORDING",
            "session_id": self.current_session.get("session_id"),
            "title": self.current_session.get("title"),
            "elapsed_seconds": round(elapsed, 1),
            "elapsed_formatted": f"{mins:02d}:{secs:02d}",
            "fps": self.current_session.get("fps", 10),
            "video_path": self.current_session.get("video_path"),
            "audio_path": self.current_session.get("audio_path"),
            "record_audio": self.current_session.get("record_audio", True)
        }

    def start_recording(self, title: str = "Google_Meet", fps: int = 10, record_audio: bool = True) -> Dict[str, Any]:
        """Starts recording the screen and audio in the background."""
        if self.is_recording:
            stat = self.get_status()
            return {
                "success": False,
                "message": f"Already recording '{stat.get('title')}' (Duration: {stat.get('elapsed_formatted')}). Stop it first with stop_screen_recording.",
                "session": stat
            }

        ensure_desktop_attached()

        clean_title = re.sub(r'[^a-zA-Z0-9_\-]', '_', (title or "Google_Meet").strip())
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"rec_{timestamp}_{clean_title}"

        session_dir = os.path.join(RECORDINGS_DIR, session_id)
        frames_dir = os.path.join(session_dir, "frames")
        os.makedirs(frames_dir, exist_ok=True)

        video_path = os.path.join(session_dir, f"{session_id}_screen.mp4")
        audio_path = os.path.join(session_dir, f"{session_id}_audio.wav")

        self.stop_event.clear()
        self.current_session = {
            "session_id": session_id,
            "title": title or "Google Meet Session",
            "start_time": datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"),
            "start_epoch": time.time(),
            "fps": max(5, min(fps, 30)),
            "session_dir": session_dir,
            "frames_dir": frames_dir,
            "video_path": video_path,
            "audio_path": audio_path,
            "record_audio": record_audio,
            "frames_captured": 0,
            "key_frames": []
        }

        # Start Video Thread
        self.video_thread = threading.Thread(
            target=self._record_video_worker,
            args=(self.current_session,),
            daemon=True
        )
        self.video_thread.start()

        # Start Audio Thread if requested
        if record_audio:
            self.audio_thread = threading.Thread(
                target=self._record_audio_worker,
                args=(self.current_session,),
                daemon=True
            )
            self.audio_thread.start()

        self.is_recording = True

        return {
            "success": True,
            "message": f"🔴 Screen recording started! Session: '{title}'. Aria is now recording your screen and meeting audio.",
            "session_id": session_id,
            "video_path": video_path,
            "start_time": self.current_session["start_time"]
        }

    def _record_video_worker(self, session: Dict[str, Any]):
        """Background worker thread capturing screen frames using MSS and OpenCV."""
        ensure_desktop_attached()
        import cv2
        import mss

        target_fps = session.get("fps", 10)
        frame_interval = 1.0 / target_fps
        video_path = session.get("video_path")
        frames_dir = session.get("frames_dir")

        out = None
        key_frames = []
        last_keyframe_time = 0.0

        try:
            with mss.MSS() as sct:
                mon = sct.monitors[1]
                w, h = mon["width"], mon["height"]

                # Prefer mp4v codec for MP4
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(video_path, fourcc, float(target_fps), (w, h))
                if not out.isOpened():
                    # Fallback to XVID / AVI if mp4v fails
                    video_path = video_path.replace(".mp4", ".avi")
                    session["video_path"] = video_path
                    fourcc = cv2.VideoWriter_fourcc(*'XVID')
                    out = cv2.VideoWriter(video_path, fourcc, float(target_fps), (w, h))

                MAX_RECORDING_SECONDS = 7200  # 2-hour hard safety cutoff
                while not self.stop_event.is_set():
                    loop_start = time.time()
                    if (loop_start - session.get("start_epoch", loop_start)) > MAX_RECORDING_SECONDS:
                        print("[AriaScreenRecorder] ⚠️ Hard safety limit reached (2 hours). Stopping recording to protect disk space.")
                        self.stop_event.set()
                        break
                    try:
                        raw_frame = np.array(sct.grab(mon))
                        bgr = cv2.cvtColor(raw_frame, cv2.COLOR_BGRA2BGR)
                        out.write(bgr)
                        frame_idx += 1
                        session["frames_captured"] = frame_idx

                        # Save a key slide / frame every 20 seconds or initial frame
                        if loop_start - last_keyframe_time >= 20.0 or frame_idx == 1:
                            kf_filename = f"frame_{len(key_frames)+1:03d}_{int(loop_start - session['start_epoch'])}s.jpg"
                            kf_path = os.path.join(frames_dir, kf_filename)
                            cv2.imwrite(kf_path, bgr, [cv2.IMWRITE_JPEG_QUALITY, 85])
                            key_frames.append(kf_path)
                            last_keyframe_time = loop_start
                    except Exception as fe:
                        # Graceful handling if individual frame fails
                        time.sleep(0.05)

                    # Maintain target frame rate
                    elapsed = time.time() - loop_start
                    sleep_dur = frame_interval - elapsed
                    if sleep_dur > 0:
                        time.sleep(sleep_dur)

        except Exception as e:
            print(f"[AriaScreenRecorder] Video recording error: {e}")
        finally:
            if out is not None:
                try:
                    out.release()
                except Exception:
                    pass
            session["key_frames"] = key_frames

    def _record_audio_worker(self, session: Dict[str, Any]):
        """Background worker thread capturing microphone / system audio."""
        import wave
        audio_path = session.get("audio_path")
        sample_rate = 16000
        channels = 1
        chunk_size = 1024

        frames = []
        p = None
        stream = None

        try:
            import pyaudio
            p = pyaudio.PyAudio()
            dev_idx = None
            try:
                def_info = p.get_default_input_device_info()
                dev_idx = def_info.get("index")
            except Exception:
                dev_idx = None

            stream = p.open(
                format=pyaudio.paInt16,
                channels=channels,
                rate=sample_rate,
                input=True,
                input_device_index=dev_idx,
                frames_per_buffer=chunk_size
            )

            while not self.stop_event.is_set():
                try:
                    data = stream.read(chunk_size, exception_on_overflow=False)
                    frames.append(data)
                except Exception:
                    time.sleep(0.02)

        except Exception as e:
            print(f"[AriaScreenRecorder] PyAudio notice (will try sounddevice or save silent audio): {e}")
            # Try sounddevice fallback if pyaudio failed
            try:
                import sounddevice as sd
                sd_frames = []
                def sd_callback(indata, frames_cnt, time_info, status):
                    if not self.stop_event.is_set():
                        sd_frames.append(indata.copy())

                with sd.InputStream(samplerate=sample_rate, channels=channels, dtype='int16', callback=sd_callback):
                    while not self.stop_event.is_set():
                        time.sleep(0.1)

                if sd_frames:
                    frames = [f.tobytes() for f in sd_frames]
            except Exception as sde:
                print(f"[AriaScreenRecorder] Sounddevice fallback notice: {sde}")

        finally:
            if stream:
                try:
                    stream.stop_stream()
                    stream.close()
                except Exception:
                    pass
            if p:
                try:
                    p.terminate()
                except Exception:
                    pass

            # Write WAV file
            try:
                with wave.open(audio_path, 'wb') as wf:
                    wf.setnchannels(channels)
                    wf.setsampwidth(2)
                    wf.setframerate(sample_rate)
                    wf.writeframes(b''.join(frames))
            except Exception as we:
                print(f"[AriaScreenRecorder] Error writing audio WAV: {we}")

    def stop_recording(self) -> Dict[str, Any]:
        """Stops the active recording session, finalizes media, and saves manifest."""
        if not self.is_recording or not self.current_session:
            return {
                "success": False,
                "message": "No screen recording is currently active."
            }

        self.stop_event.set()

        # Join worker threads
        if self.video_thread and self.video_thread.is_alive():
            self.video_thread.join(timeout=3.0)
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=3.0)

        self.is_recording = False
        session = self.current_session
        self.current_session = None

        end_epoch = time.time()
        duration = round(end_epoch - session.get("start_epoch", end_epoch), 1)
        mins = int(duration // 60)
        secs = int(duration % 60)
        duration_fmt = f"{mins:02d}:{secs:02d}"

        video_path = session.get("video_path", "")
        audio_path = session.get("audio_path", "")
        video_size = os.path.getsize(video_path) if os.path.exists(video_path) else 0
        audio_size = os.path.getsize(audio_path) if os.path.exists(audio_path) else 0

        # Sample extra keyframes if needed
        key_frames = session.get("key_frames", [])
        if not key_frames and os.path.exists(video_path):
            key_frames = self._extract_keyframes_from_video(video_path, session.get("frames_dir", ""))
            session["key_frames"] = key_frames

        # Manifest
        manifest = {
            "session_id": session.get("session_id"),
            "title": session.get("title"),
            "start_time": session.get("start_time"),
            "end_time": datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"),
            "duration_seconds": duration,
            "duration_formatted": duration_fmt,
            "fps": session.get("fps"),
            "frames_captured": session.get("frames_captured", 0),
            "video_path": video_path,
            "audio_path": audio_path,
            "video_size_mb": round(video_size / (1024 * 1024), 2),
            "audio_size_mb": round(audio_size / (1024 * 1024), 2),
            "key_frames": key_frames,
            "notes_generated": False,
            "notes_file": None
        }

        manifest_path = os.path.join(session.get("session_dir", RECORDINGS_DIR), "metadata.json")
        try:
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
        except Exception as me:
            print(f"[AriaScreenRecorder] Manifest write notice: {me}")

        self.last_completed_session = manifest

        return {
            "success": True,
            "message": f"⏹️ Recording stopped and saved successfully!\n"
                       f"• Title: {manifest['title']}\n"
                       f"• Duration: {duration_fmt} ({duration}s)\n"
                       f"• Frames Captured: {manifest['frames_captured']}\n"
                       f"• Video: {os.path.basename(video_path)} ({manifest['video_size_mb']} MB)\n"
                       f"• Audio: {os.path.basename(audio_path)} ({manifest['audio_size_mb']} MB)\n"
                       f"• Key Slides/Frames Extracted: {len(key_frames)}\n"
                       f"Ready for analysis! Say 'Aria, generate meeting notes' to create your perfect notes.",
            "session": manifest
        }

    def _extract_keyframes_from_video(self, video_path: str, output_dir: str, num_frames: int = 5) -> List[str]:
        """Extracts evenly spaced frames from recorded video."""
        import cv2
        keyframes = []
        if not os.path.exists(video_path):
            return keyframes

        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            cap.release()
            return keyframes

        step = max(1, total_frames // (num_frames + 1))
        indices = [step * (i + 1) for i in range(num_frames) if step * (i + 1) < total_frames]

        for i, idx in enumerate(indices):
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                kf_path = os.path.join(output_dir, f"extracted_frame_{i+1:02d}.jpg")
                cv2.imwrite(kf_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                keyframes.append(kf_path)

        cap.release()
        return keyframes

    def list_all_recordings(self) -> List[Dict[str, Any]]:
        """Lists all stored recording sessions with metadata."""
        recordings = []
        if not os.path.exists(RECORDINGS_DIR):
            return recordings

        for item in sorted(os.listdir(RECORDINGS_DIR), reverse=True):
            session_dir = os.path.join(RECORDINGS_DIR, item)
            if not os.path.isdir(session_dir):
                continue
            meta_file = os.path.join(session_dir, "metadata.json")
            if os.path.exists(meta_file):
                try:
                    with open(meta_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        recordings.append(data)
                except Exception:
                    pass
            else:
                # Find any mp4/avi
                files = os.listdir(session_dir)
                vid = next((os.path.join(session_dir, f) for f in files if f.endswith((".mp4", ".avi"))), None)
                if vid:
                    recordings.append({
                        "session_id": item,
                        "title": item,
                        "video_path": vid,
                        "session_dir": session_dir,
                        "notes_generated": any(f.endswith(".md") for f in files)
                    })
        return recordings


# ─────────────────────────────────────────────────────────────────────────────
# 3. MULTIMODAL MEETING ANALYZER & PERFECT NOTES GENERATOR
# ─────────────────────────────────────────────────────────────────────────────
class AriaMeetingAnalyzer:
    @staticmethod
    def transcribe_audio(audio_path: str) -> str:
        """Transcribes meeting audio using Whisper model or returns fallback text."""
        if not audio_path or not os.path.exists(audio_path) or os.path.getsize(audio_path) < 1000:
            return "[No audio recorded or audio track was silent.]"

        # 1. Try Whisper
        try:
            import whisper
            print(f"[MeetingAnalyzer] Transcribing audio with Whisper: {os.path.basename(audio_path)}...")
            model = whisper.load_model("tiny")
            result = model.transcribe(audio_path, fp16=False)
            text = result.get("text", "").strip()
            if text:
                return text
        except Exception as we:
            print(f"[MeetingAnalyzer] Whisper transcription notice: {we}")

        return "[Spoken audio transcription could not be completed; visual frame analysis will be prioritized.]"

    @classmethod
    def analyze_recording(cls, session_id_or_path: str = "", query: str = "") -> str:
        """Analyzes a recorded session (visual frames + transcript) and answers questions."""
        recorder = AriaScreenRecorder()
        meta = cls._resolve_session_manifest(session_id_or_path)
        if not meta:
            return "No recording found to analyze. Please specify a recording path or record your screen first."

        transcript = cls.transcribe_audio(meta.get("audio_path", ""))
        key_frames = meta.get("key_frames", [])

        # Call Gemini with visual frames & transcript
        prompt = (
            f"You are Aria, an elite executive AI companion.\n"
            f"You are analyzing a recorded Google Meet or screen presentation:\n"
            f"Meeting Title: {meta.get('title', 'Meeting')}\n"
            f"Recorded Duration: {meta.get('duration_formatted', 'N/A')}\n\n"
            f"Audio Transcript:\n{transcript}\n\n"
            f"User Question / Analysis Request:\n{query or 'Provide a comprehensive overview of what was discussed, what was shown on the screen, and key takeaways.'}\n\n"
            f"Synthesize your findings concisely, accurately, and helpfully."
        )

        reply = cls._call_multimodal_gemini(prompt=prompt, image_paths=key_frames)
        return reply

    @classmethod
    def generate_meeting_notes(cls, session_id_or_path: str = "", meeting_title: str = "", output_dir: str = "") -> Dict[str, Any]:
        """
        Creates the 'Perfect Meeting Notes' from the recorded screen session:
        - Executive Summary
        - Detailed Discussion Points & Technical Agenda
        - Visual & Presentation Highlights (what was on slides/screens)
        - Action Items & To-Dos (with owners/urgency)
        - Key Decisions Made
        - Follow-up Questions & Next Steps
        Saves to Desktop / Documents and opens for user review.
        """
        meta = cls._resolve_session_manifest(session_id_or_path)
        if not meta:
            return {
                "success": False,
                "message": "No recording found to generate notes from. Please record a meeting first."
            }

        title = meeting_title or meta.get("title", "Google Meet Session")
        duration_fmt = meta.get("duration_formatted", "N/A")
        date_str = meta.get("start_time", datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p"))

        print(f"[MeetingAnalyzer] Generating Perfect Notes for '{title}'...")
        transcript = cls.transcribe_audio(meta.get("audio_path", ""))
        key_frames = meta.get("key_frames", [])

        prompt = (
            f"You are Aria, the world's most capable AI chief of staff and meeting analyst.\n"
            f"Create the PERFECT, highly structured, professional meeting notes for this recorded Google Meet / screen session.\n\n"
            f"MEETING METADATA:\n"
            f"• Title: {title}\n"
            f"• Date/Time: {date_str}\n"
            f"• Duration: {duration_fmt}\n\n"
            f"AUDIO TRANSCRIPT:\n{transcript}\n\n"
            f"VISUAL CONTEXT:\n"
            f"You are also viewing {len(key_frames)} key screenshots/slides captured directly from the screen during this session.\n\n"
            f"INSTRUCTIONS:\n"
            f"Produce an immaculate, clean Markdown document with the following exact sections:\n"
            f"# 📌 Meeting Notes: {title}\n"
            f"> **Date:** {date_str} | **Duration:** {duration_fmt} | **Recorded & Analyzed by:** Aria AI\n\n"
            f"## 📋 1. Executive Summary\n"
            f"(2-3 clear, punchy sentences summarizing the core objective, outcome, and state of the discussion)\n\n"
            f"## 🎯 2. Agenda & Discussion Topics\n"
            f"(Deep-dive bullet points grouped logically by topic, extracting metrics, arguments, and technical points)\n\n"
            f"## 🖥️ 3. Visual & Presentation Highlights\n"
            f"(What was shown on screen: slides, code snippets, architecture diagrams, Google Chrome tabs, documents, or data)\n\n"
            f"## ✅ 4. Action Items & To-Dos\n"
            f"| Task / Action Item | Owner | Priority / Urgency | Status |\n"
            f"|---|---|---|---|\n"
            f"(Fill table with concrete action items derived from discussion or slides)\n\n"
            f"## 💡 5. Key Decisions & Consensus\n"
            f"(Agreements ratified, architectural or business decisions confirmed, or policies set)\n\n"
            f"## ❓ 6. Open Inquiries & Follow-Ups\n"
            f"(Questions left unresolved or scheduled for future review)\n\n"
            f"Format with pristine markdown, clean styling, and zero fluff."
        )

        notes_markdown = cls._call_multimodal_gemini(prompt=prompt, image_paths=key_frames)

        # Fallback notes structure if API was unreachable or offline
        if not notes_markdown or "error:" in notes_markdown.lower():
            notes_markdown = (
                f"# 📌 Meeting Notes: {title}\n"
                f"> **Date:** {date_str} | **Duration:** {duration_fmt} | **Recorded by:** Aria AI\n\n"
                f"## 📋 1. Executive Summary\n"
                f"Recorded session of '{title}' spanning {duration_fmt}. Key presentation frames and meeting audio were preserved.\n\n"
                f"## 🎯 2. Spoken Transcript Highlights\n"
                f"{transcript[:600]}...\n\n"
                f"## 🖥️ 3. Visual Highlights\n"
                f"Captured {len(key_frames)} key visual slides and frames in session archive.\n\n"
                f"## ✅ 4. Action Items\n"
                f"- [ ] Review recorded session archive and complete designated follow-ups.\n"
            )

        # Save notes to Desktop and Session Directory
        user_home = os.path.expandvars(r"%USERPROFILE%")
        target_dir = output_dir if output_dir and os.path.exists(output_dir) else os.path.join(user_home, "Desktop")
        clean_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', title)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        notes_filename = f"Meeting_Notes_{clean_name}_{timestamp}.md"
        desktop_notes_path = os.path.join(target_dir, notes_filename)

        # Write to desktop
        try:
            with open(desktop_notes_path, "w", encoding="utf-8") as f:
                f.write(notes_markdown)
        except Exception as e:
            desktop_notes_path = os.path.join(meta.get("session_dir", RECORDINGS_DIR), notes_filename)
            with open(desktop_notes_path, "w", encoding="utf-8") as f:
                f.write(notes_markdown)

        # Also write copy into session folder
        session_dir = meta.get("session_dir")
        if session_dir and os.path.exists(session_dir):
            try:
                with open(os.path.join(session_dir, "meeting_notes.md"), "w", encoding="utf-8") as f:
                    f.write(notes_markdown)
            except Exception:
                pass

        # Update metadata.json
        meta["notes_generated"] = True
        meta["notes_file"] = desktop_notes_path
        if session_dir:
            try:
                with open(os.path.join(session_dir, "metadata.json"), "w", encoding="utf-8") as f:
                    json.dump(meta, f, indent=2)
            except Exception:
                pass

        # Launch / open file for the user automatically
        try:
            os.startfile(desktop_notes_path)
        except Exception:
            pass

        return {
            "success": True,
            "message": f"✨ Perfect Meeting Notes created successfully!\n"
                       f"• File saved to: {desktop_notes_path}\n"
                       f"• Opened automatically on your Desktop for review.\n\n"
                       f"{notes_markdown[:400]}...",
            "notes_file": desktop_notes_path,
            "notes_content": notes_markdown
        }

    @staticmethod
    def _resolve_session_manifest(session_id_or_path: str = "") -> Optional[Dict[str, Any]]:
        """Resolves metadata dictionary from session ID, file path, or latest session."""
        recorder = AriaScreenRecorder()
        target = session_id_or_path.strip() if session_id_or_path else ""

        # 1. If explicit path provided
        if target and os.path.exists(target):
            if os.path.isdir(target):
                mf = os.path.join(target, "metadata.json")
                if os.path.exists(mf):
                    with open(mf, "r", encoding="utf-8") as f:
                        return json.load(f)
            elif target.endswith(".json"):
                with open(target, "r", encoding="utf-8") as f:
                    return json.load(f)
            elif target.endswith((".mp4", ".avi", ".wav")):
                sdir = os.path.dirname(target)
                mf = os.path.join(sdir, "metadata.json")
                if os.path.exists(mf):
                    with open(mf, "r", encoding="utf-8") as f:
                        return json.load(f)
                return {
                    "session_id": os.path.basename(sdir),
                    "title": os.path.basename(target),
                    "video_path": target if target.endswith((".mp4", ".avi")) else "",
                    "audio_path": target if target.endswith(".wav") else "",
                    "session_dir": sdir,
                    "key_frames": []
                }

        # 2. Check if it's a known session ID
        if target:
            candidate_dir = os.path.join(RECORDINGS_DIR, target)
            if os.path.exists(candidate_dir):
                mf = os.path.join(candidate_dir, "metadata.json")
                if os.path.exists(mf):
                    with open(mf, "r", encoding="utf-8") as f:
                        return json.load(f)

        # 3. Fallback to last completed session
        if recorder.last_completed_session:
            return recorder.last_completed_session

        # 4. Fallback to most recent folder in recordings dir
        all_recs = recorder.list_all_recordings()
        if all_recs:
            return all_recs[0]

        return None

    @staticmethod
    def _call_multimodal_gemini(prompt: str, image_paths: List[str] = None) -> str:
        """Sends prompt and images to Gemini 2.5 Flash / 2.0 Flash."""
        from dotenv import load_dotenv
        try:
            from core.paths import ENV_FILE
            load_dotenv(ENV_FILE)
        except Exception:
            pass

        gemini_key = os.environ.get("GEMINI_API_KEY", "")
        if not gemini_key or gemini_key == "your_gemini_api_key_here":
            return f"[Analysis Note]: Gemini API Key is not configured in .env. Here is your text summary:\n{prompt[:300]}..."

        try:
            from google import genai
            from google.genai import types
            from PIL import Image

            client = genai.Client(api_key=gemini_key)
            contents = []

            # Attach visual frames (up to 6 representative frames)
            if image_paths:
                for img_p in image_paths[:6]:
                    if os.path.exists(img_p):
                        try:
                            im = Image.open(img_p)
                            # Resize if wide
                            if im.width > 1280:
                                ratio = 1280.0 / im.width
                                im = im.resize((1280, int(im.height * ratio)), Image.Resampling.LANCZOS)
                            buf = io.BytesIO()
                            im.save(buf, format="JPEG", quality=80)
                            contents.append(types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg"))
                        except Exception as ie:
                            print(f"[MeetingAnalyzer] Error loading frame {img_p}: {ie}")

            contents.append(prompt)

            models_to_try = ["gemini-3.8-flash", "gemini-flash-latest", "gemini-3.1-flash-lite", "gemini-2.5-flash"]
            last_err = None
            for mod_name in models_to_try:
                try:
                    response = client.models.generate_content(
                        model=mod_name,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            max_output_tokens=3000,
                            temperature=0.3
                        )
                    )
                    if response and response.text:
                        return response.text.strip()
                except Exception as ex:
                    last_err = ex
                    continue

            return f"Multimodal analysis notice: {last_err}"
        except Exception as e:
            return f"Multimodal analysis error: {e}"


# ─────────────────────────────────────────────────────────────────────────────
# 4. PUBLIC CONVENIENCE FUNCTIONS FOR ARIA ADK & SYSTEM TOOLS
# ─────────────────────────────────────────────────────────────────────────────
_RECORDER = AriaScreenRecorder()

def start_screen_recording(title: str = "Google_Meet", fps: int = 10, record_audio: bool = True) -> str:
    """
    Start recording your computer screen and meeting audio (e.g. for Google Meets, Zoom, or presentations).
    Aria records quietly in the background while you focus on your call.
    """
    res = _RECORDER.start_recording(title=title, fps=fps, record_audio=record_audio)
    return res.get("message", "Screen recording command processed.")

def stop_screen_recording() -> str:
    """
    Stop the currently active screen recording session, finalize the video and audio,
    and prepare the meeting for analysis and notes generation.
    """
    res = _RECORDER.stop_recording()
    return res.get("message", "Screen recording stopped.")

def get_recording_status() -> str:
    """Check whether Aria is currently recording your screen, elapsed time, and session info."""
    stat = _RECORDER.get_status()
    if stat.get("recording"):
        return f"🔴 RECORDING IN PROGRESS:\n• Title: {stat.get('title')}\n• Elapsed: {stat.get('elapsed_formatted')} ({stat.get('elapsed_seconds')}s)\n• Target FPS: {stat.get('fps')}\n• Audio Enabled: {stat.get('record_audio')}"
    return f"⚪ IDLE: Aria is not currently recording. Say 'Aria, record my screen' to start."

def list_recordings() -> str:
    """List all past recorded screen & Google Meet sessions stored on this laptop."""
    recs = _RECORDER.list_all_recordings()
    if not recs:
        return "No screen recordings found in the Aria vault. Say 'Record my screen' to create your first one!"
    lines = [f"Found {len(recs)} past recording session(s):"]
    for r in recs[:10]:
        title = r.get("title", "Session")
        dur = r.get("duration_formatted", "N/A")
        date = r.get("start_time", "")
        notes = "📝 Notes Ready" if r.get("notes_generated") else "○ No Notes Yet"
        lines.append(f"• [{notes}] {title} ({dur}) — {date}")
    return "\n".join(lines)

def analyze_recording(recording_path: str = "", query: str = "") -> str:
    """
    Analyze a recorded Google Meet or screen recording by transcribing the audio
    and visually inspecting key presentation slides with Gemini.
    """
    return AriaMeetingAnalyzer.analyze_recording(session_id_or_path=recording_path, query=query)

def generate_meeting_notes(recording_path: str = "", meeting_title: str = "") -> str:
    """
    Generate comprehensive 'Perfect Meeting Notes' from your recorded Google Meet or screen session.
    Includes Executive Summary, Agenda Points, Visual Slide Highlights, Action Items Table,
    Key Decisions, and automatically saves and opens the markdown notes on your Desktop.
    """
    res = AriaMeetingAnalyzer.generate_meeting_notes(session_id_or_path=recording_path, meeting_title=meeting_title)
    return res.get("message", "Notes generated.")

def register_tool() -> tuple:
    """Dynamic tool auto-registration for Aria ADK."""
    return ("aria_screen_recorder", start_screen_recording)
