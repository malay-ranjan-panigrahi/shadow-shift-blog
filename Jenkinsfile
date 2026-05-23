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
                withCredentials([usernamePassword(credentialsId: env.GIT_CREDENTIALS_ID, usernameVariable: 'GIT_USER', passwordVariable: 'GIT_PAT')])  {  
                    sh '''
                        # 0. Wipe out any folder left over from previous failed builds
                        rm -rf gitops-repo
                       
                        # 1. Clone the new GitOps repository
                        git clone https://${GIT_USER}:${GIT_PAT}@github.com/malay-ranjan-panigrahi/shadow-shift-gitops.git gitops-repo
                        
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

        stage('Automated AI Health Check & Auto-Rollback') {
            steps {
                echo "⏳ Waiting 45 seconds for ArgoCD to spin up the new pods..."
                sleep 45

                echo "🌐 Firing synthetic traffic to test the new deployment..."
                sh '''
                    # Hit the real endpoint and a fake one to generate log data
                    curl -s http://localhost:80 > /dev/null || true
                    curl -s http://localhost:80/hidden-test-path > /dev/null || true
                '''

                echo "🧠 Triggering AI SRE Agent..."
                sh '''
                    # 1. Create a Python virtual environment for Jenkins and install dependencies
                    python3 -m venv ai-env
                    . ai-env/bin/activate
                    pip install ollama
                    
                    # 2. Dynamically pull logs directly from the Production Deployment
                    kubectl logs deploy/blog-prod -n default --tail=100 > nginx_access.log
                    
                    # 3. Run the AI analysis and capture the output
                    REPORT=$(python3 ai_sre_agent.py)
                    echo "$REPORT"
                    
                    # 4. The Automated Decision Engine
                    if echo "$REPORT" | grep -q "\\[FAIL\\]"; then
                        echo "🚨 AI DETECTED ANOMALIES. INITIATING AUTOMATED ROLLBACK!"
                        
                        cd gitops-repo
                        # Automatically revert the last Git commit
                        git revert --no-edit HEAD
                        git push origin main
                        
                        echo "⏪ GitOps rollback triggered. Failing pipeline."
                        exit 1
                    else
                        echo "✅ AI approved the release. Deployment stabilized."
                    fi
                '''
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