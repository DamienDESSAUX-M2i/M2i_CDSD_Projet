import os
from dataclasses import dataclass


@dataclass
class MongoConfig:
    user: str = os.getenv("MONGO_USER", "admin")
    password: str = os.getenv("MONGO_PASSWORD", "admin0000")
    host: str = "localhost"  # os.getenv("MONGO_HOST", "localhost")
    port: int = os.getenv("MONGO_PORT", 27017)
    dbname: str = os.getenv("MONGO_DBNAME", "audio_midi")
    collection_pitch_contour: str = "pitch_contour"
    collection_note_midi: str = "note_midi"
    collection_beat_position: str = "beat_position"
    collection_chord: str = "chord"

    @property
    def connection_string(self) -> str:
        return f"mongodb://{self.user}:{self.password}@{self.host}:{self.port}/"


mongo_config = MongoConfig()
