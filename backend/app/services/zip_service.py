import zipfile
import json
from pathlib import Path
from typing import List, Dict, Any

class ZipService:
    """
    Bundles rendered trivia short videos and metadata into a clean ZIP archive.
    """

    def create_batch_zip(
        self,
        video_files: List[Path],
        output_zip_path: Path,
        manifest_data: Dict[str, Any],
    ) -> Path:
        output_zip_path.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # 1. Add manifest summary JSON
            manifest_json_str = json.dumps(manifest_data, indent=2)
            zf.writestr("manifest.json", manifest_json_str)

            # 2. Add each video file
            for video_path in video_files:
                if video_path.is_file():
                    zf.write(video_path, arcname=video_path.name)

        return output_zip_path


zip_service = ZipService()
