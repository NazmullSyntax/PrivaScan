## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- Windows, macOS, or Linux
- ~500 MB of disk space

### 5-Step Installation

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/privascan.git
cd privascan

# 2. Create a virtual environment
python -m venv venv

# Activate it:
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download the spaCy language model
python -m spacy download en_core_web_sm

# 5. Run the app
streamlit run 0_🏠_Home.py
