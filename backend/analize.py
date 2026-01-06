from google import genai
import time
import json
import os

# 1. 클라이언트 설정
client = genai.Client(api_key="AIzaSyDbvnUhZVmJqwY5uKdkahs48agzagY4KE4")

def analyze_boxing_video_v2_5(video_path):
    print(f"분석 시작: {video_path}")
    
    # 2. 영상 업로드
    print("🚀 구글 서버에 영상 업로드 중...")
    video_file = client.files.upload(file=video_path)
    
    # 3. 처리 대기 (ACTIVE 상태 확인)
    print("⚙️ AI가 영상을 읽는 중입니다", end="")
    while True:
        file_status = client.files.get(name=video_file.name)
        if file_status.state.name == "ACTIVE":
            print("\n✅ 영상 준비 완료!")
            break
        elif file_status.state.name == "FAILED":
            raise Exception("영상 처리 실패")
        print(".", end="", flush=True)
        time.sleep(5)

    # 4. 분석 실행 (사용 가능한 최신 모델 적용)
    print("🥊 gemini-2.5-flash 모델로 정밀 분석 중...")
    
    prompt = """
    당신은 전문 복싱 코치입니다. 영상을 분석하여 다음 JSON 형식으로 응답하세요.
    반드시 화면에 박힌 노란색 타임코드(MM:SS)를 정확히 읽어서 기술해야 합니다.
    
    {
      "summary": "복서의 전반적인 스타일(예: 인파이터, 아웃복서)과 핵심 장단점",
      "feedbacks": [
        {
          "timestamp": "MM:SS",
          "issue": "어떤 동작에서 어떤 실수가 발생했는지 구체적 기술",
          "drill": "이 문제를 해결하기 위한 구체적인 훈련법(수건 끼우기, 쉐도우 등)"
        }
      ],
      "benchmark_boxer": "이 복서가 롤모델로 삼으면 좋은 선수 1~2명",
      "youtube_keyword": "개선을 위해 유튜브에 검색할 최적의 키워드"
    }
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash", # 확인된 목록 중 최적 모델 사용
        contents=[video_file, prompt],
        config={
            "response_mime_type": "application/json"
        }
    )

    # 5. 결과 반환 및 파일 삭제
    result = json.loads(response.text)
    client.files.delete(name=video_file.name)
    return result

# --- 실행부 ---
if __name__ == "__main__":
    target = "c:/boxing_ai/output_final.mp4"
    try:
        analysis = analyze_boxing_video_v2_5(target)
        
        # 결과 화면 출력
        print("\n" + "="*50)
        print("🥊 AI 복싱 분석 리포트 (JSON) 🥊")
        print("="*50)
        print(json.dumps(analysis, indent=2, ensure_ascii=False))
        
        # 파일 저장
        with open("c:/boxing_ai/analysis_result.json", "w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        print("\n✅ 'analysis_result.json' 파일로 저장되었습니다.")

    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")