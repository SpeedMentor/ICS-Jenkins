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
            gcloud auth activate-service-account --key-file="$GCP_KEY_FILE"
            gcloud config set project "${PROJECT_ID}"
            gcloud auth configure-docker "${REGION}-docker.pkg.dev" -q
          '''
        }
      }
    }

    stage('Build & Push Image') {
      steps {
        sh '''
          set -e
          echo "[BUILD] ${IMAGE}"
          docker build -t "${IMAGE}" ./app
          echo "[PUSH] ${IMAGE}"
          docker push "${IMAGE}"
        '''
      }
    }

    stage('Get Kube Credentials') {
      steps {
        sh '''
          set -e
          gcloud container clusters get-credentials "${CLUSTER_NAME}" --zone "${ZONE}"
        '''
      }
    }

    stage('Deploy to GKE') {
      steps {
        sh '''
          set -e
          export IMAGE="${IMAGE}"
          # deployment.yaml içinde image: ${IMAGE} beklenir
          envsubst < k8s/deployment.yaml > "${RENDERED_DEPLOY}"

          kubectl -n "${NAMESPACE}" apply -f "${RENDERED_DEPLOY}"
          kubectl -n "${NAMESPACE}" apply -f k8s/ingress.yaml

          kubectl -n "${NAMESPACE}" annotate deploy/fastapi-demo \
            kubernetes.io/change-cause="Release ${IMAGE}" --overwrite

          kubectl -n "${NAMESPACE}" rollout status deploy/fastapi-demo --timeout=300s
        '''
      }
    }

    stage('Proof (timestamped)') {
      steps {
        sh '''
          set -e
          TS=$(date "+%Y%m%d-%H%M%S")
          EXT_IP=$(kubectl -n "${NAMESPACE}" get ing fastapi-ing -o jsonpath='{.status.loadBalancer.ingress[0].ip}' || true)
          echo "[$(date "+%Y-%m-%d %H:%M:%S%z")] EXT_IP=${EXT_IP}" | tee "deploy-proof-${TS}.log"

          if [ -n "$EXT_IP" ]; then
            curl -s "http://$EXT_IP/"         | tee "app-proof-${TS}.html" >/dev/null
            curl -si "http://$EXT_IP/healthz" | tee "app-health-${TS}.log" >/dev/null
          else
            echo "Ingress IP not ready yet" | tee -a "deploy-proof-${TS}.log"
          fi
        '''
      }
    }
  }

  post {
    always {
      archiveArtifacts artifacts: 'k8s/_rendered-deployment.yaml,**/*.log,**/*.html', onlyIfSuccessful: false
    }
  }
}
