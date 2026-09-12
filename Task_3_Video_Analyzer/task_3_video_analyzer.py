from pathlib import Path
import cv2
from mutagen import File as MutagenFile
import json
import datetime


# Supported video extensions
SUPPORTED_EXTENSIONS = {
    ".mp4", ".mkv", ".avi", ".mov", ".wmv",
    ".flv", ".webm", ".m4v", ".mpeg", ".mpg",
    ".3gp", ".ts", ".mts", ".m2ts"
}

# Container format labels
CONTAINER_MAP = {
    ".mp4":  "MPEG-4 Container (.mp4)",
    ".mkv":  "Matroska Container (.mkv)",
    ".avi":  "AVI Container (.avi)",
    ".mov":  "QuickTime Container (.mov)",
    ".wmv":  "Windows Media Video (.wmv)",
    ".flv":  "Flash Video (.flv)",
    ".webm": "WebM Container (.webm)",
    ".m4v":  "iTunes Video (.m4v)",
    ".mpeg": "MPEG Container (.mpeg)",
    ".mpg":  "MPEG Container (.mpg)",
    ".3gp":  "3GPP Container (.3gp)",
    ".ts":   "MPEG Transport Stream (.ts)",
    ".mts":  "AVCHD Transport Stream (.mts)",
    ".m2ts": "Blu-ray Transport Stream (.m2ts)",
}

# Common video codec FourCC → human-readable name
VIDEO_CODEC_MAP = {
    "avc1": "H.264 / AVC",
    "h264": "H.264 / AVC",
    "hevc": "H.265 / HEVC",
    "hvc1": "H.265 / HEVC",
    "vp80": "VP8",
    "vp09": "VP9",
    "vp90": "VP9",
    "av01": "AV1",
    "xvid": "Xvid / MPEG-4",
    "divx": "DivX / MPEG-4",
    "mp4v": "MPEG-4 Visual",
    "theo": "Theora",
    "wmv3": "WMV3 / VC-1",
    "wmv2": "WMV2",
    "wmv1": "WMV1",
    "mjpg": "Motion JPEG",
    "flv1": "Flash Video (Sorenson H.263)",
    "dvsd": "DV (SD)",
    "raw ": "Raw / Uncompressed",
    "": "Unknown",
}

# Audio codec labels from mutagen format name
AUDIO_CODEC_MAP = {
    "MP3": "MP3 (MPEG Layer 3)",
    "FLAC": "FLAC (Lossless)",
    "AAC": "AAC (Advanced Audio Coding)",
    "MP4": "AAC (MPEG-4 Audio)",
    "OGG": "Vorbis (OGG)",
    "OPUS": "Opus",
    "WMA": "WMA (Windows Media Audio)",
    "AIFF": "AIFF (Lossless)",
    "WAV": "PCM / WAV",
    "WAVE": "PCM / WAV",
}


def get_file_info(video_path):
    path = Path(video_path)

    if not path.exists():
        raise FileNotFoundError("Video file does not exist.")

    if not path.is_file():
        raise ValueError("The given path is not a file.")

    ext = path.suffix.lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: '{ext}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    file_size = path.stat().st_size

    return {
        "file_name": path.name,
        "file_size_bytes": file_size,
        "file_size_kb": round(file_size / 1024, 2),
        "file_size_mb": round(file_size / (1024 * 1024), 2),
        "file_extension": ext,
        "container": CONTAINER_MAP.get(ext, f"Unknown ({ext})")
    }


def format_duration(seconds):
    if seconds is None or seconds <= 0:
        return "Unknown"

    total = int(seconds)
    hours = total // 3600
    minutes = (total % 3600) // 60
    secs = total % 60

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    return f"{minutes:02d}:{secs:02d}"


def decode_fourcc(fourcc_int):
    try:
        chars = []

        for _ in range(4):
            chars.append(chr(fourcc_int & 0xFF))
            fourcc_int >>= 8

        return "".join(chars).lower().strip()

    except Exception:
        return ""


def get_channel_label(channels):
    if channels is None:
        return "Unknown"

    channel_map = {
        1: "Mono",
        2: "Stereo",
        6: "5.1 Surround",
        8: "7.1 Surround"
    }

    return channel_map.get(int(channels), f"{channels} channels")


def estimate_resolution_quality(height):
    if height is None or height == 0:
        return "Unknown"

    if height >= 2160:
        return "4K / UHD"
    elif height >= 1440:
        return "1440p / 2K"
    elif height >= 1080:
        return "1080p / Full HD"
    elif height >= 720:
        return "720p / HD"
    elif height >= 480:
        return "480p / SD"
    else:
        return f"Low Resolution ({height}p)"


def get_video_stream_info(cap, file_size_bytes):
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc_int = int(cap.get(cv2.CAP_PROP_FOURCC))
    bitrate_raw = cap.get(cv2.CAP_PROP_BITRATE)

    # Duration
    duration_s = None

    if fps and fps > 0 and frame_count and frame_count > 0:
        duration_s = round(frame_count / fps, 2)

    # Codec label
    fourcc_code = decode_fourcc(fourcc_int)
    codec = VIDEO_CODEC_MAP.get(
        fourcc_code,
        fourcc_code.upper() if fourcc_code else "Unknown"
    )

    # Resolution
    resolution = f"{width} x {height}" if (width and height) else "Unknown"

    # Frame rate
    fps_display = f"{round(fps, 3)} fps" if fps else "Unknown"

    # Bitrate
    bitrate_kbps = None

    if bitrate_raw and bitrate_raw > 0:
        # cv2 returns bits/sec from CAP_PROP_BITRATE
        bitrate_kbps = round(bitrate_raw / 1000, 1)
    elif duration_s and duration_s > 0 and file_size_bytes:
        # Estimate overall bitrate from file size
        bitrate_kbps = round(
            (file_size_bytes * 8) / (duration_s * 1000),
            1
        )

    return {
        "width": width,
        "height": height,
        "resolution": resolution,
        "frame_rate": round(fps, 3) if fps else None,
        "frame_rate_display": fps_display,
        "frame_count": int(frame_count) if frame_count else None,
        "codec_fourcc": fourcc_code.upper(),
        "codec": codec,
        "bitrate_kbps": bitrate_kbps,
        "duration_seconds": duration_s,
        "duration_formatted": format_duration(duration_s),
        "resolution_quality": estimate_resolution_quality(height)
    }


def get_audio_stream_info(audio_path):
    """
    Extract audio stream properties from the video container
    using mutagen, which can read audio tracks embedded in
    MP4 / M4A / MKV and standalone audio formats.
    """
    try:
        audio = MutagenFile(str(audio_path))

        if audio is None or not hasattr(audio, "info"):
            return None

        info = audio.info

        sample_rate = getattr(info, "sample_rate", None)
        channels = getattr(info, "channels", None)
        # mutagen returns bitrate in bps for all formats
        bitrate_bps = getattr(info, "bitrate", None)

        # Identify codec from mutagen type
        codec_type = type(audio).__name__.upper()
        codec = AUDIO_CODEC_MAP.get(codec_type, codec_type)

        bitrate_kbps = (
            round(int(bitrate_bps) / 1000, 1)
            if bitrate_bps else None
        )

        return {
            "codec": codec,
            "channels": channels,
            "channel_label": get_channel_label(channels) if channels else "Unknown",
            "sample_rate_hz": sample_rate,
            "sample_rate_khz": (
                round(int(sample_rate) / 1000, 1)
                if sample_rate else None
            ),
            "bitrate_bps": bitrate_bps,
            "bitrate_kbps": bitrate_kbps
        }

    except Exception:
        return None


def get_container_metadata(video_path):
    path = Path(video_path)
    stat = path.stat()

    metadata = {}

    created = datetime.datetime.fromtimestamp(
        stat.st_ctime
    ).strftime("%Y-%m-%d %H:%M:%S")

    modified = datetime.datetime.fromtimestamp(
        stat.st_mtime
    ).strftime("%Y-%m-%d %H:%M:%S")

    metadata["File Created"] = created
    metadata["File Modified"] = modified

    # Try mutagen easy tags for embedded title, artist etc.
    try:
        audio = MutagenFile(str(video_path), easy=True)

        if audio:
            tag_map = {
                "title": "Title",
                "artist": "Artist",
                "album": "Album",
                "date": "Year",
                "genre": "Genre",
                "comment": "Comment",
                "encoder": "Encoder",
                "copyright": "Copyright",
            }

            for key, label in tag_map.items():
                value = audio.get(key)

                if value:
                    if isinstance(value, list):
                        metadata[label] = ", ".join(str(v) for v in value)
                    else:
                        metadata[label] = str(value)

    except Exception:
        pass

    return metadata


def analyze_video(video_path):
    path = Path(video_path)

    print("\nAnalyzing video...")

    file_info = get_file_info(path)

    print("Opening video stream...")

    cap = cv2.VideoCapture(str(path))

    if not cap.isOpened():
        raise ValueError(
            "Cannot open video file. "
            "The file may be corrupt or use an unsupported codec."
        )

    try:
        print("Extracting video stream properties...")

        video_info = get_video_stream_info(
            cap,
            file_info["file_size_bytes"]
        )

    finally:
        cap.release()

    print("Extracting audio stream properties...")

    audio_info = get_audio_stream_info(path)

    print("Reading container metadata...")

    metadata = get_container_metadata(path)

    report = {
        "file_information": file_info,
        "video": video_info,
        "audio": audio_info,
        "metadata": metadata
    }

    return report


def save_report(report):
    reports_folder = Path("reports")
    reports_folder.mkdir(exist_ok=True)

    report_path = reports_folder / "video_report.json"

    with open(
        report_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            report,
            file,
            indent=4,
            ensure_ascii=False
        )

    return report_path


def print_report(report):
    file_info = report["file_information"]
    video = report["video"]
    audio = report["audio"]
    metadata = report["metadata"]

    print("\n")
    print("=" * 55)
    print("          VIDEO METADATA REPORT")
    print("=" * 55)

    print(f"\n{'File Name':<16}: {file_info['file_name']}")
    print(f"{'File Size':<16}: {file_info['file_size_mb']} MB")
    print(f"{'Container':<16}: {file_info['container']}")
    print(f"{'Duration':<16}: {video['duration_formatted']}")

    print("\nVIDEO")
    print("-" * 55)

    print(f"{'Resolution':<16}: {video['resolution']}")
    print(f"{'Frame Rate':<16}: {video['frame_rate_display']}")

    bitrate_str = (
        f"{video['bitrate_kbps']} kbps"
        if video.get("bitrate_kbps")
        else "Unknown"
    )

    print(f"{'Bit Rate':<16}: {bitrate_str}")
    print(f"{'Codec':<16}: {video['codec']}")

    print("\nAUDIO")
    print("-" * 55)

    if audio:
        print(f"{'Codec':<16}: {audio.get('codec', 'Unknown')}")
        ch = audio.get("channels")
        cl = audio.get("channel_label", "Unknown")
        print(f"{'Channels':<16}: {ch} ({cl})" if ch else f"{'Channels':<16}: Unknown")

        sr = audio.get("sample_rate_khz")
        print(
            f"{'Sampling Rate':<16}: {sr} kHz"
            if sr else f"{'Sampling Rate':<16}: Unknown"
        )

        abr = audio.get("bitrate_kbps")
        print(
            f"{'Bit Rate':<16}: {abr} kbps"
            if abr else f"{'Bit Rate':<16}: Unknown"
        )

    else:
        print(f"{'Codec':<16}: Not detected")
        print(f"{'Channels':<16}: N/A")
        print(f"{'Sampling Rate':<16}: N/A")
        print(f"{'Bit Rate':<16}: N/A")

    print("\nMETADATA")
    print("-" * 55)

    if metadata:
        for key, value in metadata.items():
            print(f"{key:<16}: {value}")
    else:
        print("No embedded metadata found.")

    print("\n" + "=" * 55)


def main():

    print("=" * 55)
    print("          MULTIMEDIA ANALYZER - VIDEO")
    print("=" * 55)

    video_path = input(
        "\nEnter video file path: "
    ).strip()

    try:

        report = analyze_video(video_path)

        print_report(report)

        report_path = save_report(report)

        print(
            f"\nReport saved to: {report_path}"
        )

    except FileNotFoundError as error:
        print(f"\nError: {error}")

    except ValueError as error:
        print(f"\nError: {error}")

    except Exception as error:
        print(f"\nUnexpected error: {error}")


if __name__ == "__main__":
    main()
