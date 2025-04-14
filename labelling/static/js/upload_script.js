function uploadFile() {
    const formData = new FormData();
    const file = document.getElementById('file-input').files[0];
    formData.append("file", file);
  
    // 프로그래스바를 보이도록 설정
    document.getElementById('progress-container').style.display = 'block';
    const progressBar = document.getElementById('progress-bar');
  
    // Fetch API를 사용하여 파일 업로드
    fetch("/upload/", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            // 업로드 완료 후 상태 업데이트
            document.getElementById('upload-status').innerText = data.message;
            document.getElementById('show-result-btn').style.display = 'inline-block';  // 결과 확인 버튼 보이기
        } else {
            document.getElementById('upload-status').innerText = data.error;
        }
  
        // 프로그래스바 숨기기
        document.getElementById('progress-container').style.display = 'none';
    })
    .catch(error => {
        document.getElementById('upload-status').innerText = '업로드 중 오류가 발생했습니다.';
        document.getElementById('progress-container').style.display = 'none';
    });
  }
  
  function uploadText() {
    const formData = new FormData();
    const text = document.getElementById('text-input').value;
    
    if (!text.trim()) {
      alert("텍스트를 입력해주세요.");
      return;
    }
  
    // 텍스트를 파일로 변환
    const blob = new Blob([text], { type: "text/plain" });
    formData.append("file", blob, "uploaded_text.txt");
  
    // 프로그래스바를 보이도록 설정
    document.getElementById('progress-container').style.display = 'block';
    const progressBar = document.getElementById('progress-bar');
  
    // Fetch API를 사용하여 텍스트 파일 업로드
    fetch("/upload/", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            // 업로드 완료 후 상태 업데이트
            document.getElementById('upload-status').innerText = data.message;
            document.getElementById('show-result-btn').style.display = 'inline-block';  // 결과 확인 버튼 보이기
        } else {
            document.getElementById('upload-status').innerText = data.error;
        }
  
        // 프로그래스바 숨기기
        document.getElementById('progress-container').style.display = 'none';
    })
    .catch(error => {
        document.getElementById('upload-status').innerText = '업로드 중 오류가 발생했습니다.';
        document.getElementById('progress-container').style.display = 'none';
    });
  }
  
  function fetchResult() {
    const fileName = document.getElementById('file-name').value;
    fetch(`/result/${fileName}/`)
        .then(response => response.json())
        .then(data => {
            const resultDiv = document.getElementById('results');
            if (data.error) {
                resultDiv.innerText = data.error;
            } else {
                resultDiv.innerText = JSON.stringify(data, null, 2);
            }
        });
  }
  