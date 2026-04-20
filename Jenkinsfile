pipeline {
    agent any

    environment {
        PATH              = "/usr/local/bin:${env.PATH}"
        DOCKERHUB_USER    = 'rajujha373'
        IMAGE_NAME        = 'aceest-fitness-jenkins'
        DOCKER_IMAGE      = "${DOCKERHUB_USER}/${IMAGE_NAME}"
        DOCKER_TAG        = "${env.BUILD_NUMBER}"
        // Jenkins credential ID — add via: Manage Jenkins → Credentials → dockerhub-credentials
        DOCKERHUB_CREDS   = 'dockerhub-credentials'
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
                sh """
                    docker build \
                        -t ${DOCKER_IMAGE}:${DOCKER_TAG} \
                        -t ${DOCKER_IMAGE}:latest \
                        .
                """
            }
        }

        stage('Docker Push') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: "${DOCKERHUB_CREDS}",
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh """
                        echo "${DOCKER_PASS}" | docker login -u "${DOCKER_USER}" --password-stdin
                        docker push ${DOCKER_IMAGE}:${DOCKER_TAG}
                        docker push ${DOCKER_IMAGE}:latest
                        docker logout
                    """
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                sh """
                    export KUBECONFIG=$HOME/.kube/config
                    echo "Using KUBECONFIG: \$KUBECONFIG"
                    kubectl config current-context
                    kubectl set image deployment/aceest-fitness \
                        aceest-fitness=${DOCKER_IMAGE}:${DOCKER_TAG}
                    kubectl rollout status deployment/aceest-fitness --timeout=120s
                """
            }
        }
    }

    post {
        success {
            echo "BUILD #${env.BUILD_NUMBER} PASSED — Image '${DOCKER_IMAGE}:${DOCKER_TAG}' pushed to Docker Hub and deployed."
        }
        failure {
            echo "BUILD #${env.BUILD_NUMBER} FAILED — Running rollback..."
            sh '''
                export KUBECONFIG=$HOME/.kube/config
                kubectl rollout undo deployment/aceest-fitness || true
            '''
        }
        always {
            cleanWs()
        }
    }
}
