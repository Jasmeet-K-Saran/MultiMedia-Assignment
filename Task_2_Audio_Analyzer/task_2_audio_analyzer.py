from pathlib import Path
from mutagen import File as MutagenFile
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.wave import WAVE
from mutagen.oggvorbis import OggVorbis
import json


# Supported audio extensions
SUPPORTED_EXTENSIONS = {
    ".mp3", ".flac", ".wav", ".ogg", ".m4a", ".aac",
    ".wma", ".aiff", ".aif", ".opus"
}


def get_file_info(audio_path):
    path = Path(audio_path)

    if not path.exists():
        raise FileNotFoundError("Audio file does not exist.")

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
        "file_extension": ext
    }


def format_duration(seconds):
    if seconds is None:
        return "Unknown"

    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    return f"{minutes:02d}:{secs:02d}"


def get_channel_label(channels):
    if channels is None:
        return "Unknown"

    channel_map = {
        1: "Mono",
        2: "Stereo",
        6: "5.1 Surround",
        8: "7.1 Surround"
    }

    return channel_map.get(channels, f"{channels} channels")


def get_audio_properties(audio_path):
    path = Path(audio_path)
    ext = path.suffix.lower()

    duration = None
    sample_rate = None
    channels = None
    bitrate = None
    codec = None

    try:
        if ext == ".mp3":
            audio = MP3(str(path))
            info = audio.info
            duration = info.length
            sample_rate = info.sample_rate
            channels = info.channels
            bitrate = info.bitrate
            codec = "MP3"

        elif ext == ".flac":
            audio = FLAC(str(path))
            info = audio.info
            duration = info.length
            sample_rate = info.sample_rate
            channels = info.channels
            bitrate = info.bits_per_sample * info.sample_rate * info.channels
            codec = "FLAC"

        elif ext == ".wav":
            audio = WAVE(str(path))
            info = audio.info
            duration = info.length
            sample_rate = info.sample_rate
            channels = info.channels
            bitrate = info.bits_per_sample * info.sample_rate * info.channels
            codec = "PCM/WAV"

        elif ext in (".m4a", ".aac"):
            audio = MP4(str(path))
            info = audio.info
            duration = info.length
            sample_rate = info.sample_rate
            channels = info.channels
            bitrate = info.bitrate
            codec = "AAC"

        elif ext == ".ogg":
            audio = OggVorbis(str(path))
            info = audio.info
            duration = info.length
            sample_rate = info.sample_rate
            channels = info.channels
            bitrate = info.bitrate
            codec = "Vorbis"

        else:
            # Generic fallback using MutagenFile
            audio = MutagenFile(str(path))

            if audio and hasattr(audio, "info"):
                info = audio.info
                duration = getattr(info, "length", None)
                sample_rate = getattr(info, "sample_rate", None)
                channels = getattr(info, "channels", None)
                bitrate = getattr(info, "bitrate", None)
                codec = type(audio).__name__

    except Exception as error:
        raise ValueError(f"Failed to read audio properties: {error}")

    return {
        "duration_seconds": round(duration, 2) if duration else None,
        "duration_formatted": format_duration(duration),
        "sample_rate_hz": sample_rate,
        "sample_rate_khz": round(sample_rate / 1000, 1) if sample_rate else None,
        "channels": channels,
        "channel_label": get_channel_label(channels),
        "bitrate_bps": bitrate,
        "bitrate_kbps": round(bitrate / 1000, 1) if bitrate else None,
        "codec": codec
    }


def get_metadata_tags(audio_path):
    path = Path(audio_path)
    ext = path.suffix.lower()
    tags = {}

    try:
        audio = MutagenFile(str(path), easy=True)

        if audio is None:
            return tags

        tag_map = {
            "title": "Title",
            "artist": "Artist",
            "album": "Album",
            "albumartist": "Album Artist",
            "date": "Year",
            "genre": "Genre",
            "tracknumber": "Track Number",
            "discnumber": "Disc Number",
            "comment": "Comment",
            "composer": "Composer",
            "copyright": "Copyright",
            "encoder": "Encoder",
            "language": "Language",
        }

        for key, label in tag_map.items():
            value = audio.get(key)

            if value:
                if isinstance(value, list):
                    tags[label] = ", ".join(str(v) for v in value)
                else:
                    tags[label] = str(value)

    except Exception:
        pass

    return tags


def classify_audio(properties):
    bitrate = properties.get("bitrate_kbps")
    channels = properties.get("channels")
    sample_rate = properties.get("sample_rate_hz")
    codec = properties.get("codec", "")

    quality_label = "Unknown"

    if bitrate:
        if bitrate >= 320:
            quality_label = "High Quality"
        elif bitrate >= 192:
            quality_label = "Good Quality"
        elif bitrate >= 128:
            quality_label = "Standard Quality"
        else:
            quality_label = "Low Quality"

    elif sample_rate:
        if sample_rate >= 44100:
            quality_label = "CD Quality or above"
        else:
            quality_label = "Below CD Quality"

    channel_label = properties.get("channel_label", "Unknown")

    lossless = codec in ("FLAC", "PCM/WAV", "ALAC")

    return {
        "quality": quality_label,
        "lossless": lossless,
        "audio_type": "Lossless" if lossless else "Lossy"
    }


def analyze_audio(audio_path):
    path = Path(audio_path)

    print("\nAnalyzing audio...")

    file_info = get_file_info(path)

    print("Extracting audio properties...")

    properties = get_audio_properties(path)

    print("Reading metadata tags...")

    metadata = get_metadata_tags(path)

    print("Classifying audio quality...")

    classification = classify_audio(properties)

    report = {
        "file_information": file_info,
        "audio_properties": properties,
        "classification": classification,
        "metadata": metadata
    }

    return report


def save_report(report):
    reports_folder = Path("reports")
    reports_folder.mkdir(exist_ok=True)

    report_path = reports_folder / "audio_report.json"

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
    props = report["audio_properties"]
    classification = report["classification"]
    metadata = report["metadata"]

    print("\n")
    print("=" * 55)
    print("          AUDIO METADATA REPORT")
    print("=" * 55)

    print(f"\n{'File Name':<16}: {file_info['file_name']}")
    print(f"{'File Size':<16}: {file_info['file_size_kb']} KB")
    print(f"{'Container':<16}: {file_info['file_extension'].upper().lstrip('.')}")
    print(f"{'Duration':<16}: {props['duration_formatted']}")

    print("\nAUDIO")
    print("-" * 55)

    print(f"{'Codec':<16}: {props['codec'] or 'Unknown'}")
    print(f"{'Channels':<16}: {props['channels']} ({props['channel_label']})")
    print(f"{'Sampling Rate':<16}: {props['sample_rate_khz']} kHz")
    print(f"{'Bit Rate':<16}: {props['bitrate_kbps']} kbps")

    print("\nQUALITY")
    print("-" * 55)

    print(f"{'Audio Type':<16}: {classification['audio_type']}")
    print(f"{'Quality':<16}: {classification['quality']}")
    print(f"{'Lossless':<16}: {'Yes' if classification['lossless'] else 'No'}")

    if metadata:
        print("\nMETADATA")
        print("-" * 55)

        for key, value in metadata.items():
            print(f"{key:<16}: {value}")

    print("\n" + "=" * 55)


def main():

    print("=" * 55)
    print("          MULTIMEDIA ANALYZER - AUDIO")
    print("=" * 55)

    audio_path = input(
        "\nEnter audio file path: "
    ).strip()

    try:

        report = analyze_audio(audio_path)

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
