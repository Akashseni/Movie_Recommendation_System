// Jenkinsfile — full CI/CD pipeline for the Movie Recommendation System
//
// Pipeline shape:
//   Checkout -> Backend (install/lint/test) -> Frontend (install/lint/test/build)
//   -> Build Docker images -> Push to registry -> Deploy -> Smoke test
//
// Per-language stages run inside disposable Docker agents (python:3.12-slim,
// node:20-alpine) so the Jenkins host itself only needs Docker installed —
// no manual Python/Node provisioning on the agent.
//
// Required Jenkins setup (see README.md "Jenkins setup" section):
//   - Plugins: Pipeline, Docker Pipeline, Git, JUnit, HTML Publisher, Credentials Binding
//   - Credential: "dockerhub-creds" (Username with password) for Docker Hub
//   - Credential: "deploy-server-ssh" (SSH key) if deploying to a remote host
//   - Docker installed and running on the Jenkins agent, with the jenkins user
//     in the docker group

pipeline {
    agent any

    options {
        buildDiscarder(logRotator(numToKeepStr: '20'))
        disableConcurrentBuilds()
        timeout(time: 30, unit: 'MINUTES')
    }

    parameters {
        choice(name: 'DEPLOY_ENV', choices: ['staging', 'production'], description: 'Target environment for the Deploy stage')
        booleanParam(name: 'SKIP_DEPLOY', defaultValue: false, description: 'Run CI only, skip the deploy stage')
    }

    environment {
        DOCKERHUB_CREDS   = credentials('dockerhub-creds')
        DOCKERHUB_USER    = "${DOCKERHUB_CREDS_USR}"
        IMAGE_TAG         = "${env.BUILD_NUMBER}-${GIT_COMMIT?.take(7) ?: 'local'}"
        BACKEND_IMAGE     = "${DOCKERHUB_USER}/movie-recsys-backend"
        FRONTEND_IMAGE    = "${DOCKERHUB_USER}/movie-recsys-frontend"
        VITE_API_BASE_URL = "${params.DEPLOY_ENV == 'production' ? 'https://api.movie-recsys.example.com' : 'http://localhost:8000'}"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.GIT_COMMIT_SHORT = sh(script: 'git rev-parse --short HEAD || echo local', returnStdout: true).trim()
                }
            }
        }

        stage('Backend: Install & Lint') {
            agent { docker { image 'python:3.12-slim'; args '-u root'; reuseNode true } }
            steps {
                dir('backend') {
                    sh '''
                        pip install --default-timeout=120 --retries=5 --no-cache-dir -r requirements-dev.txt
                        flake8 app --max-line-length=100 --extend-ignore=E203,W503
                        black --check app tests
                    '''
                }
            }
        }

        stage('Backend: Test') {
            agent { docker { image 'python:3.12-slim'; args '-u root'; reuseNode true } }
            steps {
                dir('backend') {
                    sh '''
                        pip install --default-timeout=120 --retries=5 --no-cache-dir -r requirements-dev.txt
                        pytest tests/ -v --junitxml=test-results.xml --cov=app --cov-report=xml --cov-report=term
                    '''
                }
            }
            post {
                always {
                    junit 'backend/test-results.xml'
                }
            }
        }

        stage('Frontend: Install & Lint') {
            agent { docker { image 'node:20-alpine'; reuseNode true } }
            steps {
                dir('frontend') {
                    sh '''
                        npm install
                        npm run lint
                    '''
                }
            }
        }

        stage('Frontend: Test & Build') {
            agent { docker { image 'node:20-alpine'; reuseNode true } }
            steps {
                dir('frontend') {
                    sh '''
                        npm install
                        npx vitest run --reporter=junit --outputFile=test-results.xml
                        npm run build
                    '''
                }
            }
            post {
                always {
                    junit 'frontend/test-results.xml'
                }
            }
        }

        stage('Build Docker Images') {
            steps {
                dir('backend') {
                    sh "docker build -t ${BACKEND_IMAGE}:${IMAGE_TAG} -t ${BACKEND_IMAGE}:latest ."
                }
                dir('frontend') {
                    sh "docker build --build-arg VITE_API_BASE_URL=${VITE_API_BASE_URL} -t ${FRONTEND_IMAGE}:${IMAGE_TAG} -t ${FRONTEND_IMAGE}:latest ."
                }
            }
        }

        stage('Push to Registry') {
            steps {
                sh '''
                    echo "$DOCKERHUB_CREDS_PSW" | docker login -u "$DOCKERHUB_USER" --password-stdin
                    docker push ${BACKEND_IMAGE}:${IMAGE_TAG}
                    docker push ${BACKEND_IMAGE}:latest
                    docker push ${FRONTEND_IMAGE}:${IMAGE_TAG}
                    docker push ${FRONTEND_IMAGE}:latest
                    docker logout
                '''
            }
        }

        stage('Deploy') {
            when {
                expression { return !params.SKIP_DEPLOY }
            }
            steps {
                sh '''
                    export IMAGE_TAG=${IMAGE_TAG}
                    export DOCKERHUB_USER=${DOCKERHUB_USER}
                    export VITE_API_BASE_URL=${VITE_API_BASE_URL}
                    docker compose -f docker-compose.yml pull
                    docker compose -f docker-compose.yml up -d --remove-orphans
                '''
            }
        }
        stage('Smoke Test') {
            when {
                expression { return !params.SKIP_DEPLOY }
            }
            steps {
                sh '''
                    for i in $(seq 1 10); do
                        if curl -sf http://backend:8000/health; then
                            echo "Backend is healthy"
                            break
                        fi
                        echo "Waiting for backend..."
                        sleep 3
                    done

                    curl -sf http://backend:8000/health
                    curl -sf http://frontend:80/ > /dev/null

                    echo "Smoke tests passed!"
                '''
            }
        }
    }
    post {
        success {
            echo "Build ${env.BUILD_NUMBER} deployed successfully to ${params.DEPLOY_ENV} (tag: ${env.IMAGE_TAG})"
            // slackSend / emailext notification hooks go here
        }
        failure {
            echo "Build ${env.BUILD_NUMBER} failed — check stage logs above"
        }
        always {
            sh 'docker system prune -f --filter "until=24h" || true'
            deleteDir()
        }
    }
}
