<!--
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                              🏃‍♂️ HealthTracker                               ║
║                    Professional Health Tracking Application                  ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
-->

<div align="center">

<!-- ══════════════════════════════════════════════════════════════════════════ -->
<!--                                BADGES                                      -->
<!-- ══════════════════════════════════════════════════════════════════════════ -->

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-blue?style=for-the-badge)]()

<br/>
<!-- ══════════════════════════════════════════════════════════════════════════ -->
<!--                                HEADER                                      -->
<!-- ══════════════════════════════════════════════════════════════════════════ -->

<br/>
# 🏃‍♂️ HealthTracker

### Your Personal AI-Powered Health & Nutrition Companion

*A comprehensive Python-based health tracking application for monitoring nutrition, fitness, and wellness metrics with advanced analytics.*

<br/>

[📖 Overview](#overview) • [✨ Features](#features) • [🛠️ Tech Stack](#tech-stack) • [📦 Installation](#installation) • [🚀 Usage](#usage) • [📂 Structure](#project-structure) • [🤝 Contributing](#contributing) • [👤 Author](#author)

<br/>

</div>

---

## 📖 Overview

HealthTracker is a powerful, interactive health and nutrition tracking application built with **Python** and **Streamlit**. It helps users monitor daily health metrics, generate personalized meal plans using optimization algorithms, and track their fitness progress over time with beautiful visualizations.

### 🎯 What It Does

| Capability | Description |
|:-----------|:------------|
| 📊 **Body Metrics** | BMI, BMR, TDEE, body fat %, lean mass calculations |
| 🍽️ **Meal Planning** | AI-powered 7-day personalized meal plans |
| 💧 **Health Tracking** | Water intake, weight logging, daily streaks |
| 📈 **Analytics** | Interactive charts, trends, progress tracking |

### 💡 Portfolio Project Demonstrates

This project showcases proficiency in:

| Skill Area | Technologies Used |
|:-----------|:------------------|
| 🐍 **Python Development** | Clean code, OOP, data structures, algorithms |
| 🌐 **Web Development** | Streamlit web framework, responsive UI |
| 📊 **Data Science** | Pandas, NumPy for data processing |
| 📈 **Visualization** | Plotly, Matplotlib for interactive charts |
| 🤖 **Machine Learning** | scikit-learn for predictive features |
| ⚙️ **Optimization** | PuLP for mathematical meal planning optimization |

---

## ✨ Features

### 📊 Health Metrics Dashboard

- **BMI Calculator** — Instant Body Mass Index calculation with health categorization
- **BMR & TDEE** — Basal Metabolic Rate and Total Daily Energy Expenditure
- **Body Composition** — Body fat percentage, lean body mass, ideal weight calculations
- **Macro Targets** — Personalized protein, carbs, and fat goals based on objectives

### 🍽️ Intelligent Meal Planning

- **7-Day Meal Plan Generator** — Personalized weekly meal plans tailored to user goals
- **Smart Food Swaps** — AI-powered food substitutions for variety and nutrition
- **Dietary Preferences** — Support for Vegetarian and Vegan diets
- **Allergy Filtering** — Exclude allergens from meal plans

### 📈 Analytics & Visualization

- **Daily Trends** — Interactive charts for daily nutrition tracking
- **Weekly Summaries** — Comprehensive weekly nutrition breakdowns
- **Macro Distribution** — Pie charts showing macro ratios
- **Protein Tracking** — Line plots for protein intake trends
- **Progress Bars** — Visual progress towards daily targets

### 💧 Holistic Health Tracking

- **Water Intake** — Track daily hydration with visual progress
- **Weight Tracking** — Log and visualize weight changes over time
- **Streak System** — Daily tracking streaks for motivation

---

## 🛠️ Tech Stack

| Category | Technology |
|:---------|:-----------|
| **Language** | Python 3.8+ |
| **Web Framework** | Streamlit |
| **Data Processing** | Pandas, NumPy |
| **Machine Learning** | scikit-learn |
| **Optimization** | PuLP |
| **Visualization** | Plotly, Matplotlib |

---

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Step-by-Step Setup

```bash
# STEP 1: Clone the Repository
git clone https://github.com/Maitreyee/HealthTracker.git
cd HealthTracker

# STEP 2: Create Virtual Environment
python -m venv venv

# STEP 3: Activate Environment
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# STEP 4: Install Dependencies
pip install -r requirements.txt

# STEP 5: Run the Application
streamlit run app.py
```

---

## 🚀 Usage

### Starting the Application

```bash
streamlit run app.py
```

The application will open in your browser at **`http://localhost:8501`**

### Getting Started Guide

| Step | Action | What to Do |
|:----:|:-------|:-----------|
| 1️⃣ | **Set Profile** | Enter age, weight, height, gender in sidebar |
| 2️⃣ | **Choose Goal** | Select activity level & fitness objective |
| 3️⃣ | **Calculate** | Click "Calculate My Needs" for personalized targets |
| 4️⃣ | **Track** | Generate meal plan or start manual tracking |

---

## 📂 Project Structure

```
HealthTracker/
│
├── app.py                      # Main Streamlit application
├── constants.py                # Configuration constants
├── requirements.txt            # Python dependencies
│
├── data/                       # Data directory
│   ├── nutrition_data_optimized.csv   # Food nutrition database
│   └── tips.csv                       # Health tips
│
├── utils/                      # Utility modules
│   ├── __init__.py            # Package initialization
│   ├── analytics.py           # Chart & visualization functions
│   ├── data_loader.py         # Data loading utilities
│   ├── meal_generator.py     # Meal plan generation logic
│   └── ui_components.py       # Reusable UI components
│
├── water_tracker.py           # Water intake tracking
├── weight_tracker.py          # Weight tracking
└── streaks.py                 # Daily streak system
```

### File Descriptions

| File | Purpose |
|:-----|:--------|
| `app.py` | Main application entry point with UI and routing |
| `constants.py` | Configuration constants (BMI categories, macro ratios, activity multipliers) |
| `requirements.txt` | Python dependencies |
| `utils/analytics.py` | Plotly chart generation for visualizations |
| `utils/data_loader.py` | CSV and database loading utilities |
| `utils/meal_generator.py` | Meal plan generation using optimization algorithms |
| `utils/ui_components.py` | Reusable Streamlit UI components |
| `water_tracker.py` | Water intake tracking module |
| `weight_tracker.py` | Weight logging and trend visualization |
| `streaks.py` | Daily tracking streak system |

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

```bash
# 1. Fork the repository
# Click the "Fork" button on GitHub

# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/HealthTracker.git
cd HealthTracker

# 3. Create a feature branch
git checkout -b feature/amazing-feature

# 4. Make your changes
# - Follow the existing code style
# - Add tests if applicable
# - Update documentation

# 5. Commit and push
git add .
git commit -m 'Add amazing feature'
git push origin feature/amazing-feature

# 6. Open a Pull Request
```

---

## 👤 Author

<div align="center">

### Maitreyee

| Contact | Link |
|:--------|:-----|
| 🐙 **GitHub** | [@Maitreyee](https://github.com/maitreyeeraneee) |
| 💼 **LinkedIn** | [Maitreyee](https://www.linkedin.com/in/maitreyeerane/) |

---

**Python Developer | Data Science Enthusiast | Open Source Contributor**

</div>

---

<div align="center">

![----------------------------------------------------](https://capsule-render.vercel.app/api?type=waving&color=gradient&height=80&section=footer)

<br/>

### ⭐ Star this repo if you found it useful!!

<br/>

**Built with ❤️ using Python & Streamlit**

</div>

