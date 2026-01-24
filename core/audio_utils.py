# core/audio_utils.py
"""
Audio utility functions
"""
import mutagen
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.ogg import OggFileType
from mutagen.mp4 import MP4
import wave
from pathlib import Path
from typing import Dict, Optional, List  # DODAJ 'List' OVDE!


def get_audio_duration(filepath: str) -> Optional[int]:
    """Vrati trajanje audio fajla u sekundama"""
    try:
        path = Path(filepath)
        if not path.exists():
            return None
        
        # Prvo probaj mutagen.File
        audio = mutagen.File(filepath, easy=True)
        if audio is not None:
            return int(audio.info.length)
        
        # Fallback za specifične formate
        suffix = path.suffix.lower()
        
        if suffix == '.mp3':
            return int(MP3(filepath).info.length)
        elif suffix == '.flac':
            return int(FLAC(filepath).info.length)
        elif suffix in ['.ogg', '.oga']:
            return int(OggFileType(filepath).info.length)
        elif suffix in ['.m4a', '.aac', '.mp4']:
            return int(MP4(filepath).info.length)
        elif suffix == '.wav':
            with wave.open(filepath, 'r') as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                return int(frames / rate)
        
        return None
        
    except Exception as e:
        print(f"⚠️ Error reading duration from {filepath}: {e}")
        return None


def format_duration(seconds: Optional[int]) -> str:
    """Formatiraj trajanje u MM:SS format"""
    if seconds is None: 
        return "0:00"
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes}:{seconds:02d}"


def is_audio_file(filepath: str) -> bool:
    """Proveri da li je fajl audio format"""
    audio_extensions = {'.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac', '.oga', '.mp4'}
    return Path(filepath).suffix.lower() in audio_extensions


def get_audio_metadata(filepath: str) -> Dict:
    """Vrati osnovne metadata za audio fajl"""
    try:
        path = Path(filepath)
        if not path.exists():
            return {}
        
        audio = mutagen.File(filepath, easy=True)
        if audio is None:
            return {}
        
        # Default vrednosti
        title = path.stem
        artist = "Unknown"
        album = "Unknown"
        year = ""
        genre = ""
        track = "0"
        
        # Pokušaj da dobiješ metadata
        if hasattr(audio, 'get'):
            title_list = audio.get("title", [title])
            artist_list = audio.get("artist", [artist])
            album_list = audio.get("album", [album])
            date_list = audio.get("date", [year])
            genre_list = audio.get("genre", [genre])
            track_list = audio.get("tracknumber", [track])
            
            title = str(title_list[0]) if title_list else title
            artist = str(artist_list[0]) if artist_list else artist
            album = str(album_list[0]) if album_list else album
            year = str(date_list[0]) if date_list else year
            genre = str(genre_list[0]) if genre_list else genre
            track = str(track_list[0]) if track_list else track
        
        metadata = {
            "title": title,
            "artist": artist,
            "album": album,
            "year": year,
            "genre": genre,
            "track": track,
            "bitrate": getattr(audio.info, 'bitrate', 0) if hasattr(audio, 'info') else 0,
            "sample_rate": getattr(audio.info, 'sample_rate', 0) if hasattr(audio, 'info') else 0,
            "channels": getattr(audio.info, 'channels', 2) if hasattr(audio, 'info') else 2,
            "duration": int(audio.info.length) if hasattr(audio, 'info') and hasattr(audio.info, 'length') else 0,
            "file_size": path.stat().st_size,
            "file_format": path.suffix.lower()[1:] if path.suffix else "unknown"
        }
        
        return metadata
        
    except Exception as e:
        print(f"⚠️ Error reading metadata from {filepath}: {e}")
        return {
            "title": Path(filepath).stem,
            "artist": "Unknown",
            "album": "Unknown",
            "year": "",
            "genre": "",
            "track": "0",
            "bitrate": 0,
            "sample_rate": 0,
            "channels": 2,
            "duration": 0,
            "file_size": Path(filepath).stat().st_size if Path(filepath).exists() else 0,
            "file_format": Path(filepath).suffix.lower()[1:] if Path(filepath).suffix else "unknown"
        }


def get_audio_formats() -> Dict[str, str]:
    """Vrati rečnik podržanih audio formata"""
    return {
        '.mp3': 'MP3 Audio',
        '.wav': 'WAV Audio',
        '.flac': 'FLAC Audio',
        '.ogg': 'Ogg Vorbis',
        '.oga': 'Ogg Audio',
        '.m4a': 'MPEG-4 Audio',
        '.aac': 'AAC Audio',
        '.mp4': 'MPEG-4 Audio',
        '.wma': 'Windows Media Audio',
        '.opus': 'Opus Audio'
    }


def get_file_size_mb(filepath: str) -> float:
    """Vrati veličinu fajla u MB"""
    try:
        size_bytes = Path(filepath).stat().st_size
        return size_bytes / (1024 * 1024)
    except:
        return 0.0


def is_valid_audio_file(filepath: str) -> bool:
    """Proveri da li je fajl validan audio fajl"""
    if not is_audio_file(filepath):
        return False
    
    try:
        # Pokušaj da otvoriš fajl da vidiš da li je validan
        audio = mutagen.File(filepath, easy=True)
        return audio is not None
    except:
        return False


def get_audio_info_summary(filepath: str) -> str:
    """Vrati kratak summary audio fajla"""
    if not Path(filepath).exists():
        return "File not found"
    
    try:
        metadata = get_audio_metadata(filepath)
        duration = format_duration(metadata.get("duration"))
        size_mb = get_file_size_mb(filepath)
        
        info_parts = []
        
        if metadata.get("artist") != "Unknown":
            info_parts.append(f"Artist: {metadata['artist']}")
        
        if metadata.get("title") and metadata['title'] != Path(filepath).stem:
            info_parts.append(f"Title: {metadata['title']}")
        
        info_parts.append(f"Duration: {duration}")
        info_parts.append(f"Format: {metadata.get('file_format', 'Unknown').upper()}")
        info_parts.append(f"Size: {size_mb:.2f} MB")
        
        if metadata.get("bitrate", 0) > 0:
            info_parts.append(f"Bitrate: {metadata['bitrate'] // 1000} kbps")
        
        return " • ".join(info_parts)
        
    except Exception as e:
        return f"Error: {str(e)}"


def scan_audio_files(directory: str) -> List[str]:
    """Skeniraj direktorijum za audio fajlove"""
    audio_files = []
    dir_path = Path(directory)
    
    if not dir_path.exists() or not dir_path.is_dir():
        return audio_files
    
    extensions = list(get_audio_formats().keys())
    
    for ext in extensions:
        # Skeniraj za mala i velika slova ekstenzije
        audio_files.extend([str(f) for f in dir_path.rglob(f"*{ext}")])
        audio_files.extend([str(f) for f in dir_path.rglob(f"*{ext.upper()}")])
    
    return sorted(audio_files, key=lambda x: Path(x).stem.lower())