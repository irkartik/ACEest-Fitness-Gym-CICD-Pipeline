# ACEest Fitness and Gym

A desktop GUI application for ACEest Functional Fitness, built with Python and Tkinter. Displays workout and nutrition plans for different fitness programs.

## Prerequisites

- Python 3.12+
- Tkinter (included with most Python installations)

## Local Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/<your-username>/ACEest-Fitness-Gym-CICD-Pipeline.git
   cd ACEest-Fitness-Gym-CICD-Pipeline
   ```

2. **Create and activate a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # macOS / Linux
   venv\Scripts\activate      # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r app/requirements.txt
   ```

4. **Run the application**
   ```bash
   python -m app.main
   ```

## Running Tests

```bash
python -m pytest tests/ -v
```

## Project Structure

```
├── app/
│   ├── main.py            # Application entry point
│   └── requirements.txt   # Python dependencies
├── tests/                 # Pytest test suite
└── Screenshots/           # App screenshots
```
