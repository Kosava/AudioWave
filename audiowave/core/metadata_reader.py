# core/metadata_reader.py
"""
Advanced Metadata Reader - Podrška za sve audio formate
Podržava: MP3 (ID3v2), FLAC, OGG, M4A, WAV, WMA
"""

import mutagen
from mutagen.mp3 import MP3
from mutagen.flac import FLAC, Picture
from mutagen.oggvorbis import OggVorbis
from mutagen.mp4 import MP4, MP4Cover
from mutagen.wave import WAVE
from mutagen.id3 import ID3, APIC
from pathlib import Path
from typing import Dict, Optional, List, Tuple
import base64
from io import BytesIO


class MetadataReader:
    """Napredno čitanje metadata iz audio fajlova"""
    
    def __init__(self):
        self.debug = False
    
    def read_metadata(self, filepath: str) -> Dict:
        """Pročitaj sve metadata iz audio fajla"""
        try:
            path = Path(filepath)
            if not path.exists():
                return self._empty_metadata(filepath, "File not found")
            
            audio = mutagen.File(filepath)
            
            if audio is None:
                return self._empty_metadata(filepath, "Unsupported format")
            
            metadata = {
                'filepath': str(path.absolute()),
                'filename': path.name,
                'file_format': path.suffix.lower()[1:] if path.suffix else 'unknown',
                'file_size': path.stat().st_size,
            }
            
            if hasattr(audio, 'info'):
                metadata.update(self._read_audio_info(audio.info))
            
            metadata.update(self._read_tags(audio, path.suffix.lower()))
            
            artwork_data = self._read_album_art(audio, path.suffix.lower())
            metadata['has_artwork'] = artwork_data is not None
            metadata['artwork_data'] = artwork_data
            
            if self.debug:
                print(f"✅ Read metadata from: {path.name}")
            
            return metadata
            
        except Exception as e:
            if self.debug:
                print(f"❌ Error reading metadata from {filepath}: {e}")
            return self._empty_metadata(filepath, str(e))
    
    def _empty_metadata(self, filepath: str, error: str = "") -> Dict:
        """Vrati prazan metadata dict sa default vrednostima"""
        path = Path(filepath)
        return {
            'filepath': str(path.absolute()) if path.exists() else filepath,
            'filename': path.name if path.exists() else Path(filepath).name,
            'file_format': path.suffix.lower()[1:] if path.suffix else 'unknown',
            'file_size': path.stat().st_size if path.exists() else 0,
            'title': path.stem if path.exists() else 'Unknown',
            'artist': 'Unknown Artist',
            'album': 'Unknown Album',
            'album_artist': '',
            'date': '',
            'genre': '',
            'track': '0',
            'disc': '0',
            'comment': '',
            'composer': '',
            'publisher': '',
            'copyright': '',
            'bpm': '0',
            'lyrics': '',
            'bitrate': 0,
            'sample_rate': 0,
            'channels': 2,
            'duration': 0,
            'has_artwork': False,
            'artwork_data': None,
            'error': error
        }
    
    def _read_audio_info(self, info) -> Dict:
        """Pročitaj tehničke informacije"""
        return {
            'bitrate': getattr(info, 'bitrate', 0),
            'sample_rate': getattr(info, 'sample_rate', 0),
            'channels': getattr(info, 'channels', 2),
            'duration': int(getattr(info, 'length', 0))
        }
    
    def _read_tags(self, audio, file_ext: str) -> Dict:
        """Pročitaj tekstualne tagove"""
        tags = {
            'title': '', 'artist': '', 'album': '', 'album_artist': '',
            'date': '', 'genre': '', 'track': '0', 'disc': '0',
            'comment': '', 'composer': '', 'publisher': '', 'copyright': '',
            'bpm': '0', 'lyrics': ''
        }
        
        if file_ext == '.mp3':
            tags.update(self._read_mp3_tags(audio))
        elif file_ext in ['.flac', '.ogg', '.oga']:
            tags.update(self._read_vorbis_tags(audio))
        elif file_ext in ['.m4a', '.mp4', '.aac']:
            tags.update(self._read_m4a_tags(audio))
        elif file_ext == '.wav':
            tags.update(self._read_wav_tags(audio))
        else:
            tags.update(self._read_generic_tags(audio))
        
        for key in tags:
            if tags[key] is None:
                tags[key] = '' if key not in ['track', 'disc', 'bpm'] else '0'
        
        return tags
    
    def _read_mp3_tags(self, audio) -> Dict:
        """Pročitaj ID3 tagove iz MP3"""
        tags = {}
        
        if hasattr(audio, 'tags') and audio.tags:
            id3 = audio.tags
            
            tags['title'] = self._get_id3_text(id3, 'TIT2')
            tags['artist'] = self._get_id3_text(id3, 'TPE1')
            tags['album'] = self._get_id3_text(id3, 'TALB')
            tags['album_artist'] = self._get_id3_text(id3, 'TPE2')
            
            date = self._get_id3_text(id3, 'TDRC')
            if not date:
                date = self._get_id3_text(id3, 'TYER')
            tags['date'] = str(date) if date else ''
            
            tags['genre'] = self._get_id3_text(id3, 'TCON')
            
            track = self._get_id3_text(id3, 'TRCK')
            tags['track'] = str(track).split('/')[0] if track else '0'
            
            disc = self._get_id3_text(id3, 'TPOS')
            tags['disc'] = str(disc).split('/')[0] if disc else '0'
            
            if 'COMM' in id3:
                comm = id3.get('COMM')
                if comm and len(comm.text) > 0:
                    tags['comment'] = str(comm.text[0])
            
            tags['composer'] = self._get_id3_text(id3, 'TCOM')
            tags['publisher'] = self._get_id3_text(id3, 'TPUB')
            tags['copyright'] = self._get_id3_text(id3, 'TCOP')
            
            bpm = self._get_id3_text(id3, 'TBPM')
            tags['bpm'] = str(bpm) if bpm else '0'
            
            if 'USLT' in id3:
                uslt = id3.get('USLT')
                if uslt and hasattr(uslt, 'text'):
                    tags['lyrics'] = str(uslt.text)
        
        return tags
    
    def _get_id3_text(self, id3, frame_id: str) -> Optional[str]:
        """Izvuci tekst iz ID3 frame-a"""
        try:
            if frame_id in id3:
                frame = id3[frame_id]
                if hasattr(frame, 'text') and len(frame.text) > 0:
                    return str(frame.text[0])
        except:
            pass
        return None
    
    def _read_vorbis_tags(self, audio) -> Dict:
        """Pročitaj Vorbis Comments (FLAC, OGG)"""
        tags = {}
        
        if hasattr(audio, 'tags') and audio.tags:
            vorbis = audio.tags
            
            tags['title'] = self._get_vorbis_tag(vorbis, 'title')
            tags['artist'] = self._get_vorbis_tag(vorbis, 'artist')
            tags['album'] = self._get_vorbis_tag(vorbis, 'album')
            tags['album_artist'] = self._get_vorbis_tag(vorbis, 'albumartist')
            tags['date'] = self._get_vorbis_tag(vorbis, 'date')
            tags['genre'] = self._get_vorbis_tag(vorbis, 'genre')
            
            track = self._get_vorbis_tag(vorbis, 'tracknumber')
            tags['track'] = str(track).split('/')[0] if track else '0'
            
            disc = self._get_vorbis_tag(vorbis, 'discnumber')
            tags['disc'] = str(disc).split('/')[0] if disc else '0'
            
            tags['comment'] = self._get_vorbis_tag(vorbis, 'comment')
            tags['composer'] = self._get_vorbis_tag(vorbis, 'composer')
            tags['publisher'] = self._get_vorbis_tag(vorbis, 'publisher')
            tags['copyright'] = self._get_vorbis_tag(vorbis, 'copyright')
            
            bpm = self._get_vorbis_tag(vorbis, 'bpm')
            tags['bpm'] = str(bpm) if bpm else '0'
            
            tags['lyrics'] = self._get_vorbis_tag(vorbis, 'lyrics')
        
        return tags
    
    def _get_vorbis_tag(self, vorbis, key: str) -> Optional[str]:
        """Izvuci vrednost iz Vorbis tag-a"""
        try:
            if key in vorbis:
                value = vorbis[key]
                if isinstance(value, list) and len(value) > 0:
                    return str(value[0])
                return str(value)
        except:
            pass
        return None
    
    def _read_m4a_tags(self, audio) -> Dict:
        """Pročitaj M4A/MP4/AAC tagove"""
        tags = {}
        
        if hasattr(audio, 'tags') and audio.tags:
            m4a = audio.tags
            
            tags['title'] = self._get_m4a_tag(m4a, '©nam')
            tags['artist'] = self._get_m4a_tag(m4a, '©ART')
            tags['album'] = self._get_m4a_tag(m4a, '©alb')
            tags['album_artist'] = self._get_m4a_tag(m4a, 'aART')
            tags['date'] = self._get_m4a_tag(m4a, '©day')
            tags['genre'] = self._get_m4a_tag(m4a, '©gen')
            
            if 'trkn' in m4a:
                trkn = m4a['trkn']
                if isinstance(trkn, list) and len(trkn) > 0:
                    if isinstance(trkn[0], tuple):
                        tags['track'] = str(trkn[0][0])
                    else:
                        tags['track'] = str(trkn[0])
            
            if 'disk' in m4a:
                disk = m4a['disk']
                if isinstance(disk, list) and len(disk) > 0:
                    if isinstance(disk[0], tuple):
                        tags['disc'] = str(disk[0][0])
                    else:
                        tags['disc'] = str(disk[0])
            
            tags['comment'] = self._get_m4a_tag(m4a, '©cmt')
            tags['composer'] = self._get_m4a_tag(m4a, '©wrt')
            tags['copyright'] = self._get_m4a_tag(m4a, 'cprt')
            
            if 'tmpo' in m4a:
                tmpo = m4a['tmpo']
                if isinstance(tmpo, list) and len(tmpo) > 0:
                    tags['bpm'] = str(tmpo[0])
            
            tags['lyrics'] = self._get_m4a_tag(m4a, '©lyr')
        
        return tags
    
    def _get_m4a_tag(self, m4a, key: str) -> Optional[str]:
        """Izvuci vrednost iz M4A tag-a"""
        try:
            if key in m4a:
                value = m4a[key]
                if isinstance(value, list) and len(value) > 0:
                    return str(value[0])
                return str(value)
        except:
            pass
        return None
    
    def _read_wav_tags(self, audio) -> Dict:
        """Pročitaj WAV INFO tags"""
        tags = {}
        
        if hasattr(audio, 'tags') and audio.tags:
            wav = audio.tags
            tags['title'] = self._get_vorbis_tag(wav, 'title')
            tags['artist'] = self._get_vorbis_tag(wav, 'artist')
            tags['album'] = self._get_vorbis_tag(wav, 'album')
            tags['date'] = self._get_vorbis_tag(wav, 'date')
            tags['genre'] = self._get_vorbis_tag(wav, 'genre')
            tags['comment'] = self._get_vorbis_tag(wav, 'comment')
        
        return tags
    
    def _read_generic_tags(self, audio) -> Dict:
        """Fallback za nepoznate formate"""
        tags = {}
        
        try:
            if hasattr(audio, 'tags') and audio.tags:
                easy_audio = mutagen.File(audio.filename, easy=True)
                if easy_audio:
                    tags['title'] = self._get_easy_tag(easy_audio, 'title')
                    tags['artist'] = self._get_easy_tag(easy_audio, 'artist')
                    tags['album'] = self._get_easy_tag(easy_audio, 'album')
                    tags['date'] = self._get_easy_tag(easy_audio, 'date')
                    tags['genre'] = self._get_easy_tag(easy_audio, 'genre')
                    
                    track = self._get_easy_tag(easy_audio, 'tracknumber')
                    tags['track'] = str(track).split('/')[0] if track else '0'
        except:
            pass
        
        return tags
    
    def _get_easy_tag(self, audio, key: str) -> Optional[str]:
        """Izvuci vrednost iz easy mode tag-a"""
        try:
            if key in audio:
                value = audio[key]
                if isinstance(value, list) and len(value) > 0:
                    return str(value[0])
                return str(value)
        except:
            pass
        return None
    
    def _read_album_art(self, audio, file_ext: str) -> Optional[str]:
        """Pročitaj album art i vrati kao base64"""
        try:
            if file_ext == '.mp3':
                return self._read_mp3_artwork(audio)
            elif file_ext == '.flac':
                return self._read_flac_artwork(audio)
            elif file_ext in ['.m4a', '.mp4', '.aac']:
                return self._read_m4a_artwork(audio)
            elif file_ext in ['.ogg', '.oga']:
                return self._read_ogg_artwork(audio)
        except Exception as e:
            if self.debug:
                print(f"⚠️ Error reading artwork: {e}")
        
        return None
    
    def _read_mp3_artwork(self, audio) -> Optional[str]:
        """Izvuci album art iz MP3 (APIC frame)"""
        if hasattr(audio, 'tags') and audio.tags:
            for tag in audio.tags.values():
                if isinstance(tag, APIC):
                    return base64.b64encode(tag.data).decode('utf-8')
        return None
    
    def _read_flac_artwork(self, audio) -> Optional[str]:
        """Izvuci album art iz FLAC"""
        if hasattr(audio, 'pictures') and len(audio.pictures) > 0:
            picture = audio.pictures[0]
            return base64.b64encode(picture.data).decode('utf-8')
        return None
    
    def _read_m4a_artwork(self, audio) -> Optional[str]:
        """Izvuci album art iz M4A/MP4"""
        if hasattr(audio, 'tags') and audio.tags and 'covr' in audio.tags:
            covers = audio.tags['covr']
            if isinstance(covers, list) and len(covers) > 0:
                return base64.b64encode(bytes(covers[0])).decode('utf-8')
        return None
    
    def _read_ogg_artwork(self, audio) -> Optional[str]:
        """Izvuci album art iz OGG"""
        if hasattr(audio, 'tags') and audio.tags:
            if 'metadata_block_picture' in audio.tags:
                picture_data = audio.tags['metadata_block_picture'][0]
                picture = Picture(base64.b64decode(picture_data))
                return base64.b64encode(picture.data).decode('utf-8')
        return None
    
    def has_tags(self, filepath: str) -> bool:
        """Proveri da li fajl ima tagove"""
        try:
            audio = mutagen.File(filepath)
            return audio is not None and hasattr(audio, 'tags') and audio.tags is not None
        except:
            return False


def read_metadata(filepath: str) -> Dict:
    """Wrapper funkcija"""
    reader = MetadataReader()
    return reader.read_metadata(filepath)


def read_basic_metadata(filepath: str) -> Dict:
    """Pročitaj samo osnovne tagove"""
    reader = MetadataReader()
    metadata = reader.read_metadata(filepath)
    
    return {
        'title': metadata.get('title', 'Unknown'),
        'artist': metadata.get('artist', 'Unknown Artist'),
        'album': metadata.get('album', 'Unknown Album'),
        'duration': metadata.get('duration', 0),
        'filepath': filepath
    }


def has_album_art(filepath: str) -> bool:
    """Brza provjera album art"""
    reader = MetadataReader()
    metadata = reader.read_metadata(filepath)
    return metadata.get('has_artwork', False)


def get_album_art(filepath: str) -> Optional[str]:
    """Vrati samo album art (base64)"""
    reader = MetadataReader()
    metadata = reader.read_metadata(filepath)
    return metadata.get('artwork_data')
