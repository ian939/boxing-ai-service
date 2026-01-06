from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from google import genai
import subprocess
import os
import shutil
import json
import time
import os
from dotenv import load_dotenv
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()

# 1. CORS 설정 (나중에 프론트엔드와 연결하기 위해 필수)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 폴더 설정
BASE_DIR = "c:/boxing_ai"
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
PROCESSED_DIR = os.path.join(BASE_DIR, "processed")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

# 정적 파일 서버 설정 (웹 브라우저에서 변환된 영상을 볼 수 있게 함)
app.mount("/processed", StaticFiles(directory=PROCESSED_DIR), name="processed")

# --- 내부 처리 함수들 ---

def add_timecode(input_path, output_path):
    """FFmpeg을 사용하여 노란색 타임코드를 삽입합니다."""
    font_path = "C\\:/Windows/Fonts/arial.ttf"
    drawtext_filter = (
        f"drawtext=fontfile='{font_path}': "
        "text='%{pts\\:gmtime\\:0\\:%M\\\\\\:%S}': "
        "x=w-tw-50: y=50: fontcolor=yellow: fontsize=100: box=1: boxcolor=black@0.5"
    )
    command = [
        'ffmpeg', '-i', input_path,
        '-vf', drawtext_filter,
        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '28',
        '-c:a', 'copy', '-y', output_path
    ]
    subprocess.run(command, check=True)

def analyze_video(video_path):
    """Gemini 2.5 Flash를 사용하여 영상을 분석하고 JSON을 반환합니다."""
    # 업로드
    video_file = client.files.upload(file=video_path)
    
    # 대기
    while True:
        status = client.files.get(name=video_file.name)
        if status.state.name == "ACTIVE": break
        time.sleep(5)
    
    # 분석
    prompt = "당신은 전문 복싱 코치입니다. 영상의 타임코드를 읽고 동작을 분석하여 JSON으로만 응답하세요."
    # (프롬프트 내용은 이전과 동일하게 유지)
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[video_file, prompt],
        config={"response_mime_type": "application/json"}
    )
    
    result = json.loads(response.text)
    client.files.delete(name=video_file.name) # 서버 용량 관리
    return result

# --- API 엔드포인트 ---

@app.post("/analyze")
async def analyze_endpoint(file: UploadFile = File(...)):
    try:
        # 1. 원본 파일 저장
        input_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 2. 타임코드 삽입 (전처리)
        processed_filename = f"pro_{file.filename}"
        output_path = os.path.join(PROCESSED_DIR, processed_filename)
        add_timecode(input_path, output_path)
        
        # 3. AI 분석
        report = analyze_video(output_path)
        
        # 4. 결과 반환
        return {
            "video_url": f"http://localhost:8000/processed/{processed_filename}",
            "report": report
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
