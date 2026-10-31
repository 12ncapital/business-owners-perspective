# The Business Owner's Perspective: Moat Tracker

[ **[日本語版ドキュメントはこちら (README_ja.md)](README_ja.md)** ]

Official Python companion script and financial dataset for the book ***THE BUSINESS OWNER'S PERSPECTIVE***.

This tool extracts and visualizes long-term financial metrics (ROE, DOE, capital allocation) from Japan's Financial Services Agency (FSA) EDINET API (the Japanese counterpart to SEC EDGAR), plotting the trajectory and economic moat expansion of elite Japanese companies in state space.

---

## Directory Structure

```text
business-owners-perspective/
├── appendix_moat_tracker.py   # Visualization script
├── requirements.txt           # Dependency list
├── LICENSE                    # MIT License
├── README.md                  # English documentation (this file)
├── README_ja.md               # Japanese documentation
├── data/                      # 16 elite Japanese companies' multi-year CSV cache
│   ├── moat_data_6857.csv     # Advantest
│   ├── moat_data_8035.csv     # Tokyo Electron
│   ├── moat_data_7011.csv     # Mitsubishi Heavy Industries
│   └── ... (16 tickers in total)
└── output/                    # Generated outputs (HTML / GIF)

```

---

## Quick Start (Offline Mode / No API Key Required)

Pre-cached financial data for the **16 companies** analyzed in the book is included in the `data/` directory. You can run and replicate the state-space animations immediately without issuing an EDINET API key.

### Requirements
* Python 3.10 or higher

### 1. Setup Environment

```bash
git clone https://github.com/12ncapital/business-owners-perspective.git
cd business-owners-perspective

# Create & activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

```

### 2. Run Visualization

```bash
# Example: Focus on Advantest (6857)
python appendix_moat_tracker.py --focus 6857

```

Outputs will be saved directly into the `output/` directory:

* `output/moat_animation_6857.html` (Interactive dynamic plot)
* `output/moat_animation_6857.gif` (Time-series animation)

---

## Advanced: Fetching New Tickers (EDINET API Key Required)

To analyze companies outside the pre-cached 16 tickers or fetch the latest annual reports, an EDINET API key (free) from Japan's FSA is required.

Pass your API key directly via CLI or set it as an environment variable:

```bash
# Direct argument
python appendix_moat_tracker.py --focus 7203 --api-key "YOUR_API_KEY"

# Or using environment variables
export EDINET_API_KEY="YOUR_API_KEY"      # macOS / Linux
$env:EDINET_API_KEY="YOUR_API_KEY"        # Windows PowerShell

python appendix_moat_tracker.py --focus 7203 --force-update

```

---

## Command-Line Arguments Reference

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `--focus` | string | `7011` | Stock ticker to highlight as the primary trajectory (e.g., 7011) |
| `--codes` | string | 16 tickers | Comma-separated tickers for state-space background cohort |
| `--api-key` | string | None | FSA EDINET API Key |
| `--force-update` | flag | off | Bypass local CSV cache and re-fetch from EDINET |
| `--datadir` | path | `data` | Directory for caching and reading financial data |
| `--outdir` | path | `output` | Directory for exported HTML and GIF files |
| `--no-gif` | flag | off | Skip GIF generation (HTML only) |
| `--no-html` | flag | off | Skip HTML generation (GIF only) |

---

## Disclaimer

1. **Not Financial Advice**: The scripts, data, and analytical models provided in this repository are strictly for educational and informational purposes. Nothing herein constitutes investment advice or a solicitation to buy/sell any securities. All investment decisions are solely the responsibility of the individual investor.
2. **Data Accuracy**: Financial metrics are extracted programmatically from disclosure documents via the EDINET API. No warranty is made regarding the completeness, accuracy, or timeliness of the data.
3. **API Changes**: Future specification updates or deprecation by the FSA may affect script behavior. Maintenance or individual issue support is not guaranteed.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.