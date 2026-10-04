pipeline {

    agent any

    environment {
        VERCEL_TOKEN = credentials('vercel-token')
    }

    stages {

        stage('Checkout') {
            steps {
                echo '======================================'
                echo 'Checking out source code'
                echo '======================================'

                checkout scm
            }
        }

        stage('Setup Python') {
            steps {
                echo '======================================'
                echo 'Setting up Python 3.12 environment'
                echo '======================================'

                bat '''
                    if exist venv rmdir /s /q venv

                    py -3.12 -m venv venv

                    venv\\Scripts\\python.exe --version

                    venv\\Scripts\\python.exe -m pip install --upgrade pip

                    venv\\Scripts\\python.exe -m pip install -r requirements.txt
                '''
            }
        }

        stage('Run Tests') {
            steps {
                echo '======================================'
                echo 'Running automated tests'
                echo '======================================'

                bat '''
                    venv\\Scripts\\python.exe -m pytest
                '''
            }
        }

        stage('Validate Flask Application') {
            steps {
                echo '======================================'
                echo 'Validating Flask application'
                echo '======================================'

                bat '''
                    venv\\Scripts\\python.exe -c "from app import app; print('Flask application loaded successfully')"
                '''
            }
        }

        stage('Deploy to Vercel') {
            steps {
                echo '======================================'
                echo 'Deploying to Vercel Production'
                echo '======================================'

                bat '''
                    npx --yes vercel deploy --prod --yes --token=%VERCEL_TOKEN%
                '''
            }
        }
    }

    post {

        success {
            echo '======================================'
            echo 'CI/CD PIPELINE SUCCESSFUL'
            echo 'Vercel deployment completed successfully'
            echo '======================================'
        }

        failure {
            echo '======================================'
            echo 'CI/CD PIPELINE FAILED'
            echo 'Vercel deployment was NOT completed'
            echo '======================================'
        }

        always {
            echo 'Jenkins pipeline finished.'
        }
    }
}