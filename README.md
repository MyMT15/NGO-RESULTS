pip3 install -r requirements.txt<!-- Other result content -->

<div style="text-align: right; margin-top: 40px;">
    <div>
        <img src="{{ url_for('static', filename='signature_abs_president.jpg') }}" alt="ABS President Signature" style="height:80px;">
    </div>
    <div>
        <span>Sign. of ABS President</span>
    </div>
</div># Student Results Portal

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

## Deploying to AWS EC2 and Running as a Systemd Service

### 1. Launch and Prepare EC2 Instance
- Launch an Ubuntu EC2 instance (e.g., Ubuntu 22.04 LTS).
- Open ports 22 (SSH), 80 (HTTP), and 3000 (Flask) in your security group.
- SSH into your instance:
  ```sh
  ssh -i /path/to/your-key.pem ubuntu@<EC2-PUBLIC-IP>
  ```
- Install dependencies:
  ```sh
  sudo apt update
  sudo apt install python3-pip python3-venv git -y
  ```

### 2. Clone/Upload Your Project and Set Up Python
- Clone your repo or upload your code.
- Set up a virtual environment and install requirements:
  ```sh
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  ```
- Add your `.env` file if needed.

### 3. Initialize the Database
```sh
python app.py
# (Ctrl+C after first run if running in development)
```

### 4. Create a Gunicorn systemd Service
Create `/etc/systemd/system/studentresults.service`:
```ini
[Unit]
Description=Gunicorn instance to serve Student Results Flask App
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/NGO
Environment="PATH=/home/ubuntu/NGO/venv/bin"
ExecStart=/home/ubuntu/NGO/venv/bin/gunicorn -w 4 -b 0.0.0.0:3000 app:app

[Install]
WantedBy=multi-user.target
```
- Adjust `User`, `WorkingDirectory`, and `Environment` as needed.

### 5. Enable and Start the Service
```sh
sudo systemctl daemon-reload
sudo systemctl start studentresults
sudo systemctl enable studentresults
```

### 6. Check Status and Logs
```sh
sudo systemctl status studentresults
sudo journalctl -u studentresults -f
```

### 7. (Optional) Use Nginx as a Reverse Proxy
- For production, proxy requests from Nginx to Gunicorn for better security and HTTPS support.

---

Now your app will auto-start on boot and restart if it fails. Access it at `http://<EC2-PUBLIC-IP>:3000` or behind Nginx on port 80.