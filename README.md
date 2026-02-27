# Peer-to-Peer Study Group Agent - Backend

## Setup
1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the API
```bash
python app.py
```

## Endpoints
- `POST /add_student`: Add a student. JSON body: `{ "name": "...", "skill": 5, "weakness": 2 }`
- `GET /get_students`: List all students.
- `POST /generate_groups`: Run the clustering algorithm and return groups.
