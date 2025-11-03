# AI Homecam Solution: Risk Detection with Google Gemini API

## 프로젝트 개요
이 프로젝트는 Google Gemini API의 멀티모달(Multimodal) 분석 능력을 활용하여 영상 속 인물의 행동을 분석하고 '넘어짐', '낙상', '발작'과 같은 잠재적 위험 상황을 감지하는 웹 애플리케이션입니다. 사용자가 비디오 파일을 업로드하면, 백엔드 서버가 이를 프레임 단위로 분할하여 Google Cloud Storage(GCS)에 저장하고, Gemini API를 통해 분석한 후 결과를 프론트엔드에 표시합니다.

## 주요 기능
*   **비디오 업로드:** 사용자가 웹 인터페이스를 통해 비디오 파일을 업로드할 수 있습니다.
*   **비디오 미리보기:** 업로드된 비디오를 웹 페이지에서 미리 볼 수 있습니다.
*   **프레임 추출:** 백엔드에서 업로드된 비디오에서 주요 프레임을 자동으로 추출합니다.
*   **Google Cloud Storage 연동:** 추출된 프레임을 Google Cloud Storage에 안전하게 저장하고 관리합니다.
*   **Google Gemini API 분석:** GCS에 저장된 프레임들을 Gemini API (`models/gemini-2.5-flash` 모델)에 전송하여 위험 상황(넘어짐, 낙상, 발작 등)을 감지합니다.
*   **분석 결과 표시:** Gemini API의 분석 결과를 한국어로 명확하게 요약하여 프론트엔드에 표시합니다. (예: "떨어짐 또는 쓰러짐 감지됨 위험도: 높음")
*   **임시 파일 및 GCS 객체 정리:** 분석 완료 후 생성된 임시 파일 및 GCS 객체를 자동으로 삭제하여 리소스를 효율적으로 관리합니다.

## 기술 스택
*   **백엔드:** Python, Flask
*   **프론트엔드:** HTML, CSS, JavaScript
*   **클라우드 서비스:** Google Cloud Platform (Google Gemini API, Google Cloud Storage)
*   **비디오 처리:** OpenCV (Python `cv2` 라이브러리)

## 설정 및 실행 방법

### 1. Google Cloud Platform 설정
이 애플리케이션을 실행하려면 Google Cloud Platform 프로젝트가 필요합니다.
1.  **Google Cloud 프로젝트 생성:** [Google Cloud Console](https://console.cloud.google.com/)에서 새 프로젝트를 생성하거나 기존 프로젝트를 선택합니다.
2.  **API 활성화:** 다음 API를 활성화해야 합니다.
    *   **Vertex AI API** (Gemini API 사용을 위해 필요)
    *   **Cloud Storage API** (비디오 프레임 저장을 위해 필요)
3.  **서비스 계정 키 생성 (선택 사항, Cloud Shell 사용 시 불필요):**
    *   로컬 환경에서 실행하는 경우, 서비스 계정 키를 생성하고 환경 변수 `GOOGLE_APPLICATION_CREDENTIALS`에 키 파일 경로를 설정해야 합니다. Cloud Shell에서는 자동으로 인증됩니다.
4.  **Cloud Storage 버킷 생성:**
    *   프로젝트 내에 새로운 Cloud Storage 버킷을 생성합니다. 버킷 이름은 `.env` 파일에 설정할 `GCS_BUCKET_NAME`과 동일해야 합니다. (예: `sesac-pkm80688068ig-video-frames`)

### 2. Gemini API 키 설정
1.  [Google AI Studio](https://aistudio.google.com/app/apikey)에서 Gemini API 키를 생성합니다.
2.  생성된 API 키를 기록해 둡니다.

### 3. 프로젝트 설정

1.  **프로젝트 클론:**
    ```bash
    git clone [YOUR_REPOSITORY_URL]
    cd ai_homecam_solution
    ```
    (현재 작업 중인 환경에서는 이 단계를 건너뛰고 `ai_homecam_solution` 디렉토리로 이동합니다.)

2.  **Python 가상 환경 설정 (권장):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Python 종속성 설치:**
    ```bash
    pip install -r requirements.txt
    ```
    `requirements.txt` 파일이 없는 경우, 다음 명령으로 수동으로 설치합니다:
    ```bash
    pip install Flask python-dotenv google-cloud-aiplatform google-generativeai google-cloud-storage opencv-python Flask-Cors
    ```

4.  **.env 파일 생성:**
    `ai_homecam_solution/backend/` 디렉토리에 `.env` 파일을 생성하고 다음 내용을 추가합니다.
    ```
    GOOGLE_CLOUD_PROJECT_ID=YOUR_PROJECT_ID
    GOOGLE_CLOUD_LOCATION=YOUR_CLOUD_REGION # 예: us-central1
    GEMINI_API_KEY=YOUR_GEMINI_API_KEY
    GCS_BUCKET_NAME=YOUR_GCS_BUCKET_NAME # 예: sesac-pkm80688068ig-video-frames
    ```
    `YOUR_PROJECT_ID`, `YOUR_CLOUD_REGION`, `YOUR_GEMINI_API_KEY`, `YOUR_GCS_BUCKET_NAME`을 실제 값으로 대체하십시오.

### 4. 애플리케이션 실행

1.  **백엔드 서버 실행:**
    `ai_homecam_solution/backend/` 디렉토리에서 다음 명령을 실행합니다:
    ```bash
    python3 app.py
    ```
    서버가 `http://0.0.0.0:8080`에서 실행됩니다. Cloud Shell을 사용하는 경우, 웹 미리보기 기능을 통해 접근해야 합니다.

2.  **프론트엔드 접속:**
    *   Cloud Shell을 사용하는 경우, Cloud Shell 인터페이스 상단의 "웹 미리보기" 버튼을 클릭하고 "포트 8080에서 미리보기"를 선택합니다.
    *   새로운 브라우저 탭이 열리면, 해당 URL (예: `https://8080-cs-aac234d0-52b1-401b-8754-d07064d260e3.cs-asia-east1-duck.cloudshell.dev/`)로 이동합니다. 이 URL은 `index.html` 파일을 직접 제공합니다.
    *   로컬에서 실행하는 경우, 웹 브라우저에서 `http://localhost:8080/`으로 접속합니다.

### 5. 애플리케이션 테스트
1.  프론트엔드 페이지에서 "Choose File" 버튼을 클릭하여 비디오 파일을 선택합니다.
2.  "Analyze Video" 버튼을 클릭하여 비디오 분석을 시작합니다.
3.  분석이 완료되면 "Analysis Results" 섹션에 감지 결과가 한국어로 표시됩니다.

## 향후 개선 사항
*   **실시간 비디오 분석:** 웹캠 또는 스트리밍 비디오 소스에서 실시간으로 프레임을 캡처하고 분석하는 기능.
*   **알림 시스템:** 위험 상황 감지 시 사용자에게 이메일, SMS 또는 기타 알림을 전송하는 기능.
*   **데이터베이스 연동:** 분석 이력 및 감지된 위험 상황 데이터를 저장하고 관리하는 기능.
*   **사용자 인증 및 권한:** 다중 사용자 환경을 위한 인증 및 권한 부여 시스템.
*   **UI/UX 개선:** 사용자 친화적인 인터페이스 및 경험 개선.
