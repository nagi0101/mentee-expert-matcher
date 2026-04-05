# Event Badge Generator

이 프로젝트는 연수생/엑스퍼트 CSV를 입력받아 이벤트 운영용 인쇄물을 생성합니다.

- 연수생 이름표 HTML/PDF
- 엑스퍼트 이름표 HTML/PDF
- 사회자용 운영표 HTML/PDF
- 테이블 표지 HTML/PDF

HTML은 항상 생성되며, PDF는 기본적으로 WeasyPrint를 우선 사용하고 실패 시 로컬 Edge/Chrome 헤드리스 인쇄를 시도합니다.

## 빠른 시작

### 1. 가상환경 생성

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 샘플 실행

```bash
python src/main.py --trainees data/trainees.sample.csv --experts data/experts.sample.csv
```

또는:

```bash
python -m src.main --trainees data/trainees.sample.csv --experts data/experts.sample.csv
```

실행 후 `output/` 아래에 다음 파일이 생성됩니다.

- `trainee_badges.html`
- `trainee_badges.pdf`
- `expert_badges.html`
- `expert_badges.pdf`
- `host_schedule.html`
- `host_schedule.pdf`
- `table_signs.html`
- `table_signs.pdf`

## 입력 CSV 형식

### `data/trainees.sample.csv`

열:

- `name`
- `org`
- `group`
- `number`

규칙:

- 총 24명이어야 합니다.
- `group`은 `A/B/C/D`만 허용됩니다.
- 각 그룹은 정확히 6명이어야 합니다.
- 각 그룹 내 `number`는 `1~6`을 정확히 한 번씩 가져야 합니다.
- `org` 값은 비어 있어도 됩니다.
- 인코딩은 `UTF-8`, `UTF-8 BOM`, `CP949`, `EUC-KR`를 지원합니다.

예시:

```csv
name,org,group,number
김민수,회사A,A,1
박서연,회사B,A,2
```

### `data/experts.sample.csv`

열:

- `name`
- `org`
- `table`
- `pair_order`

규칙:

- 총원은 최대 12명까지 허용됩니다.
- `table`은 `1~6`만 허용됩니다.
- 각 테이블에는 최대 2명까지 배정할 수 있습니다.
- `pair_order`는 `1` 또는 `2`만 허용되며, 같은 테이블 안에서 중복될 수 없습니다.
- `name`, `org` 값은 비어 있어도 됩니다. `name`이 비어 있는 행은 해당 `pair_order`의 빈 슬롯으로 처리됩니다.
- 인코딩은 `UTF-8`, `UTF-8 BOM`, `CP949`, `EUC-KR`를 지원합니다.

예시:

```csv
name,org,table,pair_order
이수현,AI,1,1
정유진,게임비즈,1,2
```

## 출력 파일 설명

- `trainee_badges.*`: 연수생 카드형 이름표. 이름, 소속, 역할, 코드, 라운드별 이동 테이블 포함
- `expert_badges.*`: 엑스퍼트 카드형 이름표. 이름, 소속/전문분야, 역할, 고정 테이블 칩 포함
- `host_schedule.*`: 사회자용 운영표. 6라운드 전체를 한 장에 압축해 테이블별 연수생 코드/이름과 엑스퍼트 이름 표시
- `table_signs.*`: 가로 A4 4패널 접이식 테이블 사인. 두 끝면을 맞대어 삼각형으로 세울 수 있게 구성

## 스케줄 규칙

연수생 이동 규칙은 아래를 구현합니다. `k`는 각 코호트 내 번호이며 테이블은 `1~6` 모듈로 순환합니다.

- `A(k)`: `k+1, k+2, k+3, k+4, k+5, k`
- `B(k)`: `k, k+4, k+5, k+1, k+2, k+3`
- `C(k)`: `k+1, k, k+4, k+2, k+5, k+3`
- `D(k)`: `k+2, k+3, k, k+4, k+5, k+1`

예:

- `A1 -> T2, T3, T4, T5, T6, T1`

프로그램은 다음 self-check를 실행합니다.

- 각 연수생이 6라운드 동안 테이블 `1~6`을 정확히 1번씩 방문하는지
- 각 라운드의 각 테이블에 연수생이 정확히 4명 배치되는지
- 각 라운드에 24명의 연수생이 중복 없이 정확히 한 번씩 배치되는지

## PDF 생성 실패 시 대체 방법

환경에 따라 WeasyPrint PDF 생성이 실패할 수 있습니다. 이 경우 HTML은 그대로 생성되며 아래 방식으로 인쇄할 수 있습니다.

1. `output/*.html` 파일을 브라우저에서 엽니다.
2. 인쇄 메뉴를 엽니다. (`Ctrl+P` 또는 `Cmd+P`)
3. 대상 프린터를 `PDF로 저장` 또는 실제 프린터로 선택합니다.
4. 용지는 `A4`, 여백은 `기본` 또는 `최소`, 배경 그래픽은 `켜기`를 권장합니다.

프로그램은 WeasyPrint 실패 시 로컬 `Microsoft Edge` 또는 `Google Chrome` 헤드리스 인쇄도 자동으로 시도합니다.

## Windows/macOS 주의사항

- Windows:
  - 일부 환경에서는 WeasyPrint가 시스템 라이브러리 문제로 실패할 수 있습니다.
  - 이 경우 Edge 헤드리스 PDF 생성 또는 브라우저 인쇄를 사용하면 됩니다.
  - 한글 폰트는 `Malgun Gothic`이 있으면 가장 안정적입니다.
- macOS:
  - `Apple SD Gothic Neo` 또는 `Noto Sans KR` 계열 폰트가 있으면 한글 출력이 안정적입니다.
  - 브라우저 인쇄 시 Safari보다 Chrome 계열이 CSS 반영이 더 일관적일 수 있습니다.

## 프로젝트 구조

```text
.
├─ README.md
├─ requirements.txt
├─ data/
│  ├─ trainees.sample.csv
│  └─ experts.sample.csv
├─ src/
│  ├─ __init__.py
│  ├─ main.py
│  ├─ load_data.py
│  ├─ schedule.py
│  ├─ render.py
│  └─ utils.py
├─ templates/
│  ├─ trainee_badges.html.j2
│  ├─ expert_badges.html.j2
│  ├─ host_schedule.html.j2
│  └─ table_signs.html.j2
├─ assets/
│  └─ styles.css
└─ output/
   └─ .gitkeep
```
