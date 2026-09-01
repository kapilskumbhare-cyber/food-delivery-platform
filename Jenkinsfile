pipeline {
    agent any

    stages {

        stage("Checkout") {
            steps {
                 checkout scm
            }
        }

        stage("Install Dependencies") {
            steps {
                sh "pip install -r requirements.txt"
            }
        }

        stage("Test") {
            steps {
               sh "python -m py_compile run.py"
            }
        }

    }
}
