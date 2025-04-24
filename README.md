# Student Results Portal

A web application for displaying student results using Flask and PostgreSQL.

## Prerequisites

- Python 3.8 or higher
- PostgreSQL
- pip (Python package manager)

## Setup Instructions

1. Create a PostgreSQL database:
```sql
CREATE DATABASE student_results;
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. Update the database connection in `app.py`:
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://username:password@localhost/student_results'
```
Replace `username` and `password` with your PostgreSQL credentials.

4. Run the application:
```bash
python app.py
```

5. Open your web browser and navigate to `http://localhost:5000`

## Features

- Student result lookup using name and phone number
- Clean and responsive user interface
- Secure database storage
- Easy to use search functionality

## Database Schema

The application uses two main tables:

1. `student` table:
   - id (Primary Key)
   - name
   - phone_number

2. `result` table:
   - id (Primary Key)
   - subject
   - marks
   - date
   - student_id (Foreign Key)

## Adding Test Data

You can add test data to the database using the PostgreSQL command line or any database management tool. Here's an example:

```sql
-- Insert a student
INSERT INTO student (name, phone_number) VALUES ('John Doe', '1234567890');

-- Insert results for the student
INSERT INTO result (subject, marks, student_id) VALUES 
('Mathematics', 85, 1),
('Science', 90, 1),
('English', 88, 1);
``` 