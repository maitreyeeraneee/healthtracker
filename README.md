# 🏃‍♂️ HealthTracker

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://streamlit.io/"><img src="https://img.shields.io/badge/Streamlit-1.28%2B-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit"></a>
  <a href="https://pandas.pydata.org/"><img src="150F4B?style=for-the-badge&logo=pandas&logoColor=white" alt="Pandas"></a>
  <a href="https://plotly.com/"><img src="https://img.shields.io/badge/Plotly-3.10%2B-3FDCF7?style=for-the-badge&logo=plotly&logoColor=white" alt="Plotly"></a>
  <a href="https://scikit-learn.org/"><img src=" F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white" alt="scikit-learn"></a>
</p>

<p align="center">
  <img src="https://img.shields.io/github/license/Maitreyee/HealthTracker?style=for-the-badge" alt="License">
  <img src="https://img.shields.io/github/stars/Maitreyee/HealthTracker?style=for-the-badge" alt="Stars">
  <img src="https://img.shields.io/github/forks/Maitreyee/HealthTracker?style=for-the-badge" alt="Forks">
  <img src="https://img.shields.io/github/issues/Maitreyee/HealthTracker?style=for-the-badge" alt="Issues">
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-tech-stack">Tech Stack</a> •
  <a href="#-installation">Installation</a> •
  <a href="#-usage">Usage</a> •
  <a href="#-project-structure">Structure</a> •
  <a href="#-future-improvements">Roadmap</a> •
  <a href="#-contributing">Contribute</a> •
  <a href="#-license">License</a>
</p>

---

## 📌 Overview

> A comprehensive **Python-based health tracking application** that helps users log and monitor daily health metrics, nutrition, and wellness data. Built with **Streamlit**, it provides an intuitive web interface for tracking your fitness journey with advanced analytics and smart recommendations.

### ✨ Key Highlights

- 🍽️ **AI-Powered Meal Planning** — Generate personalized 7-day meal plans with smart food swaps
- 📊 **Advanced Analytics** — Interactive charts and visualizations for data-driven decisions
- 💪 **Holistic Tracking** — Monitor nutrition, water intake, weight, and daily streaks
- 🎯 **Personalized Goals** — Custom macro targets based on your body metrics and objectives

---

## 🛠️ Tech Stack

| Layer | Technologies |
|:---:|:---|
| **Language** | ![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat&logo=python) Python 3.8+ |
| **Frontend** | ![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat) Streamlit Web UI |
| **Data Processing** | ![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat) Pandas • ![NumPy](https://img.shields.io/badge/NumPy-013243?style=flat) NumPy |
| **ML/Optimization** | ![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=flat) scikit-learn • ![PuLP](https://img.shields.io/badge/PuLP-2496D0?style=flat) PuLP |
| **Visualization** | ![Plotly](https://img.shields.io/badge/Plotly-3FDCF7?style=flat) Plotly • ![Matplotlib](https://img.shields.io/badge/Matplotlib-11557C?style=flat) Matplotlib |

---

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

```bash
# 1️⃣ Clone the repository
git clone https://github.com/Maitreyee/HealthTracker.git
cd HealthTracker

# 2️⃣ Create a virtual environment
python -m venv venv

# 3️⃣ Activate the environment
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 4️⃣ Install dependencies
pip install -r requirements.txt
```

---

## 🚀 Quick Start

```bash
# Run the application
streamlit run app.py
```

The app will open at **`http://localhost:8501`**

### Getting Started Guide

| Step | Action | Description |
|:---:|:---|:---|
| 1️⃣ | **Set Profile** | Enter age, weight, height, gender in the sidebar |
| 2️⃣ | **Select Goals** | Choose activity level and fitness objective |
| 3️⃣ | **Calculate** | Click "Calculate My Needs" for personalized targets |
| 4️⃣ | **Generate Plan** | Create a 7-day meal plan or start tracking manually |

---

## 📂 Project Structure

```
HealthTracker/
│
├── 📄 app.py                      # Main Streamlit application
├── 📄 constants.py                # Configuration & default values
├── 📄 requirements.txt            # Python dependencies
│
├── 📁 data/                       # Data files
│   ├── nutrition_data_optimized.csv    # Food nutrition database
│   └── tips.csv                       # Daily health tips
│
├── 📁 utils/                      # Core utilities
│   ├── __init__.py               # Package initialization
│   ├── analytics.py              # Charts & visualizations
│   ├── data_loader.py            # Data loading utilities
│   ├── meal_generator.py        # Meal plan generation
│   └── ui_components.py          # Reusable UI components
│
├── 📄 water_tracker.py            # Hydration tracking
├── 📄 weight_tracker.py           # Weight logging & trends
└── 📄 streaks.py                  # Daily streak system
```

---

## 🔮 Future Improvements

### 🤖 AI & Machine Learning
- [ ] AI-powered nutrition recommendations based on eating patterns
- [ ] Predictive analytics for weight change forecasting
- [ ] Food image recognition for instant meal logging

### 📱 User Experience
- [ ] Customizable interactive dashboard with drag-and-drop widgets
- [ ] Native iOS and Android mobile applications
- [ ] Dark/Light theme toggle

### 🌐 Social Features
- [ ] Community fitness challenges
- [ ] Progress sharing to social media
- [ ] Friend leaderboards and competitions

### 🔗 Integrations
- [ ] Wearable device sync (Fitbit, Apple Watch, Garmin)
- [ ] Google Fit & Apple Health integration
- [ ] Barcode scanner for quick food logging

---

## 🤝 Contributing

Contributions are welcome! Follow these steps:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** your changes: `git commit -m 'Add amazing feature'`
4. **Push** to the branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 HealthTracker

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🙏 Acknowledgments

- [Streamlit](https://streamlit.io/) — The fastest way to build data apps
- [Plotly](https://plotly.com/) — Interactive graphing library
- [scikit-learn](https://scikit-learn.org/) — Machine learning in Python
- [Pandas](https://pandas.pydata.org/) — Powerful data structures for data analysis

---

<div align="center">

![----------------------------------------------------](https://capsule-render.vercel.app/api?type=waving&color=gradient&height=80&section=footer)

**Built with ❤️ for a healthier lifestyle**

⭐ Star this repo if you found it useful!

</div>

