# OneDrive POS System

## Overview

Welcome to the **OneDrive POS System**! This powerful inventory management system is specifically designed for car part retail shops, providing a seamless and efficient way to manage your inventory, sales,  With OneDrive POS, you can streamline your operations, enhance customer satisfaction, and drive your business to new heights.

## Key Features

- **User -Friendly Interface**: Intuitive design that makes it easy for staff to navigate and manage inventory.
- **Real-Time Inventory Tracking**: Keep track of stock levels in real-time, ensuring you never run out of essential car parts.
- **Sales Management**: Effortlessly process sales transactions, generate invoices, and manage customer payments.
- **Comprehensive Reporting**: Generate detailed reports on sales, inventory levels, and customer activity to make informed business decisions..
- **Multi-User  Access**: Allow multiple staff members to access the system with customizable permissions.
- **Cloud Integration**: Store your data securely in the cloud, ensuring accessibility from anywhere and protection against data loss.

## Installation

To get started with the OneDrive POS System, follow these steps:

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/starktate1904/onedrive-ims.git

2. **Navigate to the driectory**:
   cd onedrive_pos

   
3. **Create Python Enviroment**:
   ```bash
   python -m venv Env

4. **Activate the scripts in the Env directory**:
   ```bash
   cd Env
   Scripts\activate
   
5. **install requirement**:
   cd ..
   cd onedrive_pos
   pip install -r requirments.txt

6. **Make Migrations and Migrate**:
  py manage.py makemigrations
  py manage.py migrate

7. **Create Superuser**:
   py manage.py createsuperuser
   save the user details youll need them to create categories in the admin panel

8. **Runserver**:
   py manage.py runserver
   navigate to the http://127.0.0.0.1:8000/admin
   enter the superuser credentials 
navigate to the categories and add categories

9. **Admin Role**:
   in the admin panel navigate to the user model
select the user
scroll down to the role field and select admin
then you ae good to go

http://127.0.0.0.1:8000/
login as admin








   


   
