pipeline {
    agent any

    stages {

        stage('Checkout SCM') {
            steps {
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    python3 -m venv .venv
                    .venv/bin/pip install --upgrade pip
                    .venv/bin/pip install -r requirements.txt
                '''
            }
        }

        stage('Test') {
            steps {
                echo "test success"
            }
        }
        stage("docker build") {
            steps {
              sh "docker build -t delivery ."
             }
           }
        stage("Docker Tag") {
            steps {
               sh "docker tag delivery kapilkumbhare/delivery:latest"
                }
              } 
        stage("Docker Login") {
          steps {
            withCredentials([
                usernamePassword(
                   credentialsId: '98877e2d-ac2c-462d-a80f-9dee539aff67',
                   usernameVariable: 'DOCKER_USER',
                   passwordVariable: 'DOCKER_PASS'
             )
         ]) {
            sh 'echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin'
            }
         }
      }

        stage("Docker Push") {
           steps {
              sh "docker push kapilkumbhare/delivery:latest"
             }
         }

        stage("Deploy") {
            steps {
                sh "docker compose pull"
                sh "docker compose up -d"
             }
          }
    }
}
