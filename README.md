**한국어** | [English](README_en.md)

# Unity Asset Text Searcher

Unity 게임의 에셋 파일과 DLL 파일에서 텍스트를 검색하는 도구입니다.

## 기능

- **Unity 에셋 검색**: TextAsset, MonoBehaviour 등에서 텍스트 검색
- **DLL 검색**: .NET DLL 파일의 문자열 리터럴 검색 (Mono.Cecil 사용)
- **자동 Unity 버전 감지**: globalgamemanagers 파일에서 Unity 버전 자동 추출
- **다양한 출력 형식**: TXT 요약 + CSV 상세 결과

## 설치

### 릴리즈 다운로드
[Releases](../../releases) 페이지에서 최신 버전을 다운로드하세요.

### 직접 실행 (Python)
```bash
pip install UnityPy pythonnet
python Unity_searcher.py
```

## 사용법

### 기본 사용
1. `Unity_Searcher.exe`를 게임의 루트 폴더 또는 `_Data` 폴더에 복사
2. `Mono.Cecil.dll`도 같은 위치에 복사 (DLL 검색 기능 사용 시)
3. 실행 후 검색할 텍스트 입력

### 명령줄 옵션
```
Unity_searcher.py [-h] [-v UNITY_VERSION] [-s SEARCH] [-d DIRECTORY] [--no-dll]

옵션:
  -h, --help            도움말 표시
  -v, --unity-version   Unity 버전 지정 (예: -v "2022.3.15f1")
  -s, --search          검색할 텍스트 (미지정 시 입력 프롬프트)
  -d, --directory       검색 디렉토리 (기본: 현재 디렉토리, 게임 루트 또는 _Data 폴더)
  --no-dll              DLL 검색 건너뛰기
```

### 예시
```bash
# 기본 실행 (대화형)
Unity_Searcher.exe

# 검색어와 디렉토리 지정
Unity_Searcher.exe -s "Hello World" -d "C:\Games\MyGame\MyGame_Data"

# Unity 버전 수동 지정
Unity_Searcher.exe -v "2021.3.0f1" -s "검색어"

# DLL 검색 제외
Unity_Searcher.exe -s "텍스트" --no-dll
```

## 출력 파일

검색 완료 후 다음 파일들이 생성됩니다:

| 파일 | 설명 |
|------|------|
| `output_[검색어].txt` | 검색 결과 요약 (TXT) |
| `output_assets_[검색어].csv` | 에셋 검색 결과 (CSV) |
| `output_dll_[검색어].csv` | DLL 검색 결과 (CSV) |

### CSV 형식

**에셋 결과 (output_assets_*.csv)**
| 컬럼 | 설명 |
|------|------|
| file_path | 파일 경로 |
| assets_name | 에셋 이름 |
| path_id | Path ID |
| type_name | 오브젝트 타입 |
| obj_name | 오브젝트 이름 |

**DLL 결과 (output_dll_*.csv)**
| 컬럼 | 설명 |
|------|------|
| file_path | 파일 경로 |
| class_name | 클래스 이름 |
| method_name | 메서드 이름 |
| text | 발견된 텍스트 |

## 요구사항

### 실행 파일 (exe)
- Windows 10/11
- `Mono.Cecil.dll` (DLL 검색 기능 사용 시)

### Python 직접 실행
- Python 3.8+
- UnityPy
- pythonnet (Mono.Cecil 사용을 위해)

## 주의사항

- Unity 버전을 자동 감지하지 못하는 경우 `-v` 옵션으로 수동 지정하세요
- `Mono.Cecil.dll`이 없으면 DLL 검색 기능이 비활성화됩니다
- 대용량 게임의 경우 검색에 시간이 걸릴 수 있습니다

## 라이선스

MIT License

## 크레딧

- Made by **Snowyegret**
- [UnityPy](https://github.com/K0lb3/UnityPy) - Unity 에셋 파싱
- [Mono.Cecil](https://github.com/jbevain/cecil) - .NET DLL 분석
