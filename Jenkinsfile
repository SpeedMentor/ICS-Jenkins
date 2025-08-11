pipeline {
  agent any
  options { timestamps() }

  environment {
    VERSION  = """v${new Date().format('yyyyMMdd-HHmmss', TimeZone.getTimeZone('UTC'))}"""
    REGISTRY = "${params.REGION}-docker.pkg.dev/${params.PROJECT_ID}/${params.REPO_NAME}"
    IMAGE    = "${REGISTRY}/${params.IMAGE_NAME}:${VERSION}"
    USE_GKE_GCLOUD_AUTH_PLUGIN = "True"
    RENDERED_DEPLOY = "k8s/_rendered-deployment.yaml"
  }

  stages {
    stage('Checkout') {
      steps { checkout scm }
    }

    stage('GCloud Auth') {
      steps {
        withCredentials([file(credentialsId: 'gcp-sa-key', variable: 'GCP_KEY_FILE')]) {
          sh '''
            set -e
            TS=$(date "+%Y%m%d-%H%M%S")
            echo "[$(date "+%Y-%m-%d %H:%M:%S%z")] gcloud auth start" | tee "auth-${TS}.log"
            gcloud auth activate-service-account --key-file="$GCP_KEY_FILE" | tee -a "auth-${TS}.log"
            gcloud config set project "${PROJECT_ID}" | tee -a "auth-${TS}.log"
            gcloud auth configure-docker "${REGION}-docker.pkg.dev" -q | tee -a "auth-${TS}.log"
          '''
        }
      }
    }

    stage('Build & Push Image') {
      steps {
        sh '''
          set -e
          TS=$(date "+%Y%m%d-%H%M%S")
          echo "[$(date "+%Y-%m-%d %H:%M:%S%z")] BUILD ${IMAGE}" | tee "build-${TS}.log"
          docker build -t "${IMAGE}" ./app 2>&1 | tee -a "build-${TS}.log"
          echo "[$(date "+%Y-%m-%d %H:%M:%S%z")] PUSH ${IMAGE}" | tee "push-${TS}.log"
          docker push "${IMAGE}" 2>&1 | tee -a "push-${TS}.log"
        '''
      }
    }

    stage('Get Kube Credentials') {
      steps {
        sh '''
          set -e
          TS=$(date "+%Y%m%d-%H%M%S")
          echo "[$(date "+%Y-%m-%d %H:%M:%S%z")] get-credentials ${CLUSTER_NAME}/${ZONE}" | tee "kube-${TS}.log"
          gcloud container clusters get-credentials "${CLUSTER_NAME}" --zone "${ZONE}" 2>&1 | tee -a "kube-${TS}.log"
        '''
      }
    }

    stage('Deploy to GKE') {
      steps {
        sh '''
          set -e
          TS=$(date "+%Y%m%d-%H%M%S")
          echo "[$(date "+%Y-%m-%d %H:%M:%S%z")] render deployment with IMAGE=${IMAGE}" | tee "deploy-${TS}.log"
          export IMAGE="${IMAGE}"
          envsubst < k8s/deployment.yaml > "${RENDERED_DEPLOY}"

          echo "[$(date "+%Y-%m-%d %H:%M:%S%z")] kubectl apply deployment" | tee -a "deploy-${TS}.log"
          kubectl -n "${NAMESPACE}" apply -f "${RENDERED_DEPLOY}" 2>&1 | tee -a "deploy-${TS}.log"

          echo "[$(date "+%Y-%m-%d %H:%M:%S%z")] kubectl apply ingress" | tee -a "deploy-${TS}.log"
          kubectl -n "${NAMESPACE}" apply -f k8s/ingress.yaml 2>&1 | tee -a "deploy-${TS}.log"

          echo "[$(date "+%Y-%m-%d %H:%M:%S%z")] annotate change-cause" | tee -a "deploy-${TS}.log"
          kubectl -n "${NAMESPACE}" annotate deploy/fastapi-demo \
            kubernetes.io/change-cause="Release ${IMAGE}" --overwrite 2>&1 | tee -a "deploy-${TS}.log"

          echo "[$(date "+%Y-%m-%d %H:%M:%S%z")] rollout status" | tee -a "deploy-${TS}.log"
          kubectl -n "${NAMESPACE}" rollout status deploy/fastapi-demo --timeout=300s 2>&1 | tee -a "deploy-${TS}.log"
        '''
      }
    }

    stage('Proof (timestamped outputs)') {
      steps {
        sh '''
          set -e
          TS=$(date "+%Y%m%d-%H%M%S")
          echo "[$(date "+%Y-%m-%d %H:%M:%S%z")] fetching Ingress IP" | tee "proof-${TS}.log"
          EXT_IP=$(kubectl -n "${NAMESPACE}" get ing fastapi-ing -o jsonpath='{.status.loadBalancer.ingress[0].ip}' || true)
          echo "EXT_IP=${EXT_IP}" | tee -a "proof-${TS}.log"

          if [ -n "$EXT_IP" ]; then
            echo "[$(date "+%Y-%m-%d %H:%M:%S%z")] curl /" | tee -a "proof-${TS}.log"
            curl -s "http://$EXT_IP/"         | tee "app-proof-${TS}.html" >/dev/null
            echo "[$(date "+%Y-%m-%d %H:%M:%S%z")] curl /healthz" | tee -a "proof-${TS}.log"
            curl -si "http://$EXT_IP/healthz" | tee "app-health-${TS}.log" >/dev/null
          else
            echo "Ingress IP not ready yet" | tee -a "proof-${TS}.log"
          fi
        '''
      }
    }
  }

  post {
    always {
      archiveArtifacts artifacts: 'k8s/_rendered-deployment.yaml,*.log,*.html', onlyIfSuccessful: false
    }
  }
}
