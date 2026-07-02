# Texture Pipeline Studio

Texture Pipeline Studio is a Blender add-on that streamlines PBR texture management for production workflows. It automatically assigns PBR texture sets from organized resolution-based folders and allows artists to switch between texture LODs (Levels of Detail) without manually reconnecting image textures.

---

## Features

- Automatic PBR texture assignment from organized resolution folders.
- Fast texture LOD switching (8K, 4K, 2K, 1K, etc.).
- Automatic node updates for compatible materials.
- Integrated into Blender's **Scene Properties** panel.
- Designed for production-ready asset libraries.
- Reduces repetitive material setup and speeds up workflows.

---

## Installation

1. Download the latest release.
2. Open **Blender**.
3. Go to **Edit → Preferences → Add-ons**.
4. Click **Install...**
5. Select the downloaded ZIP file.
6. Enable **Texture Pipeline Studio**.

---

## Usage

1. Organize your textures into resolution-based folders.
2. Open **Scene Properties → Texture Pipeline Studio**.
3. Select your texture library.
4. Assign textures to materials.
5. Switch between available texture resolutions whenever needed.

---

## Expected Folder Structure

```
texture maps/
├── 8k/
│   ├── Wood/
│   │   ├── Wood_BaseColor.png
│   │   ├── Wood_Normal.png
│   │   ├── Wood_Roughness.png
│   │   └── ...
│   └── Metal/
├── 4k/
├── 2k/
└── 1k/
```

---

## Compatibility

- Blender 4.5+
- Windows

---

## License

This project is licensed under the **GNU GPL v3.0 or later**.

---

## Report Issues

If you encounter a bug or would like to request a feature, please use the GitHub **Issues** page.

https://github.com/maddumagegihan51/texture_pipeline_studio/issues
