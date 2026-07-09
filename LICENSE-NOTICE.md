# Open Source Licenses and Notices

This project incorporates the following open-source software components. This document serves as the required notice for compliance with their respective licenses, particularly for corporate usage.

## 1. VoxCPM
- **License**: Apache License 2.0
- **Source**: [openbmb/VoxCPM]
- **Modifications**: Pursuant to Section 4(b) of the Apache License 2.0, please note that the original source code has been modified for this project to support advanced streaming and backend integration. The following files were modified:
  - `VoxCPM/src/voxcpm/__init__.py`
  - `VoxCPM/src/voxcpm/core.py`
  - `VoxCPM/src/voxcpm/model/voxcpm.py`
  - `VoxCPM/src/voxcpm/model/voxcpm2.py`
  
  Additionally, new files such as `streaming.py`, `streaming_async.py`, and `text_buffer.py` have been introduced to the `voxcpm` package.
  
All modifications are subject to the terms of the Apache License 2.0. A complete copy of the Apache License 2.0 can be found in the `VoxCPM/LICENSE` file.

## 2. Trendyol-TTS
- **License**: MIT License
- **Source**: [Trendyol/Trendyol-TTS]
- **Description**: A Turkish text-to-speech research model built on top of VoxCPM2. The model weights and inference scripts are used under the MIT License.

## 3. Piper TTS
- **License**: MIT License
- **Description**: A fast, local neural text to speech system. Used for diverse local voice synthesis under the MIT License.

---
*This notice ensures that corporate usage of the aforementioned tools complies with their respective open-source licensing requirements.*
