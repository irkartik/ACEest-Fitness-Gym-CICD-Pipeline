pipeline {
    agent any

    environment {
        PATH         = "/usr/local/bin:${env.PATH}"
        DOCKER_IMAGE = 'aceest-fitness'
        DOCKER_TAG   = "${env.BUILD_NUMBER}"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup Python Environment') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r app/requirements.txt
                '''
            }
        }

        stage('Quality Gate - Lint') {
            steps {
                sh '''
                    . venv/bin/activate
                    pip install flake8
                    flake8 app/ --max-line-length=120 --statistics --count
                '''
            }
        }

        stage('Quality Gate - Tests') {
            steps {
                sh '''
                    . venv/bin/activate
                    python -m pytest tests/ -v --tb=short --junitxml=reports/test-results.xml
                '''
            }
            post {
                always {
                    junit 'reports/test-results.xml'
                }
            }
        }

        stage('Docker Build') {
            steps {
                sh "docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} -t ${DOCKER_IMAGE}:latest ."
            }
        }
    }

    post {
        success {
            echo "BUILD #${env.BUILD_NUMBER} PASSED - All quality gates cleared. Docker image '${DOCKER_IMAGE}:${DOCKER_TAG}' is ready."
        }
        failure {
            echo "BUILD #${env.BUILD_NUMBER} FAILED - Check stage logs above for details."
        }
        always {
            cleanWs()
        }
    }
}
