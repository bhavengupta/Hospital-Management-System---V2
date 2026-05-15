<h1 align="center">🏥 Hospital Management System</h1>

<p align="center">
A scalable and feature-rich Hospital Management System built using modern full-stack technologies to streamline hospital operations, improve patient management, and automate healthcare workflows efficiently.
</p>

<hr>

<h2>📌 Overview</h2>

<p>
The Hospital Management System is a full-stack web application designed to digitize and optimize hospital management processes including patient records, appointment scheduling, doctor workflows, report generation, and automated notifications.
</p>

<p>
The project focuses on building a responsive, secure, and high-performance healthcare platform using Flask-based REST APIs and Vue.js frontend architecture.
</p>

<hr>

<h2>🚀 Features</h2>

<h3>👨‍⚕️ Patient Management</h3>

<ul>
  <li>Patient registration and authentication</li>
  <li>Digital medical history management</li>
  <li>Appointment booking and scheduling</li>
  <li>Access to downloadable medical reports</li>
</ul>

<h3>🩺 Doctor Workflow System</h3>

<ul>
  <li>Doctor dashboard and appointment handling</li>
  <li>Monthly report generation</li>
  <li>Patient diagnosis and treatment records</li>
  <li>Medical history tracking</li>
</ul>

<h3>🏢 Admin Panel</h3>

<ul>
  <li>Manage doctors, patients, and appointments</li>
  <li>Role-based access control</li>
  <li>Monitor hospital operations efficiently</li>
  <li>System-wide data management</li>
</ul>

<h3>🔔 Notification System</h3>

<ul>
  <li>Automated appointment reminder emails</li>
  <li>Background job scheduling using Celery</li>
  <li>SMTP testing integration using MailHog</li>
</ul>

<h3>⚡ Performance Optimization</h3>

<ul>
  <li>Redis caching for frequently accessed data</li>
  <li>Reduced database load and faster API responses</li>
  <li>Asynchronous task execution for better scalability</li>
</ul>

<h3>🔒 Security</h3>

<ul>
  <li>Session-based authentication using Flask-Session</li>
  <li>Role-based authorization (Admin / Doctor / Patient)</li>
  <li>Secure REST API architecture</li>
</ul>

<hr>

<h2>🛠️ Tech Stack</h2>

<h3>Frontend</h3>

<ul>
  <li>Vue.js</li>
  <li>Bootstrap</li>
  <li>JavaScript</li>
  <li>HTML5</li>
  <li>CSS3</li>
</ul>

<h3>Backend</h3>

<ul>
  <li>Flask</li>
  <li>RESTful APIs</li>
  <li>Flask-Session</li>
</ul>

<h3>Database & Caching</h3>

<ul>
  <li>Redis</li>
  <li>MySQL / SQLite / PostgreSQL</li>
</ul>

<h3>Background Processing</h3>

<ul>
  <li>Celery</li>
  <li>Redis Broker</li>
</ul>

<h3>Tools & Platforms</h3>

<ul>
  <li>Git & GitHub</li>
  <li>MailHog</li>
  <li>VS Code</li>
</ul>

<hr>

<h2>📂 Project Structure</h2>

<pre>
Hospital-Management-System/
│
├── backend/
│   ├── routes/
│   ├── models/
│   ├── services/
│   ├── tasks/
│   └── app.py
│
├── frontend/
│   ├── components/
│   ├── views/
│   └── assets/
│
├── redis/
├── reports/
├── requirements.txt
├── README.md
└── docker-compose.yml
</pre>

<hr>

<h2>⚙️ Installation</h2>

<h3>1️⃣ Clone the Repository</h3>

<pre>
git clone https://github.com/your-username/hospital-management-system.git
</pre>

<h3>2️⃣ Navigate to the Project Directory</h3>

<pre>
cd hospital-management-system
</pre>

<h3>3️⃣ Install Backend Dependencies</h3>

<pre>
pip install -r requirements.txt
</pre>

<h3>4️⃣ Install Frontend Dependencies</h3>

<pre>
npm install
</pre>

<h3>5️⃣ Start Redis Server</h3>

<pre>
redis-server
</pre>

<h3>6️⃣ Start Celery Worker</h3>

<pre>
celery -A app.celery worker --loglevel=info
</pre>

<h3>7️⃣ Run Flask Backend</h3>

<pre>
python app.py
</pre>

<h3>8️⃣ Run Vue Frontend</h3>

<pre>
npm run serve
</pre>

<hr>

<h2>💻 Core Functionalities</h2>

<ul>
  <li>RESTful API integration between frontend and backend</li>
  <li>Session-based authentication system</li>
  <li>Dynamic appointment scheduling</li>
  <li>Automated email reminders</li>
  <li>Background task processing</li>
  <li>Redis caching and optimization</li>
  <li>Report generation and downloads</li>
  <li>Role-based dashboards</li>
</ul>

<hr>

<h2>📊 System Architecture</h2>

<pre>
Vue.js Frontend
       ↓
Flask REST APIs
       ↓
Authentication & Business Logic
       ↓
Redis Cache + SQL Database
       ↓
Celery Background Workers
       ↓
MailHog SMTP Notifications
</pre>

<hr>

<h2>📸 Screenshots</h2>

<p>
Add screenshots of:
</p>

<ul>
  <li>Login Page</li>
  <li>Dashboard</li>
  <li>Appointment System</li>
  <li>Doctor Panel</li>
  <li>Patient Reports</li>
  <li>Admin Panel</li>
</ul>

<hr>

<h2>🔮 Future Enhancements</h2>

<ul>
  <li>AI-based disease prediction</li>
  <li>Video consultation integration</li>
  <li>Real-time chat support</li>
  <li>Online payment gateway</li>
  <li>Mobile application support</li>
  <li>Cloud deployment using Docker & Kubernetes</li>
</ul>

<hr>

<h2>📄 License</h2>

<p>
This project is licensed under the MIT License.
</p>

<hr>

<h2>👨‍💻 Author</h2>

<p>
Developed by <b>Bhaven Gupta</b>
</p>

<p>
If you found this project useful, consider giving it a ⭐ on GitHub.
</p>
