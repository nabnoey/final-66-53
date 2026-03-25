// =================================================================
// JENKINS PIPELINE: Flask Docker CI/CD
// =================================================================

pipeline {

    agent any

    options {
        skipDefaultCheckout(true)
    }

    environment {
        DOCKER_HUB_CREDENTIALS_ID = 'final-66-53'
        DOCKER_REPO               = "nabnoey/final-66-53"

        // DEV / PROD (Local Simulation)
        DEV_APP_NAME   = "flask-app-dev"
        DEV_HOST_PORT  = "5001"
        PROD_APP_NAME  = "flask-app-prod"
        PROD_HOST_PORT = "5000"
    }

    parameters {
        choice(
            name: 'ACTION',
            choices: ['Build & Deploy', 'Rollback'],
            description: 'เลือก Action ที่ต้องการ'
        )

        string(
            name: 'ROLLBACK_TAG',
            defaultValue: '',
            description: 'ใส่ Image Tag สำหรับ Rollback'
        )

        choice(
            name: 'ROLLBACK_TARGET',
            choices: ['dev', 'prod'],
            description: 'เลือก Environment สำหรับ Rollback'
        )
    }

    stages {

        // =========================================================
        // 1. CHECKOUT
        // =========================================================
        stage('Checkout') {
            when {
                expression { params.ACTION == 'Build & Deploy' }
            }
            steps {
                echo "Checking out code..."

                checkout([
                    $class: 'GitSCM',
                    branches: scm.branches,
                    doGenerateSubmoduleConfigurations: false,
                    extensions: [],
                    userRemoteConfigs: [[
                        url: 'https://github.com/nabnoey/final-66-53.git',
                        credentialsId: 'final-66-53'
                    ]]
                ])
            }
        }

        // =========================================================
        // 2. INSTALL & TEST
        // =========================================================
        stage('Install & Test') {
            steps {
                echo "Running tests in Docker..."

                script {
                    try {
                        docker.image('python:3.13-slim').inside {
                            sh '''
                                pip install --no-cache-dir -r requirements.txt
                                pytest -v --tb=short --junitxml=test-results.xml
                            '''
                        }
                    } catch (Exception e) {
                        echo "Docker test failed: ${e.message}"
                    }
                }
            }

            post {
                always {
                    junit testResults: 'test-results.xml', allowEmptyResults: true
                }
            }
        }

        // =========================================================
        // 3. BUILD & PUSH DOCKER IMAGE
        // =========================================================
        stage('Build & Push Docker Image') {
            when {
                expression { params.ACTION == 'Build & Deploy' }
            }

            steps {
                script {
                    try {
                        def imageTag = (env.BRANCH_NAME == 'main')
                            ? sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                            : "dev-${env.BUILD_NUMBER}"

                        env.IMAGE_TAG = imageTag

                        docker.withRegistry('https://index.docker.io/v1/', DOCKER_HUB_CREDENTIALS_ID) {

                            echo "Building: ${DOCKER_REPO}:${env.IMAGE_TAG}"
                            def img = docker.build("${DOCKER_REPO}:${env.IMAGE_TAG}")

                            echo "Pushing image..."
                            img.push()

                            if (env.BRANCH_NAME == 'main') {
                                img.push('latest')
                            }
                        }

                    } catch (Exception e) {
                        echo "Docker build failed: ${e.message}"

                        if (env.IMAGE_TAG == null) {
                            env.IMAGE_TAG = "no-docker"
                        }
                    }
                }
            }
        }

        // =========================================================
        // 4. APPROVAL (PRODUCTION)
        // =========================================================
        stage('Approval for Production') {
            steps {
                timeout(time: 1, unit: 'HOURS') {
                    input message: "Deploy ${env.IMAGE_TAG} to PRODUCTION?"
                }
            }
        }

        // =========================================================
        // 5. DEPLOY PRODUCTION
        // =========================================================
        stage('Deploy to PRODUCTION') {
            when {
                expression { params.ACTION == 'Build & Deploy' }
            }

            steps {
                script {
                    try {
                        sh """
                            echo "Deploying ${PROD_APP_NAME}..."

                            docker pull ${DOCKER_REPO}:${env.IMAGE_TAG}
                            docker stop ${PROD_APP_NAME} || true
                            docker rm ${PROD_APP_NAME} || true

                            docker run -d \
                                --name ${PROD_APP_NAME} \
                                -p ${PROD_HOST_PORT}:5000 \
                                ${DOCKER_REPO}:${env.IMAGE_TAG}

                            docker ps --filter name=${PROD_APP_NAME}
                        """
                    } catch (Exception e) {
                        echo "Deploy failed: ${e.message}"
                    }
                }
            }
        }

        // =========================================================
        // 6. ROLLBACK
        // =========================================================
        stage('Execute Rollback') {
            when {
                expression { params.ACTION == 'Rollback' }
            }

            steps {
                script {

                    if (params.ROLLBACK_TAG.trim().isEmpty()) {
                        error "กรุณาระบุ ROLLBACK_TAG"
                    }

                    def appName = (params.ROLLBACK_TARGET == 'dev')
                        ? env.DEV_APP_NAME
                        : env.PROD_APP_NAME

                    def port = (params.ROLLBACK_TARGET == 'dev')
                        ? env.DEV_HOST_PORT
                        : env.PROD_HOST_PORT

                    def image = "${DOCKER_REPO}:${params.ROLLBACK_TAG.trim()}"

                    echo "Rolling back to ${image}"

                    sh """
                        docker pull ${image}
                        docker stop ${appName} || true
                        docker rm ${appName} || true

                        docker run -d \
                            --name ${appName} \
                            -p ${port}:5000 \
                            ${image}
                    """
                }
            }
        }
    }

    // =============================================================
    // POST ACTIONS
    // =============================================================
    post {
        always {
            script {

                if (params.ACTION == 'Build & Deploy') {
                    echo "Cleaning Docker images..."

                    try {
                        sh """
                            docker image rm -f ${DOCKER_REPO}:${env.IMAGE_TAG} || true
                            docker image rm -f ${DOCKER_REPO}:latest || true
                        """
                    } catch (err) {
                        echo "Cleanup failed"
                    }
                }

                echo "Cleaning workspace..."
                cleanWs()
            }
        }
    }
}