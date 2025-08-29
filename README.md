# JSON to CSV NFT

This tool was born out of a very real pain point while creating the [**Yesquers NFT Collection**](https://opensea.io/collection/yesquers) 🔥.  
At first, we thought OpenSea required uploading NFT metadata as **JSON**… but then we realized Studio actually expects **one CSV file** with all the traits and references to the uploaded images.  

By that time, we had already generated thousands of NFTs in JSON format (like many other projects do).  
So this program was built to solve that problem — and we’re open-sourcing it hoping it helps anyone else in the same situation. 🙌

- On OpenSea: [Yesquers NFT](https://opensea.io/collection/yesquers)
- Project website: [www.yesquer.page](https://www.yesquer.page)  
- On X: [Yesquers NFT](https://x.com/yesquersnft)

---

## ✨ Features

- Convert a folder of JSON files (one per NFT) into CSV.  
- Convert a single aggregated JSON file (like `_metadata.json` or `metadata.json`) into CSV.  
- Generate one CSV per JSON for debugging, or one aggregated CSV (required for OpenSea Studio).  
- Automatically add a `filename` column mapping rows to your image files (e.g., `1.png`, `2.png`, …).  
- Flexible templates for filenames: `{token_id}.png`, `{stem}.png`, `{image_name}`, etc.  
- Supports custom column subsets, only-traits mode, and optional IPFS gateway prefix for images.  

---

## 🚀 Installation

Clone or download this repository, then make sure you have **Python 3.9+** installed.  
No external libraries are required (only the Python standard library).  

---

## 📂 Folder Mode (multiple JSON files)

If you have a folder `json/` with files like `1.json`, `2.json`, …:

**macOS / Linux / Windows**
```bash
python3 json-to-csv-nft.py --aggregate nfts.csv --filename-col filename --filename-template "{token_id}.png"
```

This will:  
- Read all JSONs from `./json/`  
- Write `./csv/` with one CSV per NFT (debugging)  
- Write one aggregated CSV at `nfts.csv` with all NFTs combined  

---

## 📄 Metadata Mode (single JSON file)

If you already have one big JSON file with all your metadata (for example `metadata.json`), you don’t need the `json/` folder.

**macOS / Linux / Windows**
```bash
python3 json-to-csv-nft.py --metadata metadata.json --filename-col filename --filename-template "{token_id}.png"
```

This will:  
- Read `metadata.json`  
- Write a single output file `metadata.csv`  
- The `filename` column will map `token_id` → `1.png`, `2.png`, …  

Perfect for uploading directly to **OpenSea Studio** alongside your images.

---

## ⚙️ Options

- `--metadata FILE` : Use a single aggregated JSON file (instead of `./json` folder).  
- `--aggregate FILE` : Specify custom name for aggregated CSV (defaults to `metadata.csv` in metadata mode).  
- `--filename-col NAME` : Add a column for filenames (e.g., `filename`).  
- `--filename-template` : Template for filenames (`{token_id}.png`, `{stem}.png`, `{image_name}`, …).  
- `--only-traits` : Export only traits (skip base columns).  
- `--fields ...` : Choose specific base columns (token_id, name, description, image, etc).  
- `--image-prefix URL` : Replace `ipfs://` with a gateway prefix (optional).  

---

## 🖼 Example Output

**Input JSON**
```json
{
  "name": "Yesquer #1",
  "description": "Made by Yesquers for Yesquers",
  "image": "ipfs://<CID>/1.png",
  "edition": 1,
  "external_url": "https://yesquer.page",
  "attributes": [
    { "trait_type": "Background", "value": "Night Time" },
    { "trait_type": "Filter", "value": "Glass" }
  ]
}
```

**Output CSV**
```csv
token_id,name,description,image,external_url,animation_url,background_color,youtube_url,filename,Background,Filter
1,Yesquer #1,Made by Yesquers for Yesquers,ipfs://<CID>/1.png,https://yesquer.page,,,,1.png,Night Time,Glass
```

---

## 💡 Notes

- Always make sure the `filename` column matches exactly the filenames of the images you uploaded (`1.png`, `2.png`, etc).  
- OpenSea Studio requires one single CSV for the collection (with a header row).  
- If in doubt, in Studio click **Download Example** to compare.  

---

## ❤️ Credits

- Built by the [Yesquers NFT](https://opensea.io/collection/yesquers) team.  
- Born out of the moment when we realized:  
  > "We don’t need to upload 2,500 JSON files to OpenSea… we just need 1 CSV."  
- Released open-source so other creators don’t waste hours figuring this out.  

Enjoy, fork, and may your mints be forever smooth! 🌿
