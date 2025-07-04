# Barcode Manager

This is a full-stack web application for managing barcodes. The backend is built with Django and the frontend is built with Vue.js.

## Features

*   **Barcode Generation:** Create and manage barcodes.
*   **User Authentication:** Secure user authentication system with WebAuthn support.
*   **User Profile Management:** Users can edit their profiles.
*   **Style Selection:** Users can choose different styles for the UI.
*   **API:** A RESTful API for interacting with the backend.

## Tech Stack

### Backend

*   [Django](https://www.djangoproject.com/)
*   [Django REST Framework](https://www.django-rest-framework.org/)
*   [Django-cors-headers](https://github.com/adamchainz/django-cors-headers)
*   [WebAuthn](https://pypi.org/project/webauthn/)
*   [PostgreSQL](https://www.postgresql.org/)

### Frontend

*   [Vue.js](https://vuejs.org/)
*   [Vue Router](https://router.vuejs.org/)
*   [Vite](https://vitejs.dev/)
*   [Axios](https://axios-http.com/)
*   [Bootstrap](https://getbootstrap.com/)
*   [Font Awesome](https://fontawesome.com/)

## Getting Started

### Prerequisites

*   Python 3.10+
*   Node.js 20.x
*   PostgreSQL

### Backend Setup

1.  Clone the repository:
    ```bash
    git clone https://github.com/your-username/Barcode_Manager.git
    cd Barcode_Manager/backend
    ```
2.  Create a virtual environment and activate it:
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```
3.  Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Set up the database:
    *   Create a PostgreSQL database.
    *   Copy the `.env.example` file to `.env` and update the database credentials.
5.  Run the database migrations:
    ```bash
    python manage.py migrate
    ```

### Frontend Setup

1.  Navigate to the frontend directory:
    ```bash
    cd ../GitHub_Pages
    ```
2.  Install the dependencies:
    ```bash
    npm install
    ```

## Running the Application

### Backend

To run the backend server, run the following command from the `backend` directory:

```bash
python manage.py runserver
```

The backend server will be running at `http://127.0.0.1:8000`.

### Frontend

To run the frontend development server, run the following command from the `GitHub_Pages` directory:

```bash
npm run dev
```

The frontend development server will be running at `http://localhost:5173`.

## Running Tests

### Backend

To run the backend tests, run the following command from the `backend` directory:

```bash
pytest
```

### Frontend

To run the frontend tests, run the following command from the `GitHub_Pages` directory:

```bash
npm run test
```

## Deployment

The frontend is automatically deployed to GitHub Pages whenever changes are pushed to the `main` branch. The backend needs to be deployed manually.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.