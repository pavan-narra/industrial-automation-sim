pipeline {
    agent any

    environment {
        PYTHON = "python"
        VENV_DIR = "venv"
    }

    stages {
        stage('Checkout') {
            steps {
                echo " Checking out source code..."
                checkout scm
            }
        }

        stage('Setup Environment') {
            steps {
                echo " Creating virtual environment and installing dependencies..."
                bat "${env.PYTHON} -m venv ${env.VENV_DIR}"
                bat ".\\${env.VENV_DIR}\\Scripts\\activate && pip install --upgrade pip pytest pymodbus freeopcua pyyaml"
            }
        }

        stage('Code Quality Check') {
            steps {
                echo " Running static checks..."
                bat ".\\${env.VENV_DIR}\\Scripts\\activate && python -m compileall src/"
            }
        }

        stage('Unit Tests') {
            steps {
                echo " Running unit tests..."
                bat ".\\${env.VENV_DIR}\\Scripts\\activate && pytest -v --junitxml=reports/unit_tests.xml"
            }
            post {
                always {
                    junit 'reports/unit_tests.xml'
                }
            }
        }

        stage('Integration Tests (FAT Simulation)') {
            steps {
                echo " Running simulated FAT tests..."
                bat ".\\${env.VENV_DIR}\\Scripts\\activate && pytest tests/test_pid.py --junitxml=reports/fat_tests.xml"
            }
            post {
                always {
                    junit 'reports/fat_tests.xml'
                }
            }
        }

        stage('Archive & Tag Release') {
            steps {
                echo " Archiving configs and test reports..."
                bat "if not exist artifacts mkdir artifacts"
                bat "copy configs\\* artifacts\\"
                archiveArtifacts artifacts: 'artifacts/**, reports/**', fingerprint: true

                script {
                    def versionTag = "v1.0.${env.BUILD_NUMBER}-FAT"
                    echo " Tagging release as ${versionTag}"
                    bat "git tag ${versionTag}"
                    bat "git push origin ${versionTag}"
                }
            }
        }
    }

    post {
        success {
            echo " Build completed successfully."
        }
        failure {
            echo " Build failed. Check test reports."
        }
    }
}
