import os
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory


def _run_command(command: list[str]) -> None:
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise RuntimeError("Required binary is missing. Make sure ffmpeg is installed.") from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() if exc.stderr else "Unknown ffmpeg error"
        raise RuntimeError(stderr) from exc


def convert_to_mp4(input_path: str, output_path: str) -> str:
    _run_command(
        [
            "ffmpeg",
            "-y",
            "-i",
            input_path,
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "23",
            "-c:a",
            "aac",
            output_path,
        ]
    )
    return output_path


def process_video_mock(input_path: str, output_path: str, progress_callback) -> None:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    for value in (10, 30, 55, 80):
        progress_callback(value)
    shutil.copyfile(input_path, output_path)
    progress_callback(100)


def process_video_real(input_path: str, output_path: str, progress_callback) -> None:
    import cv2
    import mediapipe as mp
    import numpy as np
    from scipy.ndimage import gaussian_filter1d

    def safe_crop_resize(
        frame: "np.ndarray", cx: float, cy: float, crop_w: int, crop_h: int, out_w: int, out_h: int
    ) -> "np.ndarray":
        frame_height, frame_width = frame.shape[:2]

        target_aspect_ratio = out_w / out_h
        crop_aspect_ratio = crop_w / crop_h if crop_h > 0 else target_aspect_ratio

        if crop_aspect_ratio > target_aspect_ratio:
            crop_w = int(crop_h * target_aspect_ratio)
        else:
            crop_h = int(crop_w / target_aspect_ratio)

        crop_w = min(frame_width, crop_w)
        crop_h = min(frame_height, crop_h)

        x1 = int(np.clip(cx - crop_w / 2, 0, frame_width - crop_w))
        y1 = int(np.clip(cy - crop_h / 2, 0, frame_height - crop_h))
        x2 = x1 + crop_w
        y2 = y1 + crop_h

        cropped = frame[y1:y2, x1:x2]
        if cropped.size == 0:
            cropped = frame

        return cv2.resize(cropped, (out_w, out_h), interpolation=cv2.INTER_CUBIC)

    def merge_audio(video_path: str, original_input_path: str, final_path: str) -> str:
        _run_command(
            [
                "ffmpeg",
                "-y",
                "-i",
                video_path,
                "-i",
                original_input_path,
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-map",
                "0:v:0",
                "-map",
                "1:a:0?",
                "-shortest",
                "-movflags",
                "+faststart",
                final_path,
            ]
        )
        return final_path

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    progress_callback(2)

    with TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        clean_input_path = temp_root / f"{Path(input_path).stem}_clean.mp4"
        intermediate_output_path = temp_root / "tracked_video.mp4"

        progress_callback(5)
        converted_input = convert_to_mp4(input_path, str(clean_input_path))

        target_ratio = 9 / 16
        smoothing_sigma = 2.5
        base_zoom_factor = 1.2
        min_crop_scale = 0.70
        max_crop_scale = 0.95
        zoom_smooth_multiplier = 3.0
        padding_top = 0.18

        face_detection = mp.solutions.face_detection.FaceDetection(
            model_selection=1,
            min_detection_confidence=0.45,
        )

        capture = cv2.VideoCapture(converted_input)
        if not capture.isOpened():
            face_detection.close()
            raise FileNotFoundError(f"Cannot open: {converted_input}")

        frame_width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
        output_width = int(frame_height * (9 / 16))
        output_height = frame_height
        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT)) or 1

        raw_data: list[list[float]] = []
        last_valid = [frame_width / 2, frame_height / 2, frame_width * 0.15]

        processed_analysis_frames = 0
        while capture.isOpened():
            success, frame = capture.read()
            if not success:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_detection.process(rgb)

            if results.detections:
                bbox = results.detections[0].location_data.relative_bounding_box
                xmin = max(0.0, bbox.xmin)
                ymin = max(0.0, bbox.ymin)
                box_width = min(bbox.width, 1.0 - xmin)
                box_height = min(bbox.height, 1.0 - ymin)

                center_x = (xmin + box_width / 2) * frame_width
                center_y = (ymin + box_height / 2) * frame_height - (box_height * frame_height * padding_top)
                face_width = box_width * frame_width

                last_valid = [center_x, center_y, face_width]

            raw_data.append(last_valid.copy())
            processed_analysis_frames += 1

            progress_callback(5 + int((processed_analysis_frames / total_frames) * 30))

        if not raw_data:
            capture.release()
            face_detection.close()
            raise RuntimeError("No frames were read from the uploaded video.")

        raw_array = np.array(raw_data)

        progress_callback(40)
        smooth_x = gaussian_filter1d(raw_array[:, 0], sigma=smoothing_sigma)
        smooth_y = gaussian_filter1d(raw_array[:, 1], sigma=smoothing_sigma)
        smooth_face_width = gaussian_filter1d(
            raw_array[:, 2], sigma=smoothing_sigma * zoom_smooth_multiplier
        )

        warmup_frames = int(fps * 2)
        if len(smooth_x) > warmup_frames:
            smooth_x[:warmup_frames] = smooth_x[warmup_frames]
            smooth_y[:warmup_frames] = smooth_y[warmup_frames]
            smooth_face_width[:warmup_frames] = smooth_face_width[warmup_frames]

        capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(intermediate_output_path), fourcc, fps, (output_width, output_height))

        min_crop_height = int(frame_height * min_crop_scale)
        max_crop_height = int(frame_height * max_crop_scale)

        for index in range(len(smooth_x)):
            success, frame = capture.read()
            if not success:
                break

            raw_crop_height = int(smooth_face_width[index] * base_zoom_factor / target_ratio)
            raw_crop_height = int(raw_crop_height * 2)

            crop_height = int(np.clip(raw_crop_height, min_crop_height, max_crop_height))
            crop_width = int(crop_height * target_ratio)

            final_frame = safe_crop_resize(
                frame,
                cx=smooth_x[index],
                cy=smooth_y[index],
                crop_w=crop_width,
                crop_h=crop_height,
                out_w=output_width,
                out_h=output_height,
            )
            writer.write(final_frame)
            progress_callback(45 + int(((index + 1) / len(smooth_x)) * 45))

        capture.release()
        writer.release()
        face_detection.close()

        progress_callback(92)
        merge_audio(str(intermediate_output_path), converted_input, str(destination))
        progress_callback(100)


def process_video(input_path: str, output_path: str, progress_callback) -> None:
    processor_mode = os.getenv("PROCESSOR_MODE", "mock").lower()
    if processor_mode == "mock":
        process_video_mock(input_path, output_path, progress_callback)
        return

    try:
        process_video_real(input_path, output_path, progress_callback)
    except ModuleNotFoundError as exc:
        missing_module = exc.name or "unknown dependency"
        raise RuntimeError(
            f"Real processor dependencies are missing: {missing_module}. "
            "Use PROCESSOR_MODE=mock for lightweight testing or install the real CV stack."
        ) from exc
    except RuntimeError:
        raise
