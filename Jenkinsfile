pipeline {
    agent any

    environment {
       
        DOCKER_CREDENTIALS_ID = 'docker-hub-creds'
        GIT_CREDENTIALS_ID    = 'github-creds'
        
        // my Docker Hub Image configuration
        DOCKER_IMAGE          = 'malaynew07/shadow-shift-blog'
        IMAGE_TAG             = "v1.0.${env.BUILD_NUMBER}" 
    }

    stages {
        stage('Checkout Code') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                echo "🐳 Building Docker Image: ${DOCKER_IMAGE}:${IMAGE_TAG}..."
                sh "docker build -t ${DOCKER_IMAGE}:${IMAGE_TAG} ."
            }
        }

        stage('Push to Docker Registry') {
            steps {
                echo "🚀 Pushing Image to DockerHub..."
                withCredentials([usernamePassword(credentialsId: env.DOCKER_CREDENTIALS_ID, usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh "echo \$DOCKER_PASS | docker login -u \$DOCKER_USER --password-stdin"
                    sh "docker push ${DOCKER_IMAGE}:${IMAGE_TAG}"
                }
            }
        }

        stage('Update Helm Manifests (GitOps Handoff)') {
            steps {
                echo "✍️ Cloning GitOps repo and updating values.yaml..."
                withCredentials([usernamePassword(credentialsId: env.GIT_CREDENTIALS_ID, usernameVariable: 'GIT_USER', passwordVariable: 'GIT_PAT')]) {
                    sh '''
                        # 1. Clone the new GitOps repository into a temporary folder
                        git clone https://${GIT_USER}:${GIT_PAT}@github.com/malaynew07/shadow-shift-gitops.git gitops-repo
                        
                        # 2. Enter the folder and configure Git for Jenkins
                        cd gitops-repo
                        git config user.email "jenkins@shadow-shift.local"
                        git config user.name "Jenkins CI"
                        
                        # 3. Update the image tag in the values.yaml file using sed
                        sed -i "s/tag: .*/tag: ${IMAGE_TAG}/g" helm/blog-site/values.yaml
                        
                        # 4. Commit and push back to GitHub
                        git add helm/blog-site/values.yaml
                        git commit -m "ci: update image tag to ${IMAGE_TAG} [skip ci]"
                        git push origin main
                    '''
                }
            }
        }
    }
    
    post {
        success {
            echo "✅ Pipeline Succeeded! ArgoCD will now deploy the new image."
        }
        failure {
            echo "❌ Pipeline Failed. Check the Jenkins console logs."
        }
    }
}
